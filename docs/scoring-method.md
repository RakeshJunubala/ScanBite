# Scoring method — draft v0.1 (for dietitian review)

**Status: draft.** Nothing here should go public until a registered dietitian has reviewed and signed it off.
The code lives in `backend/app/scoring/` and every number below is in `thresholds.py` or `data/additives.json`.

## In one line

**Score (0–100) = nutrition part × (1 − additive penalty) × (1 − processing penalty)**, capped at 49 for a
high-risk additive or a sweetened drink.

| Verdict | Score |
| --- | --- |
| Great | 75–100 |
| Good | 50–74 |
| Limit | 25–49 |
| Avoid | 0–24 |

## 1. Nutrition part (0–100)

Uses the per-100 g (food) or per-100 ml (drink) values from the nutrition table. The point scales are continuous
versions of the **Nutri-Score 2023** point tables, so there is a published reference to check against.

**Negative points** (more is worse):

| Nutrient | Food: 0 points at → max at | Drink: 0 points at → max at | Max points |
| --- | --- | --- | --- |
| Energy | 80 → 800 kcal | 7 → 93 kcal | 10 |
| Sugars | 3.4 → 51 g | 0.5 → 11 g | 15 food / 10 drink |
| Saturated fat | 1 → 10 g | 1 → 10 g | 10 |
| Sodium | 80 → 1,600 mg (salt 0.2 → 4 g) | same | 20 |
| Non-sugar sweeteners (drinks only) | — | present | 4 |

**Positive points** (more is better):

| Nutrient | 0 points at → max at | Max points |
| --- | --- | --- |
| Fibre | 1.9 → 7.4 g | 5 |
| Protein | 1.2 → 17 g | 7 |
| Fruit, vegetables, nuts, legumes | 40 → 80 % | 5 |

Protein only counts when negative points are below 11 (food) or 7 (drink), as in Nutri-Score, so protein
cannot rescue a product that is high in sugar, fat or salt.

**Net points → nutrition part:** net ≤ 0 → 100. Then a straight line to 25 at the Nutri-Score D/E edge
(18 net points for food, 10 for drinks), then down to 0 (at 40 for food, 25 for drinks).

Milk and dairy drinks are scored as food, as the original Nutri-Score did.

## 2. Additive penalty

Each INS additive has a draft risk level in `data/additives.json` with a one-line reason:

| Risk | Meaning | Penalty |
| --- | --- | --- |
| None / Low | Approved, no meaningful concern at normal intake | 0 |
| Moderate | Warning label abroad, a sensitivity issue, or limited evidence of harm | −10 % each |
| High | Banned or withdrawn elsewhere, or a possible carcinogen | −25 % each, and the score is capped at 49 |

The total additive penalty is capped at −50 %. Unknown codes are shown to the user but not penalised.

## 3. Processing penalty

Read from the ingredient list (Indian labels list ingredients by weight, heaviest first):

| Signal | Penalty |
| --- | --- |
| Refined flour (maida) is the first ingredient | −5 % |
| Added sugar (sugar, jaggery, syrups, honey…) in the first three ingredients* | −5 % |
| Palm oil | −3 % |
| Hydrogenated fat / vanaspati | −8 % |
| Non-sugar sweeteners | −5 % |

\*Sugar inside a compound ingredient, such as a seasoning mix, does not count. The total is capped at −20 %.

## 4. Caps

- A high-risk additive: the score is capped at 49 (Limit).
- A drink with added sugar or sweeteners: the score is capped at 49. Only unsweetened drinks can be Good or Great.

## Calibration: the 8 demo products

| Product (fictional) | Key numbers per 100 g/ml | Score | Verdict |
| --- | --- | --- | --- |
| Jowar & Millet Thins | 3 g sugar, 1.2 g sat fat, 9 g fibre | 100 | Great |
| Rolled Oats | 1 g sugar, 10 g fibre, 13 g protein | 100 | Great |
| Roasted Makhana, Peri Peri | 520 mg sodium, 10 g fibre | 91 | Great |
| Ragi Oat Cookies | 14 g sugar (jaggery), 4 g sat fat, 6 g fibre | 54 | Good |
| Zero Sugar Cola | sweeteners 951 + 950, colour 150d | 47 | Limit |
| Cola | 10.6 g sugar | 16 | Avoid |
| Multigrain Digestive Biscuits | 24 g sugar, 9.8 g sat fat, maida first | 14 | Avoid |
| Instant Masala Noodles | 1,250 mg sodium, 8.5 g sat fat | 10 | Avoid |

## Questions for the dietitian

1. Are the Nutri-Score 2023 scales right for Indian eating patterns, or should any thresholds change?
2. Should ghee, jaggery and traditional sweets be treated differently from refined equivalents? (Today jaggery counts
   as added sugar, like sugar.)
3. 100% fruit juice currently scores as Avoid (high natural sugar). Is that the message we want?
4. Are the draft additive risk levels fair, especially aspartame, sucralose, carrageenan, CMC, phosphates and TBHQ?
5. Should per-serving values affect the score, or only the display? (Today only the display.)
6. Which conditions and allergies need extra alert rules for Indian users?

## Sources behind the draft

- Santé publique France, Nutri-Score algorithm update (2023) — point tables for foods and beverages.
- UK Department of Health, *Guide to creating a front of pack nutrition label* (2016) — traffic-light levels.
- EU Regulation (EC) No 1333/2008, Annex V — warning label for six azo colours.
- EU Regulation (EU) 2022/63 — withdrawal of titanium dioxide (E171).
- IARC Monographs classifications (aspartame 2023; 4-MEI; BHA; potassium bromate).
- EFSA re-evaluations (phosphates 2019) and JECFA acceptable daily intakes.
- FSSAI (Labelling and Display) Regulations, 2020 — reference values for "% of daily limit" (to verify).
