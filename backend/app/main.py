"""HTTP API. Run locally: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Interactive docs: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .models import AdditiveFact, Product, ProductResult, ScoreResult
from .repository import ProductRepository
from .scoring import METHOD_VERSION, score_product
from .scoring.additives import describe, normalize_code
from .seed import seed
from .service import ProductService, is_valid_barcode, normalize_barcode
from .sources.off import OpenFoodFactsClient, SourceUnavailable

logger = logging.getLogger(__name__)


def build_service(settings: Settings, source=None) -> ProductService:
    repo = ProductRepository(settings.database_path)
    if settings.seed_samples:
        seed(repo)
    if source is None and settings.off_enabled:
        source = OpenFoodFactsClient(settings.off_base_url, settings.off_user_agent, settings.off_timeout_s)
    return ProductService(repo, source)


def create_app(settings: Optional[Settings] = None, service: Optional[ProductService] = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = service or build_service(settings)
        yield

    app = FastAPI(title=f"{settings.app_name} API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def svc() -> ProductService:
        return app.state.service

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "method_version": METHOD_VERSION, "products": svc().repo.count()}

    def checked(barcode: str) -> str:
        code = normalize_barcode(barcode)
        if not is_valid_barcode(code):
            raise HTTPException(status_code=400, detail="invalid_barcode")
        return code

    def looked_up(code: str) -> Optional[ProductResult]:
        """lookup(), turning an unreachable source into 503 rather than 404.

        The reason is logged here and not returned: the person only needs to
        know we couldn't check, while we need to know which source failed and why.
        """
        try:
            return svc().lookup(code)
        except SourceUnavailable as err:
            logger.warning("Product source unavailable for %s: %s", code, err)
            raise HTTPException(status_code=503, detail="source_unavailable") from err

    @app.get("/v1/products/{barcode}", response_model=ProductResult)
    def get_product(barcode: str) -> ProductResult:
        result = looked_up(checked(barcode))
        if result is None:
            raise HTTPException(status_code=404, detail="not_found")
        return result

    @app.get("/v1/products/{barcode}/alternatives", response_model=list[ProductResult])
    def get_alternatives(barcode: str, limit: int = Query(3, ge=1, le=10)) -> list[ProductResult]:
        code = checked(barcode)
        # alternatives() looks the product up first, so it can hit the source too.
        # In practice the product is already cached by the time the app asks.
        try:
            return svc().alternatives(code, limit)
        except SourceUnavailable as err:
            logger.warning("Product source unavailable for %s: %s", code, err)
            raise HTTPException(status_code=503, detail="source_unavailable") from err

    @app.get("/v1/search", response_model=list[ProductResult])
    def search(q: str = Query(..., min_length=2, max_length=80), limit: int = Query(20, ge=1, le=50)):
        return svc().search(q, limit)

    @app.post("/v1/score", response_model=ScoreResult)
    def score(product: Product) -> ScoreResult:
        return score_product(product)

    @app.get("/v1/additives/{code}", response_model=AdditiveFact)
    def additive(code: str) -> AdditiveFact:
        normalized = normalize_code(code)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_code")
        return describe(normalized)

    return app


app = create_app()
