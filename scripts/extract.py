import asyncio
import json
from pathlib import Path
from typing import TypedDict

import pandas as pd
from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup, Comment
from langchain_core.runnables import RunnableSerializable
from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError as PydanticValidationError
import logging

import ai as ai_module
import models
# Import the prompts for each of our langchain nodes steps
from prompts import (
    CATEGORY_SYSTEM,
    CATEGORY_USER,
    RETRY_CATEGORY_APPEND,
    PRODUCT_SYSTEM,
    PRODUCT_USER,
    RETRY_PRODUCT_APPEND,
)

logger = logging.getLogger(__name__)

router = APIRouter() 


EXTRACT_MODEL = "openai/gpt-5-nano"
MAX_RETRIES = 5
LLM_COST_LIMIT_USD = 5.0
DATA_OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "data_out.csv"
KEY_COLUMN = "filename"


# ---- Graph state: single context for the whole extraction flow ----
class ExtractState(TypedDict, total=False):
    """State for the extraction graph. Holds context and retry state."""
    html_content: str
    html_filtered: str
    source_filename: str | None
    category: models.Category | None
    category_retry_error: str | None
    category_attempt: int
    product: models.Product | None
    product_retry_error: str | None
    product_attempt: int
    llm_cost_so_far: float
    llm_cost_limit: float
    cost_exceeded: bool
    model: str | None  # override EXTRACT_MODEL when set (e.g. for testing)


def _sanitize_csv_cell(val: str | float | None) -> str:
    """Ensure a CSV cell has no newlines so one logical row = one physical line."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return s.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")


class OpenRouterCategoryExtractor(RunnableSerializable[dict, models.Category]):
    """Extract Category from HTML (Google Product Taxonomy). Uses ai.responses → _log_usage."""

    model: str = EXTRACT_MODEL

    def invoke(self, input: dict, **kwargs) -> models.Category:
        return asyncio.run(self.ainvoke(input, **kwargs))

    async def ainvoke(self, input: dict, **kwargs) -> models.Category:
        html = input["html"]
        model = input.get("model") or self.model
        retry_error = input.get("retry_error")
        user = CATEGORY_USER.format(html=html)
        if retry_error:
            user += RETRY_CATEGORY_APPEND.format(retry_error=retry_error)
        messages = [
            {"role": "system", "content": CATEGORY_SYSTEM},
            {"role": "user", "content": user},
        ]
        result, cost = await ai_module.responses(
            model,
            messages,
            text_format=models.Category,
        )
        return (result, cost)


class OpenRouterProductExtractor(RunnableSerializable[dict, models.Product]):
    """Extract full Product from HTML with category fixed. Uses ai.responses → _log_usage."""

    model: str = EXTRACT_MODEL

    def invoke(self, input: dict, **kwargs) -> models.Product:
        return asyncio.run(self.ainvoke(input, **kwargs))

    async def ainvoke(self, input: dict, **kwargs) -> models.Product:
        html = input["html"]
        model = input.get("model") or self.model
        category_name = input["category_name"]
        retry_error = input.get("retry_error")
        user = PRODUCT_USER.format(html=html, category_name=category_name)
        if retry_error:
            user += RETRY_PRODUCT_APPEND.format(retry_error=retry_error, category_name=category_name)
        messages = [
            {"role": "system", "content": PRODUCT_SYSTEM},
            {"role": "user", "content": user},
        ]
        result, cost = await ai_module.responses(
            model,
            messages,
            text_format=models.Product,
        )
        return (result, cost)


category_runnable = OpenRouterCategoryExtractor()
product_runnable = OpenRouterProductExtractor()


# ---- Graph nodes: each updates shared state (context + retries) ----
async def _prepare_context(state: ExtractState) -> dict:
    """Build filtered HTML and initialize retry counters."""
    soup = BeautifulSoup(state["html_content"], "html.parser")
    html_filtered = filter_html(soup)
    return {
        "html_filtered": html_filtered,
        "category_attempt": 0,
        "product_attempt": 0,
        "llm_cost_so_far": 0.0,
    }


async def _extract_category_node(state: ExtractState) -> dict:
    """Extract category; on validation error set retry_error and bump attempt. Enforces LLM cost limit."""
    limit = state.get("llm_cost_limit", LLM_COST_LIMIT_USD)
    if state.get("llm_cost_so_far", 0) >= limit:
        return {"cost_exceeded": True}

    inp = {"html": state["html_filtered"], "model": state.get("model") or EXTRACT_MODEL}
    if state.get("category_retry_error"):
        inp["retry_error"] = state["category_retry_error"]
    try:
        category, cost = await category_runnable.ainvoke(inp)
        new_total = state.get("llm_cost_so_far", 0) + cost
        if new_total > limit:
            return {"llm_cost_so_far": new_total, "cost_exceeded": True}
        return {"category": category, "category_retry_error": None, "llm_cost_so_far": new_total}
    except PydanticValidationError as e:
        attempt = state.get("category_attempt", 0) + 1
        return {"category_retry_error": str(e), "category_attempt": attempt}


async def _extract_product_node(state: ExtractState) -> dict:
    """Extract product with fixed category; on validation error set retry_error and bump attempt. Enforces LLM cost limit."""
    limit = state.get("llm_cost_limit", LLM_COST_LIMIT_USD)
    if state.get("llm_cost_so_far", 0) >= limit:
        return {"cost_exceeded": True}

    category = state["category"]
    inp = {"html": state["html_filtered"], "category_name": category.name, "model": state.get("model") or EXTRACT_MODEL}
    if state.get("product_retry_error"):
        inp["retry_error"] = state["product_retry_error"]
    try:
        product, cost = await product_runnable.ainvoke(inp)
        new_total = state.get("llm_cost_so_far", 0) + cost
        if new_total > limit:
            return {"llm_cost_so_far": new_total, "cost_exceeded": True}
        return {"product": product, "product_retry_error": None, "llm_cost_so_far": new_total}
    except PydanticValidationError as e:
        attempt = state.get("product_attempt", 0) + 1
        return {"product_retry_error": str(e), "product_attempt": attempt}


def _write_output_node(state: ExtractState) -> dict:
    """Upsert row to CSV if source_filename is set. No state change."""
    filename = state.get("source_filename")
    product = state.get("product")
    if filename and product:
        _upsert_row(filename, product)
    return {}


def _after_category(state: ExtractState) -> str:
    """Route: success -> product, retry -> category, max retries -> end, cost exceeded -> end."""
    if state.get("cost_exceeded"):
        return "__end__"
    category = state.get("category")
    # Check if the category is valid
    if category is not None:
        try:
            # Use the validator to check if the category is valid
            models.Category.validate_name_exists(category.name)
            return "extract_product"
        except ValueError:
            pass  # name not in categories.txt, retry or end below
    # If the category is not valid, retry if we haven't exceeded the max retries or end with error
    if state.get("category_attempt", 0) >= MAX_RETRIES:
        return "__end__"
    # If the category is not valid, retry the category extraction
    return "extract_category"


def _after_product(state: ExtractState) -> str:
    """Route: success -> write_output, retry -> product, max retries -> end, cost exceeded -> end."""
    if state.get("cost_exceeded"):
        return "__end__"
    product = state.get("product")
    # Check if the product is valid
    if product is not None:
        try:
            # Use the base pydantic model_validate to check if the product is on the schema
            models.Product.model_validate(product.model_dump())
            return "write_output"
        except PydanticValidationError:
            pass  # schema validation failed, retry or end below
    # If the product is not valid, retry if we haven't exceeded the max retries or end with error
    if state.get("product_attempt", 0) >= MAX_RETRIES:
        return "__end__"
    # If the product is not valid, retry the product extraction
    return "extract_product"


# Extraction graph (visual):
#
#                    START
#                      │
#                      ▼
#              prepare_context
#                      │
#                      ▼
#              extract_category
#                      │
#         ┌────────────┼────────────┐
#         │            │            │
#         ▼            ▼            ▼
#  extract_product  extract_category  END
#  (valid category) (retry category)  (max retries)
#         │
#         ▼
#   extract_product
#         │
#    ┌────┼────┐
#    │    │    │
#    ▼    ▼    ▼
# write_output  extract_product  END
# (valid product) (retry product) (max retries)
#     │
#     ▼
#    END
#
_extraction_graph = StateGraph(ExtractState)
_extraction_graph.add_node("prepare_context", _prepare_context)
_extraction_graph.add_node("extract_category", _extract_category_node)
_extraction_graph.add_node("extract_product", _extract_product_node)
_extraction_graph.add_node("write_output", _write_output_node)
_extraction_graph.add_edge(START, "prepare_context")
_extraction_graph.add_edge("prepare_context", "extract_category")
_extraction_graph.add_conditional_edges("extract_category", _after_category, path_map={
    "extract_product": "extract_product",
    "extract_category": "extract_category",
    "__end__": END,
})
_extraction_graph.add_conditional_edges("extract_product", _after_product, path_map={
    "write_output": "write_output",
    "extract_product": "extract_product",
    "__end__": END,
})
_extraction_graph.add_edge("write_output", END)
extraction_graph = _extraction_graph.compile()




def _product_to_csv_row(product: models.Product, filename: str) -> dict:
    """Build a flat row for CSV from Product and filename (key). All cells sanitized to one line per row."""
    p = product.model_dump()
    price = p.get("price", {})
    category = p.get("category", {})
    variants = p.get("variants") or []
    raw = {
        KEY_COLUMN: filename,
        "name": p.get("name", ""),
        "brand": p.get("brand", ""),
        "category": category.get("name", ""),
        "price": price.get("price"),
        "currency": price.get("currency", ""),
        "compare_at_price": price.get("compare_at_price"),
        "description": (p.get("description", "") or "")[:500],
        "key_features": "|".join(p.get("key_features") or []),
        "image_urls": "|".join((p.get("image_urls") or [])[:10]),
        "video_url": p.get("video_url") or "",
        "colors": "|".join(p.get("colors") or []),
        "variants": json.dumps(variants) if variants else "",
    }
    return {k: _sanitize_csv_cell(v) for k, v in raw.items()}


def _upsert_row(filename: str, product: models.Product) -> None:
    """Append or overwrite row in data_out.csv by filename (key). Uses pandas."""
    DATA_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = _product_to_csv_row(product, filename)
    column_order = list(row.keys())

    try:
        if DATA_OUT_PATH.exists():
            df = pd.read_csv(DATA_OUT_PATH)
            if df.empty or len(df.columns) == 0:
                df = pd.DataFrame(columns=column_order)
            else:
                if KEY_COLUMN in df.columns:
                    df = df[df[KEY_COLUMN].astype(str) != filename]
        else:
            df = pd.DataFrame(columns=column_order)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=column_order)

    new_df = pd.DataFrame([row])
    df = pd.concat([df, new_df], ignore_index=True)
    df = df.reindex(columns=column_order, fill_value="")
    df.to_csv(DATA_OUT_PATH, index=False)
    logger.info("Upserted row for %r to %s", filename, DATA_OUT_PATH)


async def extract(html_request: models.ExtractRequest, source_filename: str | None = None, model: str | None = None):
    """Extract product data from raw HTML via a single LangGraph (context + retries).
    html_request: models.ExtractRequest
    source_filename: if set, upsert result to data_out.csv (overwrite if key exists, else append).
    model: optional model override (e.g. for testing); default EXTRACT_MODEL.
    """
    initial: ExtractState = {
        "html_content": html_request.html_content,
        "source_filename": source_filename,
        "llm_cost_limit": LLM_COST_LIMIT_USD,
    }
    if model is not None:
        initial["model"] = model
    final = await extraction_graph.ainvoke(initial)

    if final.get("cost_exceeded"):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "LLM cost limit exceeded",
                "limit_usd": final.get("llm_cost_limit", LLM_COST_LIMIT_USD),
                "spent_usd": final.get("llm_cost_so_far", 0),
            },
        )
    if final.get("category") is None:
        raise HTTPException(
            status_code=422,
            detail={"step": "category", "validation_error": final.get("category_retry_error") or "Max retries exceeded"},
        )
    if final.get("product") is None:
        raise HTTPException(
            status_code=422,
            detail={"step": "product", "validation_error": final.get("product_retry_error") or "Max retries exceeded"},
        )

    return {"status": "ok", "product": final["product"].model_dump()}





def filter_html(soup: BeautifulSoup) -> str:
    """Filter the html to remove noise and only include product-relevant content.
    """
    # Work on a copy so we don't mutate the original
    soup = BeautifulSoup(str(soup), "html.parser")

    # Remove script tags that are not structured data (keep JSON-LD and application/json)
    for tag in soup.find_all("script"):
        type_ = (tag.get("type") or "").strip().lower()
        if type_ not in ("application/ld+json", "application/json"):
            tag.decompose()

    # Remove elements that rarely contain product copy
    for tag in soup.find_all(["style", "link", "noscript", "iframe", "svg"]):
        tag.decompose()

    # Remove nav, header, footer (generic layout chrome)
    for tag in soup.find_all(["nav", "header", "footer"]):
        tag.decompose()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    body = soup.find("body")
    if body:
        # Strip style/class on remaining nodes to cut tokens (keep itemprop, itemtype, itemscope)
        for tag in body.find_all(True):
            if tag.name in ("meta", "script"):
                continue
            for attr in list(tag.attrs):
                if attr in ("style", "class") and attr in tag.attrs:
                    del tag[attr]

    return soup.prettify()