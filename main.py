"""Punto di ingresso dell'applicazione — orchestratore puro.

Inizializza le dipendenze, configura l'applicazione e avvia il
loop degli eventi Qt. Non contiene logica applicativa.
"""

from __future__ import annotations

import argparse
import logging
import sys

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from ui.main_window import MainWindow
from ui.styles.neumorphism import NeumorphicStyle
from ui.tray_icon import TrayIconManager


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description=AppMeta.DISPLAY_NAME,
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Abilita log dettagliati e salva risposte API per debug",
    )
    return parser.parse_args()


def main() -> int:
    """Funzione principale — orchestra l'avvio dell'applicazione.

    Inizializza nell'ordine:
    1. Directory XDG e impostazioni
    2. QApplication con tema Breeze Dark
    3. Controller e logica di business
    4. Finestra principale e system tray
    5. Scorciatoia globale Ctrl+Q per uscita

    Returns:
        Codice di uscita dell'applicazione (0 = successo).
    """
    args = _parse_args()
    log_level = logging.DEBUG if args.debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    if args.debug:
        logger.info("Modalità DEBUG attivata")

    PathConfig.ensure_dirs()

    settings = Settings()
    settings.load()

    app = QApplication(sys.argv)
    app.setApplicationName(AppMeta.NAME)
    app.setApplicationDisplayName(AppMeta.DISPLAY_NAME)
    app.setApplicationVersion(AppMeta.VERSION)
    app.setQuitOnLastWindowClosed(True)
    # Dice a KDE quale file .desktop corrisponde a questa app.
    app.setDesktopFileName("financial_calendar")
    app.setStyleSheet(NeumorphicStyle.get_stylesheet())

    controller = AppController(settings)

    window = MainWindow(controller)
    # TrayIconManager deve restare referenziato per evitare GC;
    # il parent è la window ma teniamo comunque il riferimento per
    # sicurezza lungo tutto il ciclo di vita dell'app.
    _tray_manager = TrayIconManager(window)

    quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), window)
    quit_shortcut.activated.connect(QApplication.quit)

    window.show()
    window.load_initial_data()

    logger.info("%s v%s avviato", AppMeta.DISPLAY_NAME, AppMeta.VERSION)

    exit_code = app.exec()

    controller.shutdown()
    settings.save()

    logger.info("%s arrestato", AppMeta.DISPLAY_NAME)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
