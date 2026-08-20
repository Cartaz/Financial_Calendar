"""Timezone-aware timestamp helpers shared by calendar scrapers."""

from __future__ import annotations

from datetime import datetime, timezone

from core.exceptions import ScraperParseError


def parse_aware_iso_datetime(value: object, field_name: str = "timestamp") -> datetime:
    """Parse an ISO-8601 value and require an explicit UTC offset."""
    if value is None:
        raise ScraperParseError(f"{field_name} mancante")
    text = str(value).strip()
    if not text:
        raise ScraperParseError(f"{field_name} vuoto")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ScraperParseError(f"{field_name} non valido: {text}") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ScraperParseError(
            f"{field_name} privo di timezone esplicita: {text}"
        )
    return parsed


def normalize_iso_to_utc(value: object, field_name: str = "timestamp") -> datetime:
    """Return an aware datetime normalized to UTC."""
    return parse_aware_iso_datetime(value, field_name).astimezone(timezone.utc)
