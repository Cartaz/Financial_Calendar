"""Configuration package for Financial Calendar.

The QML presentation theme lives in ``qml/Theme.js``. This package only
exports application metadata, constants, paths and persisted settings.
"""

from config.constants import AppMeta, CalendarDefaults, PathConfig
from config.settings import Settings

__all__ = [
    "AppMeta",
    "CalendarDefaults",
    "PathConfig",
    "Settings",
]
