"""Serialized background work with queued delivery and deterministic shutdown."""

from concurrent.futures import ThreadPoolExecutor
import logging
from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class WorkQueue(QObject):
    completed = Signal(object, object, object)
    busyChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="calendar-view"
        )
        self.pending = 0
        self.closed = False
        self.completed.connect(self._deliver)

    def submit(self, work, callback):
        if self.closed:
            return
        self.pending += 1
        self.busyChanged.emit()
        future = self._executor.submit(work)

        def finished(result):
            try:
                value = result.result()
            except Exception as exc:
                logger.exception("Operazione non completata")
                self.completed.emit(callback, None, str(exc))
            else:
                self.completed.emit(callback, value, None)

        future.add_done_callback(finished)

    @Slot(object, object, object)
    def _deliver(self, callback, value, error):
        self.pending -= 1
        self.busyChanged.emit()
        if not self.closed:
            callback(value, error)

    def begin_shutdown(self):
        self.closed = True

    def shutdown(self):
        self.closed = True
        self._executor.shutdown(wait=True, cancel_futures=False)
