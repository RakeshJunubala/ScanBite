"""Open Food Facts: fallback product data.

Licence: the database is ODbL (share-alike). We keep OFF records marked
`community` and separate from our own verified records. Heavy use should
switch to their daily export instead of the live API (they rate-limit reads).
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from ..models import DataStatus, Nutriments, Product

# FLY002 is suppressed below on purpose: ruff would have this be one long string
# literal, but a field per line keeps additions and diffs readable.
FIELDS = ",".join(  # noqa: FLY002
    [
        "code",
        "product_name",
        "product_name_en",
        "brands",
        "quantity",
        "categories_tags",
        "nutriments",
        "ingredients_text",
        "ingredients_text_en",
        "additives_tags",
        "allergens_tags",
        "traces_tags",
        "labels_tags",
        "image_front_url",
        "serving_quantity",
    ]
)

# OFF allergen tags -> the words the app uses in profiles and alerts.
_ALLERGEN_NAMES = {
    "gluten": "gluten",
    "milk": "milk",
    "soybeans": "soy",
    "eggs": "egg",
    "peanuts": "peanut",
    "nuts": "tree nuts",
    "sesame-seeds": "sesame",
    "fish": "fish",
    "crustaceans": "crustaceans",
    "molluscs": "molluscs",
    "mustard": "mustard",
    "celery": "celery",
    "lupin": "lupin",
    "sulphur-dioxide-and-sulphites": "sulphites",
}

_DRINK_TAGS = {"en:beverages"}
# Milk and dairy drinks are scored as foods, as the original Nutri-Score did.
_NOT_DRINK_TAGS = {"en:dairies", "en:milks", "en:dairy-drinks", "en:fermented-milk-products"}

# Open Food Facts tag -> our category, most specific first.
#
# A product carries many tags at once ("snacks", "sweet-snacks", "biscuits"), so
# the order decides which one wins: biscuits before snacks, or every biscuit
# lands in the generic bucket.
#
# Tags are matched without their language prefix, so "en:biscuits" and
# "fr:biscuits" both hit the same row.
#
# The list exists to make categories *comparable*. A category holding two
# products cannot tell anyone whether a third is better or worse than its peers,
# so there is no value in inventing one per tag -- an unrecognised tag gives no
# category at all. Entries below earn their place from real Indian data.
_CATEGORY_PRIORITY: list[tuple[str, str]] = [
    # Savoury snacks come first. Open Food Facts' hierarchy cascades, so a potato
    # wafer carries en:biscuits by way of "biscuits-and-crackers" -- Balaji
    # Chataka Pataka arrives tagged snacks, salty-snacks, chips-and-fries,
    # crisps, namkeen *and* biscuits. The distinctive tag has to win, or crisps
    # get ranked against shortbread.
    ("chips-and-fries", "snacks"),
    ("crisps", "snacks"),
    ("namkeen", "snacks"),
    # Biscuits and bakery
    ("biscuits", "biscuits"),
    ("cookies", "biscuits"),
    ("rusks", "bakery"),
    ("toasts", "bakery"),
    ("white-breads", "bakery"),
    ("breads", "bakery"),
    ("cakes", "bakery"),
    # Noodles and pasta
    ("instant-noodles", "instant-noodles"),
    ("instant-pasta", "instant-noodles"),
    ("noodles", "instant-noodles"),
    ("pastas", "pasta"),
    # Cereals
    ("breakfast-cereals", "breakfast-cereals"),
    ("oats", "breakfast-cereals"),
    ("mueslis", "breakfast-cereals"),
    # Savoury snacks. The distinctive ones are ordered above biscuits; these are
    # the generic fallbacks, which a savoury cracker may legitimately share with
    # biscuits and should lose to it.
    ("salty-snacks", "snacks"),
    ("snacks", "snacks"),
    # Sweets
    ("chocolates", "chocolates"),
    ("ice-creams", "ice-cream"),
    ("ice-cream-in-a-box", "ice-cream"),
    # Spreads and nut butters
    ("crunchy-peanut-butters", "nut-butters"),
    ("peanut-butters", "nut-butters"),
    ("nut-butters", "nut-butters"),
    ("mixed-fruit-jams", "spreads"),
    ("jams", "spreads"),
    ("honeys", "sweeteners"),
    ("sugars", "sweeteners"),
    ("jaggery", "sweeteners"),
    # Cooking
    ("coconut-oils", "edible-oils"),
    ("sunflower-oils", "edible-oils"),
    ("soybean-oils", "edible-oils"),
    ("mustard-oils", "edible-oils"),
    ("olive-oils", "edible-oils"),
    ("vegetable-oils", "edible-oils"),
    ("ghees", "edible-oils"),
    ("masalas", "spices"),
    ("spices", "spices"),
    ("salts", "salt"),
    # Condiments
    ("plant-based-pickles", "pickles"),
    ("pickles", "pickles"),
    ("sauces", "sauces"),
    ("soups", "soups"),
    # Nuts and dried fruit
    ("dates", "dried-fruits"),
    ("raisins", "dried-fruits"),
    ("dried-fruits", "dried-fruits"),
    ("peanuts", "nuts"),
    ("almonds", "nuts"),
    ("cashew-nuts", "nuts"),
    ("nuts", "nuts"),
    # Drinks
    ("soft-drinks", "soft-drinks"),
    ("sodas", "soft-drinks"),
    ("energy-drinks", "soft-drinks"),
    ("fruit-juices", "juices"),
    ("juices", "juices"),
    ("instant-coffees", "coffee-and-tea"),
    ("coffees", "coffee-and-tea"),
    ("teas", "coffee-and-tea"),
    ("waters", "water"),
    ("dairies", "dairy"),
    ("milks", "dairy"),
    ("beverages", "drinks"),
]

# Same table keyed by tag, for normalising a category already stored.
_CATEGORY_BY_TAG = dict(_CATEGORY_PRIORITY)
CANONICAL_CATEGORIES = frozenset(_CATEGORY_BY_TAG.values())


def _strip(tag: str) -> str:
    return tag.split(":", 1)[1] if ":" in tag else tag


def _num(nutriments: dict[str, Any], key: str) -> float | None:
    value = nutriments.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalise_category(value: str | None) -> str | None:
    """A category we can compare products within, or None.

    Accepts either one of our own category names or a raw Open Food Facts tag,
    so it works on freshly mapped products and on rows already stored.
    """
    if not value:
        return None
    name = _strip(value).strip().lower()
    if name in CANONICAL_CATEGORIES:
        return name
    return _CATEGORY_BY_TAG.get(name)


def category_from_tags(tags: list[str]) -> str | None:
    """The most specific category we recognise, or None.

    Returning None matters. This used to fall back to the last tag Open Food
    Facts happened to list, which produced categories like "Groceries", "Food"
    and the misspelling "Nuttela" -- 136 different values across 215 products,
    most holding one or two items. "Better choices" ranks within a category, and
    a category of one can say nothing about anything. No category beats a
    category that only looks like one.
    """
    names = {_strip(tag).strip().lower() for tag in tags}
    for tag, canonical in _CATEGORY_PRIORITY:
        if tag in names:
            return canonical
    return None


def map_off_product(barcode: str, raw: dict[str, Any]) -> Product:
    """Convert an OFF v2 `product` object into our Product model."""
    nutr = raw.get("nutriments") or {}
    energy = _num(nutr, "energy-kcal_100g")
    if energy is None:
        kj = _num(nutr, "energy_100g")  # OFF stores energy_100g in kJ
        energy = round(kj / 4.184, 1) if kj is not None else None
    sodium_g = _num(nutr, "sodium_100g")  # grams
    if sodium_g is None:
        salt_g = _num(nutr, "salt_100g")
        sodium_g = salt_g / 2.5 if salt_g is not None else None

    tags = raw.get("categories_tags") or []
    tagset = set(tags)
    is_drink = bool(tagset & _DRINK_TAGS) and not (tagset & _NOT_DRINK_TAGS)

    name = raw.get("product_name_en") or raw.get("product_name") or "Unnamed product"
    brand = (raw.get("brands") or "").split(",")[0].strip() or None
    serving = raw.get("serving_quantity")
    try:
        serving_g = float(serving) if serving not in (None, "") else None
    except (TypeError, ValueError):
        serving_g = None

    def names(key: str) -> list[str]:
        out = []
        for tag in raw.get(key) or []:
            word = _ALLERGEN_NAMES.get(_strip(tag), _strip(tag).replace("-", " "))
            if word not in out:
                out.append(word)
        return out

    return Product(
        barcode=barcode,
        name=name.strip(),
        brand=brand,
        quantity=raw.get("quantity") or None,
        category=category_from_tags(tags),
        category_tags=list(tags),
        is_drink=is_drink,
        nutriments=Nutriments(
            energy_kcal=energy,
            fat_g=_num(nutr, "fat_100g"),
            saturated_fat_g=_num(nutr, "saturated-fat_100g"),
            trans_fat_g=_num(nutr, "trans-fat_100g"),
            sugars_g=_num(nutr, "sugars_100g"),
            sodium_mg=round(sodium_g * 1000, 1) if sodium_g is not None else None,
            fibre_g=_num(nutr, "fiber_100g"),
            protein_g=_num(nutr, "proteins_100g"),
            fruit_veg_nuts_pct=_num(nutr, "fruits-vegetables-nuts-estimate-from-ingredients_100g"),
        ),
        serving_size_g=serving_g,
        ingredients_text=raw.get("ingredients_text_en") or raw.get("ingredients_text") or None,
        additives=list(raw.get("additives_tags") or []),
        allergens=names("allergens_tags"),
        traces=names("traces_tags"),
        labels=[_strip(t) for t in raw.get("labels_tags") or []],
        image_url=raw.get("image_front_url") or None,
        status=DataStatus.community,
    )


class SourceUnavailable(Exception):
    """We could not ask the source, so we do not know whether it has the product.

    Kept separate from a lookup that succeeded and found nothing. Collapsing the
    two is how "Open Food Facts timed out" reaches a person as "we don't have
    this product" -- a claim we have no grounds to make, and one that hides a
    broken pipeline behind an ordinary-looking empty result.
    """


class ProductSource(Protocol):
    def fetch(self, barcode: str) -> Product | None:
        """The product, or None when the source genuinely has no record of it.

        Raises SourceUnavailable when the source could not be reached or its
        answer could not be used.
        """
        ...


class OpenFoodFactsClient:
    def __init__(self, base_url: str, user_agent: str, timeout_s: float = 4.0, client: httpx.Client | None = None):
        self._base = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout_s, headers={"User-Agent": user_agent})

    def fetch(self, barcode: str) -> Product | None:
        """The product, or None when OFF genuinely has no record of this barcode.

        Raises SourceUnavailable for anything that means we failed to ask:
        timeout, transport error, rate limit, server error, unusable body.
        """
        try:
            response = self._client.get(f"{self._base}/api/v2/product/{barcode}", params={"fields": FIELDS})
        except httpx.HTTPError as err:
            raise SourceUnavailable(f"{type(err).__name__}: {err}") from err
        # OFF answers a genuine miss two ways: 404, or 200 with status 0.
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise SourceUnavailable(f"HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as err:
            raise SourceUnavailable("response body was not JSON") from err
        if body.get("status") != 1 or not body.get("product"):
            return None
        return map_off_product(barcode, body["product"])
