"""Native non-blocking file selection; export uses the displayed Python snapshot."""

from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtWidgets import QFileDialog
from core.exporters import write_export


class ExportAdapter(QObject):
    message = Signal(str)
    changed = Signal()

    def __init__(self, calendar, queue, parent=None):
        super().__init__(parent)
        self.calendar, self.queue = calendar, queue
        self._dialog = None
        self._busy = False

    busy = Property(bool, lambda self: self._busy, notify=changed)

    @Slot(str)
    def exportVisible(self, format):
        if self._busy:
            return
        if format not in {"csv", "ics"}:
            self.message.emit("Formato export non valido")
            return
        rows = tuple(dict(row) for row in self.calendar.table.rows)
        if not rows:
            self.message.emit("Nessun evento visibile da esportare")
            return
        self._busy = True
        self.changed.emit()
        dialog = QFileDialog()
        self._dialog = dialog
        dialog.setWindowTitle("Esporta eventi visibili")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter(f"{format.upper()} (*.{format})")
        dialog.setDefaultSuffix(format)
        dialog.selectFile(f"financial-calendar-{datetime.now():%Y%m%d-%H%M}.{format}")

        def accepted():
            paths = dialog.selectedFiles()
            if paths:
                self.write(paths[0], format, rows)
            else:
                self._finish(None, None)

        dialog.accepted.connect(accepted)
        dialog.rejected.connect(lambda: self._finish(None, None))
        dialog.open()

    def write(self, path, format, rows):
        self.queue.submit(
            lambda: (write_export(Path(path), format, rows), len(rows)), self._finish
        )

    def _finish(self, result, error):
        self._busy = False
        self.changed.emit()
        if self._dialog:
            self._dialog.deleteLater()
            self._dialog = None
        if error:
            self.message.emit(f"Export non riuscito: {error}")
        elif result is not None:
            written, requested = result
            self.message.emit(
                f"Esportati {written} eventi"
                + (
                    f"; {requested - written} scartati: timestamp non valido"
                    if written != requested
                    else ""
                )
            )

    def stop(self):
        if self._dialog:
            self._dialog.reject()
