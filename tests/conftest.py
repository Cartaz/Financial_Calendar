"""Shared test setup: every test runs against its own temporary XDG paths."""

import pytest

from config.constants import PathConfig


@pytest.fixture(autouse=True)
def isolated_paths(monkeypatch, tmp_path):
    """Redirect settings, cache and debug files so tests never touch real data."""
    config_dir = tmp_path / "config"
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", config_dir)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", config_dir / "settings.json")
    PathConfig.ensure_dirs()
    return tmp_path
