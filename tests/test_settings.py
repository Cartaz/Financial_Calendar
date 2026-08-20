from __future__ import annotations

import builtins
import json
from concurrent.futures import ThreadPoolExecutor

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
