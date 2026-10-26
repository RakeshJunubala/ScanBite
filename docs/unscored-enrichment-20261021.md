# Online product enrichment — 21 October 2026

Checked all 276 previously unscored database barcodes against current Open Food Facts records. Found current records for 275; Dettol barcode 8901396350101 returned HTTP 404 and was outside the food-scoring scope anyway. Manufacturer and retailer pages were also researched, but no cross-barcode recipe was imported. The applied data comes from exact-barcode OFF records and their package photos.

| Database | Before | After |
|---|---:|---:|
| Products | 902 | 902 |
| Scored | 626 | 715 |
| Unscored | 276 | 187 |

Saved **89 new scores** using the unchanged ScanBite `0.2-draft` scorer. All updated products retain **community** status. This is ScanBite's custom draft method, not an official Nutri-Score certification or a medically validated rating.

Of these 89 records, 72 have ingredient lists (33 newly supplied), 65 have all four core nutrients, and 50 have both. 17 lack ingredients, so their scores omit ingredient-dependent penalties. 24 lack one core nutrient and carry the scorer's incomplete-nutrition flag. These two groups overlap. Missing ingredients alone do not trigger that flag in the current engine.

Core nutrients are energy, total sugars, saturated fat and sodium. Existing logic requires at least three of these four. Unknowns remain null; zero is only retained when explicitly declared in the source. For visually reviewed labels, ranges, less-than limits and Trace were kept unknown when the scalar model could not represent them. Unreviewed fruit/vegetable estimates were excluded from positive scoring credit.

## Matching and corrections

- Exact barcodes remain separate; no rows were merged and no flavour recipe was copied between barcodes.
- Corrected sodium unit errors using readable package photos, including Kissan sauces, Britannia Bourbon and Dr. Oetker mayonnaise.
- Corrected generic identities where the exact-barcode package supports them: Food / incorrect brand became Amul Amrakhand Mango; NG became Parle Nutricrunch Digestive Cookies; a barcode-only row became Dr. Oetker FunFoods Veg Mayonnaise Original.
- Knorr soup serving panels were converted to dry per-100-g powder using the declared powder serving weight and water-only preparation. No milk-prepared nutrition was transferred to dry products.
- Source snapshots and downloaded photos are in `outputs/unscored-enrichment-20261021/`; the applied manifest is `backend/data/enrichments/unscored-20261021.json`. Every changed row has a submissions audit entry with its previous data, source URL, retrieval time, source revision, photo URLs and review notes.

## Products still unscored

187 remain unscored. Missing panels, unreadable or wrong photos, nutrition quality errors, non-food/medicinal products, alcohol, supplements and ambiguous identities were left unchanged. The complete per-barcode review is in `outputs/unscored-enrichment-20261021/review.json`. Examples: a Fanta record shows an Everest spice photo; the Fortune mustard-oil record has a milk-food nutrition photo. Upper-bound saturated-fat declarations were not treated as exact measurements. Rooh Afza syrup declares more than 100 g sugar per 100 ml because of its density; it remains unscored because current plausibility limits cannot represent that concentration.

## Verification

- SQLite integrity: OK; exactly 89 intended product rows changed, all other product rows unchanged.
- All 89 persisted scores equal a fresh calculation by the current engine; 89 matching source audit records exist.
- Backend suite: 126 tests passed. No scorer thresholds, additive risk levels or application behavior changed.
- Database backup: `backend\data\products.backup-20261021-091427-875234.db`.
- The apply script defaults to dry run and supports an idempotent re-check; verification output is in `outputs/unscored-enrichment-20261021/verification.json`.

## External research

- [Open Food Facts API documentation](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/): product reads paced below its documented limit; source JSON cached. Batch search returned HTTP 503, so the pass used individual product lookups.
- [Parle-G manufacturer page](https://www.parleproducts.com/brands/parle-g) and [Freshdayz Parle-G retailer page](https://www.freshdayz.co.uk/products/parle-g-glucose-biscuits): retailer nutrition differed from the exact-barcode photo; the photographed panel was used.
- [Sabar Dairy Amul Masti Dahi](https://sabardairy.org/product/amul-masti-dahi/) and [Amul Dahi](https://old.amul.com/products/amul-mastidahi-info.php): differing panels and insufficient exact-pack corroboration; not substituted into unscored Dahi rows.
- [Parle Agro Appy Fizz](https://www.parleagro.com/brand/13): brand/variant research; exact-barcode OFF evidence supplied the applied panel.

## Newly scored products

Scores below are out of 100. “Core complete” means all four core nutrients, not that every possible nutrient is present. Source links lead to the exact barcode.

| Barcode | Product | Score | Core complete | Ingredients | Source |
|---|---|---:|---|---|---|
| 3948764032912 | Sprite | 11 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/3948764032912) |
| 7622202026423 | Cadbury Bournvita 500g pet | 27 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/7622202026423) |
| 7622202225598 | OREO | 10 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/7622202225598) |
| 7622202237416 | Bournvita 13.4g | 27 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/7622202237416) |
| 7622202252419 | Oreo 30 rs | 9 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/7622202252419) |
| 7622202272639 | Cadbury Dairy Milk | 10 | No: sodium_mg | Missing | [OFF](https://world.openfoodfacts.org/product/7622202272639) |
| 8000500411018 | Tic Tac Orange | 22 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8000500411018) |
| 8901014000371 | Geki Hot & Spicy Korean Cheese | 7 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901014000371) |
| 8901030902376 | Mixed Vegetable Soup | 14 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901030902376) |
| 8901030902383 | Manchow Veg | 12 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901030902383) |
| 8901030922770 | Kissan Mixed Fruit Jam | 22 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901030922770) |
| 8901030953200 | Kissan No onion no garlic Tomato Ketchup | 25 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901030953200) |
| 8901030953217 | Kissan Sweet & Spicy Sauce | 22 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901030953217) |
| 8901058016116 | KitKat 50 | 17 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901058016116) |
| 8901058018639 | Milkybar | 11 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901058018639) |
| 8901058905113 | Coated Wafer | 14 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901058905113) |
| 8901063012493 | Milk Bikis biscuits | 22 | No: sodium_mg | Yes | [OFF](https://world.openfoodfacts.org/product/8901063012493) |
| 8901063014411 | Vita Marie Gold | 18 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063014411) |
| 8901063016873 | 50-50 | 11 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063016873) |
| 8901063016934 | BRITANNIA 5050 | 11 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063016934) |
| 8901063017399 | Britannia 5050 maska chaska (300g) | 10 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901063017399) |
| 8901063028241 | 8901063028241 | 19 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901063028241) |
| 8901063032446 | Britannia Treat croissant coco cream bauli | 21 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063032446) |
| 8901063139329 | bourbon | 8 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063139329) |
| 8901063142244 | Nutri choice zero | 34 | No: sugars_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901063142244) |
| 8901063155534 | Krunch ChocoChips | 17 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901063155534) |
| 8901063162464 | BRITANNIA marie GOLD | 25 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063162464) |
| 8901063162549 | Marie gold | 17 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063162549) |
| 8901063325920 | Britannia Toastea Premium Bake Rusk with Real Elaichi | 28 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063325920) |
| 8901063341500 | White bread | 71 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063341500) |
| 8901063367180 | Brit 50 50 maska chaska 100g | 4 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901063367180) |
| 8901207026553 | Honey | 23 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901207026553) |
| 8901207053634 | Real Coconut water pet 1ltr | 53 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901207053634) |
| 8901246005373 | TOMATO KETCHUP CLASSIC BLEND | 26 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901246005373) |
| 8901262040044 | Amul shrikhand badam pista | 29 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901262040044) |
| 8901262040518 | Amul Amrakhand - Mango | 23 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901262040518) |
| 8901262151863 | Amul Fresh Cream | 49 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901262151863) |
| 8901262200004 | Butter milk amul | 100 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901262200004) |
| 8901491003162 | 8901491003162 | 13 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901491003162) |
| 8901499009661 | Kellogg's corn flakes original | 52 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901499009661) |
| 8901499010513 | Muesli Fruit, Nut & Seeds | 54 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901499010513) |
| 8901499010728 | Kellogg's chocos | 51 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901499010728) |
| 8901565001728 | Piknik Classic Tomato Chilli (fried Indian snack) | 30 | No: sodium_mg | Yes | [OFF](https://world.openfoodfacts.org/product/8901565001728) |
| 8901595862801 | 8901595862801 | 19 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901595862801) |
| 8901595862825 | Red chilli sauce | 19 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901595862825) |
| 8901719123870 | Parle-G 250g | 19 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901719123870) |
| 8901719127106 | Parle Nutricrunch Digestive Cookies | 27 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901719127106) |
| 8901719130243 | Moong Dal | 50 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901719130243) |
| 8901719131219 | Parle g 800 g | 22 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901719131219) |
| 8901719134852 | Parle G biscuit | 22 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901719134852) |
| 8901719135156 | PARLE MONACO | 10 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901719135156) |
| 8901719135163 | Parle Monaco | 9 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901719135163) |
| 8901719135170 | parle monaco 700g | 9 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901719135170) |
| 8901719135323 | parle krackjack | 18 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901719135323) |
| 8901719135729 | Biscuit | 20 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8901719135729) |
| 8901719135743 | Parle G gold | 18 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901719135743) |
| 8901725005986 | Sunfeast Yippee! masala magic | 6 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901725005986) |
| 8901725013691 | Bingo mad snack | 19 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901725013691) |
| 8901725100131 | B Natural Orange Juice 1ltr tpk | 11 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901725100131) |
| 8901764012273 | Coca Cola Coke Brand 750ml | 15 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901764012273) |
| 8901764052309 | Limca | 16 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901764052309) |
| 8901764092152 | Maaza Original 1.75ltr | 12 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901764092152) |
| 8901764092282 | Maaza | 12 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8901764092282) |
| 8901786060504 | Chaat Masala | 18 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8901786060504) |
| 8902579001438 | Appy Fizz | 13 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8902579001438) |
| 8902579001605 | Frooti mango drink | 9 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8902579001605) |
| 8902579002046 | Appy fizz | 12 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8902579002046) |
| 8903241110434 | Kolhapuri Thecha | 20 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8903241110434) |
| 8904004400021 | bhujia sev | 18 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8904004400021) |
| 8904004400922 | Haldiram's mixture | 21 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8904004400922) |
| 8904004401554 | Masala Sev Murmura | 25 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8904004401554) |
| 8904004416619 | Haldiram Matka Jhatka | 72 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8904004416619) |
| 8904422711365 | Nariyal Biscuit | 29 | No: sugars_g | Yes | [OFF](https://world.openfoodfacts.org/product/8904422711365) |
| 8906002006243 | Peanut Butter Crunchy | 23 | No: sodium_mg | Yes | [OFF](https://world.openfoodfacts.org/product/8906002006243) |
| 8906002006601 | Dr. Oetker FunFoods Veg Mayonnaise Original | 13 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906002006601) |
| 8906007611602 | Kreamy magic | 33 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8906007611602) |
| 8906010500481 | Crunchm | 20 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906010500481) |
| 8906010500870 | BALAJI CREAM ONION | 23 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906010500870) |
| 8906010501198 | Crunchem Pizzy Masala | 19 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906010501198) |
| 8906010502508 | Crunchem Peri Peri Flavour | 23 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906010502508) |
| 8906010503543 | Balaji Crunchem Chaat Chaska | 17 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906010503543) |
| 8906017290033 | Bisleri | 100 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906017290033) |
| 8906019633029 | 1 to 3 noodles chatpat masala | 8 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906019633029) |
| 8906032018520 | Patanjali | 51 | No: saturated_fat_g | Missing | [OFF](https://world.openfoodfacts.org/product/8906032018520) |
| 8906090572132 | Munchy masala | 28 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8906090572132) |
| 8906090573047 | Too yummy Chips green | 21 | Yes | Yes | [OFF](https://world.openfoodfacts.org/product/8906090573047) |
| 8906105470095 | kimia dates | 24 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8906105470095) |
| 8909081001123 | Bounce Chocho | 11 | No: saturated_fat_g | Yes | [OFF](https://world.openfoodfacts.org/product/8909081001123) |
| 8909081003394 | WOWZERS | 17 | Yes | Missing | [OFF](https://world.openfoodfacts.org/product/8909081003394) |
