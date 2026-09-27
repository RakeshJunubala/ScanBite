"""Scoring engine v0.1 (DRAFT — needs dietitian review before public release).

Score = nutrition (0-100) x (1 - additive penalty) x (1 - processing penalty),
then capped at 49 for a high-risk additive or a sweetened drink.
See docs/scoring-method.md.
"""

from __future__ import annotations

from ..models import (
    AdditiveFact,
    Level,
    NutrientFact,
    ProcessingFlag,
    Product,
    ScoreBreakdown,
    ScoreResult,
    Verdict,
)
from . import additives as additive_db
from . import thresholds as T
from .ingredients import IngredientSignals, analyse

METHOD_VERSION = "0.1-draft"

CORE_NUTRIENTS = ("energy_kcal", "sugars_g", "saturated_fat_g", "sodium_mg")

_LABELS = {
    "energy_kcal": "Energy",
    "sugars_g": "Sugar",
    "saturated_fat_g": "Saturated fat",
    "sodium_mg": "Sodium",
    "fibre_g": "Fibre",
    "protein_g": "Protein",
    "trans_fat_g": "Trans fat",
}
_UNITS = {
    "energy_kcal": "kcal",
    "sugars_g": "g",
    "saturated_fat_g": "g",
    "sodium_mg": "mg",
    "fibre_g": "g",
    "protein_g": "g",
    "trans_fat_g": "g",
}
_PROCESSING_LABELS = {
    "refined_flour_first": "Refined flour (maida) is the main ingredient",
    "added_sugar_top3": "Added sugar is among the first three ingredients",
    "palm_oil": "Contains palm oil",
    "hydrogenated_fat": "Contains hydrogenated fat (vanaspati)",
    "sweeteners": "Contains artificial or non-sugar sweeteners",
}


def _kind(product: Product) -> str:
    return "drink" if product.is_drink else "food"


def verdict_for(score: int | None) -> Verdict:
    if score is None:
        return Verdict.unknown
    for floor, name in T.VERDICT_BANDS:
        if score >= floor:
            return Verdict(name)
    return Verdict.avoid


def _level_negative(key: str, value: float, kind: str) -> Level | None:
    lights = T.TRAFFIC_LIGHTS[kind]
    if key == "sodium_mg":
        low, high = lights["salt_g"]
        value = value * 2.5 / 1000  # sodium mg -> salt g
    elif key in lights:
        low, high = lights[key]
    else:
        return None
    if value <= low:
        return "low"
    if value > high:
        return "high"
    return "medium"


def _level_positive(key: str, value: float, energy_kcal: float | None) -> Level:
    if key == "fibre_g":
        if value >= T.FIBRE_HIGH_G:
            return "high"
        return "medium" if value >= T.FIBRE_SOURCE_G else "low"
    if key == "protein_g":
        if not energy_kcal:
            return "low"
        share = value * 4 / energy_kcal
        if share >= T.PROTEIN_HIGH_ENERGY_SHARE:
            return "high"
        return "medium" if share >= T.PROTEIN_SOURCE_ENERGY_SHARE else "low"
    return "low"


def _per_serving(value: float, serving_g: float | None) -> float | None:
    if not serving_g:
        return None
    return round(value * serving_g / 100, 1)


def _nutrient_facts(product: Product, kind: str) -> list[NutrientFact]:
    n = product.nutriments
    facts: list[NutrientFact] = []
    for key in ("sugars_g", "saturated_fat_g", "sodium_mg", "trans_fat_g"):
        value = getattr(n, key)
        if value is None or (key == "trans_fat_g" and value <= 0):
            continue
        daily = T.DAILY_REFERENCE.get(key)
        level: Level | None = _level_negative(key, value, kind)
        if key == "trans_fat_g":
            level = "high" if value > 0.2 else "medium"
        facts.append(
            NutrientFact(
                key=key,
                label=_LABELS[key],
                value=round(value, 1),
                unit=_UNITS[key],
                kind="negative",
                level=level,
                percent_daily=round(value / daily * 100) if daily else None,
                per_serving=_per_serving(value, product.serving_size_g),
            )
        )
    for key in ("fibre_g", "protein_g"):
        value = getattr(n, key)
        if value is None:
            continue
        facts.append(
            NutrientFact(
                key=key,
                label=_LABELS[key],
                value=round(value, 1),
                unit=_UNITS[key],
                kind="positive",
                level=_level_positive(key, value, n.energy_kcal),
                per_serving=_per_serving(value, product.serving_size_g),
            )
        )
    if n.energy_kcal is not None:
        facts.append(
            NutrientFact(
                key="energy_kcal",
                label=_LABELS["energy_kcal"],
                value=round(n.energy_kcal),
                unit="kcal",
                kind="neutral",
                percent_daily=round(n.energy_kcal / T.DAILY_REFERENCE["energy_kcal"] * 100),
                per_serving=_per_serving(n.energy_kcal, product.serving_size_g),
            )
        )
    return facts


def nutrition_from_net(net: float, kind: str) -> float:
    """Map net points to 0-100: 0 -> 100, limit_edge -> 25, zero_at -> 0."""
    m = T.NUTRITION_MAP[kind]
    edge, zero_at = m["limit_edge"], m["zero_at"]
    if net <= 0:
        return 100.0
    if net <= edge:
        return 100.0 - net * (75.0 / edge)
    if net >= zero_at:
        return 0.0
    return 25.0 - (net - edge) * (25.0 / (zero_at - edge))


def _nutrition_score(product: Product, kind: str, sweeteners: bool) -> tuple[float, float, float]:
    """Returns (nutrition 0-100, negative points, positive points)."""
    n = product.nutriments
    negative = 0.0
    for key, scale in T.NEGATIVE_SCALES[kind].items():
        value = getattr(n, key)
        if value is not None:
            negative += scale.points(value)
    if kind == "drink" and sweeteners:
        negative += T.DRINK_SWEETENER_POINTS
    positive = 0.0
    for key, scale in T.POSITIVE_SCALES.items():
        value = getattr(n, key)
        if value is None:
            continue
        if key == "protein_g" and negative >= T.PROTEIN_COUNTS_BELOW[kind]:
            continue
        positive += scale.points(value)
    return nutrition_from_net(negative - positive, kind), negative, positive


def _processing(signals: IngredientSignals) -> list[ProcessingFlag]:
    flags = []
    for key in ("refined_flour_first", "added_sugar_top3", "palm_oil", "hydrogenated_fat", "sweeteners"):
        if getattr(signals, key):
            flags.append(ProcessingFlag(key=key, label=_PROCESSING_LABELS[key], penalty=T.PROCESSING_PENALTY[key]))
    return flags


def _join(words: list[str]) -> str:
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def _teaspoons(grams: float) -> str:
    tsp = grams / T.TEASPOON_SUGAR_G
    return "under 1 teaspoon" if tsp < 1 else f"about {round(tsp)} teaspoon{'s' if round(tsp) != 1 else ''}"


def _reason(
    product: Product,
    facts: list[NutrientFact],
    flags: list[ProcessingFlag],
    additive_facts: list[AdditiveFact],
    caps: list[str],
) -> str:
    def name(f: NutrientFact) -> str:
        return "salt" if f.key == "sodium_mg" else f.label.lower()

    highs = [name(f) for f in facts if f.kind == "negative" and f.level == "high"]
    mediums = [name(f) for f in facts if f.kind == "negative" and f.level == "medium"]
    goods = [name(f) for f in facts if f.kind == "positive" and f.level in ("medium", "high")]
    sugars = product.nutriments.sugars_g
    parts: list[str] = []
    if product.is_drink and sugars is not None and sugars >= 5 and not highs:
        if product.serving_size_g:
            amount = _teaspoons(sugars * product.serving_size_g / 100)
            parts.append(f"Sugary drink: {amount} of sugar per {product.serving_size_g:g} ml.")
        else:
            parts.append(f"Sugary drink: {_teaspoons(sugars)} of sugar per 100 ml.")
    elif highs:
        parts.append(f"High in {_join(highs)}.")
    elif goods:
        parts.append(f"Good source of {_join(goods)}.")
    elif mediums:
        parts.append(f"Moderate {_join(mediums)}.")
    else:
        parts.append("Low in sugar, saturated fat and salt.")
    flag_keys = {f.key for f in flags}
    if "hydrogenated_fat" in flag_keys:
        parts.append("Contains hydrogenated fat.")
    elif "refined_flour_first" in flag_keys:
        parts.append("Refined flour (maida) is the main ingredient.")
    elif "sweeteners" in flag_keys:
        parts.append("Contains sweeteners.")
    risky = [a for a in additive_facts if a.risk in ("moderate", "high")]
    if "high_risk_additive" in caps:
        parts.append("Has an additive we rate high risk.")
    elif risky:
        parts.append(f"{len(risky)} additive{'s' if len(risky) > 1 else ''} to watch.")
    return " ".join(parts[:2])  # two short sentences fit the verdict card


def score_product(product: Product) -> ScoreResult:
    kind = _kind(product)
    n = product.nutriments
    missing = [k for k in CORE_NUTRIENTS if getattr(n, k) is None]

    codes = additive_db.merge_codes(product.additives, additive_db.extract_codes(product.ingredients_text))
    additive_facts = [additive_db.describe(c) for c in codes]
    signals = analyse(product.ingredients_text, codes)
    flags = _processing(signals)
    facts = _nutrient_facts(product, kind)

    if len(missing) == len(CORE_NUTRIENTS):
        return ScoreResult(
            score=None,
            verdict=Verdict.unknown,
            reason="The nutrition table is missing. Add a photo of it to get a score.",
            nutrients=facts,
            additives=additive_facts,
            processing=flags,
            incomplete=True,
            missing=missing,
            method_version=METHOD_VERSION,
        )

    nutrition, _, _ = _nutrition_score(product, kind, signals.sweeteners)
    additive_penalty = min(sum(T.ADDITIVE_PENALTY[a.risk] for a in additive_facts), T.MAX_ADDITIVE_PENALTY)
    processing_penalty = min(sum(f.penalty for f in flags), T.MAX_PROCESSING_PENALTY)

    # Penalties are fractions, so they keep bad products in order instead of all hitting 0.
    total = nutrition * (1 - additive_penalty) * (1 - processing_penalty)
    caps: list[str] = []
    if any(a.risk == "high" for a in additive_facts) and total > T.CAP_SCORE:
        total = T.CAP_SCORE
        caps.append("high_risk_additive")
    if kind == "drink" and (signals.added_sugar_any or signals.sweeteners) and total > T.CAP_SCORE:
        total = T.CAP_SCORE
        caps.append("sweetened_drink")

    score = round(min(max(total, 0.0), 100.0))  # round() on a float already returns int
    return ScoreResult(
        score=score,
        verdict=verdict_for(score),
        reason=_reason(product, facts, flags, additive_facts, caps),
        nutrients=facts,
        additives=additive_facts,
        processing=flags,
        breakdown=ScoreBreakdown(
            nutrition=round(nutrition, 1),
            additive_penalty=additive_penalty,
            processing_penalty=processing_penalty,
            caps_applied=caps,
        ),
        incomplete=bool(missing),
        missing=missing,
        method_version=METHOD_VERSION,
    )
