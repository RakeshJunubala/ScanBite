# MAGGI online-data pilot

Completed 21 October 2026 against the local `backend/data/products.db`.

Ten existing barcode records were updated. Seven previously unscored products
received scores from the unchanged `0.2-draft` engine. The database still holds
902 products, now with 626 scored and 276 unscored. Of 26 MAGGI-related records,
25 now have scores. Records remain `community`, not `verified`.

## Saved results

| Barcode | Product | Pack | Score before | Score after | Evidence or distinction |
| --- | --- | --- | --- | --- | --- |
| 8901058000269 | 2-Minute Noodles, Masala | 280 g | None | 11 | Label photos; 25.6% mixed spices in tastemaker |
| 8901058000290 | 2-Minute Noodles, Masala | 70 g | None | 11 | Label photos; 25.6% mixed spices in tastemaker |
| 8901058022193 | 2-Minute Noodles, Masala | 70 g | None | 13 | Label photos; 26.2% mixed spices in tastemaker |
| 8901058000276 | 2-Minute Noodles, Masala | 140 g | None | 18 | Exact-barcode structured nutrition; ingredients unavailable |
| 8901058003000 | Pazzta, Cheese Macaroni | 75 g | None | 36 | Front-of-pack nutrition and ingredient photos |
| 89080153 | Masala-ae-Magic seasoning | 6 g | None | 19 | Label photos; 38.7% mixed-spice formulation |
| 89080672 | Masala-ae-Magic seasoning | 6 g | None | 19 | Label photos; 35.3% mixed-spice formulation |
| 8901058000252 | 2-Minute Noodles, Masala | 420 g | 10 | 7 | Replaced barcode-only name, added source ingredients, assigned category |
| 8901058003017 | Pazzta, Masala Penne | 69.5 g | 40 | 40 | Corrected category from instant noodles to pasta |
| 8901058003079 | Pazzta, Cheesy Tomato Twist | 68.5 g | 23 | 23 | Corrected category from instant noodles to pasta |

Scores below 25 map to Avoid, 25–49 to Limit under the existing draft rules.
No thresholds, additive risk tiers or scoring functions were changed.

The 140 g record is **nutrition-only evidence**. Its score of 18 omits
ingredient-dependent penalties because no ingredient list was available for
that barcode. The current engine's `incomplete` field tracks missing core
nutrition, not missing ingredients. Its score must not be interpreted as a
complete ingredient assessment or as evidence that this pack has a better recipe.

## Product and recipe differentiation

- Masala wheat noodles use refined wheat flour and palm oil. Two observed
  ingredient lists declare 25.6% versus 26.2% mixed spices **within the
  tastemaker**. These are recipe distinctions, not different marketed flavours.
  They remain separate barcode records; no nutrition was copied between them.
- Cheese Macaroni is semolina pasta. Its tastemaker lists milk solids, cheese
  (5.8%) and sweetcorn (5.5%). It is separate from Cheesy Tomato Twist, whose
  existing ingredient list includes tomato, cheese and bell pepper, and Masala
  Penne, whose existing list includes a mixed-spice tastemaker.
- Masala-ae-Magic is seasoning rather than noodles. Its two newly enriched
  barcodes have ingredient lists declaring 38.7% and 35.3% mixed spices.
  Neither was substituted with the generic current manufacturer nutrition table.
- Different pack sizes and barcodes were retained. No records were merged or
  deleted. The unscored `0941458017687` record still lacks usable nutrition and
  ingredients; another similarly named barcode was not used as a substitute.

Names and categories are stored in the normal product fields. Family, flavour,
shape where applicable, and ingredient distinctions are retained in the
manifest and in each updated record's `submissions.notes` audit entry. These
are not new public API fields or app flavour filters.

## Evidence and conversions

The reviewed manifest is
[`backend/data/enrichments/maggi-20261021.json`](../backend/data/enrichments/maggi-20261021.json).
Each entry records its exact-barcode source URL, retrieval time, Open Food Facts
revision, photo URLs, data changes and recipe notes. The source JSON and downloaded
photos are retained in `outputs/maggi-pilot-20261021/`.

- [280 g Masala nutrition photo](https://images.openfoodfacts.org/images/products/890/105/800/0269/nutrition_en.41.full.jpg)
- [70 g Masala nutrition photo, barcode 8901058000290](https://images.openfoodfacts.org/images/products/890/105/800/0290/nutrition_en.9.full.jpg)
- [70 g Masala nutrition photo, barcode 8901058022193](https://images.openfoodfacts.org/images/products/890/105/802/2193/nutrition_en.13.full.jpg)
- [Cheese Macaroni front label](https://images.openfoodfacts.org/images/products/890/105/800/3000/front_en.13.full.jpg)
- [38.7% spice-blend nutrition photo](https://images.openfoodfacts.org/images/products/000/008/908/0153/nutrition_en.16.full.jpg)
- [35.3% spice-blend nutrition photo](https://images.openfoodfacts.org/images/products/000/008/908/0672/nutrition_en.18.full.jpg)

For barcode 8901058022193, the API's sodium field would imply 1,000,000 mg per
100 g. The readable label explicitly declares **1000 mg per 100 g**, which was
stored instead. A conflicting added-sugar estimate for barcode 89080672 was
also replaced with the printed value, 12.6 g per 100 g.

Cheese Macaroni's front label gives a 75 g serving: 241 kcal, 2.3 g total fat,
2.2 g saturated fat, 5.4 g total sugars and 544.6 mg sodium. Each was multiplied
by `100 / 75` for storage per 100 g. Unavailable nutrients were kept missing,
not filled with zero. Ingredients were transcribed from the associated photos;
existing unrelated product information was retained.

Open Food Facts records are community contributions and barcode-linked images
can represent different packaging dates. This pilot records the observed source
versions; it does not establish that every currently sold pack has that recipe.

## Verification and recovery

- 126 backend tests passed, including six new enrichment tests.
- Lint passed for the new script and tests.
- Stored scores match the existing scoring engine; all updated nutrition passed
  the existing plausibility checks.
- All ten changed records have source and variant audit entries.
- Comparison with the backup confirmed that only the ten intended products changed.
- SQLite integrity check passed. A second dry run reported zero changes.
- A pre-update SQLite backup is stored at
  `backend/data/products.backup-20261021-083336-776333.db`.

The application script is
[`backend/scripts/apply_product_enrichment.py`](../backend/scripts/apply_product_enrichment.py).
It defaults to a dry run. `--apply` creates a backup and saves the full batch and
its evidence in one transaction. It rejects stale rows, mismatched source
barcodes, implausible nutrition and attempts to replace verified records.
