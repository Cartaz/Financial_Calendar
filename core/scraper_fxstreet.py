"""Scraper per il calendario economico FXStreet via API.

Recupera i dati dal calendario FXStreet usando l'API pubblica
calendar-api.fxsstatic.com. Fallback a dati di esempio se
l'API non è raggiungibile.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import requests

from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.sample_data import sample_fxstreet_events
from core.scraper_utils import format_value, save_debug_json
from config.constants import CalendarDefaults

logger = logging.getLogger(__name__)

_API_BASE = "https://calendar-api.fxsstatic.com"
_HEADERS = {
    "Accept": "application/json",
    "Referer": "https://www.fxstreet.com/",
    "Origin": "https://www.fxstreet.com",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_VOLATILITY_MAP: dict[str, ImpactLevel] = {
    "HIGH": ImpactLevel.HIGH, "MEDIUM": ImpactLevel.MID,
    "LOW": ImpactLevel.LOW, "NONE": ImpactLevel.LOW,
}

_COUNTRY_MAP: dict[str, str] = {
    "US": "USA", "EMU": "EUR", "UK": "GBP", "JP": "JPN",
    "CH": "CHF", "CA": "CAD", "AU": "AUD", "NZ": "NZD",
    "CN": "CNY", "DE": "EUR", "FR": "EUR", "IT": "EUR",
    "ES": "EUR", "NL": "EUR", "BE": "EUR", "AT": "EUR",
    "PT": "EUR", "IE": "EUR", "FI": "EUR", "GR": "EUR",
    "SK": "EUR", "SI": "EUR", "EE": "EUR", "LV": "EUR",
    "LT": "EUR", "LU": "EUR", "MT": "EUR", "CY": "EUR",
    "IN": "INR", "KR": "KRW", "SG": "SGD", "HK": "HKD",
    "TW": "TWD", "MX": "MXN", "BR": "BRL", "ZA": "ZAR",
    "SE": "SEK", "NO": "NOK", "DK": "DKK", "PL": "PLN",
    "CZ": "CZK", "HU": "HUF", "TR": "TRY", "RU": "RUB",
    "TH": "THB", "MY": "MYR", "ID": "IDN", "PH": "PHP",
    # Paesi aggiuntivi visti nelle risposte FXStreet
    "AR": "ARS", "CL": "CLP", "CO": "COP", "EG": "EGP",
    "IL": "ILS", "QA": "QAR", "RO": "RON",
    # FXStreet a volte restituisce codici ISO 2 lettere anche per
    # paesi che abbiamo mappato con codice valuta 3 lettere.
    # Aggiungiamo gli alias 2-letter → regione 3-letter.
    "AE": "AED", "SA": "SAR",
}


def _parse_api_events(data: list[dict]) -> list[CalendarEvent]:
    """Converte i dati JSON dell'API FXStreet in CalendarEvent.

    Args:
        data: Lista di dict dal JSON dell'API FXStreet.

    Returns:
        Lista di CalendarEvent.
    """
    events: list[CalendarEvent] = []
    skipped = 0

    for item in data:
        try:
            volatility_str = item.get("volatility", "LOW")
            if not isinstance(volatility_str, str):
                volatility_str = str(volatility_str) if volatility_str else "LOW"
            impact = _VOLATILITY_MAP.get(volatility_str.upper(), ImpactLevel.LOW)

            date_utc = item.get("dateUtc", "")
            time_str = ""
            date_display = ""
            utc_dt_str = ""
            if date_utc:
                try:
                    dt = datetime.fromisoformat(str(date_utc).replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M")
                    date_display = dt.strftime("%d/%m/%Y")
                    utc_dt_str = str(date_utc).replace("Z", "+00:00")
                except (ValueError, TypeError):
                    time_str = ""

            country_code = str(item.get("countryCode", ""))
            region = _COUNTRY_MAP.get(country_code, country_code)

            unit = item.get("unit")
            actual = format_value(item.get("actual"), unit)
            consensus = format_value(item.get("consensus"), unit)
            previous = format_value(item.get("previous"), unit)
            deviation = format_value(item.get("ratioDeviation"))

            revised = item.get("revised")
            if revised is not None:
                previous = format_value(revised, unit)

            event_name = str(item.get("name", ""))
            if not event_name or event_name == "None":
                skipped += 1
                continue

            events.append(CalendarEvent(
                time=time_str, country=region, impact=impact,
                event_name=event_name, actual=actual, forecast=consensus,
                previous=previous, date=date_display, utc_dt=utc_dt_str,
                deviation=deviation, source=CalendarSource.FXSTREET,
            ))
        except Exception as exc:
            logger.warning("Errore parsing FXStreet (idx %d): %s", len(events), exc)
            skipped += 1

    if skipped:
        logger.info("FXStreet: %d eventi saltati per dati mancanti", skipped)
    return events


def scrape_fxstreet_calendar() -> list[CalendarEvent]:
    """Scraping del calendario FXStreet tramite API pubblica.

    Returns:
        Lista di CalendarEvent dal calendario FXStreet.
    """
    today = datetime.now()
    from_date = today.strftime("%Y-%m-%d")
    to_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    url = f"{_API_BASE}/en/api/v1/eventDates/{from_date}/{to_date}"

    try:
        logger.info("FXStreet API: richiesta a %s", url)
        response = requests.get(
            url, headers=_HEADERS,
            timeout=CalendarDefaults.REFRESH_TIMEOUT,
            params={"volatilities": ["LOW", "MEDIUM", "HIGH"]},
        )
        logger.info("FXStreet API: status %d", response.status_code)
        response.raise_for_status()

        data = response.json()
        save_debug_json(data, "fxs_api_response")

        if isinstance(data, list) and len(data) > 0:
            events = _parse_api_events(data)
            logger.info("FXStreet API: recuperati %d eventi (da %d raw)", len(events), len(data))
            return events

        if isinstance(data, dict):
            logger.warning("FXStreet API: risposta dict con keys=%s", list(data.keys()))
            for key in ("events", "data", "results", "items"):
                inner = data.get(key)
                if isinstance(inner, list) and len(inner) > 0:
                    events = _parse_api_events(inner)
                    return events

        logger.warning("FXStreet API: risposta vuota o formato inatteso")
    except requests.RequestException as exc:
        logger.warning("FXStreet API: errore connessione, uso dati di esempio: %s", exc)
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning("FXStreet API: errore parsing, uso dati di esempio: %s", exc)

    return sample_fxstreet_events()
