from __future__ import annotations

import builtins
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from config.constants import COLUMNS, PathConfig
from config.settings import Settings


def test_settings_atomic_round_trip(monkeypatch, tmp_path) -> None:
    settings = Settings()
    assert settings.set("timezone_name", "Europe/Rome")
    assert settings.set("selected_date", "2026-08-24")

    payload = json.loads(PathConfig.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert payload["timezone_name"] == "Europe/Rome"
    assert payload["selected_date"] == "2026-08-24"
    assert not list(PathConfig.APP_CONFIG_DIR.glob(".settings.*.tmp"))


def test_settings_concurrent_writers_keep_valid_json(monkeypatch, tmp_path) -> None:
    settings = Settings()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(settings.set, "ig_sort_key", "impact")
        second = executor.submit(settings.set, "fxstreet_sort_key", "date")
        assert first.result()
        assert second.result()

    payload = json.loads(PathConfig.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert payload["ig_sort_key"] == "impact"
    assert payload["fxstreet_sort_key"] == "date"


def test_invalid_schema_falls_back_to_safe_defaults(monkeypatch, tmp_path) -> None:
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

    assert settings.get("ig_column_order") == list(range(len(COLUMNS["ig"])))
    assert settings.get("fxstreet_selected_region") == "ALL"
    assert settings.get("auto_refresh_minutes") == 15
    assert settings.get("selected_date") == ""


def test_settings_load_permission_error_does_not_crash(monkeypatch, tmp_path) -> None:
    PathConfig.SETTINGS_FILE.write_text("{}", encoding="utf-8")
    real_open = builtins.open

    def denied(path, *args, **kwargs):
        if str(path) == str(PathConfig.SETTINGS_FILE):
            raise PermissionError("denied")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", denied)
    settings = Settings()
    settings.load()
    assert settings.get("timezone_name") == "local"


def test_column_order_validation(monkeypatch, tmp_path) -> None:
    settings = Settings()
    assert settings.set("ig_column_order", [0, 4, 1, 2, 3, 5, 6, 7])
    assert settings.get("ig_column_order") == [0, 4, 1, 2, 3, 5, 6, 7]


def test_ui_state_batch_round_trip(monkeypatch, tmp_path) -> None:
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
    settings = Settings()
    with pytest.raises(ValueError):
        settings.set("auto_refresh_minutes", 7)
    assert settings.get("auto_refresh_minutes") == 15
