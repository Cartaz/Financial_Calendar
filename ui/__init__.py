"""Modulo UI — interfaccia utente dell'applicazione.

Contiene finestre, widget, stili e componenti di presentazione.
Importa da core/ e config/, ma non da main.py.
"""

from ui.main_window import MainWindow
from ui.tray_icon import TrayIconManager
from ui.timezone_toolbar import TimezoneToolbar

__all__ = [
    "MainWindow",
    "TrayIconManager",
    "TimezoneToolbar",
]
