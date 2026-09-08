"""Behavioral migration coverage: canonical queries, Qt models and real QML."""

from datetime import datetime, timedelta, timezone
import csv
import json
import time

import pytest
from PySide6.QtCore import (
    QObject,
    QMetaObject,
    Q_ARG,
    qInstallMessageHandler,
    QtMsgType,
)
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from core.cache import CalendarCache
from core.calendar_view import CalendarViewService, countdown, COLUMNS
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui.window import CalendarWindow


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def spin(app, condition, timeout=4):
    until = time.monotonic() + timeout
    while not condition() and time.monotonic() < until:
        app.processEvents()
        QTest.qWait(5)
    assert condition(), "Qt operation did not complete"


@pytest.fixture
def backend(monkeypatch, tmp_path):
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    for source in (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET):
        events = []
        for i in range(100):
            dt = now + timedelta(minutes=5 + i * 30)
            events.append(
                CalendarEvent(
                    date=dt.strftime("%d/%m/%Y"),
                    time=dt.strftime("%H:%M"),
                    country="USA" if i % 2 == 0 else "EUR",
                    impact=ImpactLevel.HIGH if i % 3 == 0 else ImpactLevel.LOW,
                    event_name=f"Event {i}",
                    actual="123K",
                    forecast="120K",
                    previous="110K",
                    utc_dt=dt.isoformat(),
                    source=source,
                )
            )
        assert CalendarCache().save(source, events, now.isoformat())
    settings = Settings()
    assert settings.set_many(
        {
            "ig_selected_region": "ALL",
            "ig_selected_impact": "ALL",
            "fxstreet_selected_region": "ALL",
            "fxstreet_selected_impact": "ALL",
            "combined_selected_region": "ALL",
            "combined_selected_impact": "ALL",
            "timezone_name": "UTC",
        }
    )
    controller = AppController(settings)
    monkeypatch.setattr(controller, "refresh_all", lambda: None)
    yield controller, settings
    controller.shutdown()


def test_view_source_filters_timezone_order_and_duplicates(backend):
    controller, settings = backend
    service = CalendarViewService(controller, settings)
    assert len(service.snapshot().rows) == 100
    assert service.change("active_source", "combined").columns == COLUMNS["combined"]
    view = service.change("region", "USA", source="combined")
    assert len(view.rows) == 100
    assert {row["duplicate_group"] for row in view.rows} == {
        f"D{i}" for i in range(1, 51)
    }
    view = service.change("impact", "HIGH", source="combined")
    assert len(view.rows) == 34
    view = service.change("search", "Event 0")
    assert len(view.rows) == 2
    before = view.rows[0]
    after = service.change("timezone_name", "UTC+02:00").rows[0]
    assert after["utc_dt"] == before["utc_dt"]
    assert after["time"] != before["time"]
    view = service.move_column("combined", 4, 0)
    assert view.columns[0] == "event_name"
    loaded = Settings()
    loaded.load()
    assert loaded.get("combined_column_order")[0] == 4
    with pytest.raises(ValueError):
        service.move_column("combined", -1, 0)


def test_relative_ranges_and_natural_sort(backend):
    service = CalendarViewService(*backend)
    all_rows = service.snapshot().rows
    assert 1 < len(service.change("range", "next24").rows) < len(all_rows)
    view = service.change("range", "today")
    assert all(
        row["date"] == datetime.now(timezone.utc).strftime("%d/%m/%Y")
        for row in view.rows
    )
    view = service.change("range", "tomorrow")
    assert all(
        row["date"]
        == (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d/%m/%Y")
        for row in view.rows
    )
    service.change("range", "all")
    view = service.change("sort", "event_name", source="ig")
    assert [row["event_name"] for row in view.rows[:12]] == [
        f"Event {i}" for i in range(12)
    ]
    view = service.change("sort", "event_name", source="ig")
    assert view.rows[0]["event_name"] == "Event 99"
    assert sum(row["next_high"] for row in view.rows) == 1
    assert countdown(300) == "tra 5 min"
    assert countdown(5400) == "tra 1 h 30 min"


def test_rejected_persistence_keeps_query_and_export_source(backend, monkeypatch):
    controller, settings = backend
    service = CalendarViewService(controller, settings)
    before = service.snapshot()
    monkeypatch.setattr(settings, "_save_locked", lambda: False)
    with pytest.raises(OSError):
        service.change("active_source", "fxstreet")
    after = service.snapshot()
    assert after.state == before.state
    assert after.rows == before.rows


def test_qml_models_interaction_export_and_geometry(app, backend, tmp_path):
    controller, settings = backend
    errors = []

    def capture(kind, context, text):
        if kind in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ) and ("qml" in text.lower() or context.file and ".qml" in context.file):
            errors.append(text)

    old = qInstallMessageHandler(capture)
    window = CalendarWindow(controller, settings, autostart=False)
    try:
        window.show()
        spin(app, lambda: window.calendar.count == 100 and not window.calendar.busy)
        assert window.calendar.sources.rowCount() == 3
        table = window.root.findChild(QObject, "eventsTable")
        assert table is not None
        assert table.property("reuseItems")
        window.root.resize(820, 560)
        QTest.qWait(50)
        assert table.property("height") >= 200
        search = window.root.findChild(QObject, "searchField")
        search.forceActiveFocus()
        for character in "Event 0":
            QTest.keyClick(window.root, character)
        spin(app, lambda: window.calendar.count == 1 and not window.calendar.busy)
        window.calendar.selectSource("combined")
        spin(app, lambda: window.calendar.count == 2 and not window.calendar.busy)
        assert window.calendar.table.columnCount() == 10
        assert all(row["duplicate_group"] for row in window.calendar.table.rows)
        assert QMetaObject.invokeMethod(
            table, "moveColumn", Q_ARG(int, 4), Q_ARG(int, 0)
        )
        spin(
            app,
            lambda: (
                window.calendar.table.columns[0] == "event_name"
                and not window.calendar.busy
            ),
        )
        output = tmp_path / "visible.csv"
        window.exporter.exportVisible("csv")
        assert window.exporter._dialog is not None
        window.exporter._dialog.selectFile(str(output))
        window.exporter._dialog.accept()
        spin(app, lambda: output.exists() and not window.exporter.busy)
        with output.open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 2
        assert {row["source"] for row in rows} == {"ig", "fxstreet"}
        assert all(row["actual"] == "123K" for row in rows)
        assert rows[0]["utc_dt"] == window.calendar.table.rows[0]["utc_dt"]
        assert rows[0]["date"] == window.calendar.table.rows[0]["date"]
        assert not errors, errors
    finally:
        window.root.close()
        window.shutdown()
        window.engine.deleteLater()
        app.processEvents()
        qInstallMessageHandler(old)
    assert settings.get("window_geometry").startswith("qml:")
    assert json.loads(settings.get("window_geometry")[4:])["width"] == 820
    assert not window.runtime.started
    assert window.queue.closed


def test_timers_are_not_postponed_by_snapshot_updates(app, backend):
    window = CalendarWindow(*backend, autostart=False)
    try:
        window.runtime.start()
        timer = window.runtime.auto_refresh_timer
        QTest.qWait(50)
        remaining = timer.remainingTime()
        window.runtime.configure_auto_refresh()
        assert timer.remainingTime() <= remaining
    finally:
        window.root.close()
        window.shutdown()
        window.engine.deleteLater()
        app.processEvents()
