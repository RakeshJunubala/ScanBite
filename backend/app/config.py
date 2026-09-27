"""Settings read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "ScanBite"))
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "data/products.db"))
    seed_samples: bool = field(default_factory=lambda: _bool("SEED_SAMPLES", True))
    off_enabled: bool = field(default_factory=lambda: _bool("OFF_ENABLED", True))
    off_base_url: str = field(default_factory=lambda: os.getenv("OFF_BASE_URL", "https://world.openfoodfacts.org"))
    # Open Food Facts asks every app to identify itself: "AppName/Version (contact)".
    off_user_agent: str = field(
        default_factory=lambda: os.getenv("OFF_USER_AGENT", "ScanBite/0.1 (set OFF_USER_AGENT to your contact email)")
    )
    off_timeout_s: float = field(default_factory=lambda: float(os.getenv("OFF_TIMEOUT_S", "4")))
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip())
    )
    # Shared secret for POST /v1/products. Empty (the default) disables
    # submissions outright: an open write endpoint would let anyone replace real
    # product data, and provisional records outrank the Open Food Facts ones.
    admin_token: str = field(default_factory=lambda: os.getenv("ADMIN_TOKEN", ""))


def get_settings() -> Settings:
    return Settings()
