"""Qt desktop shell hosting the HTML/CSS/JavaScript frontend."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from config.constants import AppMeta, PathConfig
from config.settings import Settings
from core.app_controller import AppController
from ui.bridge import CalendarBridge
from ui.runtime import CalendarRuntime

logger = logging.getLogger(__name__)


class LocalOnlyPage(QWebEnginePage):
    """Keep application navigation local and hand external links to the desktop."""

    def acceptNavigationRequest(
        self,
        url: QUrl,
        navigation_type: QWebEnginePage.NavigationType,
        is_main_frame: bool,
    ) -> bool:
        del navigation_type, is_main_frame
        if url.scheme().lower() in {"http", "https"}:
            QDesktopServices.openUrl(url)
            return False
        return url.scheme().lower() in {"", "file", "qrc", "about"}


class CalendarWindow(QMainWindow):
    """Desktop window with a WebEngine renderer and a QWebChannel bridge."""

    def __init__(
        self,
        controller: AppController,
        settings: Settings,
        *,
        debug: bool = False,
    ) -> None:
        super().__init__()
        self._settings = settings
        self.setWindowTitle(AppMeta.DISPLAY_NAME)
        self.resize(1360, 820)
        self.setMinimumSize(820, 560)
        self._restore_window_geometry()

        icon_path = PathConfig.ASSETS_DIR / "icons" / "financial-calendar.png"
        if icon_path.exists():
            from PySide6.QtGui import QIcon

            self.setWindowIcon(QIcon(str(icon_path)))

        self.view = QWebEngineView(self)
        self.page = LocalOnlyPage(self.view)
        self.view.setPage(self.page)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setCentralWidget(self.view)

        page_settings = self.page.settings()
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            False,
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,
            False,
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.NavigateOnDropEnabled,
            False,
        )
        page_settings.setAttribute(
            QWebEngineSettings.WebAttribute.DnsPrefetchEnabled,
            False,
        )
        page_settings.setUnknownUrlSchemePolicy(
            QWebEngineSettings.UnknownUrlSchemePolicy.DisallowUnknownUrlSchemes
        )

        self.runtime = CalendarRuntime(controller, settings)
        self.bridge = CalendarBridge(controller, settings, self.runtime, debug=debug)
        self.channel = QWebChannel(self.page)
        self.channel.registerObject("bridge", self.bridge)
        self.page.setWebChannel(self.channel)

        ui_dir = Path(__file__).resolve().parent
        web_dir = ui_dir / "web"
        frontend = web_dir / "index.html"
        viewport_css = web_dir / "viewport.css"
        if not frontend.exists():
            raise RuntimeError(f"Frontend HTML non trovato: {frontend}")
        if not viewport_css.exists():
            raise RuntimeError(f"CSS viewport non trovato: {viewport_css}")
        self._install_viewport_styles(viewport_css.read_text(encoding="utf-8"))
        self.view.setUrl(QUrl.fromLocalFile(str(frontend)))

        self._shortcuts: list[QShortcut] = []
        self._add_shortcut("Ctrl+R", controller.refresh_ig)
        self._add_shortcut("Ctrl+F", controller.refresh_fxstreet)
        app = QApplication.instance()
        if app is not None:
            self._add_shortcut("Ctrl+Q", app.quit)

    def _restore_window_geometry(self) -> None:
        encoded = str(self._settings.get("window_geometry") or "")
        if not encoded:
            return
        try:
            payload = QByteArray.fromBase64(encoded.encode("ascii"))
        except (UnicodeEncodeError, ValueError):
            logger.warning("Geometria finestra salvata non valida")
            return
        if payload.isEmpty() or not self.restoreGeometry(payload):
            logger.warning("Impossibile ripristinare la geometria finestra salvata")

    def _save_window_geometry(self) -> None:
        encoded = bytes(self.saveGeometry().toBase64()).decode("ascii")
        if not self._settings.set("window_geometry", encoded):
            logger.warning("Impossibile salvare la geometria finestra")

    def _install_viewport_styles(self, css: str) -> None:
        """Inject viewport constraints at document-ready."""
        source = f"""
            (() => {{
                const style = document.createElement('style');
                style.id = 'financial-calendar-viewport';
                style.textContent = {json.dumps(css)};
                document.head.appendChild(style);
            }})();
        """
        script = QWebEngineScript()
        script.setName("financial-calendar-viewport")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(source)
        self.page.scripts().insert(script)

    def _add_shortcut(self, sequence: str, callback) -> None:
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        shortcut.activated.connect(callback)
        self._shortcuts.append(shortcut)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Treat the window close button as an explicit application exit."""
        self._save_window_geometry()
        self.runtime.stop()
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()
