import asyncio
import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup, Comment
from langchain_core.runnables import RunnableSerializable
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
DATA_OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "data_out.csv"
KEY_COLUMN = "filename"


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
        retry_error = input.get("retry_error")
        user = CATEGORY_USER.format(html=html)
        if retry_error:
            user += RETRY_CATEGORY_APPEND.format(retry_error=retry_error)
        messages = [
            {"role": "system", "content": CATEGORY_SYSTEM},
            {"role": "user", "content": user},
        ]
        result = await ai_module.responses(
            self.model,
            messages,
            text_format=models.Category,
        )
        return result


class OpenRouterProductExtractor(RunnableSerializable[dict, models.Product]):
    """Extract full Product from HTML with category fixed. Uses ai.responses → _log_usage."""

    model: str = EXTRACT_MODEL

    def invoke(self, input: dict, **kwargs) -> models.Product:
        return asyncio.run(self.ainvoke(input, **kwargs))

    async def ainvoke(self, input: dict, **kwargs) -> models.Product:
        html = input["html"]
        category_name = input["category_name"]
        retry_error = input.get("retry_error")
        user = PRODUCT_USER.format(html=html, category_name=category_name)
        if retry_error:
            user += RETRY_PRODUCT_APPEND.format(retry_error=retry_error, category_name=category_name)
        messages = [
            {"role": "system", "content": PRODUCT_SYSTEM},
            {"role": "user", "content": user},
        ]
        result = await ai_module.responses(
            self.model,
            messages,
            text_format=models.Product,
        )
        return result


category_runnable = OpenRouterCategoryExtractor()
product_runnable = OpenRouterProductExtractor()


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


async def extract(html_request: models.ExtractRequest, source_filename: str | None = None):
    """Extract product data from raw HTML. Two-step flow: category then full product.
    html_request: models.ExtractRequest
    source_filename: if set, upsert result to data_out.csv (overwrite if key exists, else append).
    """

    # Shared context: filtered HTML (noise removed)
    soup = BeautifulSoup(html_request.html_content, "html.parser")
    logger.info(f"-------------------------------------Starting extraction-------------------------------------")
    input_for_llm = filter_html(soup)
    logger.info(f"-------------------------------------Filtered HTML-------------------------------------")

    # Step 1: Extract category, retry until valid (Google Product Taxonomy)
    category = None
    category_retry_error = None
    for attempt in range(MAX_RETRIES):
        try:
            inp = {"html": input_for_llm}
            if category_retry_error is not None:
                inp["retry_error"] = category_retry_error
            category = await category_runnable.ainvoke(inp)
            break
        except PydanticValidationError as e:
            category_retry_error = str(e)
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(
                    status_code=422,
                    detail={"step": "category", "validation_error": category_retry_error},
                )
    if category is None:
        raise HTTPException(status_code=422, detail={"step": "category", "validation_error": "Max retries exceeded"})

    # Step 2: Extract full Product with category fixed, retry until valid
    product = None
    product_retry_error = None
    for attempt in range(MAX_RETRIES):
        try:
            inp = {"html": input_for_llm, "category_name": category.name}
            if product_retry_error is not None:
                inp["retry_error"] = product_retry_error
            product = await product_runnable.ainvoke(inp)
            break
        except PydanticValidationError as e:
            product_retry_error = str(e)
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(
                    status_code=422,
                    detail={"step": "product", "validation_error": product_retry_error},
                )
    if product is None:
        raise HTTPException(status_code=422, detail={"step": "product", "validation_error": "Max retries exceeded"})

    if source_filename is not None:
        _upsert_row(source_filename, product)

    return {"status": "ok", "product": product.model_dump()}





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