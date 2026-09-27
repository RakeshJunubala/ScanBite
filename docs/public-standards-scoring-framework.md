# ScanBite Public-Standards Scoring Framework

Status: review draft. This is a transparent method proposal for packaged-food label guidance. It is not medical advice and should not be marketed as clinically validated unless reviewed by qualified professionals.

## 1. Purpose

ScanBite should answer one narrow question:

How favorable is this packaged food's label profile compared with other packaged foods?

It should not answer:

- Whether a person should eat it medically.
- Whether a product treats, prevents, or causes disease.
- Whether a raw ingredient, restaurant food, sweet-shop item, or bakery item has a precise verified score when no label data exists.

The app should show one product-level score and separate profile-specific alerts.

## 2. Public Sources Used

Use these as the basis for the method, not AI opinion:

| Source | Use in ScanBite |
| --- | --- |
| Nutri-Score 2023 updated algorithm, Sante publique France | Main nutrient scoring backbone for energy, sugar, saturated fat, sodium, fibre, protein, fruit/vegetable/nuts/legumes, and drink sweeteners. |
| FSSAI Labelling and Display Regulations, 2020 | Indian label context and daily reference values for display: 2000 kcal, total fat 67 g, saturated fat 22 g, trans fat 2 g, added sugar 50 g, sodium 2000 mg. |
| FSSAI draft Indian Nutrition Rating / FOPNL material | India-specific front-of-pack concept using energy, total sugars, saturated fat, sodium, and positive nutrients per 100 g/ml. |
| WHO sugars guideline, 2015 | Guardrail for strong warnings on free/added sugar and sugar-sweetened beverages. |
| ICMR-NIN Dietary Guidelines for Indians, 2024 | India-specific public-health context: limit foods high in sugar, salt, saturated fat, trans fat, and ultra-processed foods; prefer minimally processed foods. |
| UK front-of-pack traffic-light guide, 2016 | User-facing "low / medium / high" display levels for sugar, saturated fat, salt, etc. |

Primary links:

- WHO sugars guideline: https://www.who.int/publications/i/item/9789241549028
- WHO sugars news note: https://www.who.int/news/item/04-03-2015-who-calls-on-countries-to-reduce-sugars-intake-among-adults-and-children/
- FSSAI Labelling and Display Regulations compendium: https://fssai.gov.in/upload/uploadfiles/files/Compendium_Labelling_Display_23_09_2021.pdf
- FSSAI draft FOPNL / Indian Nutrition Rating notification: https://www.fssai.gov.in/upload/uploadfiles/files/Draft_Notification_HFSS_20_09_2022.pdf
- ICMR-NIN Dietary Guidelines for Indians 2024: https://www.nin.res.in/dietaryguidelines/pdfjs/locale/DGI24thJune2024fin.pdf
- Nutri-Score 2023 update overview: https://invs.santepubliquefrance.fr/nutrition-et-activite-physique/article/nutri-score-2023-update
- Nutri-Score beverage update report page: https://www.santepubliquefrance.fr/nutrition-et-activite-physique/rapportsynthese/update-nutri-score-algorithm-beverages-second-update-report-scientific-committee-nutri-score-v2-2023

## 3. Inputs

For a full packaged-food score, require at least:

- Product type: food or drink.
- Per 100 g/ml nutrition: energy, total sugars, saturated fat, sodium.
- Ingredients list where available.
- Additives where available.
- Serving size where available.

Optional but useful:

- Fibre.
- Protein.
- Fruit/vegetable/nuts/legumes percentage.
- Trans fat.
- Added sugar.
- Product category.
- Allergen labels.

## 4. Score Confidence

Every result must have a confidence label:

| Confidence | Meaning | App wording |
| --- | --- | --- |
| Verified | Checked against label photos or trusted internal review. | "Verified label data." |
| Community | Imported from Open Food Facts or another public community source. | "Community data. Check the label if this matters." |
| Provisional | User-submitted or AI-extracted, not reviewed. | "Provisional score. May change after review." |
| Estimated | Category/photo guess, no full label. | "Estimated guidance, not a full score." |
| Unknown | Not enough data. | "Not enough label data to score." |

Rule: never show an estimated result as a precise verified 0-100 score.

## 5. Product Types

Use four paths:

| Path | Examples | Output |
| --- | --- | --- |
| Packaged with label | Maggi, Thums Up, biscuits, cereals | Full 0-100 score. |
| Basic raw ingredient | rice, dal, peanuts, atta, sugar, salt | Category guidance, not the same packaged-food score unless nutrition data is known. |
| Bakery/sweets/no label | cream bun, pastry, puff, mithai | Estimated guidance after user confirmation; no precise verified score. |
| Unknown | no match and no usable photo/manual data | Unknown. |

## 6. Nutrition Score

Use Nutri-Score 2023-style nutrient points as the transparent backbone.

Negative points:

| Nutrient | Why included |
| --- | --- |
| Energy | High energy density can matter for portion control. |
| Total sugars | Public-health concern, especially drinks and sweets. |
| Saturated fat | Cardiometabolic risk marker and standard label metric. |
| Sodium | Salt/BP risk marker and standard label metric. |
| Non-sugar sweeteners in drinks | Included in Nutri-Score 2023 beverage update. |

Positive points:

| Nutrient/component | Why included |
| --- | --- |
| Fibre | Supports better carbohydrate quality and satiety. |
| Protein | Useful, but must not rescue products high in sugar/fat/salt. |
| Fruit/vegetable/nuts/legumes/millets | Aligns with food-based dietary guidance. |

Protein rule:

Protein points count only when negative points are below the Nutri-Score-style threshold. This avoids giving a high score to high-sugar or high-salt products just because they contain protein.

## 7. Convert To ScanBite 0-100

The app may keep the current 0-100 mapping:

| Score | Verdict | User meaning |
| --- | --- | --- |
| 75-100 | Great | Better packaged-food choice. |
| 50-74 | Good | Reasonable choice; check portions. |
| 25-49 | Limit | Use occasionally or in smaller portions. |
| 0-24 | Avoid | Usually a poor packaged-food choice. |
| No score | Unknown | Not enough data. |

Important wording:

Use "Limit" instead of "Bad". Use "Avoid" only as product guidance, not medical instruction.

## 8. Caps

Caps are safety guardrails.

| Trigger | Cap | Reason |
| --- | --- | --- |
| Sweetened drink with added sugar or non-sugar sweeteners | Max 49 | WHO sugar guidance and Nutri-Score beverage treatment; sugary drinks should not appear "Good". |
| High-risk additive | Max 49 | Conservative label-warning approach. |
| Missing any core nutrient | Show score as low confidence, or optionally no score if missing nutrient could materially change result. |
| No nutrition table | No full score | Prevent fake precision. |

## 9. Processing And Ingredient Signals

Use ingredients as secondary modifiers, not the main score engine.

| Signal | Suggested action |
| --- | --- |
| Refined flour/maida first ingredient | Small penalty and visible note. |
| Added sugar in first three ingredients | Small penalty and visible note. |
| Palm oil | Small penalty and visible note. |
| Hydrogenated fat/vanaspati | Larger penalty and visible warning. |
| Non-sugar sweeteners | Penalty for drinks; visible note for all foods. |
| Trans fat listed above trace level | Strong warning. |

Reasoning:

Ingredient lists help explain food quality, but nutrition values should remain the main repeatable scoring base.

## 10. Additives

Additives should be handled conservatively:

| Additive risk | Score effect | User display |
| --- | --- | --- |
| None/low | No penalty | "No known concern at normal intake." |
| Moderate | Small penalty | "Additive to watch." |
| High | Larger penalty and cap | "We rate this additive high risk." |
| Unknown | No penalty | "Not in our additive table yet." |

Do not say an additive is harmful unless the table cites a public regulatory/scientific reason.

## 11. Health Profile Alerts

Keep these separate from the base score.

Example:

- Base product score: "41, Limit."
- Diabetes profile alert: "Sugary drink. Contains 9 g sugar per 100 ml; avoid or limit strongly."

This avoids changing the product score for every user and makes the logic explainable.

Suggested alert sources:

| Profile | Inputs |
| --- | --- |
| Diabetes | sugars, added sugars, drink status, serving size. |
| High BP | sodium/salt. |
| Cholesterol/heart | saturated fat, trans fat, hydrogenated fat. |
| Pregnancy | caffeine, high-risk additives, allergen/food-safety notes only when label supports it. |
| Weight goals | energy density, sugar, serving size. |
| Allergies/diet | allergen tags, traces, ingredient words, animal-origin additives. |

Wording rule:

Alerts should say "check", "limit", "watch", or "discuss with your clinician" where appropriate. They should not diagnose or prescribe.

## 12. Raw Ingredients

Do not force rice, dal, flour, peanuts, dry fruits, sugar, and salt into the same packaged-snack score.

Use ingredient-category guidance:

| Food type | Guidance |
| --- | --- |
| Rice | Basic staple; portion and pairing matter. Prefer less polished/whole-grain options where possible. |
| Dal/pulses | Generally favorable staple protein/fibre source. |
| Whole wheat atta | Generally favorable compared with refined flour. |
| Maida/refined flour | Limit; refined grain. |
| Sugar/jaggery/honey | Added sugar; avoid as a snack product, use sparingly as ingredient. |
| Salt | No snack score; use sparingly. |
| Peanuts/nuts | Nutrient-dense, calorie-dense; watch salt/frying/coating. |
| Dry fruits | Nutrient-dense, sugar-dense; portion matters. |

These should show "basic food guidance" rather than a precise verified score unless full nutrition data is available.

## 13. Bakery, Sweets, And No-Label Foods

When barcode is not found:

1. Ask for a photo.
2. AI identifies likely food type.
3. User confirms from choices.
4. Ask only minimal extra questions that affect guidance:
   - Serving size: small/medium/large or grams.
   - Veg/egg/chicken/paneer if ambiguous.
   - Cream/frosting/filling present?
   - Fried or baked?
   - Ingredients photo if available.
5. Show estimated guidance, not verified score.

Example output:

"Estimated: Limit/Avoid. Based on typical pastry ingredients: refined flour, sugar, cream/fat. Actual recipe may vary."

## 14. Data Quality Rules

Reject or downgrade scores when:

- Serving size is impossible.
- Nutrients are physically implausible.
- Energy is missing but macros exist and conflict strongly.
- Sugar/sodium/saturated fat is missing for a packaged product.
- Product name/category is unknown and no label/photo confirms it.
- AI photo confidence is low.

Suggested confidence thresholds:

| Case | Action |
| --- | --- |
| AI top match >= 85% and user confirms | Estimated guidance allowed. |
| AI top match 60-84% | Show choices and ask user to confirm. |
| AI top match < 60% | Ask manual category or label photo. |

## 15. Review Questions For AI Models

Ask each reviewing model these exact questions:

1. Which rules are directly supported by public standards?
2. Which rules are ScanBite-specific assumptions?
3. Which thresholds could mislead Indian users?
4. Are the verdict words Great/Good/Limit/Avoid too strong?
5. Should raw ingredients receive scores or only guidance?
6. Should sweetened drinks be capped at 49 or lower?
7. Should missing core nutrients block a score completely?
8. Are any health profile alerts too medical or too confident?
9. Are additive penalties too strong, too weak, or poorly justified?
10. What exact user-facing wording reduces medical/legal risk?

## 16. Non-Negotiable Product Rules

- Never claim medical diagnosis or treatment.
- Never present AI-estimated food recognition as verified label data.
- Always show data source: verified, community, provisional, estimated, unknown.
- Always show why the score happened.
- Always separate general score from personal alerts.
- Always allow users to report wrong data.
- Keep the method versioned so old scores can be recalculated.

## 17. Recommended MVP Method Version

Name: ScanBite Public Standards Method v0.2-review

Implementation stance:

- Keep current Nutri-Score-style 0-100 engine.
- Add stronger confidence labels.
- Add explicit source attribution.
- Add no-score behavior for missing full nutrition where needed.
- Add raw-food and bakery estimated-guidance paths.
- Keep AI as extraction/review assistance, not final authority.

