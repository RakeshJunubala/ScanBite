# Moving the ScanBite catalogue between computers

`backend/data/catalogue.json` is the portable catalogue checked into Git. The initial
snapshot contains **930 products: 743 scored and 187 unscored**, using `0.2-draft`.
Unscored entries are included so research can continue on another computer.

The snapshot preserves barcode, name, brand, pack quantity, category, ingredients,
nutrition, allergens, status, stored score, scoring-method version, source version
and product update time. Community/Open Food Facts records are grouped separately
from other records, with Open Food Facts contributor attribution and an ODbL link.
Exact research sources and review notes remain in the accompanying enrichment
manifests under `backend/data/enrichments/`.

The product snapshot excludes the submissions table, including contributor identities
and private submission history. It is not a full database backup. The existing local
database and backups remain available on the original computer. Downloaded label
photos and exports under `outputs/` are also excluded from Git; public source/image
URLs in the manifests remain available, subject to those websites retaining them.
Health profiles stay on the phone and are not part of this export.

## Fresh Windows computer

Install Git and Python 3.11 or later, then run these PowerShell commands:

```powershell
git clone https://github.com/RakeshJunubala/ScanBite.git
cd ScanBite/backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/catalogue_snapshot.py restore
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The restore command creates `backend/data/products.db`. Run it before starting the
API, which otherwise creates its own database. The commands become available on the
new computer after this work has been committed and pushed.

Use `npm.cmd ci` from `mobile/` to install the Android app dependencies, then follow
the main README to configure `mobile/.env` for the new computer's backend address.
Local environments, installed dependencies and secrets are recreated on each machine.

## Publish later catalogue updates

From `backend/`, with the project's Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/catalogue_snapshot.py export
```

Review the changed `data/catalogue.json`, then commit and push it with the code and
enrichment manifests that produced the update. Export does not commit or push.
The JSON is deterministic, so unchanged records do not receive new export timestamps.
The command rejects non-finite nutrition and stored scores that do not reproduce.
When the scoring method changes, rescore the working database with the matching app
code before exporting again.

## Existing database on the destination computer

Restore never merges with or overwrites an existing database. Preserve any local
work first. You can restore to a separate file for comparison:

```powershell
.\.venv\Scripts\python.exe scripts/catalogue_snapshot.py restore --db data/products-from-git.db
```

A Git pull updates the snapshot, not a running SQLite database. Both computers
should use the same code revision and snapshot. Decide which machine has the current
catalogue before refreshing it; exports from two independently edited databases
need reconciliation rather than blindly choosing one snapshot.

## Attribution

Community records contain data from [Open Food Facts](https://world.openfoodfacts.org/)
and its contributors. Its database is available under the
[Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).
Retain the snapshot's attribution, source labels and accompanying manifests when
sharing this catalogue. These product records remain community or provisional data;
export/restore does not promote their verification status. ScanBite scores remain
the application's custom draft ratings.
