"""Failure boundaries and GUI ownership found during the desktop audit."""

from datetime import datetime, timedelta, timezone
import threading

import pytest

from config.constants import PathConfig
from config.settings import Settings
from core import app_controller, http_client
from core.cache import CalendarCache
from core.models import CalendarEvent, CalendarSource, ImpactLevel


@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(PathConfig, "APP_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(PathConfig, "APP_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(
        PathConfig, "SETTINGS_FILE", tmp_path / "config" / "settings.json"
    )
    PathConfig.ensure_dirs()


def event():
    dt = datetime.now(timezone.utc) + timedelta(hours=1)
    return CalendarEvent(
        dt.strftime("%H:%M"),
        "USA",
        ImpactLevel.HIGH,
        "Audit event",
        "",
        "",
        "",
        date=dt.strftime("%d/%m/%Y"),
        utc_dt=dt.isoformat(),
    )


def test_fast_refresh_completion_does_not_persist_on_caller_thread(
    isolated_paths, monkeypatch
):
    caller = threading.get_ident()
    saved_on = []
    monkeypatch.setattr(
        app_controller, "scrape_ig_calendar", lambda **kwargs: [event()]
    )
    controller = app_controller.AppController(Settings())
    real_submit = controller._executor.submit

    def already_completed(*args, **kwargs):
        future = real_submit(*args, **kwargs)
        future.result(timeout=2)
        return future

    monkeypatch.setattr(controller._executor, "submit", already_completed)
    monkeypatch.setattr(
        controller._cache,
        "save",
        lambda *args: saved_on.append(threading.get_ident()) or True,
    )
    try:
        controller.refresh_ig()
        assert saved_on and caller not in saved_on
        assert not controller.is_refreshing(CalendarSource.FOREXFACTORY)
    finally:
        controller.shutdown()


def test_cache_save_rejects_timestamp_overflow(isolated_paths):
    assert (
        CalendarCache().save(
            CalendarSource.FOREXFACTORY, [event()], "0001-01-01T00:00:00+14:00"
        )
        is False
    )


def test_unserializable_http_options_do_not_launch_child(monkeypatch):
    launches = []
    monkeypatch.setattr(
        http_client.subprocess, "Popen", lambda *args, **kwargs: launches.append(args)
    )
    with pytest.raises(TypeError):
        http_client.CalendarHttpClient().get(
            "https://example.org", params={"bad": object()}
        )
    assert not launches


@pytest.mark.parametrize("target", ["settings", "cache"])
def test_excessively_nested_json_is_rejected_without_startup_crash(
    isolated_paths, target
):
    if target == "settings":
        path = PathConfig.SETTINGS_FILE
        read = Settings().load
    else:
        path = PathConfig.APP_DATA_DIR / "calendar_ig.json"

        def read():
            return CalendarCache().load(CalendarSource.FOREXFACTORY)

    path.write_text("[" * 20000 + "]" * 20000, encoding="utf-8")
    assert read() is None
