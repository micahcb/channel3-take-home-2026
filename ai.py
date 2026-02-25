import logging
import os
from functools import lru_cache
from typing import Any, TypeVar

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Prices per million tokens
MODEL_PRICES: dict[str, dict[str, float]] = {
    # Google models
    "google/gemini-2.0-flash-lite-001": {"input": 0.075, "output": 0.30},
    "google/gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
    "google/gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
    "google/gemini-3-pro-preview": {"input": 2.00, "output": 12.00},
    # OpenAI models
    "openai/gpt-5": {"input": 1.25, "output": 10.00},
    "openai/gpt-5-mini": {"input": 0.25, "output": 2.00},
    "openai/gpt-5-nano": {"input": 0.05, "output": 0.40},
    # Feel free to add more models here
}

T = TypeVar("T", bound=BaseModel)


@lru_cache
def _get_client() -> AsyncOpenAI:
    """Get cached AsyncOpenAI client configured for OpenRouter."""
    api_key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTER_API_KEY not found in environment")
    return AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)



# Added a slight modification of the cost logging to be able to track full runs
def _cost_from_response(response) -> float:
    """Compute cost in USD for a single response from usage and MODEL_PRICES."""
    usage = getattr(response, "usage", None)
    if usage is None:
        logger.warning("No usage data in response")
        return 0.0

    model = getattr(response, "model", "unknown")
    input_tokens = getattr(usage, "input_tokens", 0)
    output_tokens = getattr(usage, "output_tokens", 0)

    # Handle reasoning tokens (may be in output_tokens_details)
    reasoning_tokens = 0
    output_details = getattr(usage, "output_tokens_details", None)
    if output_details:
        reasoning_tokens = getattr(output_details, "reasoning_tokens", 0) or 0

    # Get prices (default to 0 if model unknown)
    prices = MODEL_PRICES.get(model, {"input": 0, "output": 0})
    input_price = prices["input"]
    output_price = prices["output"]  # Also used for reasoning

    # Calculate cost for this single query
    single_input_cost = (input_tokens / 1_000_000) * input_price
    single_output_cost = (output_tokens / 1_000_000) * output_price
    single_reasoning_cost = (reasoning_tokens / 1_000_000) * output_price
    return single_input_cost + single_output_cost + single_reasoning_cost


def _log_usage(response) -> float:
    """Log token usage and cost extrapolation for 1M queries. Returns cost in USD for this query."""
    usage = getattr(response, "usage", None)
    if usage is None:
        logger.warning("No usage data in response")
        return 0.0

    model = getattr(response, "model", "unknown")
    input_tokens = getattr(usage, "input_tokens", 0)
    output_tokens = getattr(usage, "output_tokens", 0)
    reasoning_tokens = 0
    output_details = getattr(usage, "output_tokens_details", None)
    if output_details:
        reasoning_tokens = getattr(output_details, "reasoning_tokens", 0) or 0

    single_total = _cost_from_response(response)
    million_cost = single_total * 1_000_000

    logger.info(
        f"Token usage for {model}: "
        f"input={input_tokens}, output={output_tokens}, reasoning={reasoning_tokens} | "
        f"This query: ${single_total:.6f} | "
        f"1M queries: ${million_cost:,.2f} | "
        f"10M queries: ${million_cost * 10:,.2f}"
    )
    return single_total


async def responses(
    model: str,
    input: str | list,
    text_format: type[T] | None = None,
    **kwargs,
) -> tuple[T | Any, float]:
    """
    Call OpenRouter responses API with automatic token usage logging.

    Returns (parsed_result_or_response, cost_usd).
    OpenAI Responses API: https://platform.openai.com/docs/api-reference/responses
    """
    client = _get_client()

    if text_format is not None:
        response = await client.responses.parse(
            model=model,
            input=input,
            text_format=text_format,
            **kwargs,
        )
        cost = _log_usage(response)
        return (response.output_parsed, cost)
    else:
        response = await client.responses.create(
            model=model,
            input=input,
            **kwargs,
        )
        cost = _log_usage(response)
        return (response, cost)

