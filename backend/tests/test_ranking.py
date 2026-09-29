"""Within-category standing: the answer to "of these two, which one?"."""

from app.models import DataStatus, Product
from app.repository import ProductRepository
from app.service import MIN_CATEGORY_FOR_RANK, ProductService


def make(barcode: str, sugars: float, category: str | None = "biscuits") -> Product:
    return Product(
        barcode=barcode,
        name=f"Product {barcode[-3:]}",
        category=category,
        nutriments={"energy_kcal": 450, "sugars_g": sugars, "saturated_fat_g": 8, "sodium_mg": 300},
        status=DataStatus.community,
    )


def build(count: int, category: str | None = "biscuits") -> ProductService:
    """A category of `count` products, each worse than the last."""
    repo = ProductRepository(":memory:")
    for i in range(count):
        repo.upsert(make(f"890000000{i:04d}", sugars=float(i), category=category))
    return ProductService(repo, source=None)


def test_a_category_with_enough_products_gets_a_standing():
    svc = build(20)
    best = svc.lookup("8900000000000")  # least sugar
    worst = svc.lookup("8900000000019")

    assert best.rank is not None
    assert best.rank.category == "biscuits"
    assert best.rank.total == 20

    # Not 100%: the sugar scale is stepped, so these 20 products land on 11
    # distinct scores and the best four tie. Counting strictly below, the best
    # beats the 16 it genuinely outscores, not the 3 it matches.
    assert best.rank.better_than_percent == 84
    assert worst.rank.better_than_percent == 0
    assert best.rank.better_than_percent > worst.rank.better_than_percent


def test_products_on_the_same_verdict_are_still_told_apart():
    """The point of the feature: two "Avoid" products are not equally bad."""
    svc = build(20)
    a = svc.lookup("8900000000015")
    b = svc.lookup("8900000000018")
    assert a.score.verdict == b.score.verdict  # same verdict
    assert a.rank.better_than_percent > b.rank.better_than_percent  # different standing


def test_a_small_category_says_nothing():
    """A percentile drawn from a handful of products is noise wearing a number."""
    svc = build(MIN_CATEGORY_FOR_RANK - 1)
    assert svc.lookup("8900000000000").rank is None


def test_the_threshold_is_where_it_says_it_is():
    assert build(MIN_CATEGORY_FOR_RANK).lookup("8900000000000").rank is not None
    assert build(MIN_CATEGORY_FOR_RANK - 1).lookup("8900000000000").rank is None


def test_no_category_means_no_standing():
    """167 of the imported products have no category. They must not be ranked."""
    svc = build(20, category=None)
    assert svc.lookup("8900000000000").rank is None


def test_an_unscored_product_has_no_standing():
    repo = ProductRepository(":memory:")
    for i in range(20):
        repo.upsert(make(f"890000000{i:04d}", sugars=float(i)))
    # No nutrition table at all, so no score, so nothing to rank.
    repo.upsert(Product(barcode="8901111111116", name="Blank", category="biscuits", status=DataStatus.community))
    svc = ProductService(repo, source=None)

    result = svc.lookup("8901111111116")
    assert result.score.score is None
    assert result.rank is None


def test_products_tied_on_a_score_do_not_beat_each_other():
    repo = ProductRepository(":memory:")
    for i in range(10):
        repo.upsert(make(f"890000000{i:04d}", sugars=20.0))  # all identical
    svc = ProductService(repo, source=None)
    assert svc.lookup("8900000000000").rank.better_than_percent == 0


def test_standing_does_not_touch_the_score():
    """The score stays a pure function of the label, whatever the database holds."""
    lonely = build(1).lookup("8900000000000")
    crowded = build(30).lookup("8900000000000")
    assert lonely.score.score == crowded.score.score
    assert lonely.rank is None and crowded.rank is not None
