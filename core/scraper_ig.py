"""Scraper per il calendario economico IG tramite ForexFactory JSON.

Recupera i dati dal calendario economico usando l'endpoint JSON pubblico
di Faireconomy Media (fonte dati ForexFactory). Questo endpoint fornisce
gli stessi eventi economici che IG mostra nel suo calendario, senza
richiedere autenticazione.

Fallback a dati di esempio se l'API non è raggiungibile.
"""

from __future__ import annotations

import logging

import requests

from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.sample_data import sample_ig_events
from core.scraper_ig_parser import parse_ig_date
from core.scraper_utils import clean_string, save_debug_json
from config.constants import CalendarDefaults

logger = logging.getLogger(__name__)

_API_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

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
    """Converte i dati JSON di ForexFactory in CalendarEvent.

    Args:
        data: Lista di dict dal JSON di ForexFactory.

    Returns:
        Lista di CalendarEvent.
    """
    events: list[CalendarEvent] = []
    skipped = 0

    for item in data:
        try:
            impact_str = item.get("impact", "Low")
            if not isinstance(impact_str, str):
                impact_str = str(impact_str) if impact_str else "Low"
            impact = _IMPACT_MAP.get(impact_str, ImpactLevel.LOW)

            date_str = clean_string(item.get("date", ""))
            time_str, date_display, utc_dt_str = parse_ig_date(date_str)

            country_code = clean_string(item.get("country", ""))
            region = _COUNTRY_MAP.get(country_code, country_code)

            title = (
                clean_string(item.get("title", ""))
                or clean_string(item.get("name", ""))
            )
            if not title:
                skipped += 1
                continue

            actual = clean_string(item.get("actual", ""))
            forecast = clean_string(item.get("forecast", ""))
            previous = clean_string(item.get("previous", ""))

            events.append(CalendarEvent(
                time=time_str, country=region, impact=impact,
                event_name=title, actual=actual, forecast=forecast,
                previous=previous, date=date_display, utc_dt=utc_dt_str,
                source=CalendarSource.IG,
            ))
        except Exception as exc:
            logger.warning("Errore parsing FF (idx %d): %s", len(events), exc)
            skipped += 1

    if skipped:
        logger.info("FF: %d eventi saltati per dati mancanti", skipped)
    return events


def scrape_ig_calendar() -> list[CalendarEvent]:
    """Scraping del calendario economico tramite ForexFactory JSON.

    Usa l'endpoint pubblico nfs.faireconomy.media che fornisce
    gli eventi della settimana corrente senza autenticazione.
    Se non raggiungibile, restituisce dati di esempio.

    Returns:
        Lista di CalendarEvent dal calendario.
    """
    try:
        logger.info("FF API: richiesta a %s", _API_URL)
        response = requests.get(
            _API_URL, headers=_HEADERS,
            timeout=CalendarDefaults.REFRESH_TIMEOUT,
        )
        logger.info("FF API: status %d", response.status_code)
        response.raise_for_status()

        data = response.json()
        save_debug_json(data, "ff_api_response")

        if isinstance(data, list) and len(data) > 0:
            events = _parse_ff_events(data)
            logger.info("FF API: recuperati %d eventi (da %d raw)", len(events), len(data))
            return events

        logger.warning("FF API: risposta vuota o formato inatteso")
    except requests.RequestException as exc:
        logger.warning("FF API: errore connessione, uso dati di esempio: %s", exc)
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning("FF API: errore parsing, uso dati di esempio: %s", exc)

    return sample_ig_events()
