"""Application query service for single-source and combined calendar views."""

from __future__ import annotations

from datetime import datetime, timezone

from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource
from core.time_utils import try_parse_utc


class CalendarQueryService:
    """Provide source-agnostic calendar queries behind one Python interface."""

    def __init__(self, controller: AppController) -> None:
        self._controller = controller

    def query(
        self,
        sources: tuple[CalendarSource, ...],
        *,
        region: str,
        impact: str,
        date: str,
        timezone_name: str,
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for source in sources:
            events.extend(
                self._controller.filter_events(
                    source,
                    region=region,
                    impact=impact,
                    date=date,
                    timezone_name=timezone_name,
                )
            )
        events.sort(
            key=lambda event: (
                try_parse_utc(event.utc_dt) or datetime.max.replace(tzinfo=timezone.utc)
            )
        )
        return events
