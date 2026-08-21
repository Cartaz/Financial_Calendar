from __future__ import annotations

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from config.constants import PathConfig
from config.settings import Settings
from core.app_controller import AppController
from ui.window import CalendarWindow


def _redirect_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "settings.json")


def test_webengine_frontend_loads_offscreen(monkeypatch, tmp_path) -> None:
    _redirect_paths(monkeypatch, tmp_path)
    app = QApplication.instance() or QApplication([])
    settings = Settings()
    controller = AppController(settings)
    monkeypatch.setattr(controller, "refresh_all", lambda: None)

    window = CalendarWindow(controller, settings)
    loaded: list[bool] = []
    loop = QEventLoop()

    def on_loaded(ok: bool) -> None:
        loaded.append(ok)
        loop.quit()

    window.view.loadFinished.connect(on_loaded)
    QTimer.singleShot(8000, loop.quit)
    window.view.reload()
    loop.exec()

    try:
        assert loaded and loaded[-1] is True
        assert window.bridge.getInitialState()["app"]["name"] == "Calendario Finanziario"
    finally:
        window.close()
        app.processEvents()
        controller.shutdown()
