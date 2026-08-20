from __future__ import annotations

import threading

from config.constants import PathConfig
from config.settings import Settings
from core import app_controller
from core.models import CalendarEvent, CalendarSource, ImpactLevel


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")


def _event() -> CalendarEvent:
    return CalendarEvent(
        time="12:00",
        date="20/08/2026",
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Test",
        actual="",
        forecast="",
        previous="",
        utc_dt="2026-08-20T12:00:00+00:00",
        source=CalendarSource.FOREXFACTORY,
    )


def test_shutdown_suppresses_late_worker_notifications(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    started = threading.Event()
    release = threading.Event()

    def slow_scraper(*, debug=False):
        started.set()
        release.wait(timeout=2)
        return [_event()]

    monkeypatch.setattr(app_controller, "scrape_ig_calendar", slow_scraper)

    controller = app_controller.AppController(Settings())
    notifications = []
    controller.set_notification_callback(
        lambda name, payload: notifications.append((name, payload))
    )

    controller.refresh_ig()
    assert started.wait(timeout=1)
    controller.begin_shutdown()
    release.set()
    controller.shutdown()

    assert [name for name, _ in notifications] == ["calendar_refresh_started"]
