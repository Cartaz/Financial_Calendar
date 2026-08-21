from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from config.constants import PathConfig
from core.cache import CalendarCache
from core.models import CalendarEvent, CalendarSource, ImpactLevel


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "config" / "settings.json")


def _event(source: CalendarSource = CalendarSource.FOREXFACTORY) -> CalendarEvent:
    event_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    return CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Cached test event",
        actual="1.0%",
        forecast="0.8%",
        previous="0.7%",
        utc_dt=event_dt.isoformat(),
        source=source,
    )


def test_cache_round_trip_preserves_real_event_data(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    cache = CalendarCache()
    refreshed_at = "2026-08-21T10:30:00+00:00"

    assert cache.save(CalendarSource.FOREXFACTORY, [_event()], refreshed_at) is True

    snapshot = cache.load(CalendarSource.FOREXFACTORY)
    assert snapshot is not None
    assert snapshot.refreshed_at == refreshed_at
    assert len(snapshot.events) == 1
    assert snapshot.events[0].event_name == "Cached test event"
    assert snapshot.events[0].source == CalendarSource.FOREXFACTORY

    payload = json.loads(
        (PathConfig.APP_DATA_DIR / "calendar_ig.json").read_text(encoding="utf-8")
    )
    assert payload["version"] == 1
    assert payload["source"] == "ig"
    assert payload["events"][0]["event_name"] == "Cached test event"


def test_corrupt_cache_is_ignored_without_fabricating_data(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    PathConfig.ensure_dirs()
    path = PathConfig.APP_DATA_DIR / "calendar_fxstreet.json"
    path.write_text("{not-json", encoding="utf-8")

    snapshot = CalendarCache().load(CalendarSource.FXSTREET)

    assert snapshot is None
