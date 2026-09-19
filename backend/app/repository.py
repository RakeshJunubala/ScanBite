"""Product storage.

Week 1 uses SQLite from the Python standard library, so the API runs with no
database server. Week 2 swaps this class for a Postgres one with the same
methods; nothing else in the app talks to the database directly.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from .models import DataStatus, Product
from .scoring import score_product

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    barcode    TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    brand      TEXT,
    category   TEXT,
    status     TEXT NOT NULL,
    score      INTEGER,
    data       TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_products_category_score ON products (category, score);
CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);
"""

# A verified record is never overwritten by a lower-trust source.
_TRUST = {DataStatus.verified: 3, DataStatus.provisional: 2, DataStatus.community: 1, DataStatus.sample: 0}


class ProductRepository:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # One shared connection keeps ":memory:" databases alive for tests.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._tx() as cur:
            cur.executescript(SCHEMA)

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def count(self) -> int:
        with self._tx() as cur:
            return cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    def get(self, barcode: str) -> Optional[Product]:
        with self._tx() as cur:
            row = cur.execute("SELECT data FROM products WHERE barcode = ?", (barcode,)).fetchone()
        return Product.model_validate_json(row["data"]) if row else None

    def upsert(self, product: Product) -> bool:
        """Save a product. Returns False if a more trusted record already exists."""
        existing = self.get(product.barcode)
        if existing and _TRUST[existing.status] > _TRUST[product.status]:
            return False
        score = score_product(product).score
        with self._tx() as cur:
            cur.execute(
                """
                INSERT INTO products (barcode, name, brand, category, status, score, data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(barcode) DO UPDATE SET
                    name=excluded.name, brand=excluded.brand, category=excluded.category,
                    status=excluded.status, score=excluded.score, data=excluded.data,
                    updated_at=excluded.updated_at
                """,
                (
                    product.barcode,
                    product.name,
                    product.brand,
                    product.category,
                    product.status.value,
                    score,
                    product.model_dump_json(),
                ),
            )
        return True

    def alternatives(self, category: str, better_than: int, exclude: str, limit: int = 3) -> list[Product]:
        with self._tx() as cur:
            rows = cur.execute(
                """
                SELECT data FROM products
                WHERE category = ? AND score > ? AND barcode != ?
                ORDER BY score DESC, name ASC LIMIT ?
                """,
                (category, better_than, exclude, limit),
            ).fetchall()
        return [Product.model_validate_json(r["data"]) for r in rows]

    def search(self, query: str, limit: int = 20) -> list[Product]:
        like = f"%{query.strip().lower()}%"
        with self._tx() as cur:
            rows = cur.execute(
                """
                SELECT data FROM products
                WHERE lower(name) LIKE ? OR lower(coalesce(brand, '')) LIKE ?
                ORDER BY score DESC LIMIT ?
                """,
                (like, like, limit),
            ).fetchall()
        return [Product.model_validate_json(r["data"]) for r in rows]
