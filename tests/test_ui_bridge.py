from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtWidgets import QApplication

from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui.bridge import CalendarBridge


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")


def _future_event() -> CalendarEvent:
    event_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    return CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Test event",
        actual="1.0%",
        forecast="0.8%",
        previous="0.7%",
        utc_dt=event_dt.isoformat(),
        source=CalendarSource.FOREXFACTORY,
    )


def test_initial_state_exposes_sources_and_persisted_filters(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    controller = AppController(settings)
    bridge = CalendarBridge(controller, settings)
    try:
        assert bridge.saveFilters("ig", "USA", "HIGH") is True
        initial = bridge.getInitialState()
        sources = {source["key"]: source for source in initial["sources"]}

        assert set(sources) == {"ig", "fxstreet", "combined"}
        assert sources["ig"]["selected_region"] == "USA"
        assert sources["ig"]["selected_impact"] == "HIGH"
        assert len(sources["ig"]["columns"]) == 8
        assert len(sources["fxstreet"]["columns"]) == 9
        assert len(sources["combined"]["columns"]) == 10
        assert initial["regions"][-1] == "ALL"
        assert initial["impacts"] == ["ALL", "HIGH", "MID", "LOW"]
        assert initial["auto_refresh_options"] == [0, 5, 15, 30, 60]
        assert initial["notification_lead_options"] == [0, 5, 15, 30, 60]
    finally:
        controller.shutdown()


def test_bridge_filters_and_serializes_controller_events(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    controller = AppController(settings)
    controller.events_ig = [_future_event()]
    bridge = CalendarBridge(controller, settings)
    try:
        rows = bridge.getEvents("ig", "USA", "HIGH", "", 2.0)
        assert len(rows) == 1
        assert rows[0]["country"] == "USA"
        assert rows[0]["impact"] == "HIGH"
        assert rows[0]["event_name"] == "Test event"
        assert rows[0]["source"] == "ig"
    finally:
        controller.shutdown()


def test_column_order_is_validated_and_persisted(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    controller = AppController(settings)
    bridge = CalendarBridge(controller, settings)
    try:
        order = [0, 4, 1, 2, 3, 5, 6, 7]
        assert bridge.saveColumnOrder("ig", str(order).replace("'", '"')) is True
        assert settings.get("ig_column_order") == order
        assert bridge.saveColumnOrder("ig", "[0, 1]") is False
        assert settings.get("ig_column_order") == order
    finally:
        controller.shutdown()


def test_ui_state_sort_auto_refresh_and_notifications_are_persisted(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    qt_app = QApplication.instance() or QApplication([])
    assert qt_app is not None

    settings = Settings()
    controller = AppController(settings)
    refresh_calls: list[bool] = []
    controller.refresh_all = lambda: refresh_calls.append(True)
    bridge = CalendarBridge(controller, settings)
    try:
        assert bridge.saveUiState("fxstreet", "Europe/Rome", "2026-08-24", 5)
        assert bridge.saveSort("fxstreet", "impact", "desc")
        assert bridge.saveNotificationLead(15)

        initial = bridge.getInitialState()
        sources = {source["key"]: source for source in initial["sources"]}
        assert initial["ui_state"] == {
            "active_source": "fxstreet",
            "timezone_name": "Europe/Rome",
            "selected_date": "2026-08-24",
            "auto_refresh_minutes": 5,
            "high_notification_minutes": 15,
        }
        assert sources["fxstreet"]["sort_key"] == "impact"
        assert sources["fxstreet"]["sort_direction"] == "desc"

        bridge.start()
        assert refresh_calls == [True]
        assert bridge._auto_refresh_timer.isActive()
        assert bridge._auto_refresh_timer.interval() == 5 * 60 * 1000
        assert bridge._notification_timer.isActive()

        assert bridge.saveUiState("fxstreet", "Europe/Rome", "2026-08-24", 0)
        assert not bridge._auto_refresh_timer.isActive()
        assert bridge.saveNotificationLead(0)
        assert not bridge._notification_timer.isActive()
    finally:
        controller.shutdown()
