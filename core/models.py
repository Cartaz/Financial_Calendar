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

    def to_ig_row(self) -> list[str]:
        """Compatibility row layout for the legacy ``ig``/ForexFactory tab."""
        impact_map = {
            ImpactLevel.HIGH: "ALTO",
            ImpactLevel.MID: "MEDIO",
            ImpactLevel.LOW: "BASSO",
        }
        return [
            self.date,
            self.time,
            self.country,
            impact_map.get(self.impact, "BASSO"),
            self.event_name,
            self.actual,
            self.forecast,
            self.previous,
        ]

    def to_forexfactory_row(self) -> list[str]:
        return self.to_ig_row()

    def to_fxstreet_row(self) -> list[str]:
        return [
            self.date,
            self.time,
            self.country,
            self.event_name,
            self.impact.value,
            self.actual,
            self.deviation,
            self.forecast,
            self.previous,
        ]
