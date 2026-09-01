"""Timezone-aware timestamp helpers shared by the calendar core."""

from __future__ import annotations

from datetime import datetime, timezone

from core.exceptions import ScraperParseError


def try_parse_aware_iso(value: object) -> datetime | None:
    """Parse an ISO-8601 value when it is valid and timezone-aware."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def try_parse_utc(value: object) -> datetime | None:
    """Parse an aware ISO-8601 value and normalize it to UTC, or return None."""
    parsed = try_parse_aware_iso(value)
    return None if parsed is None else parsed.astimezone(timezone.utc)


def parse_aware_iso_datetime(value: object, field_name: str = "timestamp") -> datetime:
    """Parse an ISO-8601 value and require an explicit UTC offset."""
    if value is None:
        raise ScraperParseError(f"{field_name} mancante")
    text = str(value).strip()
    if not text:
        raise ScraperParseError(f"{field_name} vuoto")

    parsed = try_parse_aware_iso(text)
    if parsed is None:
        try:
            candidate = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ScraperParseError(f"{field_name} non valido: {text}") from exc
        if candidate.tzinfo is None or candidate.utcoffset() is None:
            raise ScraperParseError(
                f"{field_name} privo di timezone esplicita: {text}"
            )
        raise ScraperParseError(f"{field_name} non valido: {text}")
    return parsed


def normalize_iso_to_utc(value: object, field_name: str = "timestamp") -> datetime:
    """Return an aware datetime normalized to UTC."""
    return parse_aware_iso_datetime(value, field_name).astimezone(timezone.utc)
