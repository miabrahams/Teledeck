from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch
from PIL import Image
from torchvision import transforms

from ..settings import Settings

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TagPrediction:
    tag: str
    weight: float


class TaggerModel:
    def __init__(
        self,
        model: torch.nn.Module,
        allowed_tags: list[str],
        device: torch.device,
        cutoff: float,
    ) -> None:
        self._model = model
        self._tags = allowed_tags
        self._device = device
        self._cutoff = cutoff
        self._transform = transforms.Compose(
            [
                transforms.Resize((448, 448)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.48145466, 0.4578275, 0.40821073],
                    std=[0.26862954, 0.26130258, 0.27577711],
                ),
            ]
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "TaggerModel":
        device = torch.device(settings.device)

        model_path = settings.tagger_model_path()
        if not model_path.exists():
            raise FileNotFoundError(f"Tagger model not found: {model_path}")

        LOGGER.info("Loading tagger model from %s", model_path)
        checkpoint = torch.load(model_path, map_location=device)
        if isinstance(checkpoint, torch.nn.Module):
            model = checkpoint
        else:
            raise ValueError("Unsupported model checkpoint format for tagger. Expected a serialized torch.nn.Module.")

        model.to(device)
        model.eval()

        tags = _load_tags(settings.tagger_tags_path(), settings.tagger_extra_tags_path())
        return cls(model=model, allowed_tags=tags, device=device, cutoff=settings.default_cutoff)

    def predict(self, image: Image.Image, cutoff: float | None = None) -> list[TagPrediction]:
        probability_cutoff = cutoff if cutoff is not None else self._cutoff

        tensor = self._transform(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            logits = self._model(tensor)

        probabilities = torch.sigmoid(logits[0])
        selected = torch.where(probabilities >= probability_cutoff)[0]

        results: list[TagPrediction] = []
        for index in selected:
            tag = self._tags[index]
            weight = float(probabilities[index].item())
            results.append(TagPrediction(tag=tag, weight=weight))

        results.sort(key=lambda item: item.weight, reverse=True)
        return results


def _load_tags(tags_path: Path, extra_path: Path) -> list[str]:
    with tags_path.open("r", encoding="utf-8") as fp:
        base_tags: list[str] = json.load(fp)

    allowed = sorted(base_tags)

    if extra_path.exists():
        with extra_path.open("r", encoding="utf-8") as fp:
            extra_tags: Iterable[list[str | int]] = json.load(fp)
        for position, tag in extra_tags:  # type: ignore[misc]
            if position == -1:
                allowed.append(tag)  # type: ignore[arg-type]
            else:
                allowed.insert(int(position), tag)  # type: ignore[arg-type]

    return allowed


__all__ = ["TaggerModel", "TagPrediction"]
