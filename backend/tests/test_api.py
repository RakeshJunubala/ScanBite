"""HTTP tests. Needs FastAPI installed (pip install -e '.[dev]')."""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import DataStatus, Product
from app.repository import ProductRepository
from app.seed import seed
from app.service import ProductService
from app.sources.off import SourceUnavailable


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
    r = client.get("/v1/products/8900000000012")
    assert r.status_code == 404
    assert r.json()["detail"] == "not_found"


def test_invalid_barcode(client):
    assert client.get("/v1/products/12345").status_code == 400


TOKEN = "test-admin-token"
BARCODE = "8900000000012"  # valid EAN-13 check digit, not in the seed data


def _submission(**over):
    body = {
        "product": {
            "barcode": BARCODE,
            "name": "Test Namkeen",
            "brand": "Test Brand",
            "is_drink": False,
            "nutriments": {"energy_kcal": 520, "sugars_g": 3, "saturated_fat_g": 12, "sodium_mg": 900},
            # A submitter claiming "verified" must not get it.
            "status": "verified",
        },
        "submitted_by": "someone@example.com",
        "source": "pack label",
        "notes": "typed from the back of the pack",
    }
    body.update(over)
    return body


@pytest.fixture()
def admin():
    repo = ProductRepository(":memory:")
    seed(repo)
    app = create_app(Settings(admin_token=TOKEN), ProductService(repo, source=None))
    with TestClient(app) as c:
        yield c, repo


def test_submissions_are_disabled_without_an_admin_token(client):
    """The default build must not accept writes at all."""
    r = client.post("/v1/products", json=_submission())
    assert r.status_code == 503
    assert r.json()["detail"] == "submissions_disabled"


def test_submission_needs_the_right_token(admin):
    c, _ = admin
    assert c.post("/v1/products", json=_submission()).status_code == 401
    r = c.post("/v1/products", json=_submission(), headers={"X-Admin-Token": "wrong"})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_token"


def test_submission_is_always_provisional_and_hides_provenance(admin):
    c, repo = admin
    r = c.post("/v1/products", json=_submission(), headers={"X-Admin-Token": TOKEN})
    assert r.status_code == 201
    body = r.json()

    # Claimed "verified", stored as provisional.
    assert body["product"]["status"] == "provisional"
    assert repo.get(BARCODE).status.value == "provisional"
    assert body["score"]["score"] is not None

    # Provenance is recorded, but never travels back over the wire.
    serialised = r.text
    assert "someone@example.com" not in serialised
    assert "submitted_by" not in serialised
    rows = repo.submissions(BARCODE)
    assert len(rows) == 1
    assert rows[0]["submitted_by"] == "someone@example.com"
    assert rows[0]["source"] == "pack label"

    # And it is now readable like any other product.
    assert c.get(f"/v1/products/{BARCODE}").json()["product"]["name"] == "Test Namkeen"


def test_submission_refuses_an_existing_barcode_unless_overwrite(admin):
    c, repo = admin
    head = {"X-Admin-Token": TOKEN}
    assert c.post("/v1/products", json=_submission(), headers=head).status_code == 201

    again = c.post("/v1/products", json=_submission(), headers=head)
    assert again.status_code == 409
    assert again.json()["detail"] == "already_exists"

    renamed = _submission()
    renamed["product"]["name"] = "Corrected Name"
    ok = c.post("/v1/products?overwrite=true", json=renamed, headers=head)
    assert ok.status_code == 201
    assert repo.get(BARCODE).name == "Corrected Name"
    assert len(repo.submissions(BARCODE)) == 2  # both attempts kept as history


def test_submission_never_displaces_a_verified_record(admin):
    """overwrite=true still must not beat our own reviewed data."""
    c, repo = admin
    verified = Product(barcode=BARCODE, name="Reviewed By Us", status=DataStatus.verified)
    assert repo.upsert(verified)

    r = c.post("/v1/products?overwrite=true", json=_submission(), headers={"X-Admin-Token": TOKEN})
    assert r.status_code == 409
    assert r.json()["detail"] == "more_trusted_record_exists"
    assert repo.get(BARCODE).name == "Reviewed By Us"


def test_submission_validates_the_barcode(admin):
    c, _ = admin
    bad = _submission()
    bad["product"]["barcode"] = "12345"
    r = c.post("/v1/products", json=bad, headers={"X-Admin-Token": TOKEN})
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_barcode"


def test_unreachable_source_is_503_not_404():
    """"We couldn't check" must not reach the app as "we don't have it"."""

    class Broken:
        def fetch(self, barcode):
            raise SourceUnavailable("HTTP 429")

    repo = ProductRepository(":memory:")
    seed(repo)
    app = create_app(Settings(), ProductService(repo, source=Broken()))
    with TestClient(app) as c:
        r = c.get("/v1/products/8900000000012")
        assert r.status_code == 503
        assert r.json()["detail"] == "source_unavailable"
        # A product we already hold is unaffected -- it never asks the source.
        assert c.get("/v1/products/2000000000015").status_code == 200


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
