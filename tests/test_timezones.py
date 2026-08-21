from __future__ import annotations

import pytest

from core.app_controller import AppController
from core.exceptions import ScraperParseError
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_ig_parser import parse_ig_date


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


def test_forexfactory_utc_converts_to_cest_offset() -> None:
    _, _, utc_text = parse_ig_date("2026-08-20T08:30:00-04:00")
    converted = AppController._convert_events_tz([_event(utc_text)], 2.0)
    assert converted[0].time == "14:30"
    assert converted[0].date == "20/08/2026"


def test_forexfactory_utc_converts_to_cet_offset() -> None:
    _, _, utc_text = parse_ig_date("2026-01-20T08:30:00-05:00")
    converted = AppController._convert_events_tz([_event(utc_text)], 1.0)
    assert converted[0].time == "14:30"
    assert converted[0].date == "20/01/2026"


def test_timezone_conversion_crosses_midnight() -> None:
    _, _, utc_text = parse_ig_date("2026-08-20T23:30:00-04:00")
    converted = AppController._convert_events_tz([_event(utc_text)], 2.0)
    assert converted[0].time == "05:30"
    assert converted[0].date == "21/08/2026"


def test_iana_timezone_applies_dst_for_each_event_date() -> None:
    before_dst = _event("2026-03-28T12:00:00+00:00")
    after_dst = _event("2026-03-30T12:00:00+00:00")

    converted = AppController._convert_events_timezone(
        [before_dst, after_dst],
        "Europe/Rome",
    )

    assert converted[0].time == "13:00"
    assert converted[0].date == "28/03/2026"
    assert converted[1].time == "14:00"
    assert converted[1].date == "30/03/2026"


def test_named_timezone_and_fixed_offset_can_coexist() -> None:
    event = _event("2026-08-20T12:30:00+00:00")

    rome = AppController._convert_events_timezone([event], "Europe/Rome")
    fixed = AppController._convert_events_timezone([event], "UTC+05:30")

    assert rome[0].time == "14:30"
    assert fixed[0].time == "18:00"


def test_naive_timestamp_is_rejected_at_ingest() -> None:
    with pytest.raises(ScraperParseError):
        parse_ig_date("2026-08-20T14:30:00")


def test_controller_defensively_handles_naive_timestamp() -> None:
    event = _event("2026-08-20T14:30:00")
    assert AppController._convert_events_tz([event], 2.0) == [event]
