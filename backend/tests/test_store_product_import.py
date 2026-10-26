"""Store imports must not duplicate, overwrite, guess nutrition or elevate trust."""
import copy
import json
import sqlite3

import pytest

from app.models import Product
from app.repository import ProductRepository
from scripts.add_store_products import run
from scripts.audit_product_duplicates import audit, quantity_key


@pytest.fixture
def batch(tmp_path):
    path = tmp_path / "products.db"
    ProductRepository(str(path))
    product = Product(
        barcode="8901058000269", name="Test snack", brand="Test", quantity="50 g",
        category="snacks", category_tags=["en:snacks"], ingredients_text="Wheat flour, salt.",
        nutriments={"energy_kcal": 350, "sugars_g": 3, "saturated_fat_g": 2, "sodium_mg": 300},
    ).model_dump(mode="json")
    evidence = {"declared_barcode": product["barcode"], "retrieved_at": "2026-10-21T10:00:00Z",
                "sources": [{"url": "https://store.example/item/test"}],
                "stored_nutrition_basis": "per_100g", "review_notes": "Reviewed test evidence."}
    return path, {"batch_id": "test-store-batch", "entries": [{"product": product, "evidence": evidence}]}


def test_dry_run_is_read_only(batch):
    path, manifest = batch
    assert run(path, manifest)["added"] == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
    assert not list(path.parent.glob("*.backup-*.db"))


def test_apply_backs_up_inserts_provisional_and_records_audit_once(batch):
    path, manifest = batch
    manifest["entries"][0]["product"]["status"] = "verified"
    result = run(path, manifest, apply=True)
    assert result["added"] == 1
    with sqlite3.connect(result["backup"]) as backup:
        assert backup.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
    with sqlite3.connect(path) as conn:
        p = json.loads(conn.execute("SELECT data FROM products").fetchone()[0])
        assert p["status"] == "provisional"
        assert p["nutriments"]["fibre_g"] is None
        assert conn.execute("SELECT source FROM submissions").fetchone()[0] == "online store research"
    assert run(path, manifest, apply=True)["added"] == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1


@pytest.mark.parametrize(("field", "value", "message"), [
    ("barcode", "40125758", "Invalid"),
    ("ingredients_text", None, "ingredients"),
    ("category", "dairy", "category"),
])
def test_invalid_identity_or_category_prevents_writes(batch, field, value, message):
    path, manifest = batch
    manifest["entries"][0]["product"][field] = value
    with pytest.raises(ValueError, match=message):
        run(path, manifest, apply=True)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0


@pytest.mark.parametrize("mutation", ["missing_core", "bad_sodium", "wrong_barcode", "off_source", "basis"])
def test_bad_second_entry_rolls_back_whole_batch(batch, mutation):
    path, manifest = batch
    second = copy.deepcopy(manifest["entries"][0])
    second["product"]["barcode"] = "8901058022193"
    second["product"]["name"] = "Different snack"
    second["evidence"]["declared_barcode"] = "8901058022193"
    if mutation == "missing_core":
        second["product"]["nutriments"]["sugars_g"] = None
    elif mutation == "bad_sodium":
        second["product"]["nutriments"]["sodium_mg"] = 1_000_000
    elif mutation == "wrong_barcode":
        second["evidence"]["declared_barcode"] = "8901058000269"
    elif mutation == "off_source":
        second["evidence"]["sources"][0]["url"] = "https://world.openfoodfacts.org/product/8901058022193"
    else:
        second["evidence"]["stored_nutrition_basis"] = "per_serving"
    manifest["entries"].append(second)
    with pytest.raises(ValueError):
        run(path, manifest, apply=True)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
    assert not list(path.parent.glob("*.backup-*.db"))


def test_existing_barcode_cannot_be_overwritten(batch):
    path, manifest = batch
    repo = ProductRepository(str(path))
    repo.upsert(Product(barcode="8901058000269", name="Existing"))
    with pytest.raises(ValueError, match="already exists"):
        run(path, manifest, apply=True)
    assert repo.get("8901058000269").name == "Existing"


def test_equivalent_gtin_and_identity_are_blocked(batch):
    path, manifest = batch
    p = manifest["entries"][0]["product"]
    repo = ProductRepository(str(path))
    repo.upsert(Product.model_validate(p).model_copy(update={"barcode": "08901058000269"}))
    with pytest.raises(ValueError, match="equivalent GTIN"):
        run(path, manifest)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM products")
    repo.upsert(Product.model_validate(p).model_copy(update={"barcode": "8901058022193", "quantity": "50gm"}))
    with pytest.raises(ValueError, match="Brand/name/pack"):
        run(path, manifest)


def test_audit_flags_identity_matches_without_deleting_distinct_packs(batch):
    path, manifest = batch
    repo = ProductRepository(str(path))
    p = Product.model_validate(manifest["entries"][0]["product"])
    repo.upsert(p)
    repo.upsert(p.model_copy(update={"barcode": "8901058022193", "quantity": "50gm"}))
    repo.upsert(p.model_copy(update={"barcode": "8901058000290", "quantity": "100 g"}))
    with sqlite3.connect(path) as conn:
        result = audit(conn)
    assert result["unique_barcodes"] == 3
    assert not result["repeated_barcodes"]
    assert len(result["same_identity_candidates"]) == 1
    assert len(result["same_identity_candidates"][0]) == 2
    assert quantity_key("0.5 kg") == quantity_key("500 g")
    assert quantity_key("1 L") == quantity_key("1000 ml")
