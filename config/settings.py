"""Thread-safe, atomically persisted user settings."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from pathlib import Path
from typing import Any

from config.constants import CalendarDefaults, PathConfig

logger = logging.getLogger(__name__)

_AUTO_REFRESH_MINUTES = {0, 5, 15, 30, 60}
_NOTIFICATION_LEAD_MINUTES = {0, 5, 15, 30, 60}
_IG_SORT_KEYS = {
    "",
    "date",
    "time",
    "country",
    "impact",
    "event_name",
    "actual",
    "forecast",
    "previous",
}
_FXSTREET_SORT_KEYS = {
    "",
    "date",
    "time",
    "country",
    "event_name",
    "impact",
    "actual",
    "deviation",
    "forecast",
    "previous",
}
_COMBINED_SORT_KEYS = {
    "",
    "date",
    "time",
    "country",
    "impact",
    "event_name",
    "source",
    "actual",
    "forecast",
    "previous",
}


@dataclass(slots=True)
class UserSettings:
    ig_column_order: list[int] = field(
        default_factory=lambda: list(range(len(CalendarDefaults.IG_COLUMNS)))
    )
    fxstreet_column_order: list[int] = field(
        default_factory=lambda: list(range(len(CalendarDefaults.FXSTREET_COLUMNS)))
    )
    combined_column_order: list[int] = field(default_factory=lambda: list(range(10)))

    ig_selected_region: str = "ALL"
    ig_selected_impact: str = "ALL"
    fxstreet_selected_region: str = "ALL"
    fxstreet_selected_impact: str = "ALL"
    combined_selected_region: str = "ALL"
    combined_selected_impact: str = "ALL"

    last_refresh_ig: str = ""
    last_refresh_fxstreet: str = ""

    active_source: str = "ig"
    timezone_name: str = "local"
    selected_date: str = ""
    auto_refresh_minutes: int = 15
    high_notification_minutes: int = 0
    ig_sort_key: str = ""
    ig_sort_direction: str = "asc"
    fxstreet_sort_key: str = ""
    fxstreet_sort_direction: str = "asc"
    combined_sort_key: str = ""
    combined_sort_direction: str = "asc"
    window_geometry: str = ""


_SETTINGS_FIELDS = {item.name for item in fields(UserSettings)}


def _valid_column_order(value: object, count: int) -> list[int]:
    if not isinstance(value, list):
        raise ValueError("column order must be a list")
    if any(not isinstance(item, int) for item in value):
        raise ValueError("column order must contain integers")
    if sorted(value) != list(range(count)):
        raise ValueError("column order must be a complete permutation")
    return list(value)


def _normalize_timezone(value: object) -> str:
    text = str(value).strip()
    if not text:
        return "local"
    if len(text) > 128 or any(ord(char) < 32 for char in text):
        raise ValueError("invalid timezone value")
    return text


def _normalize_selected_date(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("selected date must be YYYY-MM-DD") from exc
    return parsed.isoformat()


def _normalize_minutes(value: object, allowed: set[int], label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        minutes = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if minutes not in allowed:
        raise ValueError(f"unsupported {label} interval")
    return minutes


def _normalize_setting(key: str, value: Any) -> Any:
    if key == "ig_column_order":
        return _valid_column_order(value, len(CalendarDefaults.IG_COLUMNS))
    if key == "fxstreet_column_order":
        return _valid_column_order(value, len(CalendarDefaults.FXSTREET_COLUMNS))
    if key == "combined_column_order":
        return _valid_column_order(value, 10)

    if key.endswith("_selected_region"):
        text = str(value)
        allowed = set(CalendarDefaults.REGIONS)
        return text if text in allowed else "ALL"

    if key.endswith("_selected_impact"):
        text = str(value)
        allowed = {"ALL", *CalendarDefaults.IMPACT_LEVELS}
        return text if text in allowed else "ALL"

    if key in {"last_refresh_ig", "last_refresh_fxstreet"}:
        return str(value)

    if key == "active_source":
        text = str(value)
        return text if text in {"ig", "fxstreet", "combined"} else "ig"

    if key == "timezone_name":
        return _normalize_timezone(value)

    if key == "selected_date":
        return _normalize_selected_date(value)

    if key == "auto_refresh_minutes":
        return _normalize_minutes(value, _AUTO_REFRESH_MINUTES, "auto refresh")

    if key == "high_notification_minutes":
        return _normalize_minutes(value, _NOTIFICATION_LEAD_MINUTES, "notification lead")

    if key == "ig_sort_key":
        text = str(value)
        return text if text in _IG_SORT_KEYS else ""

    if key == "fxstreet_sort_key":
        text = str(value)
        return text if text in _FXSTREET_SORT_KEYS else ""

    if key == "combined_sort_key":
        text = str(value)
        return text if text in _COMBINED_SORT_KEYS else ""

    if key in {"ig_sort_direction", "fxstreet_sort_direction", "combined_sort_direction"}:
        text = str(value)
        return text if text in {"asc", "desc"} else "asc"

    if key == "window_geometry":
        text = str(value)
        if len(text) > 16384:
            raise ValueError("window geometry payload too large")
        return text

    raise AttributeError(f"Impostazione sconosciuta: {key}")


class Settings:
    """Settings manager with serialized access and atomic replacement."""

    def __init__(self) -> None:
        self._data = UserSettings()
        self._lock = threading.RLock()

    def load(self) -> None:
        with self._lock:
            try:
                if not PathConfig.SETTINGS_FILE.exists():
                    logger.info("Nessun file impostazioni trovato, uso valori predefiniti")
                    return

                with open(PathConfig.SETTINGS_FILE, "r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                if not isinstance(raw, dict):
                    raise TypeError("settings root must be an object")

                defaults = UserSettings()
                normalized: dict[str, Any] = {}
                for key in _SETTINGS_FIELDS:
                    raw_value = raw.get(key, getattr(defaults, key))
                    try:
                        normalized[key] = _normalize_setting(key, raw_value)
                    except (TypeError, ValueError):
                        logger.warning(
                            "Valore impostazione non valido per %s, uso default",
                            key,
                        )
                        normalized[key] = getattr(defaults, key)

                legacy_region = raw.get("selected_region")
                legacy_impact = raw.get("selected_impact")
                if legacy_region is not None:
                    for key in ("ig_selected_region", "fxstreet_selected_region"):
                        if key not in raw:
                            normalized[key] = _normalize_setting(key, legacy_region)
                if legacy_impact is not None:
                    for key in ("ig_selected_impact", "fxstreet_selected_impact"):
                        if key not in raw:
                            normalized[key] = _normalize_setting(key, legacy_impact)

                self._data = UserSettings(**normalized)
                logger.info("Impostazioni caricate da %s", PathConfig.SETTINGS_FILE)
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning(
                    "Impossibile caricare le impostazioni, uso default: %s",
                    exc,
                )
                self._data = UserSettings()

    def _save_locked(self) -> bool:
        temp_path: Path | None = None
        try:
            PathConfig.ensure_dirs()
            payload = asdict(self._data)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=PathConfig.APP_CONFIG_DIR,
                prefix=".settings.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_path, PathConfig.SETTINGS_FILE)
            logger.debug("Impostazioni salvate in %s", PathConfig.SETTINGS_FILE)
            return True
        except OSError as exc:
            logger.error("Errore nel salvataggio delle impostazioni: %s", exc)
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return False

    def save(self) -> bool:
        with self._lock:
            return self._save_locked()

    def get(self, key: str) -> Any:
        if key not in _SETTINGS_FIELDS:
            raise AttributeError(f"Impostazione sconosciuta: {key}")
        with self._lock:
            value = getattr(self._data, key)
            return list(value) if isinstance(value, list) else value

    def set(self, key: str, value: Any) -> bool:
        return self.set_many({key: value})

    def set_many(self, values: dict[str, Any]) -> bool:
        """Validate and persist several settings in one atomic file replacement."""
        if not values:
            return True
        unknown = set(values) - _SETTINGS_FIELDS
        if unknown:
            raise AttributeError(f"Impostazione sconosciuta: {sorted(unknown)[0]}")

        normalized = {key: _normalize_setting(key, value) for key, value in values.items()}
        changed: dict[str, tuple[Any, Any]] = {}
        with self._lock:
            for key, value in normalized.items():
                previous = getattr(self._data, key)
                if previous != value:
                    changed[key] = (previous, value)
                    setattr(self._data, key, value)

            if not changed:
                return True

            saved = self._save_locked()
            if not saved:
                for key, (previous, _) in changed.items():
                    setattr(self._data, key, previous)

        if saved:
            for key, (_, value) in changed.items():
                self._emit_config_changed(key, value)
        return saved

    def _emit_config_changed(self, key: str, value: Any) -> None:
        try:
            from core.event_bus import EventBus

            EventBus().emit("config_changed", {"key": key, "value": str(value)})
        except Exception as exc:
            logger.debug("Impossibile emettere config_changed: %s", exc)

    def reset(self) -> bool:
        with self._lock:
            previous = self._data
            self._data = UserSettings()
            saved = self._save_locked()
            if not saved:
                self._data = previous
            return saved
