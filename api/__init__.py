import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.frontend import router as frontend_router
from api.routers.products import router as products_router

app = FastAPI(
    title="PDP Extraction API",
    description="Extract product data from raw HTML.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with timestamp and level."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


setup_logging()

app.include_router(frontend_router, prefix="/api", tags=["frontend"])
app.include_router(products_router, prefix="/api", tags=["products"])


@app.get("/health")
async def health():
    """Health check for the API."""
    return {"status": "ok"}
