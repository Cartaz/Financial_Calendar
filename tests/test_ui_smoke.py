from __future__ import annotations

import json

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

    runtime: list[dict] = []
    runtime_loop = QEventLoop()

    def on_runtime(value) -> None:
        if isinstance(value, str):
            runtime.append(json.loads(value))
        else:
            runtime.append({"probe_error": f"unexpected callback: {value!r}"})
        runtime_loop.quit()

    window.view.page().runJavaScript(
        """
        JSON.stringify((() => {
          try {
            return {
              search: Boolean(document.getElementById('event-search')),
              quickButtons: document.querySelectorAll('[data-quick-range]').length,
              navigationState: typeof state !== 'undefined' && Boolean(state.navigation),
              navigationFunction: typeof navigationFilteredEvents === 'function',
              fixedOffsetDate: isoDateInTimezone(
                new Date('2026-03-29T23:30:00Z'),
                'UTC+02:00'
              ),
              nextDay: addCalendarDays('2026-03-29', 1),
              countdown: formatCountdown(90 * 60 * 1000),
            };
          } catch (error) {
            return { probe_error: String(error) };
          }
        })())
        """,
        on_runtime,
    )
    QTimer.singleShot(4000, runtime_loop.quit)
    runtime_loop.exec()

    try:
        assert loaded and loaded[-1] is True
        assert window.bridge.getInitialState()["app"]["name"] == "Calendario Finanziario"
        assert runtime
        assert "probe_error" not in runtime[-1], runtime[-1].get("probe_error")
        assert runtime[-1]["search"] is True
        assert runtime[-1]["quickButtons"] == 4
        assert runtime[-1]["navigationState"] is True
        assert runtime[-1]["navigationFunction"] is True
        assert runtime[-1]["fixedOffsetDate"] == "2026-03-30"
        assert runtime[-1]["nextDay"] == "2026-03-30"
        assert runtime[-1]["countdown"] == "tra 1 h 30 min"
    finally:
        window.close()
        app.processEvents()
        controller.shutdown()
