from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (Path.cwd() / candidate).resolve()


def _resolve_device(value: str | None) -> str:
    if not value or value.lower() in {"auto", ""}:
        return "cuda" if _cuda_available() else "cpu"
    normalized = value.lower()
    if normalized not in {"cuda", "cpu"}:
        raise ValueError("DEVICE must be 'cuda', 'cpu', or 'auto'.")
    if normalized == "cuda" and not _cuda_available():
        raise RuntimeError("CUDA requested but not available in this runtime.")
    return normalized


def _cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


@dataclass(slots=True)
class Settings:
    http_host: str = field(default_factory=lambda: os.getenv("HTTP_HOST", "0.0.0.0"))
    http_port: int = field(default_factory=lambda: int(os.getenv("HTTP_PORT", "8080")))
    grpc_port: int = field(default_factory=lambda: int(os.getenv("GRPC_PORT", "9090")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))
    max_workers: int = field(default_factory=lambda: int(os.getenv("MAX_WORKERS", "4")))
    enable_http: bool = field(default_factory=lambda: os.getenv("ENABLE_HTTP", "1") != "0")
    enable_grpc: bool = field(default_factory=lambda: os.getenv("ENABLE_GRPC", "1") != "0")

    device: str = field(default_factory=lambda: _resolve_device(os.getenv("DEVICE", "auto")))

    model_root: Path = field(
        default_factory=lambda: _resolve_path(os.getenv("MODEL_ROOT"), Path(__file__).resolve().parent.parent / "models")
    )
    tagger_model_file: str = field(default_factory=lambda: os.getenv("TAGGER_MODEL_FILE", "model.pth"))
    tagger_base_tags: str = field(default_factory=lambda: os.getenv("TAGGER_BASE_TAGS", "tags_8041.json"))
    tagger_extra_tags: str = field(default_factory=lambda: os.getenv("TAGGER_EXTRA_TAGS", "tags_extra.json"))
    default_cutoff: float = field(default_factory=lambda: float(os.getenv("TAGGER_DEFAULT_CUTOFF", "0.35")))

    aesthetic_model_repo: str = field(
        default_factory=lambda: os.getenv("AESTHETIC_MODEL_REPO", "ramonvc/aesthetic-sharpness-v2")
    )
    aesthetic_checkpoint: str = field(
        default_factory=lambda: os.getenv("AESTHETIC_CHECKPOINT", "sac+logos+ava1-l14-linearMSE.pth")
    )
    aesthetic_pipeline_dir: Path = field(
        default_factory=lambda: _resolve_path(os.getenv("AESTHETIC_PIPELINE_DIR"), Path(__file__).resolve().parent.parent / "models" / "aesthetic-shadow-v2")
    )

    request_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")))

    def tagger_model_path(self) -> Path:
        return (self.model_root / self.tagger_model_file).resolve()

    def tagger_tags_path(self) -> Path:
        return (self.model_root / self.tagger_base_tags).resolve()

    def tagger_extra_tags_path(self) -> Path:
        return (self.model_root / self.tagger_extra_tags).resolve()

    def aesthetic_checkpoint_path(self) -> Path:
        return (self.model_root / self.aesthetic_checkpoint).resolve()

    def aesthetic_pipeline_path(self) -> Path:
        return self.aesthetic_pipeline_dir


__all__ = ["Settings"]
