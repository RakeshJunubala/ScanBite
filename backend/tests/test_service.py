from typing import Optional

from app.models import DataStatus, Nutriments, Product
from app.repository import ProductRepository
from app.seed import load_samples, seed
from app.service import ProductService, is_valid_barcode, normalize_barcode

BISCUIT = "2000000000015"
THINS = "2000000000022"
COOKIES = "2000000000039"


class FakeSource:
    def __init__(self, products: dict[str, Product]):
        self.products = products
        self.calls: list[str] = []

    def fetch(self, barcode: str) -> Optional[Product]:
        self.calls.append(barcode)
        return self.products.get(barcode)


def seeded_service(source=None) -> ProductService:
    repo = ProductRepository(":memory:")
    seed(repo)
    return ProductService(repo, source)


def test_barcode_validation():
    assert is_valid_barcode("2000000000015")
    assert not is_valid_barcode("2000000000016")  # wrong check digit
    assert is_valid_barcode("96385074")  # EAN-8
    assert not is_valid_barcode("abc")
    assert normalize_barcode("036000291452") == "0036000291452"
    assert is_valid_barcode(normalize_barcode("036000291452"))


def test_seed_loads_all_samples_once():
    repo = ProductRepository(":memory:")
    assert seed(repo) == len(load_samples())
    assert repo.count() == len(load_samples())


def test_lookup_from_own_database():
    result = seeded_service().lookup(BISCUIT)
    assert result is not None
    assert result.product.name == "Multigrain Digestive Biscuits"
    assert result.score.verdict.value == "avoid"


def test_unknown_product_falls_back_to_source_and_is_cached():
    off_product = Product(
        barcode="8900000000002",
        name="Off Biscuit",
        category="biscuits",
        nutriments=Nutriments(energy_kcal=480, sugars_g=30, saturated_fat_g=10, sodium_mg=250),
    )
    source = FakeSource({"8900000000002": off_product})
    service = seeded_service(source)
    first = service.lookup("8900000000002")
    second = service.lookup("8900000000002")
    assert first is not None and second is not None
    assert source.calls == ["8900000000002"]  # second lookup served from cache


def test_not_found_anywhere_returns_none():
    assert seeded_service(FakeSource({})).lookup("8900000000019") is None


def test_alternatives_are_same_category_and_better():
    alternatives = seeded_service().alternatives(BISCUIT)
    assert [a.product.barcode for a in alternatives] == [THINS, COOKIES]
    assert all(a.score.score > 14 for a in alternatives)


def test_verified_record_is_not_overwritten_by_community_data():
    repo = ProductRepository(":memory:")
    verified = Product(barcode="8900000000002", name="Checked name", status=DataStatus.verified)
    community = Product(barcode="8900000000002", name="Community name", status=DataStatus.community)
    assert repo.upsert(verified)
    assert not repo.upsert(community)
    assert repo.get("8900000000002").name == "Checked name"


def test_search_by_name_or_brand():
    service = seeded_service()
    assert {r.product.name for r in service.search("cola")} == {"Cola", "Zero Sugar Cola"}
    assert len(service.search("sample drinks")) == 2
