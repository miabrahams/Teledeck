from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

LOGGER = logging.getLogger(__name__)


class ImageSourceError(RuntimeError):
    pass


def load_image_from_source(source: str, *, timeout: int = 15) -> Image.Image:
    if source.startswith("http://") or source.startswith("https://"):
        LOGGER.debug("Fetching image from %s", source)
        response = requests.get(source, timeout=timeout)
        if response.status_code >= 400:
            raise ImageSourceError(f"Failed to fetch image: HTTP {response.status_code}")
        return _open_image(response.content)

    path = Path(source)
    if not path.exists():
        raise ImageSourceError(f"Image path does not exist: {source}")
    if path.is_dir():
        raise ImageSourceError(f"Expected file but found directory: {source}")
    return Image.open(path).convert("RGB")


def load_image_from_bytes(data: bytes) -> Image.Image:
    return _open_image(data)


def _open_image(data: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        raise ImageSourceError("Failed to decode image") from exc


__all__ = ["load_image_from_source", "load_image_from_bytes", "ImageSourceError"]
