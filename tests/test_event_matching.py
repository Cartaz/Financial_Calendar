from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.event_matching import build_duplicate_groups, event_identity, events_probably_duplicate
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.notification_policy import NotificationPolicy


def _event(
    source: CalendarSource,
    name: str,
    *,
    minutes: int = 5,
    country: str = "USA",
) -> CalendarEvent:
    event_dt = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country=country,
        impact=ImpactLevel.HIGH,
        event_name=name,
        actual="",
        forecast="120K",
        previous="110K",
        utc_dt=event_dt.isoformat(),
        source=source,
    )


def test_cross_source_duplicate_policy_is_canonical() -> None:
    left = _event(CalendarSource.FOREXFACTORY, "US Nonfarm Payrolls")
    right = _event(CalendarSource.FXSTREET, "Nonfarm Payrolls")
    unrelated = _event(CalendarSource.FXSTREET, "Core CPI")

    assert events_probably_duplicate(left, right)
    assert not events_probably_duplicate(left, unrelated)

    groups = build_duplicate_groups([left, right, unrelated])
    assert groups[event_identity(left)] == groups[event_identity(right)] == "D1"
    assert event_identity(unrelated) not in groups


def test_notification_policy_reuses_duplicate_policy_and_notifies_once() -> None:
    now = datetime.now(timezone.utc)
    left = _event(CalendarSource.FOREXFACTORY, "US Nonfarm Payrolls", minutes=4)
    right = _event(CalendarSource.FXSTREET, "Nonfarm Payrolls", minutes=4)
    policy = NotificationPolicy()

    first = policy.due_events([left, right], 5, now=now)
    second = policy.due_events([left, right], 5, now=now)

    assert len(first) == 1
    assert second == []
