#!/usr/bin/env python3
"""
Simple model test suite: run extraction with different models and record time, cost, errors, and product output.

Plan:
- Variable: model (list of model IDs).
- Per run we record: time_seconds, cost_usd, error (if any), product (dict or null).
- Output: JSON file (and optional stdout summary).

Usage:
  python -m scripts.run_model_test [--html path] [--out path] [--models a,b,c]
  Default: one HTML from data/, results to scripts/model_test_results.json.
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.extract import extraction_graph, LLM_COST_LIMIT_USD

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_OUT = Path(__file__).resolve().parent / "model_test_results.json"

# Models to test if not passed via CLI (keep small for speed)
DEFAULT_MODELS = ["openai/gpt-5-nano", "openai/gpt-5-mini"]


async def run_one(html_content: str, model: str) -> dict:
    """Run extraction for one model. Returns {model, time_seconds, cost_usd, error, product}."""
    initial = {
        "html_content": html_content,
        "source_filename": None,
        "llm_cost_limit": LLM_COST_LIMIT_USD,
        "model": model,
    }
    start = time.perf_counter()
    try:
        final = await extraction_graph.ainvoke(initial)
        elapsed = time.perf_counter() - start
        cost = final.get("llm_cost_so_far", 0)
        product = final.get("product")
        if final.get("cost_exceeded"):
            return {
                "model": model,
                "time_seconds": round(elapsed, 3),
                "cost_usd": round(cost, 6),
                "error": "cost limit exceeded",
                "product": None,
            }
        if product is None:
            err = final.get("product_retry_error") or final.get("category_retry_error") or "unknown"
            return {
                "model": model,
                "time_seconds": round(elapsed, 3),
                "cost_usd": round(cost, 6),
                "error": err,
                "product": None,
            }
        return {
            "model": model,
            "time_seconds": round(elapsed, 3),
            "cost_usd": round(cost, 6),
            "error": None,
            "product": product.model_dump(),
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {
            "model": model,
            "time_seconds": round(elapsed, 3),
            "cost_usd": None,
            "error": str(e),
            "product": None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run extraction with different models; output time, cost, errors, product.")
    parser.add_argument("--html", type=Path, default=None, help="HTML file path (default: first .html in data/)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output JSON path")
    parser.add_argument("--models", type=str, default=",".join(DEFAULT_MODELS), help="Comma-separated model IDs")
    args = parser.parse_args()

    if args.html is not None:
        html_path = args.html if args.html.is_absolute() else (DATA_DIR / args.html.name)
    else:
        first_html = next(DATA_DIR.glob("*.html"), None)
        html_path = first_html or (DATA_DIR / "ace.html")
    if not html_path.exists():
        print(f"HTML file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    html_content = html_path.read_text(encoding="utf-8", errors="replace")
    models_list = [m.strip() for m in args.models.split(",") if m.strip()]

    results = []
    for model in models_list:
        print(f"Testing {model}...", flush=True)
        out = asyncio.run(run_one(html_content, model))
        results.append(out)
        print(f"  time={out['time_seconds']}s cost=${out.get('cost_usd')} error={out.get('error')}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} results to {args.out}")


if __name__ == "__main__":
    main()
