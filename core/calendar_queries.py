"""Application query service for single-source and combined calendar views."""

from __future__ import annotations

from datetime import datetime, timezone

from core.app_controller import AppController
from core.event_matching import event_identity
from core.models import CalendarEvent, CalendarSource

EventIdentity = tuple[str, str, str, str]


class CalendarQueryService:
    """Provide source-agnostic calendar queries behind one Python interface."""

    def __init__(self, controller: AppController) -> None:
        self._controller = controller

    @staticmethod
    def _parse_utc(value: str) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc)

    def query(
        self,
        sources: tuple[CalendarSource, ...],
        *,
        region: str,
        impact: str,
        date: str,
        tz_offset_hours: float = 0.0,
        timezone_name: str = "",
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for source in sources:
            events.extend(
                self._controller.filter_events(
                    source,
                    region=region,
                    impact=impact,
                    date=date,
                    tz_offset_hours=tz_offset_hours,
                    timezone_name=timezone_name,
                )
            )
        events.sort(
            key=lambda event: self._parse_utc(event.utc_dt)
            or datetime.max.replace(tzinfo=timezone.utc)
        )
        return events

    def resolve_identities(
        self,
        sources: tuple[CalendarSource, ...],
        identities: set[EventIdentity],
        *,
        timezone_name: str,
    ) -> list[CalendarEvent]:
        """Resolve a UI selection against current canonical Python-owned events."""
        if not identities:
            return []
        events = self.query(
            sources,
            region="ALL",
            impact="ALL",
            date="",
            timezone_name=timezone_name,
        )
        return [event for event in events if event_identity(event) in identities]

    def combined_status(self) -> tuple[str, str, bool]:
        sources = (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET)
        timestamps = [self._controller.get_last_refresh(source) for source in sources]
        origins = [self._controller.get_data_origin(source) for source in sources]
        refreshing = any(self._controller.is_refreshing(source) for source in sources)

        parsed = [(value, self._parse_utc(value)) for value in timestamps if value]
        valid = [(value, parsed_dt) for value, parsed_dt in parsed if parsed_dt is not None]
        if valid:
            timestamp = min(valid, key=lambda item: item[1])[0]
        else:
            timestamp = next((value for value in timestamps if value), "")

        if not any(origin != "empty" for origin in origins):
            origin = "empty"
        elif any(origin == "cache" for origin in origins):
            origin = "cache"
        else:
            origin = "network"
        return timestamp, origin, refreshing
