from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, confloat


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class TagRequest(BaseModel):
    image_url: Optional[str] = Field(default=None, description="HTTP(S) URL or absolute path to the image")
    cutoff: confloat(ge=0.0, le=1.0) | None = Field(default=None, description="Probability threshold for returning tags")


class TagPrediction(BaseModel):
    tag: str
    weight: float


class TagResponse(BaseModel):
    tags: list[TagPrediction]
    cutoff: float


class ScoreRequest(BaseModel):
    image_url: Optional[str] = None


class ScoreResponse(BaseModel):
    score: float
    backend: str


__all__ = [
    "HealthResponse",
    "TagRequest",
    "TagResponse",
    "TagPrediction",
    "ScoreRequest",
    "ScoreResponse",
]
