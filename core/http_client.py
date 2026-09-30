"""HTTP with a wall-clock deadline and deterministic cancellation/reaping."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import requests


class CalendarHttpClient:
    def get(
        self,
        url: str,
        *,
        cancel_event: threading.Event | None = None,
        deadline_seconds: float = 35,
        **options,
    ) -> requests.Response:
        if cancel_event is not None and cancel_event.is_set():
            raise requests.ConnectionError("Richiesta annullata")
        # Validate the request before starting a child that waits on stdin.
        data = json.dumps({"url": url, **options}).encode()
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("http_transport.py"))],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + deadline_seconds
        try:
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    raise requests.ConnectionError("Richiesta annullata")
                if time.monotonic() >= deadline:
                    raise requests.Timeout("Scadenza totale HTTP superata")
                try:
                    stdout, stderr = process.communicate(input=data, timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    data = None
            if process.returncode:
                raise requests.ConnectionError(stderr.decode(errors="replace").strip())
            payload = json.loads(stdout)
            response = requests.Response()
            response.status_code = payload["status"]
            response._content = base64.b64decode(payload["body"])
            response.url = url
            response.raw = SimpleNamespace(
                retries=SimpleNamespace(history=(None,) * payload["retries"])
            )
            return response
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate()


def build_retry_session() -> CalendarHttpClient:
    return CalendarHttpClient()
