"""Desktop web frontend integration for Financial Calendar."""

from web_ui.bridge import CalendarBridge, WebLogHandler
from web_ui.tray import TrayIconManager
from web_ui.window import CalendarWindow

__all__ = ["CalendarBridge", "CalendarWindow", "TrayIconManager", "WebLogHandler"]
