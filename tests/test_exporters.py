from __future__ import annotations

from datetime import datetime, timezone

from core.exporters import render_csv, render_ics, write_export


def _event() -> dict[str, str]:
    return {
        "source": "ig",
        "date": "21/08/2026",
        "time": "14:30",
        "country": "USA",
        "impact": "HIGH",
        "event_name": "Payrolls, Employment; Report",
        "actual": "",
        "forecast": "120K",
        "previous": "110K",
        "deviation": "",
        "utc_dt": "2026-08-21T12:30:00+00:00",
        "duplicate_group": "D1",
    }


def test_csv_export_quotes_values_and_keeps_operational_metadata() -> None:
    content = render_csv([_event()])

    assert content.startswith("source,date,time,country,impact,event_name")
    assert '"Payrolls, Employment; Report"' in content
    assert ",D1\n" in content
    assert "2026-08-21T12:30:00+00:00" in content


def test_ics_export_has_stable_event_fields_and_escapes_text() -> None:
    generated = datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc)
    content = render_ics([_event()], generated_at=generated)

    assert "BEGIN:VCALENDAR\r\n" in content
    assert "BEGIN:VEVENT\r\n" in content
    assert "DTSTAMP:20260821T100000Z\r\n" in content
    assert "DTSTART:20260821T123000Z\r\n" in content
    assert "DURATION:PT15M\r\n" in content
    assert "SUMMARY:Payrolls\\, Employment\\; Report\r\n" in content
    assert "X-FINANCIAL-CALENDAR-DUPLICATE-GROUP:D1\r\n" in content
    assert content.endswith("END:VCALENDAR\r\n")


def test_ics_skips_events_without_a_valid_utc_timestamp() -> None:
    event = _event()
    event["utc_dt"] = "not-a-date"

    content = render_ics([event])

    assert "BEGIN:VEVENT" not in content
    assert "END:VCALENDAR" in content


def test_write_export_atomically_creates_requested_file(tmp_path) -> None:
    destination = tmp_path / "calendar.csv"

    count = write_export(destination, "csv", [_event()])

    assert count == 1
    assert destination.exists()
    assert "Payrolls" in destination.read_text(encoding="utf-8")
    assert not list(tmp_path.glob("*.tmp"))
