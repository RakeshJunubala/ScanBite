"""Write the demo products, with real engine scores, into the mobile app.

The app uses this file in demo mode, so it works without the API running.
Run from backend/: python scripts/export_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.repository import ProductRepository
from app.seed import seed
from app.service import ProductService

OUT = Path(__file__).resolve().parents[2] / "mobile" / "src" / "demo" / "demoData.json"


def main() -> None:
    repo = ProductRepository(":memory:")
    seed(repo)
    service = ProductService(repo, source=None)
    products = {}
    alternatives = {}
    for product in repo.search("", limit=100):
        result = service.lookup(product.barcode)
        assert result is not None
        products[product.barcode] = result.model_dump(mode="json")
        alternatives[product.barcode] = [a.product.barcode for a in service.alternatives(product.barcode)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"products": products, "alternatives": alternatives}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(products)} demo products to {OUT}")


if __name__ == "__main__":
    main()
