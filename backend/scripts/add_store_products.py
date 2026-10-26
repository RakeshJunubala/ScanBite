"""Insert reviewed non-OFF products, with provenance, duplicate guards and backup.

Dry run by default. Existing catalogue records are never overwritten. A repeat
of the identical applied batch is a no-op. New records are always provisional.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import DataStatus, Product
from app.plausibility import sanitise
from app.scoring import METHOD_VERSION, score_product
from app.service import is_valid_barcode
from app.sources.off import category_from_tags
from scripts.audit_product_duplicates import identity_key


def prepare(conn: sqlite3.Connection, manifest: dict) -> list[dict]:
    existing = conn.execute("SELECT barcode, data, score, source_version, score_method_version FROM products").fetchall()
    by_barcode = {row[0]: row for row in existing}
    gtins = {row[0].zfill(14) for row in existing}
    identities = {identity_key(json.loads(row[1])) for row in existing}
    seen = set()
    prepared = []
    if not manifest.get("batch_id"):
        raise ValueError("Missing batch_id")
    for entry in manifest["entries"]:
        p = Product.model_validate(entry["product"]).model_copy(update={"status": DataStatus.provisional})
        if not is_valid_barcode(p.barcode) or p.barcode in seen:
            raise ValueError(f"Invalid or repeated barcode: {p.barcode}")
        seen.add(p.barcode)
        e = entry["evidence"]
        sources = e.get("sources", [])
        if not sources or e.get("declared_barcode") != p.barcode or not e.get("retrieved_at"):
            raise ValueError(f"Missing exact-barcode evidence: {p.barcode}")
        if e.get("stored_nutrition_basis") != ("per_100ml" if p.is_drink else "per_100g"):
            raise ValueError(f"Unconfirmed nutrition basis: {p.barcode}")
        if not e.get("review_notes"):
            raise ValueError(f"Missing review notes: {p.barcode}")
        for source in sources:
            url = urlparse(source["url"])
            if url.scheme != "https" or not url.hostname or "openfoodfacts" in url.hostname:
                raise ValueError(f"Expected a non-OFF HTTPS source: {p.barcode}")
        if not p.brand or not p.quantity or not p.ingredients_text or not p.ingredients_text.strip():
            raise ValueError(f"Missing identity, pack size or ingredients: {p.barcode}")
        values = p.nutriments.model_dump()
        if any(v is not None and (not math.isfinite(v) or v < 0) for v in values.values()):
            raise ValueError(f"Invalid numeric nutrient: {p.barcode}")
        _, checks = sanitise(p.nutriments, is_drink=p.is_drink)
        if not checks.ok:
            raise ValueError(f"Implausible nutrition: {p.barcode}: {checks.summary()}")
        result = score_product(p)
        if result.score is None or result.missing:
            raise ValueError(f"All four core nutrients are required for new store products: {p.barcode}")
        if not p.category or category_from_tags(p.category_tags) != p.category:
            raise ValueError(f"Unstable or missing category: {p.barcode}")
        old = by_barcode.get(p.barcode)
        unchanged = bool(old and old[3] == manifest["batch_id"] and old[4] == METHOD_VERSION
                         and Product.model_validate_json(old[1]) == p and old[2] == result.score)
        if not unchanged:
            if p.barcode.zfill(14) in gtins:
                raise ValueError(f"Barcode already exists (including equivalent GTIN): {p.barcode}")
            if identity_key(p.model_dump()) in identities:
                raise ValueError(f"Brand/name/pack already exists: {p.barcode}")
        gtins.add(p.barcode.zfill(14))
        identities.add(identity_key(p.model_dump()))
        prepared.append({"product": p, "score": result.score, "evidence": e, "unchanged": unchanged})
    return prepared


def run(db_path: Path, manifest: dict, *, apply: bool = False) -> dict:
    if not db_path.is_file():
        raise ValueError("Database must already exist")
    with sqlite3.connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        prepared = prepare(conn, manifest)
        changes = [item for item in prepared if not item["unchanged"]]
        backup_path = None
        if apply and changes:
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
            backup_path = db_path.with_name(f"{db_path.stem}.backup-{stamp}.db")
            with (sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True) as source,
                  sqlite3.connect(backup_path) as backup):
                source.backup(backup)
            for item in changes:
                p = item["product"]
                conn.execute(
                    "INSERT INTO products (barcode,name,brand,category,status,score,score_method_version,"
                    "source_version,data) VALUES (?,?,?,?,?,?,?,?,?)",
                    (p.barcode, p.name, p.brand, p.category, p.status.value, item["score"], METHOD_VERSION,
                     manifest["batch_id"], p.model_dump_json()),
                )
                notes = {"batch_id": manifest["batch_id"], "evidence": item["evidence"],
                         "score": item["score"], "method_version": METHOD_VERSION}
                conn.execute(
                    "INSERT INTO submissions (barcode,source,notes,label_photo_url) VALUES (?,?,?,?)",
                    (p.barcode, "online store research", json.dumps(notes, ensure_ascii=False),
                     item["evidence"].get("nutrition_image_url")),
                )
            conn.commit()
        else:
            conn.rollback()
    return {"applied": apply, "added": len(changes), "backup": str(backup_path) if backup_path else None,
            "products": [{"barcode": i["product"].barcode, "name": i["product"].name,
                          "quantity": i["product"].quantity, "score": i["score"],
                          "status": i["product"].status.value, "unchanged": i["unchanged"]} for i in prepared]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--db", type=Path, default=Path("data/products.db"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = run(args.db, json.loads(args.manifest.read_text(encoding="utf-8")), apply=args.apply)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
