from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui.bridge import CalendarBridge
from ui.runtime import CalendarRuntime


class CapturingNativeActions:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []

    def export_events(self, export_format: str, events: list[dict[str, object]]) -> dict:
        assert export_format == "csv"
        self.rows = events
        return {"ok": True, "count": len(events)}


def test_export_uses_backend_values_and_visible_presentation_time(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")

    event_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    event = CalendarEvent(
        time=event_dt.strftime("%H:%M"),
        date=event_dt.strftime("%d/%m/%Y"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Payrolls",
        actual="123K",
        forecast="120K",
        previous="110K",
        utc_dt=event_dt.isoformat(),
        source=CalendarSource.FOREXFACTORY,
    )

    settings = Settings()
    controller = AppController(settings)
    controller.events_ig = [event]
    runtime = CalendarRuntime(controller, settings)
    native = CapturingNativeActions()
    bridge = CalendarBridge(controller, settings, runtime, native_actions=native)

    try:
        visible = {
            "source": "ig",
            "utc_dt": event.utc_dt,
            "country": "USA",
            "event_name": "Payrolls",
            "date": "31/12/2030",
            "time": "23:45",
            "actual": "SPOOFED",
            "forecast": "SPOOFED",
        }
        result = bridge.exportEvents("csv", json.dumps([visible]))

        assert result == {"ok": True, "count": 1}
        assert native.rows[0]["actual"] == "123K"
        assert native.rows[0]["forecast"] == "120K"
        assert native.rows[0]["date"] == "31/12/2030"
        assert native.rows[0]["time"] == "23:45"
    finally:
        controller.shutdown()
