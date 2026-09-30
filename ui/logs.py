"""Bounded incremental Qt log model and standard logging handler."""

from datetime import datetime
import logging
from PySide6.QtCore import QModelIndex, Signal, Slot
from PySide6.QtGui import QGuiApplication
from ui.models import RecordListModel


class LogModel(RecordListModel):
    queued = Signal(object)

    def __init__(self, parent=None):
        super().__init__(("time", "level", "message"), parent)
        self.queued.connect(self.append)

    @Slot(object)
    def append(self, record):
        if len(self.records) == 250:
            self.beginRemoveRows(QModelIndex(), 0, 0)
            self.records = self.records[1:]
            self.endRemoveRows()
        index = len(self.records)
        self.beginInsertRows(QModelIndex(), index, index)
        self.records = (*self.records, record)
        self.endInsertRows()

    @Slot()
    def copy(self):
        QGuiApplication.clipboard().setText(
            "\n".join(
                f"{r['time']} [{r['level']}] {r['message']}" for r in self.records
            )
        )


class QtLogHandler(logging.Handler):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def emit(self, record):
        try:
            self.model.queued.emit(
                dict(
                    time=datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                    level=record.levelname,
                    message=self.format(record),
                )
            )
        except Exception:
            self.handleError(record)
