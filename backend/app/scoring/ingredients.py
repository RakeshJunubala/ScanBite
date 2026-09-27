"""Reads an ingredient list for processing markers.

Indian labels list ingredients in descending order of weight, so position
matters: "the first ingredient" is the main one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REFINED_FLOUR = ("maida", "refined wheat flour", "refined flour")
ADDED_SUGARS = (
    "sugar",
    "invert syrup",
    "invert sugar",
    "liquid glucose",
    "glucose syrup",
    "corn syrup",
    "dextrose",
    "fructose",
    "sucrose",
    "jaggery",
    "honey",
    "malt extract",
    "maltodextrin",
)
NOT_SUGAR = ("sugar free", "sugar-free", "no added sugar")
PALM = ("palm oil", "palmolein", "palm kernel", "palm fat", "palm olein")
HYDROGENATED = ("hydrogenated", "vanaspati")
SWEETENER_WORDS = (
    "aspartame",
    "sucralose",
    "acesulfame",
    "saccharin",
    "cyclamate",
    "stevia",
    "steviol",
    "neotame",
)
SWEETENER_CODES = {"950", "951", "952", "954", "955", "960", "961", "962", "965", "966", "967", "968", "969"}


def split_ingredients(text: str | None) -> list[str]:
    """Split on commas that are not inside (), [] or {} and lower-case each item."""
    if not text:
        return []
    text = re.sub(r"^\s*ingredients?\s*[:\-]\s*", "", text.strip(), flags=re.IGNORECASE)
    items: list[str] = []
    depth = 0
    current = []
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if (ch in ",;" and depth == 0):
            item = "".join(current).strip(" .\n\t")
            if item:
                items.append(item.lower())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip(" .\n\t")
    if tail:
        items.append(tail.lower())
    return items


_PALM_RE = re.compile(r"\bpalm(?:olein)?\b")
# Innermost bracket group only; head() repeats until nothing is left to strip.
_BRACKETS_RE = re.compile(r"[\(\[\{][^\(\)\[\]\{\}]*[\)\]\}]")


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(w in text for w in words)


def head(item: str) -> str:
    """The ingredient's own name, without its bracketed sub-ingredients.

    "peri peri seasoning (salt, sugar, ...)" -> "peri peri seasoning"
    """
    previous = None
    while previous != item:
        previous = item
        item = _BRACKETS_RE.sub("", item)
    return item.strip()


def _is_added_sugar(item: str) -> bool:
    if _has_any(item, NOT_SUGAR):
        return False
    return _has_any(item, ADDED_SUGARS)


@dataclass
class IngredientSignals:
    items: list[str] = field(default_factory=list)
    refined_flour_first: bool = False
    added_sugar_top3: bool = False
    added_sugar_any: bool = False
    palm_oil: bool = False
    hydrogenated_fat: bool = False
    sweeteners: bool = False


def analyse(ingredients_text: str | None, additive_codes: list[str]) -> IngredientSignals:
    items = split_ingredients(ingredients_text)
    signals = IngredientSignals(items=items)
    if items:
        # The first item keeps its brackets: labels often write "refined wheat flour (maida)".
        signals.refined_flour_first = _has_any(items[0], REFINED_FLOUR)
        # A pinch of sugar inside a seasoning mix is not "sugar as a main ingredient".
        signals.added_sugar_top3 = any(_is_added_sugar(head(i)) for i in items[:3])
        signals.added_sugar_any = any(_is_added_sugar(i) for i in items)
        joined = " | ".join(items)
        signals.palm_oil = _has_any(joined, PALM) or bool(_PALM_RE.search(joined))
        signals.hydrogenated_fat = _has_any(joined, HYDROGENATED)
        signals.sweeteners = _has_any(joined, SWEETENER_WORDS)
    bases = {c.split("(")[0] for c in additive_codes}
    if bases & SWEETENER_CODES:
        signals.sweeteners = True
    return signals
