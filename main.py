"""Financial Calendar entry point using the Qt Quick/QML UI."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from ui.tray_icon import TrayIconManager
from ui_qml.bridge import CalendarBridge


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=AppMeta.DISPLAY_NAME)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    PathConfig.ensure_dirs()
    settings = Settings()
    settings.load()

    # QApplication is intentionally retained instead of QGuiApplication:
    # QSystemTrayIcon/QMenu still live in Qt Widgets, while the main window
    # is rendered entirely by Qt Quick.
    app = QApplication(sys.argv)
    app.setApplicationName(AppMeta.NAME)
    app.setApplicationDisplayName(AppMeta.DISPLAY_NAME)
    app.setApplicationVersion(AppMeta.VERSION)
    app.setDesktopFileName("financial_calendar")

    icon_path = PathConfig.ASSETS_DIR / "icons" / "financial-calendar.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    controller = AppController(settings)
    bridge = CalendarBridge(controller)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)

    qml_file = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        controller.shutdown()
        return 1

    window = engine.rootObjects()[0]
    tray_manager = TrayIconManager(window, bridge.refreshAll)

    # Local references live until app.exec() returns.
    _keep_alive = (engine, bridge, tray_manager, controller)

    bridge.refreshAll()

    exit_code = app.exec()
    controller.shutdown()
    settings.save()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
