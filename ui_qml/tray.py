"""System-tray integration for the QML frontend."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from config.constants import AppMeta


class TrayIconManager:
    def __init__(
        self,
        window: object,
        refresh_callback: Callable[[], None] | None = None,
    ) -> None:
        self._window = window
        self._refresh_callback = refresh_callback
        self._tray_icon: QSystemTrayIcon | None = None

        if not self.is_available():
            return

        tray = QSystemTrayIcon(self._create_icon())
        self._tray_icon = tray
        self._setup_menu()
        tray.activated.connect(self._on_activated)
        tray.show()

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def _create_icon(self) -> QIcon:
        icon = QIcon.fromTheme("calendar")
        if icon.isNull():
            icon = QIcon.fromTheme("office-calendar")
        if icon.isNull():
            icon = QApplication.windowIcon()
        return icon

    def _setup_menu(self) -> None:
        if self._tray_icon is None:
            return

        menu = QMenu()

        show_action = QAction("Mostra", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        refresh_action = QAction("Aggiorna", menu)
        refresh_action.triggered.connect(self._trigger_refresh)
        menu.addAction(refresh_action)

        menu.addSeparator()
        quit_action = QAction("Esci", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self._tray_icon.setContextMenu(menu)
        self._tray_icon.setToolTip(AppMeta.DISPLAY_NAME)

    def _is_visible(self) -> bool:
        if hasattr(self._window, "isVisible"):
            return bool(self._window.isVisible())
        return bool(getattr(self._window, "visible", False))

    def _show_window(self) -> None:
        if hasattr(self._window, "show"):
            self._window.show()
        else:
            self._window.setProperty("visible", True)

        if hasattr(self._window, "requestActivate"):
            self._window.requestActivate()
        elif hasattr(self._window, "activateWindow"):
            self._window.activateWindow()

        if hasattr(self._window, "raise_"):
            self._window.raise_()

    def _hide_window(self) -> None:
        if not self.is_available():
            return
        if hasattr(self._window, "hide"):
            self._window.hide()
        else:
            self._window.setProperty("visible", False)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._is_visible():
                self._hide_window()
            else:
                self._show_window()

    def _trigger_refresh(self) -> None:
        if self._refresh_callback is not None:
            self._refresh_callback()

    def show_message(self, title: str, message: str) -> None:
        if self._tray_icon is None:
            return
        self._tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )
