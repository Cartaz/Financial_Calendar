from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from config.settings import Settings
from core.app_controller import AppController
from ui_qml.bridge import CalendarBridge


def test_qml_engine_loads_offscreen() -> None:
    app = QApplication.instance() or QApplication([])
    settings = Settings()
    controller = AppController(settings)
    bridge = CalendarBridge(controller)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.rootContext().setContextProperty("trayAvailable", False)

    qml_file = Path(__file__).resolve().parents[1] / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    try:
        assert engine.rootObjects()
    finally:
        controller.shutdown()
        for root in engine.rootObjects():
            root.close()
        app.processEvents()
