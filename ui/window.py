"""Native QML shell: composition, window geometry and ordered lifecycle."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from PySide6.QtCore import QObject, QUrl, QByteArray, QRect
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QWidget
from config.constants import PathConfig
from ui.adapters import CalendarAdapter, PreferencesAdapter
from ui.export_adapter import ExportAdapter
from ui.logs import LogModel, QtLogHandler
from ui.runtime import CalendarRuntime
from ui.workers import WorkQueue

logger = logging.getLogger(__name__)


class CalendarWindow(QObject):
    def __init__(self, controller, settings, *, debug=False, autostart=True):
        super().__init__()
        self.controller, self.settings = controller, settings
        self._stopped = False
        if QQuickStyle.name() != "Basic":
            QQuickStyle.setStyle("Basic")
        font = PathConfig.ASSETS_DIR / "fonts" / "NotoSans.ttf"
        if font.exists():
            QFontDatabase.addApplicationFont(str(font))
        QApplication.instance().setFont(QFont("Noto Sans", 10))
        self.queue = WorkQueue(self)
        self.calendar = CalendarAdapter(controller, settings, self.queue, self)
        self.preferences = PreferencesAdapter(self.calendar, self)
        self.exporter = ExportAdapter(self.calendar, self.queue, self)
        self.logs = LogModel(self)
        self.log_handler = QtLogHandler(self.logs)
        self.log_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        self.log_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        logging.getLogger().addHandler(self.log_handler)
        self.runtime = CalendarRuntime(controller, settings, queue=self.queue)
        self.calendar.accepted.connect(self.runtime.configure_auto_refresh)
        self.calendar.accepted.connect(self.runtime.configure_notifications)
        self.engine = QQmlApplicationEngine(self)
        self.engine.quit.connect(QApplication.instance().quit)
        self.engine.setInitialProperties(
            dict(
                calendar=self.calendar,
                preferences=self.preferences,
                exporter=self.exporter,
                logs=self.logs,
            )
        )
        self.engine.load(
            QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Main.qml"))
        )
        if not self.engine.rootObjects():
            self.stop()
            self.shutdown()
            raise RuntimeError("Caricamento della UI QML non riuscito")
        self.root = self.engine.rootObjects()[0]
        self.root.setIcon(
            QIcon(str(PathConfig.ASSETS_DIR / "icons" / "financial-calendar.png"))
        )
        self._restore_geometry()
        QApplication.instance().aboutToQuit.connect(self.stop)
        if autostart:
            self.runtime.start()

    def _restore_geometry(self):
        encoded = self.settings.get("window_geometry")
        if not encoded:
            return
        try:
            if encoded.startswith("qml:"):
                data = json.loads(encoded[4:])
                x, y, width, height = (
                    int(data[k]) for k in ("x", "y", "width", "height")
                )
                maximized = bool(data.get("maximized", False))
                geometry = QRect(x, y, max(820, width), max(560, height))
            else:
                # One-time import of the previous QWidget geometry format.
                legacy = QWidget()
                if not legacy.restoreGeometry(
                    QByteArray.fromBase64(encoded.encode("ascii"))
                ):
                    legacy.deleteLater()
                    raise ValueError("Formato geometria non valido")
                geometry, maximized = legacy.geometry(), legacy.isMaximized()
                legacy.deleteLater()
            screens = QApplication.screens()
            screen = next(
                (s for s in screens if s.availableGeometry().intersects(geometry)),
                screens[0],
            )
            area = screen.availableGeometry()
            geometry.setWidth(min(geometry.width(), max(820, area.width())))
            geometry.setHeight(min(geometry.height(), max(560, area.height())))
            geometry.moveLeft(
                max(area.left(), min(geometry.x(), area.right() - geometry.width() + 1))
            )
            geometry.moveTop(
                max(
                    area.top(), min(geometry.y(), area.bottom() - geometry.height() + 1)
                )
            )
            self.root.setGeometry(geometry)
            if maximized:
                self.root.showMaximized()
        except (ValueError, TypeError, KeyError, OverflowError):
            logger.warning("Geometria salvata non valida", exc_info=True)

    def show(self):
        self.root.show()

    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        self.controller.begin_shutdown()
        self.calendar.stop()
        self.runtime.stop()
        self.exporter.stop()
        if hasattr(self, "root"):
            r = self.root.geometry()
            value = "qml:" + json.dumps(
                dict(
                    x=r.x(),
                    y=r.y(),
                    width=r.width(),
                    height=r.height(),
                    maximized=self.root.visibility().name == "Maximized",
                )
            )

            def save_geometry():
                if not self.settings.set("window_geometry", value):
                    raise OSError("Salvataggio geometria non riuscito")

            self.queue.submit(save_geometry, lambda value, error: None)
        self.queue.begin_shutdown()

    def shutdown(self):
        self.stop()
        self.controller.shutdown()
        self.queue.shutdown()
        logging.getLogger().removeHandler(self.log_handler)
