"""Financial Calendar desktop entry point with an HTML/CSS/JavaScript UI."""

from __future__ import annotations

import argparse
import logging
import sys

from PySide6.QtWidgets import QApplication

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from web_ui.bridge import WebLogHandler
from web_ui.tray import TrayIconManager
from web_ui.window import CalendarWindow


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

    controller = AppController(settings, debug=args.debug)
    app.aboutToQuit.connect(controller.begin_shutdown)

    tray_available = TrayIconManager.is_available()
    try:
        window = CalendarWindow(
            controller,
            settings,
            debug=args.debug,
            tray_available=tray_available,
        )
    except Exception:
        logging.getLogger(__name__).exception("Impossibile inizializzare la UI web")
        controller.shutdown()
        settings.save()
        return 1

    web_log_handler = WebLogHandler(window.bridge)
    web_log_handler.setLevel(logging.DEBUG if args.debug else logging.INFO)
    web_log_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    logging.getLogger().addHandler(web_log_handler)

    tray_manager = (
        TrayIconManager(window, controller.refresh_all)
        if tray_available
        else None
    )

    window.show()
    exit_code = app.exec()

    logging.getLogger().removeHandler(web_log_handler)
    controller.shutdown()
    settings.save()

    if tray_manager is not None:
        del tray_manager
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
