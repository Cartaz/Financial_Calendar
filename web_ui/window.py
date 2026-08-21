"""Qt desktop shell hosting the native HTML/CSS/JavaScript frontend."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from web_ui.bridge import CalendarBridge


class CalendarWindow(QMainWindow):
    """Desktop window with a WebEngine renderer and a QWebChannel bridge."""

    def __init__(
        self,
        controller: AppController,
        settings: Settings,
        *,
        debug: bool = False,
        tray_available: bool = False,
    ) -> None:
        super().__init__()
        self.setWindowTitle(AppMeta.DISPLAY_NAME)
        self.resize(1360, 820)
        self.setMinimumSize(820, 560)

        icon_path = PathConfig.ASSETS_DIR / "icons" / "financial-calendar.png"
        if icon_path.exists():
            from PySide6.QtGui import QIcon

            self.setWindowIcon(QIcon(str(icon_path)))

        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCentralWidget(self.view)

        page_settings = self.view.settings()
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            False,
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
            False,
        )

        app = QApplication.instance()
        self.bridge = CalendarBridge(
            controller,
            settings,
            debug=debug,
            tray_available=tray_available,
            hide_callback=self.hide,
            quit_callback=app.quit if app is not None else None,
        )
        self.channel = QWebChannel(self.view.page())
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        frontend = Path(__file__).resolve().parent.parent / "web" / "index.html"
        if not frontend.exists():
            raise RuntimeError(f"Frontend HTML non trovato: {frontend}")
        self.view.setUrl(QUrl.fromLocalFile(str(frontend)))

        self._shortcuts: list[QShortcut] = []
        self._add_shortcut("Ctrl+R", controller.refresh_ig)
        self._add_shortcut("Ctrl+F", controller.refresh_fxstreet)
        if tray_available:
            self._add_shortcut("Ctrl+M", self.hide)
        if app is not None:
            self._add_shortcut("Ctrl+Q", app.quit)

    def _add_shortcut(self, sequence: str, callback) -> None:
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        shortcut.activated.connect(callback)
        self._shortcuts.append(shortcut)
