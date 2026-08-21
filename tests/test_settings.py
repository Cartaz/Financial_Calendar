from __future__ import annotations

import builtins
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from config.constants import CalendarDefaults, PathConfig
from config.settings import Settings


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")


def test_settings_atomic_round_trip(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    assert settings.set("last_refresh_ig", "A")
    assert settings.set("last_refresh_fxstreet", "B")

    payload = json.loads(PathConfig.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert payload["last_refresh_ig"] == "A"
    assert payload["last_refresh_fxstreet"] == "B"
    assert not list(tmp_path.glob(".settings.*.tmp"))


def test_settings_concurrent_writers_keep_valid_json(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(settings.set, "last_refresh_ig", "IG")
        second = executor.submit(settings.set, "last_refresh_fxstreet", "FX")
        assert first.result()
        assert second.result()

    payload = json.loads(PathConfig.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert payload["last_refresh_ig"] == "IG"
    assert payload["last_refresh_fxstreet"] == "FX"


def test_invalid_schema_falls_back_to_safe_defaults(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    PathConfig.SETTINGS_FILE.write_text(
        json.dumps(
            {
                "ig_column_order": [999],
                "fxstreet_selected_region": "NOT_A_REGION",
                "auto_refresh_minutes": 7,
                "selected_date": "not-a-date",
                "unknown": "ignored",
            }
        ),
        encoding="utf-8",
    )

    settings = Settings()
    settings.load()

    assert settings.get("ig_column_order") == list(
        range(len(CalendarDefaults.IG_COLUMNS))
    )
    assert settings.get("fxstreet_selected_region") == "ALL"
    assert settings.get("auto_refresh_minutes") == 15
    assert settings.get("selected_date") == ""


def test_settings_load_permission_error_does_not_crash(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    PathConfig.SETTINGS_FILE.write_text("{}", encoding="utf-8")
    real_open = builtins.open

    def denied(path, *args, **kwargs):
        if str(path) == str(PathConfig.SETTINGS_FILE):
            raise PermissionError("denied")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", denied)
    settings = Settings()
    settings.load()
    assert settings.get("last_refresh_ig") == ""


def test_column_order_validation(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    assert settings.set("ig_column_order", [0, 4, 1, 2, 3, 5, 6, 7])
    assert settings.get("ig_column_order") == [0, 4, 1, 2, 3, 5, 6, 7]


def test_ui_state_batch_round_trip(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    assert settings.set_many(
        {
            "active_source": "fxstreet",
            "timezone_name": "Europe/Rome",
            "selected_date": "2026-08-24",
            "auto_refresh_minutes": 30,
            "ig_sort_key": "impact",
            "ig_sort_direction": "desc",
            "fxstreet_sort_key": "date",
            "fxstreet_sort_direction": "asc",
            "window_geometry": "geometry-data",
        }
    )

    restored = Settings()
    restored.load()
    assert restored.get("active_source") == "fxstreet"
    assert restored.get("timezone_name") == "Europe/Rome"
    assert restored.get("selected_date") == "2026-08-24"
    assert restored.get("auto_refresh_minutes") == 30
    assert restored.get("ig_sort_key") == "impact"
    assert restored.get("ig_sort_direction") == "desc"
    assert restored.get("fxstreet_sort_key") == "date"
    assert restored.get("window_geometry") == "geometry-data"


def test_ui_state_rejects_unsupported_auto_refresh(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    with pytest.raises(ValueError):
        settings.set("auto_refresh_minutes", 7)
    assert settings.get("auto_refresh_minutes") == 15
