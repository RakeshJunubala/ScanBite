import json
from pathlib import Path

import pytest

from app.models import Nutriments, Product, Verdict
from app.scoring import score_product
from app.scoring.engine import nutrition_from_net, verdict_for

SAMPLES = {
    p["name"]: Product(**p)
    for p in json.loads((Path(__file__).parents[1] / "app" / "data" / "sample_products.json").read_text())["products"]
}


def make(**kwargs) -> Product:
    nutriments = kwargs.pop("nutriments", {})
    return Product(barcode="2000000000999", name="Test", nutriments=Nutriments(**nutriments), **kwargs)


@pytest.mark.parametrize(
    "score, verdict",
    [(100, "great"), (75, "great"), (74, "good"), (50, "good"), (49, "limit"), (25, "limit"), (24, "avoid"), (0, "avoid")],
)
def test_verdict_bands(score, verdict):
    assert verdict_for(score) == Verdict(verdict)


def test_nutrition_map_edges():
    assert nutrition_from_net(-3, "food") == 100
    assert nutrition_from_net(0, "food") == 100
    assert nutrition_from_net(18, "food") == pytest.approx(25)
    assert nutrition_from_net(40, "food") == 0
    assert nutrition_from_net(10, "drink") == pytest.approx(25)
    assert nutrition_from_net(30, "drink") == 0


@pytest.mark.parametrize(
    "name, verdict",
    [
        ("Multigrain Digestive Biscuits", "avoid"),
        ("Jowar & Millet Thins", "great"),
        ("Ragi Oat Cookies", "good"),
        ("Roasted Makhana, Peri Peri", "great"),
        ("Instant Masala Noodles", "avoid"),
        ("Cola", "avoid"),
        ("Zero Sugar Cola", "limit"),
        ("Rolled Oats", "great"),
    ],
)
def test_sample_products_land_in_expected_band(name, verdict):
    assert score_product(SAMPLES[name]).verdict == Verdict(verdict)


def test_better_alternatives_outscore_the_biscuit():
    biscuit = score_product(SAMPLES["Multigrain Digestive Biscuits"]).score
    cookies = score_product(SAMPLES["Ragi Oat Cookies"]).score
    thins = score_product(SAMPLES["Jowar & Millet Thins"]).score
    assert biscuit < cookies < thins


def test_biscuit_reason_and_flags():
    result = score_product(SAMPLES["Multigrain Digestive Biscuits"])
    assert result.reason == "High in sugar and saturated fat. Refined flour (maida) is the main ingredient."
    assert {f.key for f in result.processing} == {"refined_flour_first", "added_sugar_top3", "palm_oil"}
    assert [a.code for a in result.additives if a.risk == "moderate"] == ["150d"]


def test_nutrient_facts_have_levels_daily_share_and_serving():
    result = score_product(SAMPLES["Multigrain Digestive Biscuits"])
    sugar = next(f for f in result.nutrients if f.key == "sugars_g")
    assert sugar.level == "high"
    assert sugar.percent_daily == 48
    assert sugar.per_serving == 7.2  # 30 g serving
    sodium = next(f for f in result.nutrients if f.key == "sodium_mg")
    assert sodium.level == "medium"  # 0.95 g salt
    fibre = next(f for f in result.nutrients if f.key == "fibre_g")
    assert fibre.kind == "positive" and fibre.level == "medium"


def test_sugary_drink_reason_uses_teaspoons_per_serving():
    result = score_product(SAMPLES["Cola"])
    assert result.reason.startswith("Sugary drink: about 8 teaspoons of sugar per 300 ml.")


def test_sweetened_drink_never_scores_above_limit():
    drink = make(
        is_drink=True,
        nutriments={"energy_kcal": 1, "sugars_g": 0, "saturated_fat_g": 0, "sodium_mg": 5},
        ingredients_text="Water, sweetener [960]",
    )
    result = score_product(drink)
    assert result.score <= 49
    assert "sweetened_drink" in result.breakdown.caps_applied or result.score < 49


def test_plain_water_is_great():
    water = make(is_drink=True, nutriments={"energy_kcal": 0, "sugars_g": 0, "saturated_fat_g": 0, "sodium_mg": 2})
    assert score_product(water).score == 100


def test_high_risk_additive_caps_score():
    candy = make(
        nutriments={"energy_kcal": 60, "sugars_g": 2, "saturated_fat_g": 0.5, "sodium_mg": 20},
        ingredients_text="Water, gelling agent, colour [171]",
    )
    result = score_product(candy)
    assert result.score == 49
    assert result.breakdown.caps_applied == ["high_risk_additive"]
    # States the regulator's action, not our own opinion of the additive.
    assert result.reason.endswith("Contains an additive a food regulator has prohibited.")
    assert "we rate" not in result.reason.lower()


def test_only_a_regulator_prohibition_caps_the_score():
    """A hazard classification alone must not cap. See additives.json _meta.tiering_rule.

    171 is banned in the EU, so it caps. 320 (BHA) rests on an IARC group, which
    describes the substance rather than the risk at label amounts -- it penalises
    but must not cap, or we would be asserting harm a regulator has not.
    """
    nutriments = {"energy_kcal": 60, "sugars_g": 2, "saturated_fat_g": 0.5, "sodium_mg": 20}
    prohibited = score_product(make(nutriments=nutriments, ingredients_text="Water, colour [171]"))
    classified = score_product(make(nutriments=nutriments, ingredients_text="Water, antioxidant [320]"))

    assert prohibited.breakdown.caps_applied == ["high_risk_additive"]
    assert classified.breakdown.caps_applied == []
    assert classified.score > prohibited.score  # penalised, not capped
    assert classified.score is not None


def test_missing_nutrition_table_gives_unknown():
    result = score_product(make(ingredients_text="Rice, salt"))
    assert result.score is None
    assert result.verdict == Verdict.unknown
    assert result.incomplete
    assert "nutrition table" in result.reason


def test_one_missing_core_nutrient_still_scores_but_is_flagged():
    result = score_product(make(nutriments={"energy_kcal": 120, "sugars_g": 2, "saturated_fat_g": 1}))
    assert result.score is not None
    assert result.incomplete
    assert result.missing == ["sodium_mg"]


def test_two_missing_core_nutrients_gives_no_number():
    """A confident 0-100 built on half a nutrition table is worse than no number.

    FSSAI requires these values on a packaged food, so a gap means our source
    data is poor -- not that the pack was bare.
    """
    result = score_product(make(nutriments={"energy_kcal": 120, "sugars_g": 2}))
    assert result.score is None
    assert result.verdict == Verdict.unknown
    assert result.incomplete
    assert set(result.missing) == {"saturated_fat_g", "sodium_mg"}
    # The reason names what was absent, so "no score" reads as a fact.
    assert "saturated fat" in result.reason
    assert "sodium" in result.reason


def test_protein_does_not_rescue_a_salty_fatty_product():
    base = {"energy_kcal": 500, "sugars_g": 2, "saturated_fat_g": 9, "sodium_mg": 1400}
    low_protein = score_product(make(nutriments={**base, "protein_g": 2})).score
    high_protein = score_product(make(nutriments={**base, "protein_g": 20})).score
    assert low_protein == high_protein
