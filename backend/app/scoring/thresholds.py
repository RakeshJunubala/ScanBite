"""Reference numbers used by the scoring engine.

DRAFT v0.1 — every number here must be reviewed by a registered dietitian
before public release. See docs/scoring-method.md for the reasoning.

The nutrient point scales are continuous versions of the Nutri-Score 2023
point tables (Santé publique France), so a reviewer has a known reference.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Traffic-light levels (per 100 g / 100 ml) -------------------------------
# Source: UK Department of Health, "Guide to creating a front of pack (FoP)
# nutrition label for pre-packed products sold through retail outlets" (2016).
# low = at or below the first number, high = above the second number.
TRAFFIC_LIGHTS = {
    "food": {
        "fat_g": (3.0, 17.5),
        "saturated_fat_g": (1.5, 5.0),
        "sugars_g": (5.0, 22.5),
        "salt_g": (0.3, 1.5),
    },
    "drink": {
        "fat_g": (1.5, 8.75),
        "saturated_fat_g": (0.75, 2.5),
        "sugars_g": (2.5, 11.25),
        "salt_g": (0.3, 0.75),
    },
}

# --- Daily reference values for "% of daily limit" ---------------------------
# Based on a 2,000 kcal diet. VERIFY against the FSSAI (Labelling and Display)
# Regulations, 2020 reference values before release.
DAILY_REFERENCE = {
    "energy_kcal": 2000.0,
    "sugars_g": 50.0,
    "saturated_fat_g": 22.0,
    "sodium_mg": 2000.0,
    "fat_g": 67.0,
}

# --- Claim thresholds for positives -----------------------------------------
FIBRE_SOURCE_G = 3.0  # "source of fibre" per 100 g
FIBRE_HIGH_G = 6.0  # "high fibre" per 100 g
PROTEIN_SOURCE_ENERGY_SHARE = 0.12  # 12% of energy from protein
PROTEIN_HIGH_ENERGY_SHARE = 0.20  # 20% of energy from protein

TEASPOON_SUGAR_G = 4.0


@dataclass(frozen=True)
class Scale:
    """Linear points between `zero_at` (0 points) and `max_at` (`max_points`)."""

    zero_at: float
    max_at: float
    max_points: float

    def points(self, value: float) -> float:
        if value <= self.zero_at:
            return 0.0
        if value >= self.max_at:
            return self.max_points
        return (value - self.zero_at) / (self.max_at - self.zero_at) * self.max_points


# Negative nutrients: more is worse. Sodium is in mg (salt g = sodium mg * 2.5 / 1000).
NEGATIVE_SCALES = {
    "food": {
        "energy_kcal": Scale(80, 800, 10),
        "sugars_g": Scale(3.4, 51, 15),
        "saturated_fat_g": Scale(1, 10, 10),
        "sodium_mg": Scale(80, 1600, 20),  # salt 0.2 g -> 4 g
    },
    "drink": {
        "energy_kcal": Scale(7, 93, 10),
        "sugars_g": Scale(0.5, 11, 10),
        "saturated_fat_g": Scale(1, 10, 10),
        "sodium_mg": Scale(80, 1600, 20),
    },
}

# Positive nutrients: more is better.
POSITIVE_SCALES = {
    "fibre_g": Scale(1.9, 7.4, 5),
    "protein_g": Scale(1.2, 17, 7),
    "fruit_veg_nuts_pct": Scale(40, 80, 5),
}

# Protein only counts when negative points are below this (as in Nutri-Score),
# so protein can't rescue a product that is high in sugar, fat or salt.
PROTEIN_COUNTS_BELOW = {"food": 11.0, "drink": 7.0}

# Non-sugar sweeteners in a drink add negative points (Nutri-Score 2023: 4).
DRINK_SWEETENER_POINTS = 4.0

# Net points (negatives minus positives) -> nutrition part (0-100).
# Piecewise linear: 0 net points -> 100; `limit_edge` -> 25 (edge of Avoid);
# `zero_at` -> 0. Food edges follow Nutri-Score D/E (18); drinks D/E (10).
NUTRITION_MAP = {
    "food": {"limit_edge": 18.0, "zero_at": 40.0},
    "drink": {"limit_edge": 10.0, "zero_at": 25.0},
}

# --- Penalties (fractions of the nutrition part) and caps --------------------
ADDITIVE_PENALTY = {"none": 0.0, "low": 0.0, "moderate": 0.10, "high": 0.25, "unknown": 0.0}
MAX_ADDITIVE_PENALTY = 0.50

PROCESSING_PENALTY = {
    "refined_flour_first": 0.05,
    "added_sugar_top3": 0.05,
    "palm_oil": 0.03,
    "hydrogenated_fat": 0.08,
    "sweeteners": 0.05,
}
MAX_PROCESSING_PENALTY = 0.20

# A product with a high-risk additive, or a drink with added sugar or
# sweeteners, can score at most this (top of "Limit").
CAP_SCORE = 49

# --- Verdict bands ------------------------------------------------------------
VERDICT_BANDS = [(75, "great"), (50, "good"), (25, "limit"), (0, "avoid")]
