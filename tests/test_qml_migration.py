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


def test_settings_focus_does_not_convert_relative_range_to_fixed_date(app, backend):
    window = CalendarWindow(*backend, autostart=False)
    try:
        window.show()
        spin(app, lambda: window.calendar.count == 100 and not window.calendar.busy)
        window.calendar.setFilter("range", "today")
        spin(
            app,
            lambda: (
                window.calendar.state["quick_range"] == "today"
                and not window.calendar.busy
            ),
        )
        popup = window.root.findChild(QObject, "settingsPopup")
        assert popup is not None
        assert QMetaObject.invokeMethod(popup, "open")
        field = window.root.findChild(QObject, "dateField")
        assert field is not None
        field.forceActiveFocus()
        QTest.qWait(30)
        window.root.findChild(QObject, "timezoneField").forceActiveFocus()
        QTest.qWait(30)
        spin(app, lambda: not window.calendar.busy)
        assert window.calendar.state["quick_range"] == "today"
        assert backend[1].get("selected_date") == ""
    finally:
        window.root.close()
        window.shutdown()
        window.engine.deleteLater()
        app.processEvents()


def test_header_mouse_drag_persists_visual_order(app, backend):
    from PySide6.QtCore import QPointF, Qt

    def visual_item(parent, name):
        if parent.objectName() == name:
            return parent
        for child in parent.childItems():
            found = visual_item(child, name)
            if found is not None:
                return found
        return None

    window = CalendarWindow(*backend, autostart=False)
    try:
        window.show()
        spin(app, lambda: window.calendar.count == 100 and not window.calendar.busy)
        QTest.qWait(50)
        first = visual_item(window.root.contentItem(), "headerCell0")
        third = visual_item(window.root.contentItem(), "headerCell2")
        assert first is not None and third is not None
        origin = first.mapToScene(
            QPointF(first.width() / 2, first.height() / 2)
        ).toPoint()
        target = third.mapToScene(
            QPointF(third.width() / 2, third.height() / 2)
        ).toPoint()
        QTest.mousePress(window.root, Qt.LeftButton, Qt.NoModifier, origin)
        for step in range(1, 11):
            point = origin + (target - origin) * (step / 10)
            QTest.mouseMove(window.root, point, delay=20)
        QTest.mouseRelease(window.root, Qt.LeftButton, Qt.NoModifier, target)
        QTest.qWait(100)
        spin(
            app,
            lambda: (
                window.calendar.table.columns[2] == "date" and not window.calendar.busy
            ),
        )
        assert backend[1].get("ig_column_order")[:3] == [1, 2, 0]
        assert window.calendar.state["sort_key"] == ""
        date_cell = visual_item(window.root.contentItem(), "headerCell2")
        date_cell.forceActiveFocus()
        QTest.keyClick(window.root, Qt.Key_Left, Qt.AltModifier)
        spin(
            app,
            lambda: (
                window.calendar.table.columns[1] == "date" and not window.calendar.busy
            ),
        )
        assert backend[1].get("ig_column_order")[:3] == [1, 0, 2]
        window.calendar.selectSource("fxstreet")
        spin(
            app,
            lambda: (
                window.calendar.state["active_source"] == "fxstreet"
                and not window.calendar.busy
            ),
        )
        window.calendar.selectSource("ig")
        spin(
            app,
            lambda: (
                window.calendar.state["active_source"] == "ig"
                and not window.calendar.busy
            ),
        )
        assert window.calendar.table.columns[1] == "date"
    finally:
        window.root.close()
        window.shutdown()
        window.engine.deleteLater()
        app.processEvents()


def test_settings_edits_validate_and_keep_canonical_date(app, backend):
    from PySide6.QtCore import Qt

    window = CalendarWindow(*backend, autostart=False)
    try:
        window.show()
        spin(app, lambda: window.calendar.count == 100 and not window.calendar.busy)
        popup = window.root.findChild(QObject, "settingsPopup")
        assert QMetaObject.invokeMethod(popup, "open")
        date = window.root.findChild(QObject, "dateField")
        date.forceActiveFocus()
        for character in "bad-date":
            QTest.keyClick(window.root, character)
        QTest.keyClick(window.root, Qt.Key_Return)
        spin(app, lambda: not window.calendar.busy)
        assert backend[1].get("selected_date") == ""
        assert "YYYY-MM-DD" in window.root.property("feedback")
        assert date.property("text") == ""
        wanted = datetime.now(timezone.utc).date().isoformat()
        for character in wanted:
            QTest.keyClick(window.root, character)
        QTest.keyClick(window.root, Qt.Key_Return)
        spin(
            app,
            lambda: (
                backend[1].get("selected_date") == wanted and not window.calendar.busy
            ),
        )
        assert window.calendar.state["quick_range"] == "manual"
        assert window.calendar.state["selected_date"] == wanted
        assert QMetaObject.invokeMethod(popup, "close")
    finally:
        window.root.close()
        window.shutdown()
        window.engine.deleteLater()
        app.processEvents()


def test_standalone_runtime_always_delivers_off_gui_thread(app, backend):
    import threading
    from ui.runtime import CalendarRuntime

    controller, settings = backend
    assert settings.set("high_notification_minutes", 15)
    caller = threading.get_ident()
    entered = threading.Event()
    release = threading.Event()
    delivered_on = []

    class Notifier:
        def notify(self, *args):
            delivered_on.append(threading.get_ident())
            entered.set()
            assert release.wait(timeout=2)
            return True

    runtime = CalendarRuntime(controller, settings, notifier=Notifier())
    try:
        runtime.start()
        assert entered.wait(timeout=1)
        assert caller not in delivered_on
        release.set()
        spin(app, lambda: not runtime._checking)
    finally:
        release.set()
        runtime.shutdown()
    assert runtime._queue.closed
