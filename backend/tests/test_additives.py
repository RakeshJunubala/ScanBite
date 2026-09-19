import pytest

from app.scoring.additives import describe, extract_codes, merge_codes, normalize_code


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("E150d", "150d"),
        ("en:e150d", "150d"),
        ("INS 503(ii)", "503(ii)"),
        ("e503ii", "503(ii)"),
        ("503 (ii)", "503(ii)"),
        ("322(i)", "322(i)"),
        ("INS-330", "330"),
        ("1422", "1422"),
        ("924a", "924a"),
        ("62", None),
        ("2024", None),
        ("salt", None),
    ],
)
def test_normalize_code(raw, expected):
    assert normalize_code(raw) == expected


def test_extracts_prefixed_and_bare_codes_from_indian_label():
    text = (
        "Refined wheat flour (maida) (62%), sugar, raising agents [INS 503(ii), INS 500(ii)], "
        "emulsifier [322], colour [150d], flavour enhancers (627, 631)"
    )
    assert extract_codes(text) == ["503(ii)", "500(ii)", "322", "150d", "627", "631"]


def test_quantities_are_not_mistaken_for_additives():
    text = "Wheat flour (62%), 250 g pack, 486 kcal per 100 g, 330 ml bottle, best before 2027"
    assert extract_codes(text) == []


def test_unknown_code_is_reported_without_penalty():
    fact = describe("1203")
    assert fact.known is False
    assert fact.risk == "unknown"
    assert fact.name == "INS 1203"


def test_known_code_with_subnumber_falls_back_to_base_entry():
    fact = describe("500(ii)")
    assert fact.known is True
    assert fact.name.startswith("Sodium carbonates")


def test_merge_deduplicates_across_sources():
    assert merge_codes(["en:e150d", "E322"], ["150d", "INS 322"]) == ["150d", "322"]
