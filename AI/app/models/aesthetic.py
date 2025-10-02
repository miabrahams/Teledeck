from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor, pipeline

from ..settings import Settings

LOGGER = logging.getLogger(__name__)


class _MLP(torch.nn.Module):
    def __init__(self, input_size: int = 768) -> None:
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(input_size, 1024),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(1024, 128),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(128, 64),
            torch.nn.Dropout(0.1),
            torch.nn.Linear(64, 16),
            torch.nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        return self.layers(x)


def _normalize(array: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(array, axis=-1, keepdims=True)
    norms[norms == 0] = 1
    return array / norms


@dataclass(slots=True)
class AestheticScore:
    score: float
    backend: Literal["pipeline", "mlp"]


class AestheticScorer:
    def __init__(self, backend: Literal["pipeline", "mlp"], device: torch.device, *, pipeline_dir: Path | None, checkpoint_path: Path | None) -> None:
        self._backend = backend
        self._device = device
        if backend == "pipeline":
            if pipeline_dir is None:
                raise ValueError("pipeline_dir is required when backend='pipeline'")
            LOGGER.info("Loading aesthetic pipeline from %s", pipeline_dir)
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            # Device parameter for transformers pipeline: int device index or cpu
            hf_device = 0 if device.type == "cuda" else -1
            self._pipeline = pipeline("image-classification", model=str(pipeline_dir), device=hf_device)
            self._mlp = None
            self._clip_model = None
            self._clip_processor = None
        else:
            if checkpoint_path is None or not checkpoint_path.exists():
                raise FileNotFoundError("Aesthetic checkpoint not found.")
            LOGGER.info("Loading aesthetic MLP checkpoint from %s", checkpoint_path)
            mlp = _MLP()
            state = torch.load(checkpoint_path, map_location=device)
            mlp.load_state_dict(state)
            mlp.to(device)
            mlp.eval()

            clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
            clip_model.to(device)
            clip_model.eval()
            clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

            self._pipeline = None
            self._mlp = mlp
            self._clip_model = clip_model
            self._clip_processor = clip_processor

    @classmethod
    def from_settings(cls, settings: Settings) -> "AestheticScorer":
        device = torch.device(settings.device)
        pipeline_dir = settings.aesthetic_pipeline_path()
        if pipeline_dir.exists():
            backend: Literal["pipeline", "mlp"] = "pipeline"
            checkpoint = None
        else:
            backend = "mlp"
            pipeline_dir = None
            checkpoint = settings.aesthetic_checkpoint_path()

        return cls(backend=backend, device=device, pipeline_dir=pipeline_dir, checkpoint_path=checkpoint)

    def score(self, image: Image.Image) -> AestheticScore:
        if self._backend == "pipeline":
            assert self._pipeline is not None
            outputs = self._pipeline(images=[image])
            result = outputs[0]
            if isinstance(result, list):
                hq = next((item for item in result if item["label"].lower() in {"hq", "high quality"}), result[0])
                score = float(hq["score"])
            else:
                score = float(result["score"])
            return AestheticScore(score=score, backend="pipeline")

        assert self._mlp is not None and self._clip_model is not None and self._clip_processor is not None
        processed = self._clip_processor(images=image, return_tensors="pt")
        pixel_values = processed.to(self._device)
        with torch.no_grad():
            features = self._clip_model.get_image_features(**pixel_values)
            embeddings = _normalize(features.cpu().numpy())
            tensor = torch.from_numpy(embeddings).to(self._device)
            prediction = self._mlp(tensor).cpu().numpy()[0][0]
        return AestheticScore(score=float(prediction), backend="mlp")


__all__ = ["AestheticScorer", "AestheticScore"]
