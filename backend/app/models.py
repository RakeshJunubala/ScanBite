"""Shared data models for products and scores.

All nutrient values are per 100 g (foods) or per 100 ml (drinks), the way
Indian packs print them under FSSAI labelling rules.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DataStatus(str, Enum):
    """Where a product record came from and how far to trust it."""

    verified = "verified"  # checked by our review team against label photos
    community = "community"  # imported from Open Food Facts, not yet checked
    provisional = "provisional"  # read from a user's photos, awaiting review
    sample = "sample"  # demo data bundled with the app, not a real product


class Nutriments(BaseModel):
    energy_kcal: float | None = None
    fat_g: float | None = None
    saturated_fat_g: float | None = None
    trans_fat_g: float | None = None
    sugars_g: float | None = None
    added_sugars_g: float | None = None
    sodium_mg: float | None = None
    fibre_g: float | None = None
    protein_g: float | None = None
    fruit_veg_nuts_pct: float | None = None


class Product(BaseModel):
    barcode: str
    name: str
    brand: str | None = None
    quantity: str | None = None
    category: str | None = None
    is_drink: bool = False
    nutriments: Nutriments = Field(default_factory=Nutriments)
    serving_size_g: float | None = None
    ingredients_text: str | None = None
    additives: list[str] = Field(default_factory=list)  # INS codes, e.g. "150d", "503(ii)"
    allergens: list[str] = Field(default_factory=list)  # e.g. "wheat", "milk"
    traces: list[str] = Field(default_factory=list)  # "may contain" list
    labels: list[str] = Field(default_factory=list)  # e.g. "vegetarian"
    image_url: str | None = None
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
    level: Level | None = None
    percent_daily: int | None = None
    per_serving: float | None = None


class AdditiveFact(BaseModel):
    code: str
    name: str
    function: str
    risk: Risk
    note: str | None = None
    known: bool = True
    animal: Literal["yes", "maybe", "no"] = "no"  # for vegetarian, vegan and Jain checks


class ProcessingFlag(BaseModel):
    key: str
    label: str
    penalty: float


class ScoreBreakdown(BaseModel):
    nutrition: float | None = None  # 0-100 before penalties
    additive_penalty: float = 0
    processing_penalty: float = 0
    caps_applied: list[str] = Field(default_factory=list)


class ScoreResult(BaseModel):
    score: int | None
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


class ProductSubmission(BaseModel):
    """A product someone read off a pack and sent us.

    Always stored as `provisional`, whatever `product.status` says: nothing that
    arrives over the wire has been checked by us, and `verified` means our review
    team compared it against label photos. Provenance is recorded separately from
    the product and never returned by the API.
    """

    product: Product
    submitted_by: str | None = Field(default=None, max_length=200)
    source: str | None = Field(default=None, max_length=200, description="e.g. 'pack label', 'brand website'")
    notes: str | None = Field(default=None, max_length=2000)
    label_photo_url: str | None = Field(default=None, max_length=1000)

    def to_product(self) -> Product:
        return self.product.model_copy(update={"status": DataStatus.provisional})
