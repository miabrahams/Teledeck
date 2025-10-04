from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, Optional

import pytest
import yaml
ADMIN_ROOT = Path(__file__).resolve().parents[1]
if str(ADMIN_ROOT) not in sys.path:
    sys.path.insert(0, str(ADMIN_ROOT))


@pytest.fixture
def config_loader(tmp_path, monkeypatch):
    """Prepare temporary config directory and helper to write default/local YAML."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setenv("TELEDECK_CONFIG_DIR", str(config_dir))
    monkeypatch.delenv("TELEDECK_CONFIG_FILE", raising=False)

    def _write_configs(*, default: Optional[Dict[str, Any]] = None, local: Optional[Dict[str, Any]] = None) -> Path:
        default_path = config_dir / "default.yaml"
        local_path = config_dir / "local.yaml"

        with default_path.open("w", encoding="utf-8") as default_file:
            yaml.safe_dump(default or {}, default_file)
        if local is not None:
            with local_path.open("w", encoding="utf-8") as local_file:
                yaml.safe_dump(local, local_file)
        elif local_path.exists():
            local_path.unlink()

        return config_dir

    return _write_configs


@pytest.fixture(autouse=True)
def reset_special_env(monkeypatch):
    """Ensure legacy config env vars don't leak between tests."""
    legacy_keys = [
        "APP__HTTP_PORT",
        "PORT",
        "TELEDECK_CONFIG_DIR",
        "TELEDECK_CONFIG_FILE",
    ]
    for key in legacy_keys:
        monkeypatch.delenv(key, raising=False)
