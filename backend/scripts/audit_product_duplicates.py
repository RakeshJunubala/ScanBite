"""Read-only catalogue duplicate audit; candidate matches are not merge decisions."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path


def normalise(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def quantity_key(value: str | None) -> str:
    value = (value or "").strip().lower()
    match = re.fullmatch(r"([\d.]+)\s*(kg|g|gm|grams?|ml|l|ltr|litres?)", value)
    if not match:
        return normalise(value)
    amount, unit = float(match[1]), match[2]
    if unit in {"kg", "l", "ltr", "litre", "litres"}:
        amount *= 1000
    return f"{amount:g}{'ml' if unit in {'ml', 'l', 'ltr', 'litre', 'litres'} else 'g'}"


def identity_key(product: dict) -> tuple[str, str, str]:
    return normalise(product.get("brand")), normalise(product["name"]), quantity_key(product.get("quantity"))


def audit(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT barcode, data, score FROM products ORDER BY barcode").fetchall()
    barcode_groups, gtin_groups, identity_groups, content_groups = (defaultdict(list) for _ in range(4))
    for barcode, data, score in rows:
        p = json.loads(data)
        item = {"barcode": barcode, "name": p["name"], "brand": p.get("brand"),
                "quantity": p.get("quantity"), "score": score}
        barcode_groups[barcode].append(item)
        if barcode.isdigit() and len(barcode) in {8, 12, 13, 14}:
            gtin_groups[barcode.zfill(14)].append(item)
        identity_groups[identity_key(p)].append(item)
        n = p.get("nutriments", {})
        if p.get("ingredients_text") and sum(n.get(k) is not None for k in (
            "energy_kcal", "sugars_g", "saturated_fat_g", "sodium_mg",
        )) >= 3:
            key = (normalise(p["ingredients_text"]), json.dumps(n, sort_keys=True), quantity_key(p.get("quantity")))
            content_groups[key].append(item)
    return {"total_products": len(rows), "unique_barcodes": len(barcode_groups),
            "repeated_barcodes": [g for g in barcode_groups.values() if len(g) > 1],
            "equivalent_gtin_groups": [g for g in gtin_groups.values() if len(g) > 1],
            "same_identity_candidates": [g for g in identity_groups.values() if len(g) > 1],
            "identical_panel_ingredient_pack_groups": [g for g in content_groups.values() if len(g) > 1],
            "limitation": "Name/brand/pack matches are review candidates. Missing pack sizes, different names, "
                          "recipes and legitimate alternate barcodes prevent a universal no-duplicates guarantee."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/products.db"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    with sqlite3.connect(f"file:{args.db.resolve().as_posix()}?mode=ro", uri=True) as conn:
        result = audit(conn)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
