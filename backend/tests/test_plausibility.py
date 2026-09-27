"""Physical sanity checks. Cases here are real Open Food Facts records unless noted."""

from app.models import DataStatus, Nutriments, Product
from app.plausibility import check, sanitise
from app.repository import ProductRepository
from app.scoring import score_product


def N(**kw) -> Nutriments:
    return Nutriments(**kw)


def rules(n: Nutriments, **kw) -> set[str]:
    return {p.rule for p in check(n, **kw).problems}


# --- the values that started this ------------------------------------------


def test_tata_salt_with_zero_sodium_loses_its_numbers():
    """The record that scored 100 "Great" for a product that is entirely salt.

    Every core value is present and zero, so nothing was missing and nothing
    looked wrong. A solid food made of nothing is the rule that catches it.
    """
    salt = N(energy_kcal=0, fat_g=0, saturated_fat_g=0, sugars_g=0, sodium_mg=0, protein_g=0, fibre_g=0)
    result = check(salt, is_drink=False)
    assert "solid_food_entirely_zero" in {p.rule for p in result.problems}

    clean, _ = sanitise(salt, is_drink=False)
    assert clean.sodium_mg is None and clean.energy_kcal is None

    # Four gaps, so the engine refuses a number instead of saying "Great".
    scored = score_product(
        Product(barcode="8904043901015", name="Tata Salt", nutriments=clean, status=DataStatus.community)
    )
    assert scored.score is None
    assert scored.verdict.value == "unknown"


def test_water_is_allowed_to_be_entirely_zero():
    """The trap in the rule above: for a drink, all zeroes is correct.

    Bisleri's record is all zeroes and scores 100 legitimately. A blanket
    "all zeroes is wrong" would break the one case that is right.
    """
    water = N(energy_kcal=0, fat_g=0, saturated_fat_g=0, sugars_g=0, sodium_mg=0)
    assert check(water, is_drink=True).ok

    scored = score_product(
        Product(barcode="8906017290040", name="Bisleri", is_drink=True, nutriments=water, status=DataStatus.community)
    )
    assert scored.score == 100


def test_sodium_beyond_pure_salt_is_dropped():
    """Real records: 118,000 / 211,000 / 378,667 / 385,000 mg per 100 g.

    Pure sodium chloride is 39.34% sodium, so nothing edible can exceed that.
    These are grams entered where milligrams were meant.
    """
    for sodium in (118_000, 211_000, 378_666.7, 385_000):
        n = N(energy_kcal=450, sugars_g=37, saturated_fat_g=8, sodium_mg=sodium)
        assert "sodium_above_pure_salt" in rules(n)
        clean, _ = sanitise(n)
        assert clean.sodium_mg is None


def test_an_impossible_core_value_costs_the_record_its_score():
    """A rejected value is worse evidence than an absent one.

    The real ketchup record carried 1000x its sodium. It scored 12 "Avoid" on the
    bad figure and 58 "Good" once that figure was dropped -- removing the error
    flattered the product. Refusing a number is the honest answer.
    """
    ketchup = N(energy_kcal=110, sugars_g=26, saturated_fat_g=0.1, sodium_mg=378_666.7)
    assert "core_value_rejected" in rules(ketchup)

    clean, _ = sanitise(ketchup)
    assert clean.sugars_g is None  # the whole panel goes, not just the bad field

    scored = score_product(
        Product(barcode="8901030775994", name="Ketchup", nutriments=clean, status=DataStatus.community)
    )
    assert scored.score is None


def test_a_rejected_non_core_value_leaves_the_score_alone():
    """Only the four core nutrients carry this weight; the rest just drop out."""
    n = N(energy_kcal=450, sugars_g=20, saturated_fat_g=8, sodium_mg=300, protein_g=150)
    result = check(n)
    assert "above_100g" in {p.rule for p in result.problems}
    assert "core_value_rejected" not in {p.rule for p in result.problems}
    clean, _ = sanitise(n)
    assert clean.protein_g is None
    assert clean.sugars_g == 20 and clean.sodium_mg == 300


# --- universal rules -------------------------------------------------------


def test_negative_values_are_dropped():
    assert "negative" in rules(N(sugars_g=-5))


def test_energy_beyond_pure_fat_is_dropped():
    assert "energy_above_pure_fat" in rules(N(energy_kcal=1500))
    assert check(N(energy_kcal=899)).ok  # just inside


def test_a_nutrient_over_100g_per_100g_is_dropped():
    assert "above_100g" in rules(N(sugars_g=140))


def test_saturated_fat_cannot_exceed_total_fat():
    n = N(fat_g=5, saturated_fat_g=20)
    assert "saturated_fat_above_total_fat" in rules(n)
    clean, _ = sanitise(n)
    # Both go: either could be the wrong one, and keeping total fat alone would
    # flatter the score by removing the nutrient that carries the penalty.
    assert clean.saturated_fat_g is None and clean.fat_g is None


def test_mass_cannot_exceed_100g():
    assert "mass_over_100g" in rules(N(fat_g=60, sugars_g=30, protein_g=20, fibre_g=10))


def test_energy_below_its_own_macros_is_dropped():
    """Oil declared as 0 kcal: 100 g of fat supplies 900 kcal whatever the label says."""
    n = N(energy_kcal=0, fat_g=100)
    assert "energy_below_macros" in rules(n)
    clean, _ = sanitise(n)
    assert clean.energy_kcal is None and clean.fat_g == 100


def test_atwater_leaves_normal_food_alone():
    """Real panels must survive: starch we cannot see makes energy exceed the floor."""
    biscuit = N(energy_kcal=450, fat_g=12.8, saturated_fat_g=6.2, sugars_g=21.5, sodium_mg=380, protein_g=7.1)
    almonds = N(energy_kcal=600, fat_g=52, saturated_fat_g=4, sugars_g=4, sodium_mg=1, protein_g=21, fibre_g=12)
    cola = N(energy_kcal=42, sugars_g=10.6, saturated_fat_g=0, sodium_mg=10)
    for panel in (biscuit, almonds, cola):
        assert check(panel).ok, panel


def test_rounding_does_not_trip_the_atwater_floor():
    # 9*10 + 4*(5+5) = 130 kcal floor; a label rounding to 120 must pass.
    assert check(N(energy_kcal=120, fat_g=10, sugars_g=5, protein_g=5)).ok


def test_a_complete_ordinary_panel_is_untouched():
    n = N(energy_kcal=486, fat_g=21, saturated_fat_g=9.8, sugars_g=24, sodium_mg=380, fibre_g=3.1, protein_g=7.2)
    clean, result = sanitise(n)
    assert result.ok
    assert clean is n  # no copy when there is nothing to fix


# --- the chokepoint --------------------------------------------------------


def test_upsert_refuses_to_store_impossible_values():
    """Whatever the source, storage is the line nothing bad crosses."""
    repo = ProductRepository(":memory:")
    repo.upsert(
        Product(
            barcode="8901063139329",
            name="Bourbon",
            nutriments=N(energy_kcal=450, sugars_g=37, saturated_fat_g=8, sodium_mg=118_000),
            status=DataStatus.community,
        )
    )
    stored = repo.get("8901063139329")
    assert stored.nutriments.sodium_mg is None
    assert stored.nutriments.sugars_g is None  # core value rejected, so the panel goes
    # The product is still stored and findable -- "we have this but cannot score
    # it" is more use to someone in a shop than "not found".
    assert stored.name == "Bourbon"
