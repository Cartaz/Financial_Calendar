"""ForexFactory economic-calendar scraper via the Faireconomy JSON feed.

The internal source key remains ``ig`` for compatibility with existing
settings and UI bindings, but the data provenance is ForexFactory/Faireconomy.
Production refreshes never fall back to fabricated sample events.
"""

from __future__ import annotations

import logging

import requests

from config.constants import CalendarDefaults
from core.exceptions import ScraperConnectionError, ScraperParseError
from core.http_client import build_retry_session
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_ig_parser import parse_ig_date
from core.scraper_utils import clean_string, save_debug_json

logger = logging.getLogger(__name__)

_API_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
_SESSION = build_retry_session()

_HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
}

_IMPACT_MAP: dict[str, ImpactLevel] = {
    "High": ImpactLevel.HIGH,
    "Medium": ImpactLevel.MID,
    "Low": ImpactLevel.LOW,
}

_COUNTRY_MAP: dict[str, str] = {
    "USD": "USA", "EUR": "EUR", "JPY": "JPN", "GBP": "GBP",
    "CHF": "CHF", "CAD": "CAD", "AUD": "AUD", "NZD": "NZD",
    "CNY": "CNY", "KRW": "KRW", "SGD": "SGD", "HKD": "HKD",
    "TWD": "TWD", "MXN": "MXN", "BRL": "BRL", "ZAR": "ZAR",
    "SEK": "SEK", "NOK": "NOK", "DKK": "DKK", "PLN": "PLN",
    "CZK": "CZK", "HUF": "HUF", "TRY": "TRY", "RUB": "RUB",
    "THB": "THB", "MYR": "MYR", "IDR": "IDN", "PHP": "PHP",
    "INR": "INR", "ILS": "ILS", "SAR": "SAR", "AED": "AED",
}


def _parse_ff_events(data: list[dict]) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    skipped = 0

    for raw_index, item in enumerate(data):
        try:
            impact_raw = item.get("impact", "Low")
            impact_text = impact_raw if isinstance(impact_raw, str) else str(impact_raw or "Low")
            impact = _IMPACT_MAP.get(impact_text, ImpactLevel.LOW)

            date_text = clean_string(item.get("date", ""))
            time_str, date_display, utc_dt_str = parse_ig_date(date_text)

            country_code = clean_string(item.get("country", ""))
            region = _COUNTRY_MAP.get(country_code, country_code)

            title = clean_string(item.get("title", "")) or clean_string(item.get("name", ""))
            if not title:
                raise ScraperParseError("titolo evento mancante")

            events.append(
                CalendarEvent(
                    time=time_str,
                    country=region,
                    impact=impact,
                    event_name=title,
                    actual=clean_string(item.get("actual", "")),
                    forecast=clean_string(item.get("forecast", "")),
                    previous=clean_string(item.get("previous", "")),
                    date=date_display,
                    utc_dt=utc_dt_str,
                    source=CalendarSource.FOREXFACTORY,
                )
            )
        except Exception as exc:
            logger.warning("ForexFactory: evento raw %d ignorato: %s", raw_index, exc)
            skipped += 1

    if skipped:
        logger.info("ForexFactory: %d eventi scartati", skipped)
    return events


def scrape_ig_calendar(debug: bool = False) -> list[CalendarEvent]:
    """Fetch and validate the ForexFactory/Faireconomy weekly calendar."""
    try:
        response = _SESSION.get(
            _API_URL,
            headers=_HEADERS,
            timeout=CalendarDefaults.HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScraperConnectionError(
            "Impossibile raggiungere il feed ForexFactory/Faireconomy",
            details=str(exc),
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise ScraperParseError(
            "Risposta ForexFactory non JSON",
            details=str(exc),
        ) from exc

    if debug:
        save_debug_json(data, "ff_api_response")

    if not isinstance(data, list):
        raise ScraperParseError(
            "Formato ForexFactory inatteso",
            details=f"tipo={type(data).__name__}",
        )
    if not data:
        raise ScraperParseError("Il feed ForexFactory ha restituito zero eventi raw")

    events = _parse_ff_events(data)
    if not events:
        raise ScraperParseError(
            "Nessun evento ForexFactory valido dopo il parsing",
            details=f"raw={len(data)}",
        )

    logger.info("ForexFactory: %d eventi validi da %d raw", len(events), len(data))
    return events
