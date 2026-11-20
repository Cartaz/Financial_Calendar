from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from config.settings import Settings
from core.app_controller import AppController
from core.cache import CalendarCache
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.calendar_view import CalendarViewService
from ui.runtime import CalendarRuntime


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def notify(self, title: str, body: str, *, timeout_ms: int = 7000) -> bool:
        del timeout_ms
        self.messages.append((title, body))
        return True


def _event(source: CalendarSource, name: str, *, minutes: int = 4) -> CalendarEvent:
    event_dt = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name=name,
        actual="",
        forecast="120K",
        previous="110K",
        utc_dt=event_dt.isoformat(),
        source=source,
    )


def _seed(source: CalendarSource, events: list[CalendarEvent]) -> None:
    assert CalendarCache().save(
        source,
        events,
        datetime.now(timezone.utc).isoformat(),
    )


def test_combined_source_merges_and_annotates_real_events(
    monkeypatch, tmp_path
) -> None:
    _seed(
        CalendarSource.FOREXFACTORY,
        [_event(CalendarSource.FOREXFACTORY, "Nonfarm Payrolls", minutes=60)],
    )
    _seed(
        CalendarSource.FXSTREET,
        [_event(CalendarSource.FXSTREET, "US Nonfarm Payrolls", minutes=60)],
    )
    settings = Settings()
    controller = AppController()
    view = CalendarViewService(controller, settings)
    try:
        view.change("active_source", "combined")
        view.change("region", "USA")
        view.change("impact", "HIGH")
        rows = view.change("timezone_name", "Europe/Rome").rows
        assert len(rows) == 2
        assert {row["source"] for row in rows} == {"ig", "fxstreet"}
        assert {row["duplicate_group"] for row in rows} == {"D1"}
        view.change("sort", "source")
        initial = view.snapshot()
        assert initial.state["region"] == "USA"
        assert initial.state["sort_key"] == "source"
        assert initial.state["active_source"] == "combined"
    finally:
        controller.shutdown()


def test_high_notifications_are_optional_and_deduplicated_across_sources(
    monkeypatch, tmp_path
) -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    _seed(
        CalendarSource.FOREXFACTORY,
        [_event(CalendarSource.FOREXFACTORY, "US Nonfarm Payrolls")],
    )
    _seed(
        CalendarSource.FXSTREET,
        [_event(CalendarSource.FXSTREET, "Nonfarm Payrolls")],
    )
    settings = Settings()
    controller = AppController()
    controller.refresh_all = lambda: None
    notifier = FakeNotifier()
    runtime = CalendarRuntime(controller, settings, notifier=notifier)
    view = CalendarViewService(controller, settings)
    try:
        view.change("high_notification_minutes", 5)
        runtime.configure_notifications()
        assert notifier.messages == []

        runtime.start()
        deadline = time.monotonic() + 2
        while runtime._checking and time.monotonic() < deadline:
            app.processEvents()
            QTest.qWait(5)
        assert len(notifier.messages) == 1
        title, body = notifier.messages[0]
        assert "Evento HIGH" in title
        assert "USA" in body
        assert "Payrolls" in body
        assert runtime.notification_timer.isActive()

        runtime.check_notifications()
        assert len(notifier.messages) == 1

        view.change("high_notification_minutes", 0)
        runtime.configure_notifications()
        assert not runtime.notification_timer.isActive()
    finally:
        runtime.shutdown()
        controller.shutdown()


def test_notification_time_uses_the_configured_timezone(monkeypatch, tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    event = _event(CalendarSource.FXSTREET, "CPI")
    _seed(CalendarSource.FXSTREET, [event])
    settings = Settings()
    assert settings.set_many(
        {"timezone_name": "UTC+05:30", "high_notification_minutes": 5}
    )
    controller = AppController()
    controller.refresh_all = lambda: None
    notifier = FakeNotifier()
    runtime = CalendarRuntime(controller, settings, notifier=notifier)
    try:
        runtime.start()
        deadline = time.monotonic() + 2
        while runtime._checking and time.monotonic() < deadline:
            app.processEvents()
            QTest.qWait(5)
        expected = (
            datetime.fromisoformat(event.utc_dt)
            .astimezone(timezone(timedelta(hours=5, minutes=30)))
            .strftime("%H:%M")
        )
        assert len(notifier.messages) == 1
        assert notifier.messages[0][1].endswith(expected)
    finally:
        runtime.shutdown()
        controller.shutdown()
