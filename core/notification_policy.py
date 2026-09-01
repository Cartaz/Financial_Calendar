"""Pure policy for selecting upcoming HIGH-impact desktop notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.event_matching import event_identity, events_probably_duplicate
from core.models import CalendarEvent, ImpactLevel
from core.time_utils import try_parse_utc


@dataclass(slots=True)
class NotificationPolicy:
    """Track already surfaced events and select new due HIGH notifications."""

    _notified_keys: set[tuple[str, str, str, str]] = field(default_factory=set)
    _notified_events: list[CalendarEvent] = field(default_factory=list)

    def due_events(
        self,
        events: list[CalendarEvent],
        lead_minutes: int,
        *,
        now: datetime | None = None,
    ) -> list[tuple[CalendarEvent, datetime, int]]:
        if lead_minutes <= 0:
            return []

        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            current = current.replace(tzinfo=timezone.utc)
        current = current.astimezone(timezone.utc)

        candidates: list[tuple[CalendarEvent, datetime]] = []
        for event in events:
            if event.impact != ImpactLevel.HIGH:
                continue
            event_dt = try_parse_utc(event.utc_dt)
            if event_dt is None:
                continue
            remaining = (event_dt - current).total_seconds()
            if 0 < remaining <= lead_minutes * 60:
                candidates.append((event, event_dt))

        candidates.sort(key=lambda item: item[1])
        due: list[tuple[CalendarEvent, datetime, int]] = []
        for event, event_dt in candidates:
            key = event_identity(event)
            if key in self._notified_keys:
                continue
            self._notified_keys.add(key)

            if any(events_probably_duplicate(event, previous) for previous in self._notified_events):
                continue

            self._notified_events.append(event)
            remaining_minutes = max(1, int((event_dt - current).total_seconds() // 60) + 1)
            due.append((event, event_dt, remaining_minutes))
        return due
