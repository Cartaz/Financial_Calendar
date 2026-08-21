from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtWidgets import QApplication

from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui.bridge import CalendarBridge


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def notify(self, title: str, body: str, *, timeout_ms: int = 7000) -> bool:
        del timeout_ms
        self.messages.append((title, body))
        return True


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")


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


def test_combined_source_merges_real_events_and_persists_its_state(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    controller = AppController(settings)
    controller.events_ig = [_event(CalendarSource.FOREXFACTORY, "Nonfarm Payrolls", minutes=60)]
    controller.events_fxstreet = [_event(CalendarSource.FXSTREET, "US Nonfarm Payrolls", minutes=60)]
    bridge = CalendarBridge(controller, settings, notifier=FakeNotifier())
    try:
        rows = bridge.getEventsInTimezone("combined", "USA", "HIGH", "", "Europe/Rome")
        assert len(rows) == 2
        assert {row["source"] for row in rows} == {"ig", "fxstreet"}

        assert bridge.saveFilters("combined", "USA", "HIGH")
        assert bridge.saveSort("combined", "source", "desc")
        assert bridge.saveUiState("combined", "Europe/Rome", "", 15)

        initial = bridge.getInitialState()
        sources = {source["key"]: source for source in initial["sources"]}
        assert set(sources) == {"ig", "fxstreet", "combined"}
        assert len(sources["combined"]["columns"]) == 10
        assert sources["combined"]["selected_region"] == "USA"
        assert sources["combined"]["selected_impact"] == "HIGH"
        assert sources["combined"]["sort_key"] == "source"
        assert initial["ui_state"]["active_source"] == "combined"
        assert initial["notification_lead_options"] == [0, 5, 15, 30, 60]
    finally:
        controller.shutdown()


def test_high_notifications_are_optional_and_deduplicated_across_sources(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    app = QApplication.instance() or QApplication([])
    assert app is not None

    settings = Settings()
    controller = AppController(settings)
    controller.events_ig = [_event(CalendarSource.FOREXFACTORY, "US Nonfarm Payrolls")]
    controller.events_fxstreet = [_event(CalendarSource.FXSTREET, "Nonfarm Payrolls")]
    controller.refresh_all = lambda: None
    notifier = FakeNotifier()
    bridge = CalendarBridge(controller, settings, notifier=notifier)
    try:
        assert bridge.saveNotificationLead(5)
        assert notifier.messages == []

        bridge.start()
        assert len(notifier.messages) == 1
        title, body = notifier.messages[0]
        assert "Evento HIGH" in title
        assert "USA" in body
        assert "Payrolls" in body
        assert bridge._notification_timer.isActive()

        bridge._check_high_notifications()
        assert len(notifier.messages) == 1

        assert bridge.saveNotificationLead(0)
        assert not bridge._notification_timer.isActive()
    finally:
        controller.shutdown()
