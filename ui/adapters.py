"""Focused typed QML commands and read-only presentation state."""

from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from core.calendar_view import CalendarViewService
from ui.models import CalendarTableModel, RecordListModel


class CalendarAdapter(QObject):
    changed = Signal()
    message = Signal(str)
    accepted = Signal()
    backendEvent = Signal(str, object)

    def __init__(self, controller, settings, queue, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.queue = queue
        self.service = CalendarViewService(controller, settings)
        self._view = None
        self.table = CalendarTableModel(self)
        self.sources = RecordListModel(
            ("key", "label", "status", "freshness", "error", "refreshing"), self
        )
        self.queue.busyChanged.connect(self.changed)
        self.backendEvent.connect(self._backend_event)
        controller.set_notification_callback(self.backendEvent.emit)
        self.clock = QTimer(self)
        self.clock.setInterval(30000)
        self.clock.timeout.connect(self.reload)
        self.clock.start()
        self.reload()

    tableModel = Property(QObject, lambda self: self.table, constant=True)
    sourceModel = Property(QObject, lambda self: self.sources, constant=True)
    state = Property(
        "QVariantMap",
        lambda self: self._view.state if self._view else {},
        notify=changed,
    )
    summary = Property(
        str,
        lambda self: self._view.summary if self._view else "Caricamento…",
        notify=changed,
    )
    status = Property(
        str,
        lambda self: self._view.status if self._view else "Caricamento…",
        notify=changed,
    )
    error = Property(
        str, lambda self: self._view.error if self._view else "", notify=changed
    )
    count = Property(int, lambda self: self.table.rowCount(), notify=changed)
    busy = Property(bool, lambda self: bool(self.queue.pending), notify=changed)

    def _received(self, view, error):
        if error:
            self.message.emit(error)
            self.changed.emit()
            return
        self._view = view
        self.table.replace(view)
        self.sources.replace(view.sources)
        self.changed.emit()
        self.accepted.emit()

    @Slot()
    def reload(self):
        if not self.queue.pending:
            self.queue.submit(self.service.snapshot, self._received)

    @Slot(str, object)
    def _backend_event(self, name, payload):
        # A refresh may finish during a settings operation: always enqueue this snapshot.
        self.queue.submit(self.service.snapshot, self._received)

    @Slot(str)
    def selectSource(self, value):
        self.change("active_source", value)

    @Slot(str, str)
    def setFilter(self, key, value):
        if key not in {
            "region",
            "impact",
            "selected_date",
            "timezone_name",
            "search",
            "range",
        }:
            self.message.emit("Filtro non valido")
            return
        self.change(key, value)

    def change(self, key, value):
        source = self._view.state["active_source"] if self._view else "ig"
        self.queue.submit(
            lambda: self.service.change(key, value, source=source), self._received
        )

    @Slot(int)
    def sortColumn(self, column):
        if 0 <= column < len(self.table.columns):
            self.change("sort", self.table.columns[column])

    @Slot(int, int)
    def moveColumn(self, old, new):
        source = self._view.state["active_source"] if self._view else "ig"
        self.queue.submit(
            lambda: self.service.move_column(source, old, new), self._received
        )

    @Slot("QVariantList")
    def setColumnPositions(self, positions):
        source = self._view.state["active_source"] if self._view else "ig"
        self.queue.submit(
            lambda: self.service.set_column_positions(source, positions), self._received
        )

    @Slot(str)
    def refresh(self, source):
        if source == "combined":
            self.controller.refresh_all()
        elif source == "ig":
            self.controller.refresh_ig()
        elif source == "fxstreet":
            self.controller.refresh_fxstreet()
        else:
            self.message.emit("Sorgente non valida")

    def stop(self):
        self.clock.stop()


class PreferencesAdapter(QObject):
    def __init__(self, calendar, parent=None):
        super().__init__(parent)
        self.calendar = calendar

    @Slot(int)
    def setAutoRefresh(self, minutes):
        self.calendar.change("auto_refresh_minutes", minutes)

    @Slot(int)
    def setNotificationLead(self, minutes):
        self.calendar.change("high_notification_minutes", minutes)
