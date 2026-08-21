"""Atomic persistent cache for the last valid calendar data."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.constants import PathConfig
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_metrics import ScrapeMetrics

logger = logging.getLogger(__name__)

_CACHE_VERSION = 1


@dataclass(frozen=True, slots=True)
class CacheSnapshot:
    """Validated cached events and the UTC refresh timestamp they belong to."""

    events: tuple[CalendarEvent, ...]
    refreshed_at: str


def _normalize_utc_timestamp(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("cache refresh timestamp missing")
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("cache refresh timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc).isoformat()


def _event_to_dict(event: CalendarEvent) -> dict[str, str]:
    return {
        "time": event.time,
        "country": event.country,
        "impact": event.impact.value,
        "event_name": event.event_name,
        "actual": event.actual,
        "forecast": event.forecast,
        "previous": event.previous,
        "date": event.date,
        "utc_dt": event.utc_dt,
        "deviation": event.deviation,
        "source": event.source.value,
    }


def _event_from_dict(value: object, expected_source: CalendarSource) -> CalendarEvent:
    if not isinstance(value, dict):
        raise TypeError("cached event must be an object")

    source = CalendarSource(str(value.get("source", expected_source.value)))
    if source.value != expected_source.value:
        raise ValueError("cached event source mismatch")

    event_name = str(value.get("event_name", "")).strip()
    if not event_name:
        raise ValueError("cached event name missing")

    return CalendarEvent(
        time=str(value.get("time", "")),
        country=str(value.get("country", "")),
        impact=ImpactLevel(str(value.get("impact", "LOW"))),
        event_name=event_name,
        actual=str(value.get("actual", "")),
        forecast=str(value.get("forecast", "")),
        previous=str(value.get("previous", "")),
        date=str(value.get("date", "")),
        utc_dt=str(value.get("utc_dt", "")),
        deviation=str(value.get("deviation", "")),
        source=source,
    )


class CalendarCache:
    """Persist one validated JSON snapshot per external calendar source."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    @staticmethod
    def _path(source: CalendarSource) -> Path:
        return PathConfig.APP_DATA_DIR / f"calendar_{source.value}.json"

    def load(self, source: CalendarSource) -> CacheSnapshot | None:
        path = self._path(source)
        with self._lock:
            if not path.exists():
                return None
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if not isinstance(payload, dict):
                    raise TypeError("cache root must be an object")
                if payload.get("version") != _CACHE_VERSION:
                    raise ValueError("unsupported cache version")
                if str(payload.get("source", "")) != source.value:
                    raise ValueError("cache source mismatch")

                raw_events = payload.get("events")
                if not isinstance(raw_events, list) or not raw_events:
                    raise ValueError("cache must contain events")

                refreshed_at = _normalize_utc_timestamp(payload.get("refreshed_at"))
                events = tuple(_event_from_dict(item, source) for item in raw_events)
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("Cache %s ignorata: %s", source.value, exc)
                return None

        logger.info(
            "Cache %s caricata: %d eventi, refresh %s",
            source.value,
            len(events),
            refreshed_at,
        )
        ScrapeMetrics(
            source=source.value,
            raw_count=len(events),
            valid_count=len(events),
            skipped_count=0,
            duration_ms=0,
            retries=0,
            origin="cache",
        ).log(logger)
        return CacheSnapshot(events=events, refreshed_at=refreshed_at)

    def save(
        self,
        source: CalendarSource,
        events: list[CalendarEvent],
        refreshed_at: str,
    ) -> bool:
        if not events:
            logger.warning("Cache %s non salvata: lista eventi vuota", source.value)
            return False

        try:
            normalized_timestamp = _normalize_utc_timestamp(refreshed_at)
        except (TypeError, ValueError) as exc:
            logger.error("Cache %s non salvata: %s", source.value, exc)
            return False

        payload = {
            "version": _CACHE_VERSION,
            "source": source.value,
            "refreshed_at": normalized_timestamp,
            "events": [_event_to_dict(event) for event in events],
        }

        temp_path: Path | None = None
        with self._lock:
            try:
                PathConfig.ensure_dirs()
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=PathConfig.APP_DATA_DIR,
                    prefix=f".calendar_{source.value}.",
                    suffix=".tmp",
                    delete=False,
                ) as handle:
                    temp_path = Path(handle.name)
                    json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
                    handle.flush()
                    os.fsync(handle.fileno())

                os.replace(temp_path, self._path(source))
            except OSError as exc:
                logger.error("Errore salvataggio cache %s: %s", source.value, exc)
                if temp_path is not None:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                return False

        logger.debug("Cache %s salvata con %d eventi", source.value, len(events))
        return True
