"""INS additive lookup, code normalisation and extraction from ingredient text."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..models import AdditiveFact

_DATA_FILE = Path(__file__).parent / "data" / "additives.json"

# 3-4 digits, optional letter sub-class (a-h), optional roman sub-number.
_CODE_RE = re.compile(r"^(\d{3,4})([a-h])?(?:\(?(i{1,3}|iv|v|vi)\)?)?$")
_ROMAN = {"i", "ii", "iii", "iv", "v", "vi"}

# Codes written with an explicit INS or E prefix, e.g. "INS 503(ii)", "E150d".
_PREFIXED_RE = re.compile(
    r"\b(?:ins|e)\s*-?\s*(\d{3,4}[a-h]?(?:\s*\((?:i{1,3}|iv|v|vi)\))?)",
    re.IGNORECASE,
)
# Bare codes as Indian labels often print them: "raising agents [503(ii), 500(ii)]".
_BARE_RE = re.compile(
    r"(?<![\d.])(\d{3,4}[a-h]?(?:\s*\((?:i{1,3}|iv|v|vi)\))?)(?!\s*(?:%|g\b|mg\b|ml\b|kcal|kj|\d))",
    re.IGNORECASE,
)


def normalize_code(raw: str) -> Optional[str]:
    """Turn "E150d", "en:e503ii", "INS 322(i)" or "503 (ii)" into "150d", "503(ii)", "322(i)".

    Returns None when the text is not an additive code.
    """
    s = raw.strip().lower()
    s = s.removeprefix("en:")
    s = re.sub(r"^(ins|e)\s*-?\s*", "", s)
    s = s.replace(" ", "")
    m = _CODE_RE.match(s)
    if not m:
        return None
    digits, letter, roman = m.group(1), m.group(2) or "", m.group(3)
    number = int(digits)
    if not 100 <= number <= 1599:
        return None
    code = digits + letter
    if roman and roman in _ROMAN:
        code += f"({roman})"
    return code


def base_code(code: str) -> str:
    """"503(ii)" -> "503"; "150d" stays "150d" (letters are distinct additives)."""
    return code.split("(")[0]


@lru_cache(maxsize=1)
def _table() -> dict[str, dict]:
    data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    return {row["code"]: row for row in data["additives"]}


def lookup(code: str) -> Optional[dict]:
    table = _table()
    return table.get(code) or table.get(base_code(code))


def describe(code: str) -> AdditiveFact:
    row = lookup(code)
    if row is None:
        return AdditiveFact(
            code=code,
            name=f"INS {code}",
            function="Additive",
            risk="unknown",
            note="Not in our additive table yet",
            known=False,
        )
    return AdditiveFact(
        code=code,
        name=row["name"],
        function=row["function"],
        risk=row["risk"],
        note=row.get("note"),
        known=True,
        animal=row.get("animal", "no"),
    )


def animal_origin(code: str) -> str:
    row = lookup(code)
    return row.get("animal", "no") if row else "no"


def extract_codes(ingredients_text: Optional[str]) -> list[str]:
    """Find additive codes in an ingredient list.

    Prefixed codes (INS 322, E150d) are always taken. Bare numbers are taken
    only when they are in our additive table, so "62%" or "250 g" never match.
    """
    if not ingredients_text:
        return []
    found: list[str] = []

    def add(code: Optional[str]) -> None:
        if code and code not in found:
            found.append(code)

    for m in _PREFIXED_RE.finditer(ingredients_text):
        add(normalize_code(m.group(1)))
    for m in _BARE_RE.finditer(ingredients_text):
        code = normalize_code(m.group(1))
        if code and lookup(code) is not None:
            add(code)
    return found


def merge_codes(*lists: list[str]) -> list[str]:
    """Normalise and de-duplicate codes from several sources, keeping order."""
    out: list[str] = []
    for codes in lists:
        for raw in codes:
            code = normalize_code(raw)
            if code and code not in out:
                out.append(code)
    return out
