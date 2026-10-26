"""Catalogue portability must preserve identities/scores and never replace a database."""
import json
import sqlite3
from contextlib import closing

import pytest

from app.models import Product
from app.repository import ProductRepository
from scripts.catalogue_snapshot import export_catalogue, restore_catalogue


@pytest.fixture
def snapshot(tmp_path):
    source = tmp_path / "source.db"
    repo = ProductRepository(str(source))
    repo.upsert(Product(barcode="8901058000269", name="Example", brand="Test", quantity="50 g",
                        nutriments={"energy_kcal": 350, "sugars_g": 3, "saturated_fat_g": 2, "sodium_mg": 300}),
                source_version="test-source")
    repo.upsert(Product(barcode="8901058022193", name="Unscored", status="provisional"))
    with closing(sqlite3.connect(source)) as conn, conn:
        conn.execute("INSERT INTO submissions (barcode,submitted_by,notes) VALUES (?,?,?)",
                     ("8901058000269", "private@example.com", "Private review history"))
    path = tmp_path / "catalogue.json"
    export_catalogue(source, path)
    return source, path


def test_round_trip_preserves_every_product_column_and_excludes_private_history(snapshot, tmp_path):
    source, path = snapshot
    original = path.read_bytes()
    assert b"private@example.com" not in original and b"Private review history" not in original
    restored = tmp_path / "restored.db"
    assert restore_catalogue(path, restored)["products"] == 2
    with closing(sqlite3.connect(source)) as before, closing(sqlite3.connect(restored)) as after:
        old_rows = before.execute("SELECT * FROM products ORDER BY barcode").fetchall()
        new_rows = after.execute("SELECT * FROM products ORDER BY barcode").fetchall()
        # JSON formatting can change; its product values must not.
        assert [r[:8] + (json.loads(r[8]),) + r[9:] for r in old_rows] == [
            r[:8] + (json.loads(r[8]),) + r[9:] for r in new_rows]
        assert after.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 0
    export_catalogue(restored, path)
    assert path.read_bytes() == original


def test_restore_never_overwrites_existing_database(snapshot):
    source, path = snapshot
    before = source.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        restore_catalogue(path, source)
    assert source.read_bytes() == before


@pytest.mark.parametrize("mutation", ["score", "count", "duplicate", "version", "status", "attribution"])
def test_invalid_snapshot_creates_no_database(snapshot, tmp_path, mutation):
    _, path = snapshot
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["collections"]["open_food_facts"]
    if mutation == "score":
        rows[0]["score"] = -100
    elif mutation == "count":
        data["product_count"] += 1
    elif mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "version":
        data["score_method_version"] = "unsupported"
    elif mutation == "status":
        rows[0]["data"]["status"] = "verified"
    else:
        data.pop("open_food_facts_notice")
    path.write_text(json.dumps(data), encoding="utf-8")
    target = tmp_path / "restored.db"
    with pytest.raises(ValueError):
        restore_catalogue(path, target)
    assert not target.exists()


def test_export_cannot_replace_its_source_database(snapshot):
    source, _ = snapshot
    before = source.read_bytes()
    with pytest.raises(ValueError, match="differ"):
        export_catalogue(source, source)
    assert source.read_bytes() == before
