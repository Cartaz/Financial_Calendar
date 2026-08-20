from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from core.app_controller import AppController
from core.exceptions import ScraperParseError
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_ig_parser import parse_ig_date
from ui_qml.bridge import local_utc_offset_hours, nearest_timezone_index


def _event(utc_dt: str) -> CalendarEvent:
    return CalendarEvent(
        time="",
        date="",
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Test",
        actual="",
        forecast="",
        previous="",
        utc_dt=utc_dt,
        source=CalendarSource.FOREXFACTORY,
    )


def test_forexfactory_minus_0400_normalizes_to_utc() -> None:
    time_text, date_text, utc_text = parse_ig_date("2026-08-20T08:30:00-04:00")
    assert time_text == "12:30"
    assert date_text == "20/08/2026"
    assert utc_text == "2026-08-20T12:30:00+00:00"


def test_forexfactory_utc_converts_to_cest() -> None:
    _, _, utc_text = parse_ig_date("2026-08-20T08:30:00-04:00")
    converted = AppController._convert_events_tz([_event(utc_text)], 2.0)
    assert converted[0].time == "14:30"
    assert converted[0].date == "20/08/2026"


def test_timezone_conversion_crosses_midnight() -> None:
    _, _, utc_text = parse_ig_date("2026-08-20T23:30:00-04:00")
    converted = AppController._convert_events_tz([_event(utc_text)], 2.0)
    assert converted[0].time == "05:30"
    assert converted[0].date == "21/08/2026"


def test_naive_timestamp_is_rejected_at_ingest() -> None:
    with pytest.raises(ScraperParseError):
        parse_ig_date("2026-08-20T14:30:00")


def test_controller_defensively_handles_naive_timestamp() -> None:
    event = _event("2026-08-20T14:30:00")
    assert AppController._convert_events_tz([event], 2.0) == [event]


def test_rome_dst_offset_summer_and_winter() -> None:
    rome = ZoneInfo("Europe/Rome")
    summer = datetime(2026, 8, 20, 12, 0, tzinfo=rome)
    winter = datetime(2026, 1, 20, 12, 0, tzinfo=rome)
    assert local_utc_offset_hours(summer) == 2.0
    assert local_utc_offset_hours(winter) == 1.0
    assert nearest_timezone_index(2.0) != nearest_timezone_index(1.0)
