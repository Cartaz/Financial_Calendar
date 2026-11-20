"""Financial Calendar desktop entry point with a native QML UI."""

from __future__ import annotations

import argparse
import logging
import signal
import socket
import sys
from typing import Callable

from PySide6.QtCore import QSocketNotifier
from PySide6.QtWidgets import QApplication

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from ui.window import CalendarWindow


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=AppMeta.DISPLAY_NAME)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def _quit_on_termination_signals(app: QApplication) -> Callable[[], None]:
    """Turn SIGTERM/SIGINT into a normal Qt quit so shutdown runs in order.

    Python only runs signal handlers between bytecodes, which never happens
    while Qt's C++ event loop is idle. The wakeup socket makes the loop notice.
    Returns a function that restores the default handlers once the loop ends.
    """
    receiver, sender = socket.socketpair()
    receiver.setblocking(False)
    sender.setblocking(False)
    signal.set_wakeup_fd(sender.fileno())
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: None)

    def restore_default_signals() -> None:
        # Once the loop is quitting nothing reads the socket any more: a
        # further signal must terminate as usual, e.g. if shutdown hangs.
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, signal.SIG_DFL)
        signal.set_wakeup_fd(-1)

    notifier = QSocketNotifier(receiver.fileno(), QSocketNotifier.Type.Read, app)

    def on_signal() -> None:
        try:
            received = receiver.recv(64)
        except BlockingIOError:
            return
        if received:
            logging.getLogger(__name__).info("Segnale di chiusura ricevuto")
            app.quit()

    notifier.activated.connect(on_signal)
    app._signal_sockets = (receiver, sender)  # keep the pair alive with the app
    return restore_default_signals


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
    restore_default_signals = _quit_on_termination_signals(app)

    controller = AppController(debug=args.debug)
    app.aboutToQuit.connect(controller.begin_shutdown)

    try:
        window = CalendarWindow(controller, settings, debug=args.debug)
    except Exception:
        restore_default_signals()
        logging.getLogger(__name__).exception("Impossibile inizializzare la UI")
        controller.shutdown()
        settings.save()
        return 1

    window.show()
    try:
        return app.exec()
    finally:
        restore_default_signals()
        window.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
