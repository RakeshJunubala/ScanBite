"""Storage behaviour, especially keeping stored scores and the engine in step."""

import sqlite3

from app.models import DataStatus, Product
from app.repository import ProductRepository
from app.scoring import METHOD_VERSION


def _product(barcode: str, name: str = "Test", **nutriments) -> Product:
    values = {"energy_kcal": 450, "sugars_g": 20.0, "saturated_fat_g": 8, "sodium_mg": 300}
    values.update(nutriments)
    return Product(
        barcode=barcode,
        name=name,
        category="biscuits",
        nutriments=values,
        status=DataStatus.community,
    )


def _stored(repo: ProductRepository, barcode: str) -> sqlite3.Row:
    # Reading raw columns is the point of these tests.
    with repo._tx() as cur:
        return cur.execute(
            "SELECT score, score_method_version FROM products WHERE barcode = ?", (barcode,)
        ).fetchone()


def test_upsert_records_the_method_that_produced_the_score():
    repo = ProductRepository(":memory:")
    repo.upsert(_product("8900000000012"))

    row = _stored(repo, "8900000000012")
    assert row["score_method_version"] == METHOD_VERSION
    assert row["score"] is not None
    assert repo.stale_count() == 0


def test_rescore_stale_updates_rows_written_by_an_older_method():
    repo = ProductRepository(":memory:")
    repo.upsert(_product("8900000000012"))

    # Simulate the rules having changed since this row was written.
    with repo._tx() as cur:
        cur.execute("UPDATE products SET score = 99, score_method_version = '0.0-old'")

    assert repo.stale_count() == 1
    assert repo.rescore_stale() == 1

    row = _stored(repo, "8900000000012")
    assert row["score_method_version"] == METHOD_VERSION
    assert row["score"] != 99  # recomputed from `data`, not left as the old value
    assert repo.stale_count() == 0
    assert repo.rescore_stale() == 0  # nothing left to do


def test_alternatives_ranking_follows_the_rescore():
    """The bug this column exists to prevent: ranking on a stale score column."""
    repo = ProductRepository(":memory:")
    repo.upsert(_product("8900000000012", "Sugary", sugars_g=40))  # really scores 14
    repo.upsert(
        _product(
            "8901719134845", "Better",
            sugars_g=1, saturated_fat_g=0.5, sodium_mg=30, fibre_g=8, protein_g=10, energy_kcal=350,
        )  # really scores 100
    )

    # Leave the stored column as a stale method would have: the worse product
    # looking good and the better one looking bad.
    with repo._tx() as cur:
        cur.execute("UPDATE products SET score = 90, score_method_version = '0.0-old' WHERE name = 'Sugary'")
        cur.execute("UPDATE products SET score = 10, score_method_version = '0.0-old' WHERE name = 'Better'")

    # "Better choices" recommends the sugary one, because it ranks on the column.
    assert [p.name for p in repo.alternatives("biscuits", 20, exclude="x")] == ["Sugary"]

    repo.rescore_stale()

    # Now it recommends the one that is actually better.
    assert [p.name for p in repo.alternatives("biscuits", 20, exclude="x")] == ["Better"]


def test_migration_adds_the_column_to_a_database_that_predates_it(tmp_path):
    """A database created before the column existed must not need deleting."""
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript(
        """
        CREATE TABLE products (
            barcode    TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            brand      TEXT,
            category   TEXT,
            status     TEXT NOT NULL,
            score      INTEGER,
            data       TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    product = _product("8900000000012")
    old.execute(
        "INSERT INTO products (barcode, name, status, score, data) VALUES (?, ?, ?, ?, ?)",
        (product.barcode, product.name, product.status.value, 42, product.model_dump_json()),
    )
    old.commit()
    old.close()

    repo = ProductRepository(str(path))  # opening it runs the migration

    # The pre-existing row has a NULL version, which must count as stale.
    assert repo.stale_count() == 1
    assert repo.rescore_stale() == 1
    assert _stored(repo, "8900000000012")["score_method_version"] == METHOD_VERSION
    assert repo.get("8900000000012").name == "Test"  # the original row survived
