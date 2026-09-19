"""HTTP tests. Needs FastAPI installed (pip install -e '.[dev]')."""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repository import ProductRepository  # noqa: E402
from app.seed import seed  # noqa: E402
from app.service import ProductService  # noqa: E402


@pytest.fixture()
def client():
    repo = ProductRepository(":memory:")
    seed(repo)
    app = create_app(Settings(), ProductService(repo, source=None))
    with TestClient(app) as c:
        yield c


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["products"] == 8


def test_product_found(client):
    r = client.get("/v1/products/2000000000015")
    assert r.status_code == 200
    body = r.json()
    assert body["product"]["name"] == "Multigrain Digestive Biscuits"
    assert body["score"]["verdict"] == "avoid"
    assert any(n["key"] == "sugars_g" for n in body["score"]["nutrients"])


def test_product_not_found(client):
    r = client.get("/v1/products/8900000000019")
    assert r.status_code == 404
    assert r.json()["detail"] == "not_found"


def test_invalid_barcode(client):
    assert client.get("/v1/products/12345").status_code == 400


def test_alternatives(client):
    r = client.get("/v1/products/2000000000015/alternatives")
    assert [a["product"]["name"] for a in r.json()] == ["Jowar & Millet Thins", "Ragi Oat Cookies"]


def test_score_endpoint(client):
    r = client.post(
        "/v1/score",
        json={"barcode": "1", "name": "Water", "is_drink": True,
              "nutriments": {"energy_kcal": 0, "sugars_g": 0, "saturated_fat_g": 0, "sodium_mg": 1}},
    )
    assert r.json()["score"] == 100


def test_additive_lookup(client):
    assert client.get("/v1/additives/E150d").json()["name"] == "Sulphite ammonia caramel"
    assert client.get("/v1/additives/salt").status_code == 400
