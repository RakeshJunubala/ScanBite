import json
from pathlib import Path

import httpx
import pytest

from app.models import DataStatus
from app.sources.off import OpenFoodFactsClient, SourceUnavailable, map_off_product

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "off_product.json").read_text())


def test_maps_off_fields_to_product():
    p = map_off_product("8900000000002", FIXTURE["product"])
    assert p.name == "Test Cream Biscuits"
    assert p.brand == "Test Brand"
    assert p.category == "biscuits"
    assert not p.is_drink
    assert p.nutriments.energy_kcal == 495
    assert p.nutriments.sodium_mg == 240.0  # OFF stores sodium in grams
    assert p.nutriments.fibre_g == 1.4
    assert p.serving_size_g == 25
    assert p.allergens == ["gluten", "milk", "soy"]
    assert p.traces == ["tree nuts", "peanut"]
    assert "vegetarian" in p.labels
    assert p.status == DataStatus.community


def test_energy_falls_back_to_kilojoules_and_sodium_to_salt():
    raw = {"product_name": "X", "nutriments": {"energy_100g": 418.4, "salt_100g": 1.0}}
    p = map_off_product("8900000000019", raw)
    assert p.nutriments.energy_kcal == 100.0
    assert p.nutriments.sodium_mg == 400.0


def test_beverages_are_drinks_but_milk_is_food():
    cola = map_off_product("1", {"categories_tags": ["en:beverages", "en:carbonated-drinks", "en:sodas"]})
    milk = map_off_product("2", {"categories_tags": ["en:dairies", "en:milks", "en:beverages"]})
    assert cola.is_drink
    assert not milk.is_drink


def _client(handler) -> OpenFoodFactsClient:
    return OpenFoodFactsClient("https://off.test", "Test/0.1", client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_client_returns_product_and_sends_fields():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json=FIXTURE)

    p = _client(handler).fetch("8900000000002")
    assert p is not None and p.name == "Test Cream Biscuits"
    assert "/api/v2/product/8900000000002" in seen["url"]
    assert "fields=" in seen["url"]


def test_client_returns_none_only_when_off_genuinely_has_no_record():
    # The two ways OFF reports a real miss.
    assert _client(lambda r: httpx.Response(200, json={"status": 0})).fetch("1") is None
    assert _client(lambda r: httpx.Response(404)).fetch("1") is None


def test_client_raises_when_it_could_not_ask():
    """A failure to reach OFF must never look like "OFF doesn't have it"."""

    def boom(request):
        raise httpx.ConnectError("offline")

    def timeout(request):
        raise httpx.ReadTimeout("too slow")

    for handler in (
        lambda r: httpx.Response(503),  # OFF down
        lambda r: httpx.Response(429),  # rate limited
        lambda r: httpx.Response(500),
        lambda r: httpx.Response(200, text="<html>not json</html>"),
        boom,
        timeout,
    ):
        with pytest.raises(SourceUnavailable):
            _client(handler).fetch("1")
