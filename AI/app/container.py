from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .models.aesthetic import AestheticScorer
from .models.tagger import TaggerModel
from .settings import Settings


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    tagger: TaggerModel
    aesthetic: AestheticScorer


@lru_cache(maxsize=1)
def get_container() -> ServiceContainer:
    settings = Settings()
    tagger = TaggerModel.from_settings(settings)
    aesthetic = AestheticScorer.from_settings(settings)
    return ServiceContainer(settings=settings, tagger=tagger, aesthetic=aesthetic)


__all__ = ["ServiceContainer", "get_container"]
