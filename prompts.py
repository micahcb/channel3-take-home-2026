"""Prompts for each step of the PDP extraction flow.

Flow: (1) Extract category from HTML, retry until valid. (2) Extract full Product
from HTML using that category, retry until valid.
"""

from pathlib import Path

# ---- Step 1: Extract category only (Google Product Taxonomy) ----
# Ideally we do not need to give the entire possible list of categories to the llm, but will log success rate in order to balance prompt size and success rate.
# Goal is to limit overall cost to minimize cost_input_tokens(prompt size) * success rate. Assuming output_tokens is constant.

# NOTE (prompt caching): We include the full category list in the system prompt so the
# model can pick an exact, valid category. OpenRouter/OpenAI cache the long system
# prefix automatically (min 1024 tokens). After the first request you pay a reduced
# "cache read" rate (e.g. 0.25–0.5x input price) for the taxonomy; only the variable
# user message (HTML) is charged at full input cost per request.

_CATEGORY_INSTRUCTION = (
    "You extract exactly one product category from the given HTML. "
    "Output a Category with a single field: name. "
    "The name must be an exact category from the list below (Google Product Taxonomy). "
    "Choose the most specific applicable category. Output only the Category object."
)

_CATEGORIES_FILE = Path(__file__).resolve().parent / "categories.txt"


def _load_category_list() -> str:
    """Load category lines from categories.txt, skipping comments and blanks."""
    if not _CATEGORIES_FILE.exists():
        return ""
    lines = []
    with open(_CATEGORIES_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return "\n".join(lines)


# Build system prompt once at import: instruction + full taxonomy for exact matching.
# Large static prefix is cached by the provider to reduce per-request input cost.
_category_list = _load_category_list()
CATEGORY_SYSTEM = f"{_CATEGORY_INSTRUCTION}\n\nValid categories (use one exactly as written):\n\n{_category_list}"

CATEGORY_USER = "From this HTML, extract the product category (Google Product Taxonomy). Output a Category with field name.\n\n{html}"

RETRY_CATEGORY_APPEND = "\n\nPrevious attempt failed: {retry_error}. Output a valid Category whose name is exactly one of the valid categories listed in the system prompt."

# ---- Step 2: Extract full Product (category is fixed) ----
# Exact data model for the LLM (category is provided; use it exactly).
PRODUCT_SYSTEM = """You extract product data from HTML and output a valid Product. Use the exact category provided; do not change it. Prefer full-resolution image URLs when possible.

Exact data model:


Product:
  name: str
  price: Price (use the provided price model exactly)
  description: str
  key_features: list[str]
  image_urls: list[str] (FULL URLS)
  video_url: str | None = None
  category: Category  (use the provided category exactly)
  brand: str
  colors: list[str]
  variants: list[Variant]

Category:
  name: str  (use the provided category exactly)

Price:
  price: float
  currency: str
  compare_at_price: float | None = None (If a product is on sale, this is the original price)


Variant:
  title: str
  options: list[OptionEntry]

OptionEntry:
  value: str
  available: bool = True
  price: float | None = None (None = use parent product price/no variant specific price)


Output only valid one valid Product JSON that matches this schema."""

PRODUCT_USER = (
    "Extract product data from this HTML. Use this exact category: {category_name}\n\n{html}"
)

RETRY_PRODUCT_APPEND = "\n\nPrevious attempt failed: {retry_error}. Fix and output a valid Product. Keep category as: {category_name}."
