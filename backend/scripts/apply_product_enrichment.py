"""Apply a reviewed, barcode-specific enrichment manifest using ScanBite's scorer.

Dry run by default. --apply backs up the SQLite database and writes the products
and their source/variant evidence together in one transaction. No web fetching.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import DataStatus, Nutriments, Product
from app.plausibility import sanitise
from app.scoring import METHOD_VERSION, score_product
from app.service import is_valid_barcode
from app.sources.off import category_from_tags


def prepare(conn: sqlite3.Connection, manifest: dict) -> list[dict]:
    """Validate every row before allowing any writes; never silently drop bad data."""
    prepared = []
    seen = set()
    for entry in manifest["entries"]:
        code = entry["barcode"]
        if code in seen or not is_valid_barcode(code):
            raise ValueError(f"Invalid or repeated barcode: {code}")
        seen.add(code)
        row = conn.execute("SELECT data, score FROM products WHERE barcode = ?", (code,)).fetchone()
        if row is None:
            raise ValueError(f"Product does not exist: {code}")
        old = Product.model_validate_json(row[0])
        if old.barcode != code or old.status is not DataStatus.community:
            raise ValueError(f"Only matching community records may be enriched: {code}")
        evidence = entry["evidence"]
        source_url = urlparse(evidence["source_url"])
        if source_url.scheme != "https" or code not in source_url.path or not evidence["retrieved_at"]:
            raise ValueError(f"Missing barcode-specific source evidence: {code}")
        changes = dict(entry["changes"])
        if set(changes) - (Product.model_fields.keys() - {"barcode", "status"}):
            raise ValueError(f"Unexpected fields, identity or trust change: {code}")
        data = old.model_dump(mode="json")
        if "nutriments" in changes:
            nutrition = changes.pop("nutriments")
            if set(nutrition) - Nutriments.model_fields.keys():
                raise ValueError(f"Unknown nutrient field: {code}")
            data["nutriments"].update(nutrition)
        data.update(changes)
        product = Product.model_validate(data)
        for nutrient, value in product.nutriments.model_dump().items():
            if value is not None and not math.isfinite(value):
                raise ValueError(f"Non-finite nutrient {nutrient} for {code}")
        _, checked = sanitise(product.nutriments, is_drink=product.is_drink)
        if not checked.ok:
            raise ValueError(f"Implausible nutrition for {code}: {checked.summary()}")
        if product.category_tags and category_from_tags(product.category_tags) != product.category:
            raise ValueError(f"Category would change on next server startup: {code}")
        score = score_product(product)
        unchanged = product.model_dump(mode="json") == old.model_dump(mode="json") and row[1] == score.score
        digest = hashlib.sha256(row[0].encode("utf-8")).hexdigest()
        if not unchanged and digest != entry["expected_data_sha256"]:
            raise ValueError(f"Product changed since evidence review: {code}")
        prepared.append({
            "barcode": code, "product": product, "score": score, "entry": entry,
            "before": json.loads(row[0]), "old_score": row[1], "unchanged": unchanged,
        })
    return prepared


def run(db_path: Path, manifest: dict, *, apply: bool = False) -> dict:
    if not db_path.is_file():
        raise ValueError(f"Database does not exist: {db_path}")
    conn = sqlite3.connect(db_path)
    backup_path = None
    try:
        # Hold a write reservation through validation, backup and update so a
        # concurrent API submission cannot be replaced by a stale research copy.
        conn.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        prepared = prepare(conn, manifest)
        changes = [item for item in prepared if not item["unchanged"]]
        if apply and changes:
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
            backup_path = db_path.with_name(f"{db_path.stem}.backup-{stamp}.db")
            # Backup through a second connection: backup() on the connection
            # holding an active transaction can wait for itself indefinitely.
            with (
                sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True) as source,
                sqlite3.connect(backup_path) as dest,
            ):
                source.backup(dest)
            for item in changes:
                product = item["product"]
                conn.execute(
                    "UPDATE products SET name=?, brand=?, category=?, status=?, score=?, "
                    "score_method_version=?, source_version=?, data=?, updated_at=datetime('now') WHERE barcode=?",
                    (product.name, product.brand, product.category, product.status.value, item["score"].score,
                     METHOD_VERSION, manifest["batch_id"], product.model_dump_json(), product.barcode),
                )
                notes = {"batch_id": manifest["batch_id"], "variant": item["entry"]["variant"],
                         "evidence": item["entry"]["evidence"], "before": item["before"],
                         "old_score": item["old_score"], "new_score": item["score"].score}
                conn.execute(
                    "INSERT INTO submissions (barcode, source, notes, label_photo_url) VALUES (?, ?, ?, ?)",
                    (product.barcode, "online product enrichment", json.dumps(notes, ensure_ascii=False),
                     item["entry"]["evidence"].get("photos", {}).get("nutrition")),
                )
            conn.commit()
        else:
            conn.rollback()
        return {"applied": apply, "backup": str(backup_path) if backup_path else None,
                "changed": len(changes), "newly_scored": sum(
                    i["old_score"] is None and i["score"].score is not None for i in changes),
                "products": [{"barcode": i["barcode"], "name": i["product"].name,
                              "quantity": i["product"].quantity, "category": i["product"].category,
                              "old_score": i["old_score"], "score": i["score"].score,
                              "verdict": i["score"].verdict.value, "variant": i["entry"]["variant"],
                              "ingredients_available": bool(i["product"].ingredients_text),
                              "missing_core": i["score"].missing, "unchanged": i["unchanged"]}
                             for i in prepared]}
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--db", type=Path, default=Path("data/products.db"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = run(args.db, json.loads(args.manifest.read_text(encoding="utf-8")), apply=args.apply)
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
