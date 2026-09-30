"""Load the real QML shell with isolated settings and no network startup."""

import os
import sys
import tempfile
from pathlib import Path


def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QTimer, qInstallMessageHandler, QtMsgType
    from PySide6.QtQuick import QSGRendererInterface
    from PySide6.QtWidgets import QApplication
    from config.constants import PathConfig
    from config.settings import Settings
    from core.app_controller import AppController
    from ui.window import CalendarWindow

    failures = []

    def message(kind, context, text):
        print(text, flush=True)
        if kind in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ) and ("qml" in text.lower() or context.file and ".qml" in context.file):
            failures.append(text)

    old = qInstallMessageHandler(message)
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        PathConfig.APP_CONFIG_DIR = Path(directory)
        PathConfig.APP_DATA_DIR = Path(directory) / "data"
        PathConfig.SETTINGS_FILE = Path(directory) / "settings.json"
        settings = Settings()
        controller = AppController(settings)
        window = CalendarWindow(controller, settings, autostart=False)
        window.show()

        def verify():
            api = window.root.rendererInterface().graphicsApi()
            print(f"Scene graph: {api.name}")
            if "--require-rhi" in sys.argv and api in (
                QSGRendererInterface.Software,
                QSGRendererInterface.Unknown,
                QSGRendererInterface.Null,
            ):
                failures.append("RHI renderer required")
            app.quit()

        QTimer.singleShot(700, verify)
        app.exec()
        window.shutdown()
        window.engine.deleteLater()
        app.processEvents()
    qInstallMessageHandler(old)
    if failures:
        raise SystemExit("QML load emitted warnings")
    print("QML load: OK")


if __name__ == "__main__":
    main()
