"""Look inside the product database. Read-only.

Run from backend/:

    python scripts/inspect_db.py                          # summary
    python scripts/inspect_db.py --search parle           # find by name or brand
    python scripts/inspect_db.py --barcode 8901719134845  # one product in full
    python scripts/inspect_db.py --category biscuits      # what is in a category
    python scripts/inspect_db.py --unscored               # why products have no score
    python scripts/inspect_db.py --sql "SELECT ..."       # anything else

Opens the database read-only, so it is safe to run while the API is serving.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings

BAR = "-" * 72


def clean(value: object, width: int = 0) -> str:
    """Product names carry characters a Windows console cannot print."""
    text = str(value if value is not None else "")
    text = text.encode("ascii", "replace").decode()
    return text[:width].ljust(width) if width else text


def connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def summary(con: sqlite3.Connection, path: str) -> None:
    total = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    scored = con.execute("SELECT COUNT(*) FROM products WHERE score IS NOT NULL").fetchone()[0]
    size = Path(path).stat().st_size / 1024 / 1024

    print(f"{path}   {size:.2f} MB")
    print(BAR)
    print(f"products {total}    scored {scored}    unscored {total - scored} ({(total - scored) * 100 // max(total, 1)}%)")

    print("\nwhere the data came from")
    for r in con.execute("SELECT status, COUNT(*) n FROM products GROUP BY status ORDER BY n DESC"):
        print(f"  {clean(r['status'], 22)} {r['n']:>5}")

    print("\nverdict spread")
    bands = [("Great", 75, 100), ("Good", 50, 74), ("Limit", 25, 49), ("Avoid", 0, 24)]
    for label, low, high in bands:
        n = con.execute("SELECT COUNT(*) FROM products WHERE score BETWEEN ? AND ?", (low, high)).fetchone()[0]
        bar = "#" * min(round(n / max(scored, 1) * 40), 40)
        print(f"  {label:<8} {n:>5}  {bar}")
    none = total - scored
    print(f"  {'no score':<8} {none:>5}  {'#' * min(round(none / max(total, 1) * 40), 40)}")

    print("\ncategories (>= 8 products can support a ranking)")
    rows = con.execute(
        "SELECT COALESCE(category,'(none)') c, COUNT(*) n FROM products GROUP BY c ORDER BY n DESC"
    ).fetchall()
    for r in rows:
        note = "rankable" if r["n"] >= 8 and r["c"] != "(none)" else ""
        print(f"  {clean(r['c'], 24)} {r['n']:>5}  {note}")
    print(f"\n  {len(rows)} distinct categories")


def rows_table(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("nothing found")
        return
    print(f"{'barcode':<15} {'name':<34} {'category':<20} {'score':>5}  status")
    print(BAR)
    for r in rows:
        score = "-" if r["score"] is None else str(r["score"])
        print(
            f"{clean(r['barcode'], 15)} {clean(r['name'], 34)} "
            f"{clean(r['category'] or '-', 20)} {score:>5}  {clean(r['status'])}"
        )
    print(f"\n{len(rows)} row(s)")


def one_product(con: sqlite3.Connection, barcode: str) -> None:
    row = con.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
    if row is None:
        print(f"{barcode} is not in the database")
        return
    print(f"{clean(row['name'])}   [{row['barcode']}]")
    print(BAR)
    for key in ("brand", "category", "status", "score", "score_method_version", "source_version", "updated_at"):
        print(f"  {key:<22} {clean(row[key] if row[key] is not None else '-')}")

    product = json.loads(row["data"])
    print("\n  nutriments per 100 g/ml")
    for key, value in product["nutriments"].items():
        print(f"    {key:<22} {'-' if value is None else value}")
    for key in ("ingredients_text", "allergens", "traces", "labels", "additives", "image_url"):
        value = product.get(key)
        if value:
            print(f"\n  {key}\n    {clean(value if isinstance(value, str) else ', '.join(map(str, value)))[:300]}")


def unscored(con: sqlite3.Connection) -> None:
    """Which nutrients are missing from the products we cannot score."""
    rows = con.execute("SELECT name, data FROM products WHERE score IS NULL").fetchall()
    core = ("energy_kcal", "sugars_g", "saturated_fat_g", "sodium_mg")
    tally: dict[str, int] = {}
    for r in rows:
        n = json.loads(r["data"])["nutriments"]
        missing = tuple(k for k in core if n.get(k) is None)
        key = ", ".join(missing) if missing else "(all present -- check plausibility)"
        tally[key] = tally.get(key, 0) + 1
    print(f"{len(rows)} products have no score. What they are missing:\n")
    for key, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>5}  {key}")
    print("\nFirst few:")
    for r in rows[:10]:
        print(f"  {clean(r['name'], 46)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=None, help="database path (default: DATABASE_PATH from settings)")
    parser.add_argument("--search", help="find products by name or brand")
    parser.add_argument("--barcode", help="show one product in full")
    parser.add_argument("--category", help="list a category, best score first")
    parser.add_argument("--unscored", action="store_true", help="why products have no score")
    parser.add_argument("--sql", help="run any read-only query")
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    sys.stdout.reconfigure(errors="replace")
    path = args.db or get_settings().database_path
    if not Path(path).exists():
        print(f"No database at {path}")
        return 1
    con = connect(path)

    if args.barcode:
        one_product(con, args.barcode.strip())
    elif args.search:
        like = f"%{args.search.strip().lower()}%"
        rows_table(
            con.execute(
                "SELECT barcode,name,category,score,status FROM products "
                "WHERE lower(name) LIKE ? OR lower(COALESCE(brand,'')) LIKE ? "
                "ORDER BY score DESC NULLS LAST LIMIT ?",
                (like, like, args.limit),
            ).fetchall()
        )
    elif args.category:
        rows_table(
            con.execute(
                "SELECT barcode,name,category,score,status FROM products "
                "WHERE category = ? ORDER BY score DESC NULLS LAST LIMIT ?",
                (args.category.strip().lower(), args.limit),
            ).fetchall()
        )
    elif args.unscored:
        unscored(con)
    elif args.sql:
        rows = con.execute(args.sql).fetchall()
        for r in rows[: args.limit]:
            print("  ".join(clean(v) for v in tuple(r)))
        print(f"\n{len(rows)} row(s)")
    else:
        summary(con, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
