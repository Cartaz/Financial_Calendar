"""Typed domain models for economic-calendar events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CalendarSource(Enum):
    """Economic-calendar data source.

    ``IG`` remains an alias for the historical internal key so existing
    persisted state and bridge bindings keep working.
    """

    FOREXFACTORY = "ig"
    IG = "ig"
    FXSTREET = "fxstreet"


class ImpactLevel(Enum):
    HIGH = "HIGH"
    MID = "MID"
    LOW = "LOW"


@dataclass(frozen=True)
class CalendarEvent:
    """One economic-calendar event.

    ``utc_dt`` is either an aware ISO-8601 UTC timestamp or an empty string.
    """

    time: str
    country: str
    impact: ImpactLevel
    event_name: str
    actual: str
    forecast: str
    previous: str
    date: str = ""
    utc_dt: str = ""
    deviation: str = ""
    source: CalendarSource = CalendarSource.FOREXFACTORY
