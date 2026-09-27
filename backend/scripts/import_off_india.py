"""Import India-tagged products from Open Food Facts into our database.

Run from backend/:

    python scripts/import_off_india.py --limit 200        # try it out first
    python scripts/import_off_india.py                    # the full pull

Open Food Facts rate-limits reads, so this pages politely and can be re-run:
progress is kept in a state file next to the database and picked up where it
stopped. Re-running after a completed import refreshes the records.

Licence: Open Food Facts data is ODbL (share-alike). Caching lookups is one
thing; holding and shipping a derived database is a heavier obligation, and it
needs checking before public release. See docs/ and app/sources/off.py.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.models import DataStatus
from app.repository import ProductRepository
from app.service import is_valid_barcode, normalize_barcode
from app.sources.off import FIELDS, map_off_product

SEARCH_URL = "https://world.openfoodfacts.org/api/v2/search"
COUNTRY = "india"
SOURCE_VERSION = "off-api-v2"

# Open Food Facts asks for roughly 10 search requests a minute. 7 seconds keeps
# us inside that with room to spare; the whole pull is bounded by this, not by us.
DEFAULT_DELAY_S = 7.0
DEFAULT_PAGE_SIZE = 100
MAX_RETRIES = 4


@dataclass
class Counts:
    seen: int = 0
    imported: int = 0
    skipped_more_trusted: int = 0
    skipped_bad_barcode: int = 0
    failed: int = 0
    reasons: dict[str, int] = field(default_factory=dict)

    def note(self, reason: str) -> None:
        self.reasons[reason] = self.reasons.get(reason, 0) + 1


def fetch_page(client: httpx.Client, page: int, page_size: int) -> dict:
    """One page of results, retrying on the throttling and outage codes."""
    params = {
        "countries_tags_en": COUNTRY,
        "fields": FIELDS,
        "page_size": page_size,
        "page": page,
    }
    delay = 10.0
    for attempt in range(1, MAX_RETRIES + 1):
        response = client.get(SEARCH_URL, params=params)
        if response.status_code == 200:
            return response.json()
        if response.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
            print(f"    HTTP {response.status_code}, waiting {delay:.0f}s (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(delay)
            delay *= 2
            continue
        response.raise_for_status()
    raise RuntimeError(f"page {page} kept failing")


def store(repo: ProductRepository, raw: dict, counts: Counts) -> None:
    counts.seen += 1
    code = normalize_barcode(str(raw.get("code") or "").strip())

    # A record whose barcode our own validation rejects would be unreachable:
    # GET /v1/products/{barcode} returns 400 before it ever reaches the database.
    if not is_valid_barcode(code):
        counts.skipped_bad_barcode += 1
        return

    try:
        product = map_off_product(code, raw)
    except Exception as err:  # noqa: BLE001 - one malformed record must not end a 23k import
        counts.failed += 1
        counts.note(f"map failed: {type(err).__name__}")
        return

    if product.name == "Unnamed product":
        counts.failed += 1
        counts.note("no product name")
        return

    assert product.status is DataStatus.community, "imports must not claim a higher trust than community"

    if repo.upsert(product, source_version=SOURCE_VERSION):
        counts.imported += 1
    else:
        # upsert() refuses to let community data displace a more trusted record.
        counts.skipped_more_trusted += 1


def load_state(path: Path) -> int:
    if not path.exists():
        return 1
    try:
        return int(json.loads(path.read_text(encoding="utf-8"))["next_page"])
    except (ValueError, KeyError, OSError):
        return 1


def save_state(path: Path, next_page: int) -> None:
    path.write_text(json.dumps({"next_page": next_page}, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=0, help="stop after about this many products (0 = all)")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_S, help="seconds between requests")
    parser.add_argument("--db", default=None, help="database path (default: DATABASE_PATH from settings)")
    parser.add_argument("--restart", action="store_true", help="ignore saved progress and start from page 1")
    parser.add_argument("--dry-run", action="store_true", help="fetch and map, write nothing")
    args = parser.parse_args()

    settings = get_settings()
    db_path = args.db or settings.database_path
    if settings.off_user_agent.startswith("ScanBite/0.1 (set "):
        print("Refusing to run with the placeholder OFF_USER_AGENT.")
        print("Open Food Facts asks apps to identify themselves. Set it to your contact email:")
        print('  export OFF_USER_AGENT="ScanBite/0.1 (you@example.com)"')
        return 2

    repo = ProductRepository(db_path)
    state_path = Path(db_path).with_suffix(".import-state.json")
    page = 1 if args.restart else load_state(state_path)
    counts = Counts()

    print(f"database   : {db_path} ({repo.count()} products now)")
    print(f"state file : {state_path}")
    print(f"starting at page {page}, {args.page_size} per page, {args.delay:.1f}s between requests")
    if args.dry_run:
        print("DRY RUN - nothing will be written")
    print()

    headers = {"User-Agent": settings.off_user_agent, "Accept": "application/json"}
    total = None
    try:
        with httpx.Client(timeout=60.0, headers=headers) as client:
            while True:
                body = fetch_page(client, page, args.page_size)
                if total is None:
                    total = body.get("count")
                    print(f"Open Food Facts reports {total} products tagged {COUNTRY}\n")

                products = body.get("products") or []
                if not products:
                    print("No more products.")
                    break

                for raw in products:
                    if args.dry_run:
                        counts.seen += 1
                    else:
                        store(repo, raw, counts)

                print(
                    f"  page {page:>3}: +{len(products):>3} seen={counts.seen} "
                    f"imported={counts.imported} skipped={counts.skipped_more_trusted + counts.skipped_bad_barcode} "
                    f"failed={counts.failed}"
                )

                page += 1
                if not args.dry_run:
                    save_state(state_path, page)

                if args.limit and counts.seen >= args.limit:
                    print(f"\nReached --limit {args.limit}.")
                    break
                if total and counts.seen >= total:
                    break
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nInterrupted. Re-run to carry on from where it stopped.")
    except Exception as err:  # noqa: BLE001 - report and let the caller resume
        print(f"\nStopped on {type(err).__name__}: {err}")
        print("Re-run to carry on from where it stopped.")
        return 1

    print()
    print(f"seen                   : {counts.seen}")
    print(f"imported               : {counts.imported}")
    print(f"skipped, more trusted  : {counts.skipped_more_trusted}")
    print(f"skipped, bad barcode   : {counts.skipped_bad_barcode}")
    print(f"failed                 : {counts.failed}")
    for reason, n in sorted(counts.reasons.items(), key=lambda kv: -kv[1]):
        print(f"    {reason}: {n}")
    print(f"products in database   : {repo.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
