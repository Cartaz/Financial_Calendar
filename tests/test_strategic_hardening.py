from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWidgets import QApplication

from config.constants import PathConfig
from config.settings import Settings
from core import scraper_fxstreet, scraper_ig
from core.scraper_utils import save_debug_json
from core.time_utils import try_parse_utc
from ui.runtime import CalendarRuntime
from ui.window import CalendarWindow, LocalOnlyPage


class FakeController:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def refresh_all(self) -> None:
        self.refresh_calls += 1

    def filter_events(self, *args, **kwargs):
        return []


class FakeNotifier:
    def notify(self, title: str, body: str) -> bool:
        return True


def test_try_parse_utc_is_tolerant_and_normalizes_offsets() -> None:
    parsed = try_parse_utc("2026-08-20T08:30:00-04:00")
    assert parsed is not None
    assert parsed.isoformat() == "2026-08-20T12:30:00+00:00"
    assert parsed.utcoffset() == timedelta(0)
    assert try_parse_utc("2026-08-20T12:30:00") is None
    assert try_parse_utc("not-a-date") is None
    assert try_parse_utc("") is None


def test_debug_json_uses_canonical_application_data_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "canonical-data")

    save_debug_json({"ok": True}, "sample")

    output = PathConfig.APP_DATA_DIR / "debug" / "sample.json"
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": True}


def test_scraper_parsers_skip_bad_records_but_surface_internal_bugs(monkeypatch) -> None:
    assert scraper_ig._parse_ff_events([None, {}]) == []
    assert scraper_fxstreet._parse_api_events([None, {}]) == []

    def broken_clean_string(value):
        raise RuntimeError("programming bug")

    monkeypatch.setattr(scraper_ig, "clean_string", broken_clean_string)
    with pytest.raises(RuntimeError, match="programming bug"):
        scraper_ig._parse_ff_events(
            [{"date": "2026-08-20T08:30:00-04:00", "title": "Event"}]
        )

    monkeypatch.setattr(scraper_fxstreet, "clean_string", broken_clean_string)
    with pytest.raises(RuntimeError, match="programming bug"):
        scraper_fxstreet._parse_api_events(
            [
                {
                    "dateUtc": "2026-08-20T12:30:00Z",
                    "countryCode": "US",
                    "name": "Event",
                    "volatility": "HIGH",
                }
            ]
        )


def test_runtime_stop_is_idempotent_and_stops_owned_timers() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    settings = Settings()
    controller = FakeController()
    runtime = CalendarRuntime(controller, settings, notifier=FakeNotifier())

    runtime.start()
    assert runtime.started is True
    assert runtime.auto_refresh_timer.isActive()
    assert controller.refresh_calls == 1

    runtime.stop()
    runtime.stop()

    assert runtime.started is False
    assert not runtime.auto_refresh_timer.isActive()
    assert not runtime.notification_timer.isActive()


def test_webengine_navigation_and_settings_are_deny_by_default(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(PathConfig, "SETTINGS_FILE", tmp_path / "config" / "settings.json")

    app = QApplication.instance() or QApplication([])
    assert app is not None

    page = LocalOnlyPage()
    navigation_type = QWebEnginePage.NavigationType.NavigationTypeOther
    assert page.acceptNavigationRequest(QUrl("file:///tmp/example.html"), navigation_type, True)
    assert page.acceptNavigationRequest(QUrl("qrc:///qtwebchannel/qwebchannel.js"), navigation_type, True)
    assert not page.acceptNavigationRequest(QUrl("data:text/html,test"), navigation_type, True)
    assert not page.acceptNavigationRequest(QUrl("custom-scheme:payload"), navigation_type, True)
    page.deleteLater()

    from core.app_controller import AppController

    settings = Settings()
    controller = AppController(settings)
    window = CalendarWindow(controller, settings)
    try:
        web_settings = window.page.settings()
        assert not web_settings.testAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls
        )
        assert not web_settings.testAttribute(
            QWebEngineSettings.WebAttribute.NavigateOnDropEnabled
        )
        assert not web_settings.testAttribute(
            QWebEngineSettings.WebAttribute.DnsPrefetchEnabled
        )
        assert web_settings.unknownUrlSchemePolicy() == (
            QWebEngineSettings.UnknownUrlSchemePolicy.DisallowUnknownUrlSchemes
        )
    finally:
        window.close()
        app.processEvents()
        controller.shutdown()


def test_release_publish_is_gated_by_ci_and_has_no_branch_cleanup() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "  publish:\n" in workflow
    assert "    needs: test\n" in workflow
    assert "github.event_name == 'push'" in workflow
    assert "gh release create" in workflow
    assert "Deleting merged branch" not in workflow
    assert not (root / ".github" / "workflows" / "publish-release.yml").exists()
