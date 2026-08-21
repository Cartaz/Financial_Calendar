"""System tray integration for the desktop web frontend."""

from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from config.constants import AppMeta, PathConfig


class TrayIconManager:
    """Own the optional system tray icon and its menu for the app lifetime."""

    def __init__(
        self,
        window: QWidget,
        refresh_callback: Callable[[], None],
    ) -> None:
        self._window = window
        self._tray = QSystemTrayIcon(window)

        icon_path = PathConfig.ASSETS_DIR / "icons" / "financial-calendar.png"
        if icon_path.exists():
            self._tray.setIcon(QIcon(str(icon_path)))
        else:
            self._tray.setIcon(window.windowIcon())
        self._tray.setToolTip(AppMeta.DISPLAY_NAME)

        menu = QMenu(window)
        show_action = QAction("Mostra finestra", menu)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)

        refresh_action = QAction("Aggiorna tutti i calendari", menu)
        refresh_action.triggered.connect(refresh_callback)
        menu.addAction(refresh_action)

        menu.addSeparator()
        quit_action = QAction("Esci", menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        self._menu = menu
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.show_window()
