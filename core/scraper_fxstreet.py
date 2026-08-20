"""FXStreet economic-calendar scraper via the public calendar API."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests

from config.constants import CalendarDefaults
from core.exceptions import ScraperConnectionError, ScraperParseError
from core.http_client import build_retry_session
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_utils import clean_string, format_value, save_debug_json
from core.time_utils import normalize_iso_to_utc

logger = logging.getLogger(__name__)

_API_BASE = "https://calendar-api.fxsstatic.com"
_SESSION = build_retry_session()
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
    "HIGH": ImpactLevel.HIGH,
    "MEDIUM": ImpactLevel.MID,
    "LOW": ImpactLevel.LOW,
    "NONE": ImpactLevel.LOW,
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
    "AR": "ARS", "CL": "CLP", "CO": "COP", "EG": "EGP",
    "IL": "ILS", "QA": "QAR", "RO": "RON", "AE": "AED", "SA": "SAR",
}


def _parse_api_events(data: list[dict]) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []
    skipped = 0

    for raw_index, item in enumerate(data):
        try:
            volatility_raw = item.get("volatility", "LOW")
            volatility = (
                volatility_raw
                if isinstance(volatility_raw, str)
                else str(volatility_raw or "LOW")
            )
            impact = _VOLATILITY_MAP.get(volatility.upper(), ImpactLevel.LOW)

            dt_utc = normalize_iso_to_utc(item.get("dateUtc"), "FXStreet dateUtc")
            country_code = clean_string(item.get("countryCode", ""))
            region = _COUNTRY_MAP.get(country_code, country_code)

            event_name = clean_string(item.get("name", ""))
            if not event_name:
                raise ScraperParseError("nome evento mancante")

            unit = item.get("unit")
            previous = format_value(item.get("previous"), unit)
            revised = item.get("revised")
            if revised is not None:
                previous = format_value(revised, unit)

            events.append(
                CalendarEvent(
                    time=dt_utc.strftime("%H:%M"),
                    country=region,
                    impact=impact,
                    event_name=event_name,
                    actual=format_value(item.get("actual"), unit),
                    forecast=format_value(item.get("consensus"), unit),
                    previous=previous,
                    date=dt_utc.strftime("%d/%m/%Y"),
                    utc_dt=dt_utc.isoformat(),
                    deviation=format_value(item.get("ratioDeviation")),
                    source=CalendarSource.FXSTREET,
                )
            )
        except Exception as exc:
            logger.warning("FXStreet: evento raw %d ignorato: %s", raw_index, exc)
            skipped += 1

    if skipped:
        logger.info("FXStreet: %d eventi scartati", skipped)
    return events


def _extract_event_list(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("events", "data", "results", "items"):
            inner = payload.get(key)
            if isinstance(inner, list):
                return inner
    raise ScraperParseError(
        "Formato FXStreet inatteso",
        details=f"tipo={type(payload).__name__}",
    )


def scrape_fxstreet_calendar(debug: bool = False) -> list[CalendarEvent]:
    """Fetch and validate the next seven UTC calendar days from FXStreet."""
    today_utc = datetime.now(timezone.utc)
    from_date = today_utc.strftime("%Y-%m-%d")
    to_date = (today_utc + timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"{_API_BASE}/en/api/v1/eventDates/{from_date}/{to_date}"

    try:
        response = _SESSION.get(
            url,
            headers=_HEADERS,
            timeout=CalendarDefaults.HTTP_TIMEOUT,
            params={"volatilities": ["LOW", "MEDIUM", "HIGH"]},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScraperConnectionError(
            "Impossibile raggiungere l'API FXStreet",
            details=str(exc),
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise ScraperParseError(
            "Risposta FXStreet non JSON",
            details=str(exc),
        ) from exc

    if debug:
        save_debug_json(payload, "fxs_api_response")

    raw_events = _extract_event_list(payload)
    if not raw_events:
        raise ScraperParseError("FXStreet ha restituito zero eventi raw")

    events = _parse_api_events(raw_events)
    if not events:
        raise ScraperParseError(
            "Nessun evento FXStreet valido dopo il parsing",
            details=f"raw={len(raw_events)}",
        )

    logger.info("FXStreet: %d eventi validi da %d raw", len(events), len(raw_events))
    return events
