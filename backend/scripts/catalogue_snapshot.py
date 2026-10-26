"""Export a Git-friendly product catalogue or restore it into a new SQLite file.

Only product records are transferred. Private submission history is excluded.
Restore refuses existing databases and checks every score before creating a file.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import DataStatus, Product
from app.repository import SCHEMA
from app.scoring import METHOD_VERSION, score_product

DATA = Path(__file__).resolve().parents[1] / "data"
COLUMNS = ("barcode", "name", "brand", "category", "status", "score", "score_method_version",
           "source_version", "data", "updated_at")
NOTICE = {
    "attribution": "Contains data from Open Food Facts and its contributors.",
    "source": "https://world.openfoodfacts.org/",
    "database_license": "https://opendatacommons.org/licenses/odbl/1-0/",
    "note": "Open Food Facts-derived records are grouped separately. Other-source evidence is in enrichment manifests.",
}


def validate(snapshot: dict) -> list[dict]:
    if snapshot.get("format_version") != 1 or snapshot.get("score_method_version") != METHOD_VERSION:
        raise ValueError("Unsupported snapshot format or scoring method; use the matching code revision")
    if snapshot.get("open_food_facts_notice") != NOTICE:
        raise ValueError("Missing or changed Open Food Facts attribution")
    groups = snapshot["collections"]
    if set(groups) != {"open_food_facts", "other_sources"}:
        raise ValueError("Unexpected catalogue collections")
    rows, seen = [], set()
    for group, records in groups.items():
        for row in records:
            if set(row) != set(COLUMNS) or not isinstance(row["data"], dict):
                raise ValueError("Unexpected product record fields")
            p = Product.model_validate(row["data"])
            if p.barcode in seen:
                raise ValueError(f"Repeated barcode: {p.barcode}")
            seen.add(p.barcode)
            if any(row[k] != getattr(p, k) for k in ("barcode", "name", "brand", "category", "status")):
                raise ValueError(f"Product metadata disagrees with its data: {p.barcode}")
            if (group == "open_food_facts") != (p.status is DataStatus.community):
                raise ValueError(f"Incorrect source collection: {p.barcode}")
            if any(v is not None and not math.isfinite(v) for v in p.nutriments.model_dump().values()):
                raise ValueError(f"Non-finite nutrient: {p.barcode}")
            if row["score_method_version"] != METHOD_VERSION or row["score"] != score_product(p).score:
                raise ValueError(f"Stored score does not reproduce: {p.barcode}")
            rows.append(row)
    if len(rows) != snapshot["product_count"]:
        raise ValueError("Snapshot product count does not match its records")
    return sorted(rows, key=lambda row: row["barcode"])


def export_catalogue(db: Path, destination: Path) -> dict:
    if db.resolve() == destination.resolve():
        raise ValueError("Snapshot destination must differ from database")
    with closing(sqlite3.connect(f"file:{db.resolve().as_posix()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        records = []
        for row in conn.execute(f"SELECT {','.join(COLUMNS)} FROM products ORDER BY barcode"):
            record = dict(row)
            record["data"] = json.loads(record["data"])
            records.append(record)
    snapshot = {
        "format_version": 1, "score_method_version": METHOD_VERSION,
        "product_count": len(records), "open_food_facts_notice": NOTICE,
        "collections": {
            "open_food_facts": [r for r in records if r["status"] == "community"],
            "other_sources": [r for r in records if r["status"] != "community"],
        },
    }
    validate(snapshot)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Deterministic output: no export timestamp, stable ordering and real JSON nulls.
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        temporary = Path(directory) / "catalogue.json"
        temporary.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                             encoding="utf-8")
        temporary.replace(destination)
    return summary(snapshot)


def restore_catalogue(snapshot_path: Path, db: Path) -> dict:
    if db.exists():
        raise ValueError("Refusing to overwrite an existing database; choose a new database path")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    rows = validate(snapshot)
    db.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=db.parent) as directory:
        temporary = Path(directory) / "products.db"
        with closing(sqlite3.connect(temporary)) as conn:
            conn.executescript(SCHEMA)
            with conn:
                for row in rows:
                    values = [json.dumps(row[k], ensure_ascii=False, allow_nan=False) if k == "data" else row[k]
                              for k in COLUMNS]
                    conn.execute(f"INSERT INTO products ({','.join(COLUMNS)}) VALUES ({','.join('?' for _ in COLUMNS)})",
                                 values)
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Restored database failed integrity check")
        # Publish the complete database without replacing a concurrently created file.
        os.link(temporary, db)
    return summary(snapshot)


def summary(snapshot: dict) -> dict:
    rows = [r for records in snapshot["collections"].values() for r in records]
    scored = sum(r["score"] is not None for r in rows)
    return {"products": len(rows), "scored": scored, "unscored": len(rows) - scored,
            "score_method_version": snapshot["score_method_version"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "restore"])
    parser.add_argument("--db", type=Path, default=DATA / "products.db")
    parser.add_argument("--snapshot", type=Path, default=DATA / "catalogue.json")
    args = parser.parse_args()
    result = export_catalogue(args.db, args.snapshot) if args.action == "export" else restore_catalogue(
        args.snapshot, args.db)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
