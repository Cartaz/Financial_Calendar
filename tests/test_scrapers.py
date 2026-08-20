from __future__ import annotations

import requests
import pytest

from core.exceptions import ScraperConnectionError, ScraperParseError
from core import scraper_fxstreet, scraper_ig


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class FailingSession:
    def get(self, *args, **kwargs):
        raise requests.ConnectionError("offline")


class StaticSession:
    def __init__(self, payload):
        self._payload = payload

    def get(self, *args, **kwargs):
        return FakeResponse(self._payload)


def test_forexfactory_network_error_never_returns_demo_data(monkeypatch) -> None:
    monkeypatch.setattr(scraper_ig, "_SESSION", FailingSession())
    with pytest.raises(ScraperConnectionError):
        scraper_ig.scrape_ig_calendar()


def test_fxstreet_network_error_never_returns_demo_data(monkeypatch) -> None:
    monkeypatch.setattr(scraper_fxstreet, "_SESSION", FailingSession())
    with pytest.raises(ScraperConnectionError):
        scraper_fxstreet.scrape_fxstreet_calendar()


def test_forexfactory_zero_valid_events_is_parse_error(monkeypatch) -> None:
    monkeypatch.setattr(
        scraper_ig,
        "_SESSION",
        StaticSession(
            [
                {
                    "date": "2026-08-20T08:30:00-04:00",
                    "country": "USD",
                    "title": "",
                }
            ]
        ),
    )
    with pytest.raises(ScraperParseError):
        scraper_ig.scrape_ig_calendar()


def test_fxstreet_zero_valid_events_is_parse_error(monkeypatch) -> None:
    monkeypatch.setattr(
        scraper_fxstreet,
        "_SESSION",
        StaticSession(
            [
                {
                    "dateUtc": "2026-08-20T12:30:00Z",
                    "countryCode": "US",
                    "name": "",
                    "volatility": "HIGH",
                }
            ]
        ),
    )
    with pytest.raises(ScraperParseError):
        scraper_fxstreet.scrape_fxstreet_calendar()


def test_raw_payload_is_not_persisted_without_debug(monkeypatch) -> None:
    payload = [
        {
            "date": "2026-08-20T08:30:00-04:00",
            "country": "USD",
            "title": "Valid Event",
            "impact": "High",
        }
    ]
    monkeypatch.setattr(scraper_ig, "_SESSION", StaticSession(payload))
    calls = []
    monkeypatch.setattr(
        scraper_ig,
        "save_debug_json",
        lambda data, name: calls.append((data, name)),
    )
    events = scraper_ig.scrape_ig_calendar(debug=False)
    assert events
    assert calls == []
