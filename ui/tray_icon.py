"""Gestore della system tray icon con menu contestuale.

Implementa l'integrazione KDE Plasma: il pulsante X chiude
completamente l'applicazione (conforme §3.5), mentre il clic
sull'icona del tray fa toggle della visibilità. L'uscita
effettiva avviene tramite "Esci" nel menu o Ctrl+Q.
La minimizzazione temporanea è disponibile tramite Ctrl+M.
"""

from __future__ import annotations

import logging

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from config.constants import AppMeta

logger = logging.getLogger(__name__)


class TrayIconManager:
    """Gestore dell'icona nel system tray con menu contestuale KDE.

    Implementa il comportamento KDE standard (conforme §3.5):
    - Pulsante X → chiusura completa (QApplication.quit)
    - Clic sull'icona → toggle visibilità
    - Menu contestuale con azioni principali
    - Uscita tramite "Esci" nel menu o Ctrl+Q
    - Minimizzazione temporanea tramite Ctrl+M

    Args:
        window: Finestra principale dell'applicazione.
    """

    def __init__(self, window: object) -> None:
        """Inizializza il gestore del tray icon.

        Args:
            window: Finestra principale dell'applicazione (QMainWindow).
        """
        self._window = window
        self._tray_icon = QSystemTrayIcon(self._create_icon(), window)
        self._setup_menu()
        self._tray_icon.activated.connect(self._on_activated)
        self._tray_icon.show()

    def _create_icon(self) -> QIcon:
        """Crea l'icona del tray usando il tema di sistema.

        Usa l'icona di sistema 'calendar' come fallback. Se non
        disponibile, usa l'icona predefinita dell'applicazione.

        Returns:
            QIcon per il system tray.
        """
        icon = QIcon.fromTheme("calendar")
        if icon.isNull():
            icon = QIcon.fromTheme("office-calendar")
        if icon.isNull():
            icon = QApplication.windowIcon()
        return icon

    def _setup_menu(self) -> None:
        """Configura il menu contestuale del tray icon."""
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

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Gestisce il clic sull'icona del tray per toggle visibilità.

        Args:
            reason: Motivo dell'attivazione dell'icona.
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._window.isVisible():
                self._window.hide()
            else:
                self._window.show()
                self._window.activateWindow()
                self._window.raise_()

    def _show_window(self) -> None:
        """Mostra e attiva la finestra principale."""
        self._window.show()
        self._window.activateWindow()
        self._window.raise_()

    def _trigger_refresh(self) -> None:
        """Emette il segnale per aggiornare i calendari."""
        if hasattr(self._window, 'load_initial_data'):
            self._window.load_initial_data()

    def show_message(self, title: str, message: str) -> None:
        """Mostra una notifica tramite il system tray.

        Args:
            title: Titolo della notifica.
            message: Corpo del messaggio.
        """
        self._tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
