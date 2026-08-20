from __future__ import annotations

from PySide6.QtCore import Qt

from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui_qml.bridge import CalendarBridge, CalendarTableModel


def _event(time_text: str, name: str) -> CalendarEvent:
    return CalendarEvent(
        time=time_text,
        date="20/08/2026",
        country="USA",
        impact=ImpactLevel.LOW,
        event_name=name,
        actual="",
        forecast="",
        previous="",
        source=CalendarSource.FOREXFACTORY,
    )


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")


def test_sort_survives_model_refresh() -> None:
    model = CalendarTableModel(CalendarSource.FOREXFACTORY)
    model.set_events([_event("15:00", "late"), _event("09:00", "early")])
    model.sortColumn(1)
    assert model.data(model.index(0, 1), int(Qt.ItemDataRole.DisplayRole)) == "09:00"

    model.set_events([_event("18:00", "later"), _event("07:00", "earlier")])
    assert model.data(model.index(0, 1), int(Qt.ItemDataRole.DisplayRole)) == "07:00"
    assert model.sortColumnIndex == 1
    assert model.sortAscending is True


def test_column_order_persists_through_bridge(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    settings = Settings()
    controller = AppController(settings)
    bridge = CalendarBridge(controller)
    try:
        bridge.columnMoved("ig", 4, 4, 1)
        assert bridge.getColumnOrder("ig") == [0, 4, 1, 2, 3, 5, 6, 7]
        assert bridge.preferredColumnWidth("ig", 4) == 300
    finally:
        controller.shutdown()
