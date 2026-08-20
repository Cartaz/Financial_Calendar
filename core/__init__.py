"""Modulo core — logica di business dell'applicazione.

Contiene i modelli dati, l'event bus, le eccezioni personalizzate,
gli scraper, i dati di esempio e il controller principale.
Non importa mai da ui/.
"""

from core.event_bus import EventBus
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.exceptions import (
    AppError,
    ScraperError,
    ScraperConnectionError,
    ScraperParseError,
    ConfigError,
    ConfigValidationError,
)
from core.app_controller import AppController
from core.scraper_utils import save_debug_json, clean_string, format_value
from core.scraper_ig_parser import parse_ig_date
from core.sample_data import sample_ig_events, sample_fxstreet_events

__all__ = [
    "EventBus",
    "CalendarEvent",
    "CalendarSource",
    "ImpactLevel",
    "AppError",
    "ScraperError",
    "ScraperConnectionError",
    "ScraperParseError",
    "ConfigError",
    "ConfigValidationError",
    "AppController",
    "save_debug_json",
    "clean_string",
    "format_value",
    "parse_ig_date",
    "sample_ig_events",
    "sample_fxstreet_events",
]
