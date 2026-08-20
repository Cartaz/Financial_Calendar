"""Costanti globali dell'applicazione.

Contiene metadati dell'app, vincoli UI, valori predefiniti e percorsi
calcolati dinamicamente con pathlib. Nessun valore hardcoded.
"""

from __future__ import annotations

import os
from pathlib import Path


class AppMeta:
    """Metadati dell'applicazione."""

    NAME = "financial_calendar"
    DISPLAY_NAME = "Calendario Finanziario"
    VERSION = "1.0.0"
    AUTHOR = "User"
    DESCRIPTION = "Visualizzatore di calendari economici IG e FXStreet"
    ICON_NAME = "financial-calendar"


class UIConstraints:
    """Vincoli e dimensioni dell'interfaccia utente."""

    WINDOW_MIN_WIDTH = 1100
    WINDOW_MIN_HEIGHT = 700
    WINDOW_DEFAULT_WIDTH = 1300
    WINDOW_DEFAULT_HEIGHT = 800

    # Padding e margini (neumorphism vuole più respiro rispetto a Breeze)
    CARD_PADDING = 24
    CARD_MARGIN = 8
    CARD_BORDER_RADIUS = 24       # radius-lg delle linee guida
    BORDER_WIDTH = 1

    # Badge / chip
    SHORTCUT_BADGE_SPACING = 10
    SHORTCUT_BADGE_RADIUS = 8
    MAX_GRID_COLUMNS = 3

    # Indicatore di stato — leggermente più grande per essere visibile
    # anche sulle superfici neumorphic a basso contrasto
    INDICATOR_DIAMETER = 10

    # Pulsanti
    BUTTON_PADDING_H = 24         # più aria rispetto a 16 di Breeze
    BUTTON_PADDING_V = 12
    BUTTON_BORDER_RADIUS = 16     # radius-md delle linee guida
    ICON_BUTTON_SIZE = 44         # pulsanti icona tondi (neumorphism classico)

    # Campi di testo / combobox / dateedit
    FIELD_PADDING_H = 16
    FIELD_PADDING_V = 10
    FIELD_BORDER_RADIUS = 16      # uguale ai pulsanti per coerenza

    ANIMATION_DURATION_MIN = 120
    ANIMATION_DURATION_MAX = 240


class CalendarDefaults:
    """Valori predefiniti per i calendari."""

    IG_URL = "https://www.ig.com/uk/economic-calendar"
    FXSTREET_URL = "https://www.fxstreet.com/economic-calendar"
    IG_COLUMNS = ["Data", "Ora", "Paese", "Importanza", "Evento", "Attuale", "Previsione", "Precedente"]
    FXSTREET_COLUMNS = ["Data", "Ora", "Paese", "Evento", "Impatto", "Attuale", "Dev", "Consensus", "Precedente"]
    REFRESH_TIMEOUT = 30
    REGIONS = ["EUR", "USA", "JPN", "GBP", "CHF", "CAD", "AUD", "NZD", "CNY", "ALL"]
    IMPACT_LEVELS = ["HIGH", "MID", "LOW"]
    # Mostra solo gli eventi a partire da (now - PAST_EVENT_CUTOFF_HOURS).
    # eventi più vecchi vengono filtrati prima di popolare la tabella.
    PAST_EVENT_CUTOFF_HOURS = 24

    # Mappa codice regione (3 lettere, usato internamente) →
    # ISO 3166-1 alpha-2 (2 lettere, lowercase) per il nome del file
    # della bandiera SVG in assets/flags/.
    # EUR è mappato a "eu" (bandiera dell'Unione Europea), convenzione
    # standard nei calendari finanziari.
    FLAG_CODES: dict[str, str] = {
        "USA": "us", "EUR": "eu", "JPN": "jp", "GBP": "gb",
        "CHF": "ch", "CAD": "ca", "AUD": "au", "NZD": "nz",
        "CNY": "cn", "KRW": "kr", "SGD": "sg", "HKD": "hk",
        "TWD": "tw", "MXN": "mx", "BRL": "br", "ZAR": "za",
        "SEK": "se", "NOK": "no", "DKK": "dk", "PLN": "pl",
        "CZK": "cz", "HUF": "hu", "TRY": "tr", "RUB": "ru",
        "THB": "th", "MYR": "my", "IDN": "id", "PHP": "ph",
        "INR": "in", "ILS": "il", "SAR": "sa", "AED": "ae",
        # Regioni aggiuntive viste nelle risposte FXStreet
        "ARS": "ar", "CLP": "cl", "COP": "co", "EGP": "eg",
        "QAR": "qa", "RON": "ro",
    }


class PathConfig:
    """Percorsi calcolati dinamicamente conforme XDG Base Directory."""

    _xdg_config = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    _xdg_data = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    APP_CONFIG_DIR = _xdg_config / AppMeta.NAME
    SETTINGS_FILE = APP_CONFIG_DIR / "settings.json"
    APP_DATA_DIR = _xdg_data / AppMeta.NAME
    DESKTOP_FILE = Path.home() / ".local" / "share" / "applications" / f"{AppMeta.NAME}.desktop"
    # Directory delle bandiere SVG (assets/flags/) relativa al progetto.
    # Calcolata da constants.py che si trova in <project>/config/.
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    ASSETS_DIR = PROJECT_ROOT / "assets"
    FLAGS_DIR = ASSETS_DIR / "flags"

    @classmethod
    def ensure_dirs(cls) -> None:
        """Crea le directory necessarie se non esistono."""
        cls.APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
