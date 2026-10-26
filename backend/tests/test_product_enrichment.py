"""A reviewed update cannot cross barcodes, lose evidence or invent nutrients."""

import hashlib
import json
import sqlite3

import pytest

from app.models import DataStatus, Product
from app.repository import ProductRepository
from app.scoring import score_product
from scripts.apply_product_enrichment import run


@pytest.fixture
def batch(tmp_path):
    path = tmp_path / "products.db"
    repo = ProductRepository(str(path))
    for code in ("8901058000269", "8901058022193"):
        repo.upsert(Product(barcode=code, name="Masala", nutriments={"energy_kcal":384, "sugars_g":1.8}))
    entries = []
    with sqlite3.connect(path) as conn:
        for code, data in conn.execute("SELECT barcode, data FROM products"):
            entries.append({
                "barcode": code, "expected_data_sha256": hashlib.sha256(data.encode()).hexdigest(),
                "changes": {"nutriments": {"saturated_fat_g":8.2, "sodium_mg":1000}},
                "variant": {"flavour":"Masala"},
                "evidence": {"source_url":f"https://world.openfoodfacts.org/api/v2/product/{code}.json",
                             "retrieved_at":"2026-10-21T06:00:00Z", "photos": {}},
            })
    return path, {"batch_id":"test-enrichment", "entries":entries}


def test_dry_run_does_not_update_or_create_backups(batch):
    path, manifest = batch
    result = run(path, manifest)
    assert result["newly_scored"] == 2
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products WHERE score IS NULL").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 0
    assert not list(path.parent.glob("*.backup-*.db"))


def test_apply_backs_up_records_provenance_and_is_idempotent(batch):
    path, manifest = batch
    result = run(path, manifest, apply=True)
    assert result["changed"] == 2
    with sqlite3.connect(result["backup"]) as backup:
        assert backup.execute("SELECT COUNT(*) FROM products WHERE score IS NULL").fetchone()[0] == 2
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT data, score FROM products").fetchall()
        for data, stored_score in rows:
            product = Product.model_validate_json(data)
            assert stored_score == score_product(product).score
            assert product.nutriments.fibre_g is None  # Missing is not zero.
            assert product.status is DataStatus.community
        notes = json.loads(conn.execute("SELECT notes FROM submissions LIMIT 1").fetchone()[0])
        assert notes["variant"]["flavour"] == "Masala"
        assert notes["before"]["nutriments"]["sodium_mg"] is None
    again = run(path, manifest, apply=True)
    assert again["changed"] == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 2


def test_one_implausible_panel_prevents_the_entire_batch(batch):
    path, manifest = batch
    manifest["entries"][1]["changes"]["nutriments"]["sodium_mg"] = 1_000_000
    with pytest.raises(ValueError, match="Implausible"):
        run(path, manifest, apply=True)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products WHERE score IS NULL").fetchone()[0] == 2


@pytest.mark.parametrize("nutrient", ["energy_kcal", "protein_g", "fruit_veg_nuts_pct"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")], ids=["nan", "inf", "negative-inf"])
def test_nonfinite_nutrient_prevents_all_updates_and_audit_writes(batch, nutrient, value):
    path, manifest = batch
    # A valid first entry must not be applied when a later panel is invalid.
    manifest["entries"][1]["changes"]["nutriments"][nutrient] = value
    with sqlite3.connect(path) as conn:
        before = conn.execute("SELECT * FROM products ORDER BY barcode").fetchall()
    with pytest.raises(ValueError, match="Non-finite nutrient"):
        run(path, manifest, apply=True)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT * FROM products ORDER BY barcode").fetchall() == before
        assert conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 0
    assert not list(path.parent.glob("*.backup-*.db"))


def test_source_must_reference_the_same_barcode(batch):
    path, manifest = batch
    manifest["entries"][0]["evidence"]["source_url"] = "https://example.com/other-product"
    with pytest.raises(ValueError, match="source evidence"):
        run(path, manifest, apply=True)


def test_product_changed_since_research_is_not_overwritten(batch):
    path, manifest = batch
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT barcode, data FROM products LIMIT 1").fetchone()
        product = json.loads(row[1])
        product["name"] = "Newer information"
        conn.execute("UPDATE products SET data=? WHERE barcode=?", (json.dumps(product), row[0]))
    with pytest.raises(ValueError, match="changed since"):
        run(path, manifest, apply=True)


def test_verified_product_and_identity_changes_are_rejected(batch):
    path, manifest = batch
    manifest["entries"][0]["changes"]["status"] = "verified"
    with pytest.raises(ValueError, match="trust change"):
        run(path, manifest, apply=True)
    manifest["entries"][0]["changes"].pop("status")
    with sqlite3.connect(path) as conn:
        code = manifest["entries"][0]["barcode"]
        data = json.loads(conn.execute("SELECT data FROM products WHERE barcode=?", (code,)).fetchone()[0])
        data["status"] = "verified"
        conn.execute("UPDATE products SET data=?, status='verified' WHERE barcode=?", (json.dumps(data), code))
    with pytest.raises(ValueError, match="community records"):
        run(path, manifest, apply=True)
