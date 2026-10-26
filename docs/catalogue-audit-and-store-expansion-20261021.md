# Catalogue duplicate audit and non-OFF store expansion

Reviewed on 21 October 2026.

The database has no repeated barcode rows or equivalent UPC/EAN/GTIN representations. This does **not** prove every physical product identity is unique. Six existing pairs share normalized brand and product name; four also have matching declared pack sizes, while two pairs lack pack sizes. They remain review candidates. No records were deleted or merged.

## Existing potential duplicate pairs

| Product | Barcodes | Pack | Assessment |
|---|---|---|---|
| Sprite, Coca-Cola | 3948764032912 / 8901764032912 | 250 ml | Same stated identity; alternate barcode or erroneous source record needs confirmation. |
| Thums Up | 3948764042911 / 8901764042911 | 250 ml | Same stated identity; conflicting scores also warrant source/recipe review. |
| MAGGI Masala 2-Minute Noodles | 8901058000290 / 8901058022193 | 70 g | Prior pilot kept distinct barcode/label versions; matching names alone do not justify merging. |
| Britannia Milk Bikis | 8901063012493 / 8901063012868 | Unknown | Missing pack sizes prevent deciding if these are the same SKU. |
| Amul Cheese | 8901262020039 / 8901262020244 | 200 g | Generic names may hide slices, cubes or another format; needs label confirmation. |
| Parle Monaco | 8901719135088 / 8901719135118 | Unknown | Missing pack sizes/variant detail prevent a duplicate decision. |

An exact panel + normalized ingredient text + pack comparison found no cross-barcode identical groups among records with ingredients and at least three core nutrients. Incomplete records and inconsistent naming limit this check. Duplicate checking cannot establish GS1 ownership, physical pack equivalence or recipe currency from a checksum alone.

## New products added

Added **10 new products** from BigBasket indexed supermarket listings and Slurrp Farm’s manufacturer storefront. No Open Food Facts lookup or product data was used for this batch. A 902-product catalogue is only a small subset of Open Food Facts; the store expansion is a source-diversification step, not evidence that OFF has been exhausted.

| Metric | Before | After |
|---|---:|---:|
| Total products | 902 | 912 |
| Scored | 715 | 725 |
| Unscored | 187 | 187 |

All ten new records have ingredient lists and all four core nutrients (energy, total sugars, saturated fat, sodium). Scores use the unchanged `0.2-draft` ScanBite method. They are **provisional**, not independently verified pack records, and retain source evidence in the submissions audit table. Optional undeclared nutrients remain unknown. No price or retailer recommendation affects scoring.

| Barcode | Product | Pack | Score / 100 | Source |
|---|---|---|---:|---|
| 8908006217076 | Slurrp Farm Millet Spinach Dosa Mix | 150 g | 95 | [Source](https://www.bigbasket.com/pd/40125757/slurrp-farm-millet-dosa-mix-supergrains-spinach-150-g/) |
| 8906143891081 | The Whole Truth Orange Dark Cocoa Bar - Sweetened With Dates | 80 g | 25 | [Source](https://www.bigbasket.com/pd/40290578/the-whole-truth-orange-dark-chocolate-no-added-sugar-80-g/) |
| 8906143891470 | The Whole Truth Creamy & Crunchy Ragi Chocolate - Sweetened With Dates | 50 g | 24 | [Source](https://www.bigbasket.com/pd/40316242/the-whole-truth-creamy-crunchy-ragi-chocolate-50-g/) |
| 8901042973296 | MTR Dry Jamun | 200 g | 17 | [Source](https://www.bigbasket.com/pd/40376053/mtr-foods-dry-jamun-200-g/) |
| 8906069400022 | Veeba Thousand Island Dressing | 300 g | 17 | [Source](https://www.bigbasket.com/pd/40049007/veeba-thousand-island-dressing-300-g-bottle/) |
| 8904424805512 | Happilo Prasadam Makhana | 200 g | 100 | [Source](https://www.bigbasket.com/pd/40362552/happilo-prasadam-makhana-200-g/) |
| 8906081122773 | Happilo Himalayan Pink Salt & Pepper Makhana | 20 g | 22 | [Source](https://bbnow.bigbasket.com/pd/40362555/happilo-himalayan-pink-salt-pepper-makhana-20-g/) |
| 8908006217915 | Slurrp Farm Classic Millet Pancake Mix | 150 g | 67 | [Source](https://slurrpfarm.com/products/classic-millet-pancake-no-maida) |
| 8908006217892 | Slurrp Farm Blueberry Millet Pancake Mix | 150 g | 61 | [Source](https://slurrpfarm.com/products/millet-and-blueberry-pancake) |
| 8908006217083 | Slurrp Farm Banana Choco-Chip Millet Pancake Mix | 150 g | 46 | [Source](https://slurrpfarm.com/products/millet-pancake-banana-choco-chip-and-supergrains) |

## Source review and exclusions

- Retailer listings often put internal product IDs such as 40125758 or 40290579 in an EAN field. Those were not used as scanner barcodes. Only valid checksum barcodes explicitly associated with the chosen pack were accepted.
- Manufacturer bundle identifiers such as `8908006217915/3` were excluded; only the valid single-pack barcode was added.
- Per-serving panels were converted to per 100 g using the explicitly declared serving mass. Blueberry and banana pancakes use the current manufacturer per-40-g images. Flavours retain their own ingredient lists and panels.
- The classic pancake nutrition table declares 1.2 g saturated fat/100 g, while its footer says not more than 1%. The explicit table value is retained with the discrepancy recorded in source notes; physical-pack review remains needed.
- The salted makhana retailer lists sugar in seasoning but 0 g added sugar. Added sugar is left unknown in the product; the raw 0 declaration is preserved in source evidence. Total sugars are declared and available for scoring.
- Orange cocoa-bar trans fat is reported as less than 0.5 g. It remains unknown in the scalar model rather than becoming an exact 0.5 g.
- MTR Paneer Makhani was not added because the reviewed panel omitted total sugar. Other candidates lacked a valid product barcode or an unambiguous nutrition basis. Existing Saffola Peppy Tomato barcode 8901088068741 was skipped.
- One direct BigBasket page request returned HTTP 429, so further direct page requests were stopped. Retailer data came from the indexed listing results already available; manufacturer JSON and images were downloaded directly. Indexed retailer data may lag the current physical pack. These sources were not labelled verified.
- Empty allergen/traces fields mean no statement was captured. They do not establish allergen absence. The report records allergen information from explicit ingredients or supplied label statements.

## Files and repeatable checks

- Applied manifest: `backend/data/enrichments/store-products-20261021.json`.
- Source transcriptions, manufacturer product JSON and images: `outputs/store-expansion-20261021/`.
- Duplicate audit: `backend/scripts/audit_product_duplicates.py` (read-only); detailed JSON before and after is in the output directory.
- Insert tool: `backend/scripts/add_store_products.py`; dry run by default. It validates every entry before a transactional insert, rejects existing/equivalent barcodes and matching normalized brand/name/pack, forces provisional status and saves a database backup plus source audit entries. It never overwrites existing products.
- Validation: 139 backend tests passed; lint passed for the new scripts/tests. Database integrity OK, all 902 existing product rows unchanged, ten intended rows added, ten provenance entries, and no additional duplicate candidates.
- All ten saved scores equal fresh engine calculations. Reapplying the identical batch is a no-op.
- Backup: `backend\data\products.backup-20261021-094501-580503.db`.

Run from the repository root using an environment with backend dependencies installed:

```powershell
python backend/scripts/audit_product_duplicates.py --db backend/data/products.db
python backend/scripts/add_store_products.py backend/data/enrichments/store-products-20261021.json --db backend/data/products.db
```

The second command is a dry run; an already-applied batch reports zero additions.
