from typing import Any
from pathlib import Path
from pydantic import BaseModel, field_validator

# Load categories once at module level
CATEGORIES_FILE = Path(__file__).parent / "categories.txt"
VALID_CATEGORIES = set()
if CATEGORIES_FILE.exists():
    with open(CATEGORIES_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                VALID_CATEGORIES.add(line)

class Category(BaseModel):
    # A category from Google's Product Taxonomy
    # https://www.google.com/basepages/producttype/taxonomy.en-US.txt
    name: str

    @field_validator("name")
    @classmethod
    def validate_name_exists(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category '{v}' is not a valid category in categories.txt")
        return v

class Price(BaseModel):
    price: float
    currency: str
    # If a product is on sale, this is the original price
    compare_at_price: float | None = None

class OptionEntry(BaseModel):
    """One variant option (e.g. size '9') with availability and optional price."""
    value: str  # e.g. "9", "9.5", "Red"
    available: bool = True
    price: float | None = None  # None = use parent product price


class Variant(BaseModel):
    """Product variant (e.g. Size or Color) with a list of choices."""
    title: str  # e.g. "Size", "Color"
    options: list[OptionEntry]  # e.g. [{"value": "9", "available": True, "price": None}, {"value": "9.5", "available": False, "price": 99.5}]


# This is the final product schema that you need to output.
# You may add additional models as needed.
class Product(BaseModel):
    name: str
    price: Price
    description: str
    key_features: list[str]
    image_urls: list[str]
    video_url: str | None = None
    category: Category
    brand: str
    colors: list[str]
    variants: list[Variant]


class ExtractRequest(BaseModel):
    html_content: str
    

