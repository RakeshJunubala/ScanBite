# Store expansion, second batch — 21 October 2026

Added **18** new products to `backend/data/products.db`: **930 total, 743 scored, 187 unscored**. All 912 previous product rows are unchanged. No Open Food Facts data was used.

## Sources and method

Seven entries use reviewed BigBasket indexed listing text; eleven use manufacturer label images and exact single-pack barcode variants from public manufacturer product JSON. Retailer text is a reviewed transcription, not a downloaded raw HTML snapshot. Sources, original nutrition basis, raw declared values, conversions and notes are saved per product in the manifest and database submission audit.

Zepto, Instamart and JioMart were also checked for discovery. Their reviewed listings did not supply a sufficiently complete exact-barcode nutrition record for direct import. Manufacturer evidence supplied the usable records. No retailer SKU, article ID or product URL ID was substituted for a barcode.

- [Zepto Slurrp Farm listing](https://www.zepto.com/brand/slurrp-farm?spvid=73863313-6f6c-4187-991d-da91dc8c5e69)
- [Instamart breakfast-mix listing](https://instamart.in/cb/slurrp-farm/breakfast-mixes)
- [JioMart foxtail-millet noodles listing](https://www.jiomart.com/product/slurrp-farm-foxtail-millet-noodles-192-g-mffmtm-7507111)

All new entries are **provisional**, with ingredients and the four required core nutrients (energy, total sugar, saturated fat, sodium). Scores use the existing **0.2-draft** custom engine; they are not an official certified nutrition rating. No scoring thresholds were changed. All stored food values are per 100 g of the dry/as-sold food. Unknown optional nutrients remain null. No fruit/nut percentage credits were estimated.

## Added products

| Barcode | Product | Pack | Score / 100 | Evidence |
|---|---|---|---:|---|
| 8908006217038 | Slurrp Farm Choco Ragi Cookies | 80 g | 52 | [Manufacturer](https://slurrpfarm.com/products/the-good-cookie-tasty-no-maida-no-refined-sugar-choco-ragi-cookie) |
| 8908006217045 | Slurrp Farm Banana Oat Cookies | 80 g | 52 | [Manufacturer](https://slurrpfarm.com/products/the-good-cookie-yummy-no-maida-no-refined-sugar-banana-oat-cookies) |
| 8906131685029 | Slurrp Farm Milky Choco Chip Cookies | 80 g | 45 | [Manufacturer](https://slurrpfarm.com/products/milky-choco-chip-cookies) |
| 8906131680598 | Slurrp Farm Mild Masala Millet Hakka Noodles | 192 g | 100 | [Manufacturer](https://slurrpfarm.com/products/millet-noodles-mild-masala) |
| 8906131681717 | Slurrp Farm Curry Masala Millet Hakka Noodles | 192 g | 75 | [Manufacturer](https://slurrpfarm.com/products/millet-noodles-curry-masala) |
| 8906131681137 | Slurrp Farm Multigrain Macaroni Pasta | 400 g | 96 | [Manufacturer](https://slurrpfarm.com/products/macaroni-pasta) |
| 8906131681120 | Slurrp Farm Multigrain Fusilli Pasta | 400 g | 96 | [Manufacturer](https://slurrpfarm.com/products/fusilli-pasta) |
| 8908006217717 | Slurrp Farm Jaggery Powder | 300 g | 23 | [Manufacturer](https://slurrpfarm.com/products/natural-jaggery-powder) |
| 8908006217090 | Slurrp Farm Chocolate Millet Pancake Mix | 150 g | 55 | [Manufacturer](https://slurrpfarm.com/products/chocolate-millet-pancake-copy) |
| 8906131684930 | Slurrp Farm Mild Masala Millet Hakka Noodles | 96 g | 100 | [Manufacturer](https://slurrpfarm.com/products/millet-noodles-mild-masala-serves-2) |
| 8906131684923 | Slurrp Farm Classic Masala Millet Hakka Noodles | 96 g | 96 | [Manufacturer](https://slurrpfarm.com/products/classic-masala-serves-2-96-gms) |
| 8906082570467 | Cornitos Taco Shells 15 cm | 12 pcs | 100 | [BigBasket](https://www.bigbasket.com/pd/40166032/cornitos-taco-shells-6-inches-12-pcs/) |
| 8909081013089 | Sunfeast Farmlite Sugar Free Hazelnut & Oats Cookies | 100 g | 17 | [BigBasket](https://www.bigbasket.com/pd/40371634/sunfeast-farmlite-hazelnut-oat-cookies-100-g/) |
| 8901242513841 | Bambino Roasted Dalia | 500 g | 100 | [BigBasket](https://www.bigbasket.com/pd/40362416/bambino-roasted-dalia-500-g/) |
| 8901242112303 | Bambino Daily Spirali Pasta | 500 g | 100 | [BigBasket](https://www.bigbasket.com/pd/40224915/bambino-daily-pasta-made-from-durum-wheat-spirali-500-g/) |
| 8901042971773 | MTR Besan Ladoo | 200 g | 13 | [BigBasket](https://www.bigbasket.com/pd/40313108/mtr-besan-undeladoo-made-with-100-pure-ghee-200-g/) |
| 8901512948700 | ACT II Caramel Bliss Coffee Caramel Popcorn | 70 g | 38 | [BigBasket](https://bbnow.bigbasket.com/pd/40368280/act-ii-caramel-bliss-coffee-caramel-flavour-popcorn-70-g-pouch/) |
| 8901042972961 | MTR 3 Minute Protein Khatta Meetha Poha | 80 g | 24 | [BigBasket](https://www.bigbasket.com/pd/40372593/mtr-khatta-meetha-poha-3-minute-breakfast-80-g/) |

## Held back and source discrepancies

- Bagrrys muesli: indexed text described 400 g, while the reopened listing displayed 375 g. Not imported; candidate transcription retained in `held-for-review.json`.
- Classic Masala noodles 192 g (`8906131680581`): manufacturer back photo and separate nutrition image show materially different panels. Not imported. The distinct 96-g barcode has its own reviewed panel.
- True Elements Fruity Delight muesli: indexed ingredients use an illustrative fruit list ("e.g."); deferred until an exact label is available.
- Chocolate pancake mix: Instamart generic panel conflicts with the manufacturer and lacks sodium/barcode. Used the complete manufacturer panel, without combining values from different sources.
- Excluded retailer-internal numeric SKUs, incomplete core panels, bounded saturated-fat values and ambiguous combined-product nutrition. No missing nutrition was guessed.
- Pack sizes and recipes are separate identities: Mild Masala 96 g and 192 g have distinct barcodes and different panels. Neither panel was copied to the other.

## Duplicate and integrity checks

No repeated barcodes or equivalent zero-padded GTINs. No new brand/name/pack review pairs. Six pre-existing possible duplicate pairs remain unresolved, as recorded in the earlier catalogue audit; a universal no-duplicates guarantee would be inaccurate. One identical-panel group is legitimate macaroni versus fusilli pasta, with different shapes, names and barcodes.

SQLite integrity is OK. All 18 scores reproduce using the current engine, all 18 have complete core panels, and all 18 have source-audit records. Repeating the import would insert zero products. Verification output: `outputs/store-expansion-2-20261021/verification.json`.

Backup before insertion: `backend\data\products.backup-20261021-135236-691664.db`.

Manifest: `backend/data/enrichments/store-products-2-20261021.json`. Research images and manufacturer JSON: `outputs/store-expansion-2-20261021/`.

Backend regression validation: 139 tests passed (one existing dependency deprecation warning).
