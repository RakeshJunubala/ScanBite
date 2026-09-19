from app.scoring.ingredients import analyse, head, split_ingredients


def test_split_respects_brackets():
    text = "Ingredients: Refined wheat flour (maida) (62%), raising agents [503(ii), 500(ii)], salt."
    assert split_ingredients(text) == [
        "refined wheat flour (maida) (62%)",
        "raising agents [503(ii), 500(ii)]",
        "salt",
    ]


def test_head_strips_nested_brackets():
    assert head("peri peri seasoning (salt, sugar (2%), acid [330])") == "peri peri seasoning"


def test_refined_flour_first_detected():
    s = analyse("Refined wheat flour (maida), sugar, palm oil", [])
    assert s.refined_flour_first
    assert s.added_sugar_top3
    assert s.palm_oil


def test_whole_wheat_first_is_not_refined():
    s = analyse("Whole wheat flour (atta) (80%), jaggery, salt", [])
    assert not s.refined_flour_first
    assert s.added_sugar_top3  # jaggery is added sugar


def test_sugar_inside_a_seasoning_mix_is_not_a_main_ingredient():
    s = analyse("Makhana (85%), rice bran oil, seasoning (salt, sugar, chilli)", [])
    assert not s.added_sugar_top3
    assert s.added_sugar_any


def test_palm_written_in_brackets_is_detected():
    s = analyse("Wheat flour, edible vegetable oil (palm), salt", [])
    assert s.palm_oil


def test_no_added_sugar_claim_is_not_sugar():
    s = analyse("Oats, no added sugar, almonds", [])
    assert not s.added_sugar_any


def test_sweeteners_from_codes_or_words():
    assert analyse("Water, sweetener [955]", ["955"]).sweeteners
    assert analyse("Water, aspartame", []).sweeteners
    assert not analyse("Water, salt", []).sweeteners


def test_hydrogenated_fat():
    assert analyse("Wheat flour, hydrogenated vegetable oil, sugar", []).hydrogenated_fat
    assert analyse("Wheat flour, vanaspati, sugar", []).hydrogenated_fat
