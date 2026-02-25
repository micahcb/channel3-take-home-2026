import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

DATA_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "data_out.csv"


def _load_products() -> list[dict]:
    """Load products from data_out.csv. Returns list of dicts with string values."""
    if not DATA_CSV.exists():
        return []
    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) < 2:
        return []
    headers = [h.strip() for h in rows[0]]
    products = []
    for values in rows[1:]:
        if not (values and values[0].strip()):
            continue
        row = {}
        for j, h in enumerate(headers):
            row[h] = values[j] if j < len(values) else ""
        products.append(row)
    return products


@router.get("/products")
async def list_products(brand: str | None = None):
    """List all products, optionally filtered by brand."""
    products = _load_products()
    if brand is not None:
        products = [p for p in products if p.get("brand") == brand]
    return {"products": products}


@router.get("/products/{filename:path}")
async def get_product(filename: str):
    """Get a single product by filename (slug)."""
    products = _load_products()
    for p in products:
        if p.get("filename") == filename:
            return {"product": p}
    raise HTTPException(status_code=404, detail="Not found")
