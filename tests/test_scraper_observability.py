from __future__ import annotations

import json
import logging
from pathlib import Path

from core import scraper_fxstreet, scraper_ig


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class _Retries:
    history = (object(), object())


class _Raw:
    retries = _Retries()


class _Response:
    status_code = 200
    raw = _Raw()

    def __init__(self, payload) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class _Session:
    def __init__(self, payload) -> None:
        self._payload = payload

    def get(self, *args, **kwargs):
        return _Response(self._payload)


def _load(name: str):
    with open(FIXTURES / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_forexfactory_refresh_logs_complete_metrics(monkeypatch, caplog) -> None:
    payload = _load("forexfactory_api_anonymized.json")
    monkeypatch.setattr(scraper_ig, "_SESSION", _Session(payload))

    with caplog.at_level(logging.INFO, logger=scraper_ig.__name__):
        events = scraper_ig.scrape_ig_calendar()

    assert len(events) == 5
    text = caplog.text
    assert "ForexFactory refresh metrics:" in text
    assert "raw=5" in text
    assert "valid=5" in text
    assert "skipped=0" in text
    assert "retries=2" in text
    assert "origin=network" in text


def test_fxstreet_refresh_logs_complete_metrics(monkeypatch, caplog) -> None:
    payload = _load("fxstreet_api_anonymized.json")
    monkeypatch.setattr(scraper_fxstreet, "_SESSION", _Session(payload))

    with caplog.at_level(logging.INFO, logger=scraper_fxstreet.__name__):
        events = scraper_fxstreet.scrape_fxstreet_calendar()

    assert len(events) == 3
    text = caplog.text
    assert "FXStreet refresh metrics:" in text
    assert "raw=3" in text
    assert "valid=3" in text
    assert "skipped=0" in text
    assert "retries=2" in text
    assert "origin=network" in text
