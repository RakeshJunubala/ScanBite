"""Shared data models for products and scores.

All nutrient values are per 100 g (foods) or per 100 ml (drinks), the way
Indian packs print them under FSSAI labelling rules.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DataStatus(str, Enum):
    """Where a product record came from and how far to trust it."""

    verified = "verified"  # checked by our review team against label photos
    community = "community"  # imported from Open Food Facts, not yet checked
    provisional = "provisional"  # read from a user's photos, awaiting review
    sample = "sample"  # demo data bundled with the app, not a real product


class Nutriments(BaseModel):
    energy_kcal: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    sugars_g: Optional[float] = None
    added_sugars_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    fibre_g: Optional[float] = None
    protein_g: Optional[float] = None
    fruit_veg_nuts_pct: Optional[float] = None


class Product(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    quantity: Optional[str] = None
    category: Optional[str] = None
    is_drink: bool = False
    nutriments: Nutriments = Field(default_factory=Nutriments)
    serving_size_g: Optional[float] = None
    ingredients_text: Optional[str] = None
    additives: list[str] = Field(default_factory=list)  # INS codes, e.g. "150d", "503(ii)"
    allergens: list[str] = Field(default_factory=list)  # e.g. "wheat", "milk"
    traces: list[str] = Field(default_factory=list)  # "may contain" list
    labels: list[str] = Field(default_factory=list)  # e.g. "vegetarian"
    image_url: Optional[str] = None
    status: DataStatus = DataStatus.community


class Verdict(str, Enum):
    great = "great"
    good = "good"
    limit = "limit"
    avoid = "avoid"
    unknown = "unknown"


Level = Literal["low", "medium", "high"]
Risk = Literal["none", "low", "moderate", "high", "unknown"]


class NutrientFact(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    kind: Literal["negative", "positive", "neutral"]
    level: Optional[Level] = None
    percent_daily: Optional[int] = None
    per_serving: Optional[float] = None


class AdditiveFact(BaseModel):
    code: str
    name: str
    function: str
    risk: Risk
    note: Optional[str] = None
    known: bool = True
    animal: Literal["yes", "maybe", "no"] = "no"  # for vegetarian, vegan and Jain checks


class ProcessingFlag(BaseModel):
    key: str
    label: str
    penalty: float


class ScoreBreakdown(BaseModel):
    nutrition: Optional[float] = None  # 0-100 before penalties
    additive_penalty: float = 0
    processing_penalty: float = 0
    caps_applied: list[str] = Field(default_factory=list)


class ScoreResult(BaseModel):
    score: Optional[int]
    verdict: Verdict
    reason: str
    nutrients: list[NutrientFact] = Field(default_factory=list)
    additives: list[AdditiveFact] = Field(default_factory=list)
    processing: list[ProcessingFlag] = Field(default_factory=list)
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    incomplete: bool = False
    missing: list[str] = Field(default_factory=list)
    method_version: str


class ProductResult(BaseModel):
    """What the app receives after a scan."""

    product: Product
    score: ScoreResult
