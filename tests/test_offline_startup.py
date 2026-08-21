from __future__ import annotations

import threading
from concurrent.futures import Future
from datetime import datetime, timedelta, timezone

from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from core.cache import CalendarCache
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui.bridge import CalendarBridge


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "config" / "settings.json")


def _future_event(source: CalendarSource = CalendarSource.FOREXFACTORY) -> CalendarEvent:
    event_dt = datetime.now(timezone.utc) + timedelta(hours=3)
    return CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Offline cached event",
        actual="",
        forecast="0.8%",
        previous="0.7%",
        utc_dt=event_dt.isoformat(),
        source=source,
    )


def test_controller_and_bridge_start_with_cached_data(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    refreshed_at = "2026-08-21T10:30:00+00:00"
    cache = CalendarCache()
    assert cache.save(CalendarSource.FOREXFACTORY, [_future_event()], refreshed_at)

    settings = Settings()
    controller = AppController(settings)
    bridge = CalendarBridge(controller, settings)
    try:
        assert controller.get_data_origin(CalendarSource.FOREXFACTORY) == "cache"
        assert controller.get_last_refresh(CalendarSource.FOREXFACTORY) == refreshed_at

        initial = bridge.getInitialState()
        source = next(item for item in initial["sources"] if item["key"] == "ig")
        assert source["data_origin"] == "cache"
        assert source["last_refresh_iso"] == refreshed_at

        rows = bridge.getEvents("ig", "ALL", "ALL", "", 0.0)
        assert len(rows) == 1
        assert rows[0]["event_name"] == "Offline cached event"
    finally:
        controller.shutdown()


def test_failed_refresh_keeps_cached_events_available(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    refreshed_at = "2026-08-21T10:30:00+00:00"
    assert CalendarCache().save(
        CalendarSource.FOREXFACTORY,
        [_future_event()],
        refreshed_at,
    )

    controller = AppController(Settings())
    future: Future = Future()
    future.set_exception(RuntimeError("offline"))
    refreshing = threading.Event()
    refreshing.set()

    try:
        controller._complete_refresh(  # noqa: SLF001 - deterministic lifecycle test
            future,
            CalendarSource.FOREXFACTORY,
            refreshing,
        )

        assert controller.get_data_origin(CalendarSource.FOREXFACTORY) == "cache"
        assert controller.get_last_refresh(CalendarSource.FOREXFACTORY) == refreshed_at
        events = controller.filter_events(CalendarSource.FOREXFACTORY)
        assert len(events) == 1
        assert events[0].event_name == "Offline cached event"
    finally:
        controller.shutdown()


def test_successful_refresh_replaces_cache_and_uses_utc_timestamp(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    controller = AppController(settings)
    future: Future = Future()
    future.set_result([_future_event()])
    refreshing = threading.Event()
    refreshing.set()

    try:
        controller._complete_refresh(  # noqa: SLF001 - deterministic lifecycle test
            future,
            CalendarSource.FOREXFACTORY,
            refreshing,
        )

        assert refreshing.is_set() is False
        assert controller.get_data_origin(CalendarSource.FOREXFACTORY) == "network"
        refreshed_at = controller.get_last_refresh(CalendarSource.FOREXFACTORY)
        parsed = datetime.fromisoformat(refreshed_at)
        assert parsed.utcoffset() == timedelta(0)
        assert settings.get("last_refresh_ig") == refreshed_at

        snapshot = CalendarCache().load(CalendarSource.FOREXFACTORY)
        assert snapshot is not None
        assert snapshot.refreshed_at == refreshed_at
        assert snapshot.events[0].event_name == "Offline cached event"
    finally:
        controller.shutdown()
