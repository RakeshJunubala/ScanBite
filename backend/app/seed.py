"""Load the fictional demo products. Run: python -m app.seed"""

from __future__ import annotations

import json
from pathlib import Path

from .config import get_settings
from .models import Product
from .repository import ProductRepository

SAMPLES_FILE = Path(__file__).parent / "data" / "sample_products.json"


def load_samples() -> list[Product]:
    data = json.loads(SAMPLES_FILE.read_text(encoding="utf-8"))
    return [Product(**p) for p in data["products"]]


def seed(repo: ProductRepository) -> int:
    return sum(1 for p in load_samples() if repo.upsert(p))


if __name__ == "__main__":
    settings = get_settings()
    count = seed(ProductRepository(settings.database_path))
    print(f"Seeded {count} sample products into {settings.database_path}")
