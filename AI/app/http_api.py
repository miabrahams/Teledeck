from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from .container import ServiceContainer, get_container
from .models.tagger import TagPrediction as ModelTagPrediction
from .schemas import (
    HealthResponse,
    ScoreRequest,
    ScoreResponse,
    TagPrediction,
    TagRequest,
    TagResponse,
)
from .utils import ImageSourceError, load_image_from_bytes, load_image_from_source

LOGGER = logging.getLogger(__name__)


def create_http_app(container: ServiceContainer | None = None) -> FastAPI:
    app = FastAPI(title="Teledeck AI Service", version="1.0.0")

    if container is None:
        container = get_container()

    app.dependency_overrides[_get_container] = lambda: container

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.post("/v1/tags", response_model=TagResponse)
    async def tag_image(payload: TagRequest, container: ServiceContainer = Depends(_get_container)) -> TagResponse:
        if not payload.image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        try:
            image = load_image_from_source(payload.image_url, timeout=container.settings.request_timeout_seconds)
        except ImageSourceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        predictions = container.tagger.predict(image, cutoff=payload.cutoff)
        return _format_tag_response(predictions, cutoff=payload.cutoff, default_cutoff=container.settings.default_cutoff)

    @app.post("/v1/score", response_model=ScoreResponse)
    async def score_image(payload: ScoreRequest, container: ServiceContainer = Depends(_get_container)) -> ScoreResponse:
        if not payload.image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        try:
            image = load_image_from_source(payload.image_url, timeout=container.settings.request_timeout_seconds)
        except ImageSourceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        result = container.aesthetic.score(image)
        return ScoreResponse(score=result.score, backend=result.backend)

    @app.post("/predict/file", response_model=list[TagPrediction])
    async def legacy_predict_file(
        file: UploadFile = File(...),
        cutoff: float | None = None,
        container: ServiceContainer = Depends(_get_container),
    ) -> list[TagPrediction]:
        contents = await file.read()
        try:
            image = load_image_from_bytes(contents)
        except ImageSourceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        predictions = container.tagger.predict(image, cutoff=cutoff)
        return [TagPrediction(tag=item.tag, weight=item.weight) for item in predictions]

    @app.post("/predict/url", response_model=list[TagPrediction])
    async def legacy_predict_url(
        image_path: str,
        cutoff: float | None = None,
        container: ServiceContainer = Depends(_get_container),
    ) -> list[TagPrediction]:
        try:
            image = load_image_from_source(image_path, timeout=container.settings.request_timeout_seconds)
        except ImageSourceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        predictions = container.tagger.predict(image, cutoff=cutoff)
        return [TagPrediction(tag=item.tag, weight=item.weight) for item in predictions]

    return app


def _get_container() -> ServiceContainer:
    return get_container()


def _format_tag_response(
    predictions: list[ModelTagPrediction],
    *,
    cutoff: float | None,
    default_cutoff: float,
) -> TagResponse:
    active_cutoff = cutoff if cutoff is not None else default_cutoff
    payload = [TagPrediction(tag=item.tag, weight=item.weight) for item in predictions]
    return TagResponse(tags=payload, cutoff=active_cutoff)


__all__ = ["create_http_app"]
