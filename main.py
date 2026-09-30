"""Financial Calendar desktop entry point with a native QML UI."""

from __future__ import annotations

import argparse
import logging
import sys

from PySide6.QtWidgets import QApplication

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from ui.window import CalendarWindow


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

    app = QApplication([sys.argv[0]])
    app.setApplicationName(AppMeta.NAME)
    app.setApplicationDisplayName(AppMeta.DISPLAY_NAME)
    app.setApplicationVersion(AppMeta.VERSION)
    app.setDesktopFileName("financial_calendar")
    app.setQuitOnLastWindowClosed(True)

    controller = AppController(settings, debug=args.debug)
    app.aboutToQuit.connect(controller.begin_shutdown)

    try:
        window = CalendarWindow(controller, settings, debug=args.debug)
    except Exception:
        logging.getLogger(__name__).exception("Impossibile inizializzare la UI")
        controller.shutdown()
        settings.save()
        return 1

    window.show()
    try:
        return app.exec()
    finally:
        window.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
