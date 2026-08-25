from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from config.constants import PathConfig
from config.settings import Settings
from core import app_controller as app_controller_module
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource, ImpactLevel


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(
        PathConfig,
        "SETTINGS_FILE",
        tmp_path / "config" / "settings.json",
    )


def _future_event() -> CalendarEvent:
    event_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    return CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Available source event",
        actual="",
        forecast="1.0%",
        previous="0.9%",
        utc_dt=event_dt.isoformat(),
        source=CalendarSource.FOREXFACTORY,
    )


def test_refresh_all_keeps_available_source_when_other_source_fails(
    monkeypatch,
    tmp_path,
) -> None:
    _redirect_paths(monkeypatch, tmp_path)

    monkeypatch.setattr(
        app_controller_module,
        "scrape_ig_calendar",
        lambda debug=False: [_future_event()],
    )

    def fail_fxstreet(debug=False):
        raise RuntimeError("FXStreet unavailable")

    monkeypatch.setattr(app_controller_module, "scrape_fxstreet_calendar", fail_fxstreet)

    controller = AppController(Settings())
    notifications: list[tuple[str, dict]] = []
    completed = threading.Event()

    def receive(event_name: str, payload: dict) -> None:
        notifications.append((event_name, dict(payload)))
        terminal = [
            name
            for name, _ in notifications
            if name in {"calendar_refreshed", "calendar_refresh_error"}
        ]
        if len(terminal) >= 2:
            completed.set()

    controller.set_notification_callback(receive)
    try:
        controller.refresh_all()
        assert completed.wait(timeout=3.0)

        assert controller.get_data_origin(CalendarSource.FOREXFACTORY) == "network"
        assert controller.get_data_origin(CalendarSource.FXSTREET) == "empty"
        assert [
            event.event_name
            for event in controller.filter_events(CalendarSource.FOREXFACTORY)
        ] == ["Available source event"]
        assert controller.filter_events(CalendarSource.FXSTREET) == []

        refreshed = [
            payload
            for name, payload in notifications
            if name == "calendar_refreshed" and payload.get("source") == "ig"
        ]
        failed = [
            payload
            for name, payload in notifications
            if name == "calendar_refresh_error"
            and payload.get("source") == "fxstreet"
        ]
        assert len(refreshed) == 1
        assert refreshed[0]["count"] == 1
        assert len(failed) == 1
        assert "FXStreet unavailable" in failed[0]["error"]

        cache_path = PathConfig.APP_DATA_DIR / "calendar_ig.json"
        assert cache_path.exists()
        assert not (PathConfig.APP_DATA_DIR / "calendar_fxstreet.json").exists()
    finally:
        controller.shutdown()
