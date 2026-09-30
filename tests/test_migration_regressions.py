from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time

import pytest
import requests
from config.settings import Settings
from config.timezones import resolve_timezone
from core.http_client import CalendarHttpClient
from core.http_transport import LimitedRetry
from core.exporters import render_csv, write_export
from core.notification_policy import NotificationPolicy
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.time_utils import try_parse_utc


@pytest.mark.parametrize(
    "zone", ["../Rome", "/Europe/Rome", "UTC+14:01", "UTC+25:00", "no-such-zone"]
)
def test_timezone_validation_rejects_invalid_paths_and_offsets(zone):
    with pytest.raises(ValueError):
        resolve_timezone(zone)


@pytest.mark.parametrize("minutes", [float("inf"), float("nan"), 5.5, True])
def test_settings_reject_non_integral_minutes(minutes):
    with pytest.raises(ValueError):
        Settings().set("auto_refresh_minutes", minutes)


def test_extreme_timestamp_is_tolerant():
    assert try_parse_utc("0001-01-01T00:00:00+14:00") is None
    assert try_parse_utc("9999-12-31T23:59:59-14:00") is None


def test_csv_protects_formulas_and_preserves_economic_numbers():
    text = render_csv(
        [
            dict(
                event_name='=HYPERLINK("bad")',
                actual="-1.2%",
                forecast="+123K",
                previous="@SUM(A1)",
            )
        ]
    )
    assert "'=HYPERLINK" in text
    assert "'@SUM" in text
    assert "-1.2%" in text and "'-1.2%" not in text
    assert "+123K" in text and "'+123K" not in text


def test_ics_reports_only_written_events(tmp_path):
    target = tmp_path / "events.ics"
    assert (
        write_export(
            target,
            "ics",
            [
                {"utc_dt": "invalid"},
                {"utc_dt": "2026-01-01T00:00:00Z", "event_name": "Good"},
            ],
        )
        == 1
    )
    assert target.read_text().count("BEGIN:VEVENT") == 1


def test_notification_failed_delivery_can_retry_and_exact_minutes():
    now = datetime.now(timezone.utc)
    dt = now + timedelta(minutes=5)
    event = CalendarEvent(
        date=dt.strftime("%d/%m/%Y"),
        time=dt.strftime("%H:%M"),
        country="USA",
        impact=ImpactLevel.HIGH,
        event_name="Payrolls",
        actual="",
        forecast="",
        previous="",
        utc_dt=dt.isoformat(),
        source=CalendarSource.FOREXFACTORY,
    )
    policy = NotificationPolicy()
    first = policy.due_events([event], 5, now=now, commit=False)
    assert len(first) == 1 and first[0][2] == 5
    assert policy.due_events([event], 5, now=now, commit=False) == first
    policy.mark_delivered(event)
    assert policy.due_events([event], 5, now=now, commit=False) == []
    policy.due_events([], 5, now=dt + timedelta(seconds=1))
    assert not policy._notified_keys and not policy._notified_events


@pytest.fixture
def server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/slow":
                time.sleep(2)
            self.send_response(200)
            self.end_headers()
            try:
                self.wfile.write(b'{"ok": true}')
            except BrokenPipeError:
                pass

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{http.server_port}"
    http.shutdown()
    http.server_close()
    thread.join()


def test_http_subprocess_preserves_response(server):
    response = CalendarHttpClient().get(server, timeout=(1, 1))
    response.raise_for_status()
    assert response.json() == {"ok": True}


def test_http_deadline_and_cancellation_reap_child(server, monkeypatch):
    from core import http_client

    real_popen = http_client.subprocess.Popen
    children = []

    def start(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(http_client.subprocess, "Popen", start)
    start_time = time.monotonic()
    with pytest.raises(requests.Timeout):
        CalendarHttpClient().get(server + "/slow", timeout=(1, 5), deadline_seconds=0.3)
    assert time.monotonic() - start_time < 1.2
    cancel = threading.Event()
    timer = threading.Timer(0.2, cancel.set)
    timer.start()
    try:
        with pytest.raises(requests.ConnectionError, match="annullata"):
            CalendarHttpClient().get(
                server + "/slow", timeout=(1, 5), cancel_event=cancel
            )
    finally:
        timer.join()
    assert children and all(child.poll() is not None for child in children)


def test_retry_after_is_capped():
    class Response:
        headers = {"Retry-After": "86400"}

    assert LimitedRetry().get_retry_after(Response()) == 2
