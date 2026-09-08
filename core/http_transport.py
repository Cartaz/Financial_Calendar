"""Bounded HTTP subprocess. No Qt, application imports or persistent state."""

from __future__ import annotations

import base64
import json
import sys

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class LimitedRetry(Retry):
    def get_retry_after(self, response):
        delay = super().get_retry_after(response)
        return min(delay, 2.0) if delay is not None else None


def main() -> int:
    options = json.load(sys.stdin)
    url = options.pop("url")
    if isinstance(options.get("timeout"), list):
        options["timeout"] = tuple(options["timeout"])
    session = requests.Session()
    retry = LimitedRetry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods={"GET"},
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    try:
        with session.get(url, stream=True, **options) as response:
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > 8 * 1024 * 1024:
                    raise ValueError("Risposta HTTP troppo grande")
            json.dump(
                {
                    "status": response.status_code,
                    "body": base64.b64encode(data).decode("ascii"),
                    "retries": len(response.raw.retries.history),
                },
                sys.stdout,
            )
        return 0
    except (requests.RequestException, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
