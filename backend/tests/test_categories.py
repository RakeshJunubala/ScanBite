"""Category mapping. A category exists to rank products against their peers."""

from app.sources.off import CANONICAL_CATEGORIES, map_off_product, normalise_category


def category_for(*tags: str) -> str | None:
    return map_off_product("8901234567895", {"product_name": "X", "categories_tags": list(tags)}).category


def test_the_most_specific_tag_wins():
    """Products carry several tags at once, so order decides."""
    assert category_for("en:snacks", "en:sweet-snacks", "en:biscuits") == "biscuits"
    assert category_for("en:beverages", "en:soft-drinks") == "soft-drinks"
    assert category_for("en:beverages", "en:waters") == "water"


def test_an_unrecognised_tag_gives_no_category():
    """The old fallback took the last tag, whatever it was.

    That turned Nutella into the category "Nuttela", and produced "Groceries",
    "Food" and 134 other values across 215 products -- most holding one or two
    items. A category of one cannot rank anything.
    """
    assert category_for("en:nuttela") is None
    assert category_for("en:groceries") is None
    assert category_for("en:food") is None
    assert category_for("en:some-tag-we-have-never-seen") is None
    assert category_for() is None


def test_related_tags_collapse_into_one_comparable_category():
    """Real tags seen in the import that were fragmenting the space."""
    for tag in ("en:peanut-butters", "en:crunchy-peanut-butters", "en:nut-butters"):
        assert category_for(tag) == "nut-butters"
    for tag in ("en:coconut-oils", "en:sunflower-oils", "en:soybean-oils"):
        assert category_for(tag) == "edible-oils"
    for tag in ("en:breads", "en:white-breads", "en:toasts", "en:rusks"):
        assert category_for(tag) == "bakery"
    for tag in ("en:ice-creams", "en:ice-cream-in-a-box"):
        assert category_for(tag) == "ice-cream"
    for tag in ("en:masalas", "en:spices"):
        assert category_for(tag) == "spices"


def test_language_prefixes_do_not_matter():
    assert category_for("fr:biscuits") == "biscuits"
    assert category_for("biscuits") == "biscuits"
    assert category_for("en:Biscuits") == "biscuits"


def test_normalise_accepts_our_own_names_and_raw_tags():
    """Used to clean up rows written before the fallback was removed."""
    assert normalise_category("biscuits") == "biscuits"  # already ours
    assert normalise_category("en:peanut-butters") == "nut-butters"  # raw tag
    assert normalise_category("peanut-butters") == "nut-butters"  # stored tag
    assert normalise_category("Groceries") is None
    assert normalise_category("Nuttela") is None
    assert normalise_category(None) is None
    assert normalise_category("") is None


def test_every_mapped_value_is_canonical():
    """Nothing may map to a name that is not in the canonical set."""
    for tag in ("en:biscuits", "en:snacks", "en:dates", "en:teas", "en:milks"):
        assert category_for(tag) in CANONICAL_CATEGORIES


def test_renormalise_fixes_rows_written_before_the_fallback_was_removed():
    """Stored rows keep junk categories until something goes back over them."""
    from app.models import DataStatus, Product
    from app.repository import ProductRepository

    repo = ProductRepository(":memory:")
    for barcode, category in [
        ("8901719134845", "Groceries"),        # junk -> cleared
        ("8901063139329", "peanut-butters"),   # real tag -> canonical
        ("8901058017687", "biscuits"),         # already ours -> untouched
    ]:
        repo.upsert(Product(barcode=barcode, name="X", category=category, status=DataStatus.community))

    assert repo.renormalise_categories() == 2
    assert repo.get("8901719134845").category is None
    assert repo.get("8901063139329").category == "nut-butters"
    assert repo.get("8901058017687").category == "biscuits"

    # The column and the JSON must agree, or a product is ranked in one category
    # and displayed in another.
    with repo._tx() as cur:
        column = cur.execute("SELECT category FROM products WHERE barcode = ?", ("8901063139329",)).fetchone()[0]
    assert column == repo.get("8901063139329").category

    assert repo.renormalise_categories() == 0  # idempotent


def test_a_cascading_tag_does_not_beat_the_distinctive_one():
    """Balaji Chataka Pataka, a real record, arrives with all of these at once.

    Open Food Facts' hierarchy cascades, so a potato wafer carries en:biscuits
    by way of "biscuits-and-crackers". Ranked as a biscuit it was compared
    against shortbread.
    """
    balaji = (
        "en:snacks", "en:salty-snacks", "en:sweet-snacks", "en:appetizers",
        "en:biscuits-and-cakes", "en:biscuits-and-crackers", "en:chips-and-fries",
        "en:biscuits", "en:crisps", "en:crackers-appetizers", "en:namkeen",
    )
    assert category_for(*balaji) == "snacks"

    # A savoury cracker sharing only the generic snack tag stays a biscuit:
    # its composition is closer to shortbread than to a crisp.
    assert category_for("en:snacks", "en:salty-snacks", "en:biscuits") == "biscuits"


def test_stored_tags_let_a_wrong_category_be_corrected_later():
    """Without the source's own tags, a category is frozen at import time."""
    from app.models import DataStatus, Product
    from app.repository import ProductRepository

    repo = ProductRepository(":memory:")
    # As an older mapping would have filed it: a potato wafer under biscuits.
    repo.upsert(
        Product(
            barcode="8906010500764",
            name="Balaji Wafers",
            category="biscuits",
            category_tags=["en:snacks", "en:chips-and-fries", "en:biscuits", "en:crisps"],
            status=DataStatus.community,
        )
    )
    # A row from before we kept tags cannot be corrected, only cleaned.
    repo.upsert(Product(barcode="8901063139329", name="Old Row", category="biscuits", status=DataStatus.community))

    assert repo.renormalise_categories() == 1
    assert repo.get("8906010500764").category == "snacks"  # re-derived from tags
    assert repo.get("8901063139329").category == "biscuits"  # no tags, left alone
