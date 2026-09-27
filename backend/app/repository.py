"""Product storage.

Week 1 uses SQLite from the Python standard library, so the API runs with no
database server. Week 2 swaps this class for a Postgres one with the same
methods; nothing else in the app talks to the database directly.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .models import DataStatus, Product
from .scoring import METHOD_VERSION, score_product

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    barcode    TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    brand      TEXT,
    category   TEXT,
    status     TEXT NOT NULL,
    score      INTEGER,
    -- Which method produced `score`. Search and alternatives rank on the stored
    -- column while a lookup rescores from `data`, so without this a change to
    -- the scoring rules splits the two apart silently -- the detail view says 52
    -- and the "better choices" list still ranks it as 49. See rescore_stale().
    score_method_version TEXT,
    data       TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_products_category_score ON products (category, score);
CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);

-- Who submitted what, append-only. Kept out of the products table, and out of
-- every API response, because submitted_by can be a person's email address. The
-- week-4 review tool reads this to decide whether a provisional record is
-- trustworthy, so superseded rows are history, not clutter.
CREATE TABLE IF NOT EXISTS submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode         TEXT NOT NULL,
    submitted_by    TEXT,
    source          TEXT,
    notes           TEXT,
    label_photo_url TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_submissions_barcode ON submissions (barcode);
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
        self._migrate()

    def _migrate(self) -> None:
        """Add columns to databases created before those columns existed.

        CREATE TABLE IF NOT EXISTS is a no-op on an existing table, so a new
        column never reaches a database that already has products in it.
        """
        with self._tx() as cur:
            columns = {r["name"] for r in cur.execute("PRAGMA table_info(products)").fetchall()}
            if "score_method_version" not in columns:
                # NULL on existing rows, which rescore_stale() treats as stale.
                cur.execute("ALTER TABLE products ADD COLUMN score_method_version TEXT")

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

    def get(self, barcode: str) -> Product | None:
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
                INSERT INTO products
                    (barcode, name, brand, category, status, score, score_method_version, data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(barcode) DO UPDATE SET
                    name=excluded.name, brand=excluded.brand, category=excluded.category,
                    status=excluded.status, score=excluded.score,
                    score_method_version=excluded.score_method_version, data=excluded.data,
                    updated_at=excluded.updated_at
                """,
                (
                    product.barcode,
                    product.name,
                    product.brand,
                    product.category,
                    product.status.value,
                    score,
                    METHOD_VERSION,
                    product.model_dump_json(),
                ),
            )
        return True

    def stale_count(self, version: str = METHOD_VERSION) -> int:
        """Rows whose stored score was produced by a different method version."""
        with self._tx() as cur:
            return cur.execute(
                "SELECT COUNT(*) FROM products WHERE score_method_version IS NOT ?", (version,)
            ).fetchone()[0]

    def rescore_stale(self, version: str = METHOD_VERSION) -> int:
        """Recompute every score not produced by the current method. Returns how many.

        Run this whenever METHOD_VERSION changes. The product itself is stored as
        JSON in `data`, so rescoring needs no network and no source lookup -- it
        replays the current engine over what we already hold.

        `IS NOT` rather than `!=` so that NULL (a row written before the column
        existed) counts as stale instead of silently comparing unequal to
        everything and nothing.
        """
        with self._tx() as cur:
            rows = cur.execute(
                "SELECT barcode, data FROM products WHERE score_method_version IS NOT ?", (version,)
            ).fetchall()

        if not rows:
            return 0

        updates = []
        for row in rows:
            product = Product.model_validate_json(row["data"])
            updates.append((score_product(product).score, version, row["barcode"]))

        with self._tx() as cur:
            cur.executemany(
                "UPDATE products SET score = ?, score_method_version = ? WHERE barcode = ?", updates
            )
        return len(updates)

    def record_submission(
        self,
        barcode: str,
        submitted_by: str | None = None,
        source: str | None = None,
        notes: str | None = None,
        label_photo_url: str | None = None,
    ) -> None:
        """Log where a submitted product came from. Never returned by the API."""
        with self._tx() as cur:
            cur.execute(
                """
                INSERT INTO submissions (barcode, submitted_by, source, notes, label_photo_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (barcode, submitted_by, source, notes, label_photo_url),
            )

    def submissions(self, barcode: str) -> list[dict]:
        """Submission history for one barcode, newest first. For the review tool."""
        with self._tx() as cur:
            rows = cur.execute(
                "SELECT * FROM submissions WHERE barcode = ? ORDER BY id DESC", (barcode,)
            ).fetchall()
        return [dict(r) for r in rows]

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
