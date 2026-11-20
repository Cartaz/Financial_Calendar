"""Global application metadata, data-source constants and XDG paths."""

from __future__ import annotations

import os
from pathlib import Path


class AppMeta:
    NAME = "financial_calendar"
    DISPLAY_NAME = "Calendario Finanziario"
    VERSION = "1.1.0"
    ICON_NAME = "financial-calendar"


# Source keys shown by the UI; "combined" merges both feeds.
SOURCES = {"forexfactory": "ForexFactory", "fxstreet": "FXStreet", "combined": "Tutti"}

# Canonical column keys per source, in default display order.
COLUMNS: dict[str, tuple[str, ...]] = {
    "forexfactory": (
        "date",
        "time",
        "country",
        "impact",
        "event_name",
        "actual",
        "forecast",
        "previous",
    ),
    "fxstreet": (
        "date",
        "time",
        "country",
        "event_name",
        "impact",
        "actual",
        "deviation",
        "forecast",
        "previous",
    ),
    "combined": (
        "date",
        "time",
        "country",
        "impact",
        "event_name",
        "source",
        "actual",
        "forecast",
        "previous",
        "deviation",
    ),
}

COLUMN_LABELS = {
    "date": "Data",
    "time": "Ora",
    "country": "Paese",
    "impact": "Impatto",
    "event_name": "Evento",
    "source": "Sorgente",
    "actual": "Attuale",
    "forecast": "Previsione",
    "previous": "Precedente",
    "deviation": "Dev",
}


class CalendarDefaults:
    # requests supports a (connect_timeout, read_timeout) tuple.
    HTTP_TIMEOUT = (5, 15)

    REGIONS = ["ALL", "EUR", "USA", "JPN", "GBP", "CHF", "CAD", "AUD", "NZD", "CNY"]
    IMPACT_LEVELS = ["HIGH", "MID", "LOW"]
    PAST_EVENT_CUTOFF_HOURS = 24

    FLAG_CODES: dict[str, str] = {
        "USA": "us",
        "EUR": "eu",
        "JPN": "jp",
        "GBP": "gb",
        "CHF": "ch",
        "CAD": "ca",
        "AUD": "au",
        "NZD": "nz",
        "CNY": "cn",
        "KRW": "kr",
        "SGD": "sg",
        "HKD": "hk",
        "TWD": "tw",
        "MXN": "mx",
        "BRL": "br",
        "ZAR": "za",
        "SEK": "se",
        "NOK": "no",
        "DKK": "dk",
        "PLN": "pl",
        "CZK": "cz",
        "HUF": "hu",
        "TRY": "tr",
        "RUB": "ru",
        "THB": "th",
        "MYR": "my",
        "IDN": "id",
        "PHP": "ph",
        "INR": "in",
        "ILS": "il",
        "SAR": "sa",
        "AED": "ae",
        "ARS": "ar",
        "CLP": "cl",
        "COP": "co",
        "EGP": "eg",
        "QAR": "qa",
        "RON": "ro",
    }


class PathConfig:
    """Paths following the XDG Base Directory specification."""

    _xdg_config = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    _xdg_data = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    APP_CONFIG_DIR = _xdg_config / AppMeta.NAME
    SETTINGS_FILE = APP_CONFIG_DIR / "settings.json"
    APP_DATA_DIR = _xdg_data / AppMeta.NAME

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    ASSETS_DIR = PROJECT_ROOT / "assets"
    FLAGS_DIR = ASSETS_DIR / "flags"

    @classmethod
    def ensure_dirs(cls) -> None:
        cls.APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
