from __future__ import annotations

from pathlib import Path

from admin.lib.config import Settings, create_export_location


def test_settings_loads_default_only(config_loader):
    config_loader(default={"app": {"http_port": 4100}})

    cfg = Settings()

    assert cfg.app.http_port == 4100
    assert cfg.PORT == 4100


def test_settings_local_override_takes_precedence(config_loader):
    config_loader(
        default={"app": {"http_port": 4100}},
        local={"app": {"http_port": 4200}},
    )

    cfg = Settings()

    assert cfg.app.http_port == 4200


def test_settings_env_override(config_loader, monkeypatch):
    config_loader(default={"app": {"http_port": 4100}})
    monkeypatch.setenv("APP__HTTP_PORT", "4300")

    cfg = Settings()

    assert cfg.app.http_port == 4300


def test_settings_legacy_override(config_loader, monkeypatch):
    config_loader(default={"app": {"http_port": 4100}})
    monkeypatch.setenv("PORT", "4400")

    cfg = Settings()

    assert cfg.app.http_port == 4400
    assert cfg.PORT == 4400


def test_settings_path_accessors_reflect_overrides(config_loader, tmp_path):
    default_paths = {
        "paths": {
            "db_path": str((tmp_path / "db.sqlite").resolve()),
            "media_root": str((tmp_path / "media").resolve()),
            "orphan_root": str((tmp_path / "orphans").resolve()),
        }
    }
    config_loader(default=default_paths)

    cfg = Settings()

    db_path = default_paths["paths"]["db_path"]
    media_root = default_paths["paths"]["media_root"]
    orphan_path = default_paths["paths"]["orphan_root"]

    assert cfg.DB_PATH == Path(db_path)
    assert cfg.MEDIA_PATH == Path(media_root)
    assert cfg.ORPHAN_PATH == Path(orphan_path)


def test_create_export_location_sets_up_media_tree(tmp_path):
    base_paths = {
        "db_path": str((tmp_path / "teledeck.db").resolve()),
        "media_root": str((tmp_path / "media").resolve()),
        "orphan_root": str((tmp_path / "orphans").resolve()),
        "export_root": str((tmp_path / "exports").resolve()),
    }
    cfg = Settings(paths=base_paths)

    overrides = create_export_location("channel42", None, cfg)

    export_base = Path(base_paths["export_root"]) / "channel42"
    media_dir = export_base / "media"
    db_path = export_base / "teledeck_export.db"

    assert export_base.is_dir()
    assert media_dir.is_dir()
    assert overrides.MEDIA_PATH == media_dir
    assert overrides.DB_PATH == db_path
