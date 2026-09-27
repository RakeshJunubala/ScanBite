"""Physical sanity checks on a nutrition panel.

Crowd-sourced and photo-read data contains values that cannot be true: a decimal
slipped, grams entered where milligrams were meant, a zero left in an empty
field. Open Food Facts records Tata Salt with 0 mg sodium, which scored 100 --
"Great" -- for a product that is entirely salt.

These rules need no knowledge of what the product is. They come from mass,
chemistry and the energy content of the macronutrients, so they hold for any
food and cannot be argued with.

An implausible value is **dropped, never corrected**. We do not know the true
figure, and inventing one in a health app is worse than admitting a gap. Dropping
it hands the record to the scoring engine's missing-nutrient rule, which already
refuses to put a number on a panel with two or more gaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Nutriments

# Sodium chloride is 39.34% sodium by mass, so nothing edible exceeds this per
# 100 g. Values far above it are the milligram/gram confusion: Open Food Facts
# has Indian records at 118,000-385,000 mg.
MAX_SODIUM_MG = 39_400

# Pure fat is 900 kcal per 100 g, the ceiling for any food.
MAX_ENERGY_KCAL = 900

# Energy implied by the macronutrients we can see, using the Atwater factors
# (4 kcal/g protein and carbohydrate, 9 kcal/g fat). Sugars are a subset of
# carbohydrate, so this is a floor, not an estimate -- real energy is usually
# higher because of starch we cannot see. A declared energy below this floor is
# impossible rather than merely odd.
ATWATER_TOLERANCE = 0.75

# Below this the floor is too small to judge: rounding alone could explain it.
MIN_FLOOR_TO_JUDGE_KCAL = 20

CORE = ("energy_kcal", "sugars_g", "saturated_fat_g", "sodium_mg")


@dataclass(frozen=True)
class Problem:
    rule: str
    detail: str
    fields: tuple[str, ...]


@dataclass
class Result:
    dropped: dict[str, float] = field(default_factory=dict)
    problems: list[Problem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def summary(self) -> str:
        return "; ".join(p.detail for p in self.problems)


def _positive(value: float | None) -> float:
    return value if value and value > 0 else 0.0


def check(n: Nutriments, *, is_drink: bool = False) -> Result:
    """Which values in this panel cannot be true, and why."""
    result = Result()
    # Read model_fields off the class: on the instance it is deprecated in
    # Pydantic 2.11 and goes away in 3.0.
    values = {name: getattr(n, name) for name in Nutriments.model_fields}

    def drop(rule: str, detail: str, *names: str) -> None:
        present = tuple(name for name in names if values.get(name) is not None)
        if not present:
            return
        for name in present:
            result.dropped[name] = values[name]
            values[name] = None
        result.problems.append(Problem(rule=rule, detail=detail, fields=present))

    # 1. Negative quantities.
    for name, value in list(values.items()):
        if value is not None and value < 0:
            drop("negative", f"{name} is negative ({value})", name)

    # 2. Hard physical ceilings.
    if (values.get("sodium_mg") or 0) > MAX_SODIUM_MG:
        drop(
            "sodium_above_pure_salt",
            f"sodium {values['sodium_mg']:.0f} mg/100 g exceeds pure salt ({MAX_SODIUM_MG} mg)",
            "sodium_mg",
        )
    if (values.get("energy_kcal") or 0) > MAX_ENERGY_KCAL:
        drop(
            "energy_above_pure_fat",
            f"energy {values['energy_kcal']:.0f} kcal/100 g exceeds pure fat ({MAX_ENERGY_KCAL} kcal)",
            "energy_kcal",
        )
    for name in ("sugars_g", "saturated_fat_g", "fat_g", "protein_g", "fibre_g", "added_sugars_g", "trans_fat_g"):
        if (values.get(name) or 0) > 100:
            drop("above_100g", f"{name} is {values[name]} g per 100 g", name)

    # 3. Subset violations. Either figure could be the wrong one, so both go:
    #    keeping the narrower would leave a contradiction, and keeping the wider
    #    would flatter the score by removing a penalised nutrient.
    sat, fat = values.get("saturated_fat_g"), values.get("fat_g")
    if sat is not None and fat is not None and sat > fat + 0.5:
        drop(
            "saturated_fat_above_total_fat",
            f"saturated fat {sat} g exceeds total fat {fat} g",
            "saturated_fat_g",
            "fat_g",
        )
    added, sugars = values.get("added_sugars_g"), values.get("sugars_g")
    if added is not None and sugars is not None and added > sugars + 0.5:
        drop(
            "added_sugar_above_total_sugar",
            f"added sugar {added} g exceeds total sugars {sugars} g",
            "added_sugars_g",
            "sugars_g",
        )

    # 4. Mass. Sugars are part of carbohydrate, so this sum is a lower bound on
    #    the real total; exceeding 100 g in 100 g of food is impossible.
    mass = sum(_positive(values.get(k)) for k in ("fat_g", "sugars_g", "protein_g", "fibre_g"))
    if mass > 100:
        drop(
            "mass_over_100g",
            f"fat, sugars, protein and fibre total {mass:.1f} g in 100 g",
            "fat_g",
            "sugars_g",
            "protein_g",
            "fibre_g",
        )

    # 5. Atwater floor: declared energy cannot be less than its own macros.
    floor = 9 * _positive(values.get("fat_g")) + 4 * (
        _positive(values.get("sugars_g")) + _positive(values.get("protein_g"))
    )
    energy = values.get("energy_kcal")
    if energy is not None and floor >= MIN_FLOOR_TO_JUDGE_KCAL and energy < floor * ATWATER_TOLERANCE:
        drop(
            "energy_below_macros",
            f"energy {energy:.0f} kcal is below the {floor:.0f} kcal its own fat, sugar and protein supply",
            "energy_kcal",
        )

    # 6. A solid food made of nothing. Water and soda water are genuinely all
    #    zeroes, which is why this is limited to foods -- a blanket rule would
    #    reject the one case that is correct.
    if not is_drink:
        core = [values.get(k) for k in CORE]
        if all(v is not None for v in core) and all(v == 0 for v in core):
            drop(
                "solid_food_entirely_zero",
                "a solid food with no energy, sugar, saturated fat or sodium is not a food",
                *CORE,
            )

    # 7. Whoever filled in a value that cannot be true was not being careful, so
    #    the rest of the panel has not earned any trust either. An absent value
    #    means we do not know; a rejected one means this record is demonstrably
    #    unreliable, which is a stronger statement and deserves more weight.
    #
    #    Without this, removing an impossible figure can flatter a product:
    #    a real ketchup record with 1000x its sodium scored 12 "Avoid" on the bad
    #    data and 58 "Good" once the sodium was dropped. Refusing to score it is
    #    the honest answer -- better no number than a reassuring wrong one.
    if any(name in result.dropped for name in CORE) and any(values.get(name) is not None for name in CORE):
        drop("core_value_rejected", "a core nutrient was impossible, so the whole panel is untrusted", *CORE)

    return result


def sanitise(n: Nutriments, *, is_drink: bool = False) -> tuple[Nutriments, Result]:
    """The panel with impossible values removed, plus what was removed and why."""
    result = check(n, is_drink=is_drink)
    if result.ok:
        return n, result
    return n.model_copy(update=dict.fromkeys(result.dropped, None)), result
