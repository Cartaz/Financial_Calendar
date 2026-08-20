"""Modulo di configurazione dell'applicazione.

Contiene costanti, tema e impostazioni. È il livello più basso
dell'architettura e non importa da nessun altro modulo dell'app.
"""

from config.theme import ThemeColors
from config.constants import AppMeta, UIConstraints, CalendarDefaults
from config.settings import Settings

__all__ = [
    "ThemeColors",
    "AppMeta",
    "UIConstraints",
    "CalendarDefaults",
    "Settings",
]
