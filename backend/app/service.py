"""Product lookup: our database first, then Open Food Facts."""

from __future__ import annotations

from .models import CategoryRank, Product, ProductResult, ScoreResult
from .repository import ProductRepository
from .scoring import score_product
from .sources.off import ProductSource

# Below this many scored products, a percentile is noise wearing a number.
MIN_CATEGORY_FOR_RANK = 8


def normalize_barcode(code: str) -> str:
    """Strip spaces and turn a 12-digit UPC-A into the 13-digit form OFF stores."""
    code = "".join(code.split())
    return "0" + code if len(code) == 12 and code.isdigit() else code


def is_valid_barcode(code: str) -> bool:
    """EAN-8, UPC-A (12) or EAN-13 digits with a correct check digit."""
    if not code.isdigit() or len(code) not in (8, 12, 13):
        return False
    digits = [int(d) for d in code]
    body, check = digits[:-1], digits[-1]
    # Weights 3,1,3,... counted from the digit next to the check digit.
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


class ProductService:
    def __init__(self, repo: ProductRepository, source: ProductSource | None = None):
        self.repo = repo
        self.source = source

    def lookup(self, barcode: str) -> ProductResult | None:
        """Our database first, then the source. None means nobody has it.

        Lets SourceUnavailable through on purpose, so the caller can say "we
        couldn't check" rather than "it doesn't exist". Anything already cached
        is answered from our own database and never depends on the source.
        """
        product = self.repo.get(barcode)
        if product is None and self.source is not None:
            product = self.source.fetch(barcode)
            if product is not None:
                self.repo.upsert(product)  # cache so we don't ask OFF again
        if product is None:
            return None
        score = score_product(product)
        return ProductResult(product=product, score=score, rank=self.rank(product, score))

    def rank(self, product: Product, score: ScoreResult) -> CategoryRank | None:
        """Where this product stands among its category, or None if we cannot say.

        Kept out of the scoring engine on purpose: score_product() is a pure
        function of one label, while this depends on everything else we hold.
        Mixing them would make a score irreproducible from the published method.

        Silent below MIN_CATEGORY_FOR_RANK. A percentile drawn from four products
        looks precise and means nothing, and the categories that small are mostly
        ones our mapping has not learned yet.
        """
        if score.score is None or not product.category:
            return None
        below, total = self.repo.category_standing(product.category, score.score)
        if total < MIN_CATEGORY_FOR_RANK:
            return None
        peers = total - 1  # everyone but this product
        if peers <= 0:
            return None
        return CategoryRank(
            category=product.category,
            better_than_percent=round(below / peers * 100),
            total=total,
        )

    def alternatives(self, barcode: str, limit: int = 3) -> list[ProductResult]:
        current = self.lookup(barcode)
        if current is None or not current.product.category or current.score.score is None:
            return []
        better = self.repo.alternatives(
            current.product.category, current.score.score, exclude=barcode, limit=limit
        )
        return [ProductResult(product=p, score=score_product(p)) for p in better]

    def search(self, query: str, limit: int = 20) -> list[ProductResult]:
        return [ProductResult(product=p, score=score_product(p)) for p in self.repo.search(query, limit)]
