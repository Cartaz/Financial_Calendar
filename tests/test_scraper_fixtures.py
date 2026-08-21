from __future__ import annotations

import json
from pathlib import Path

from core import scraper_fxstreet, scraper_ig
from core.models import CalendarSource, ImpactLevel


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str):
    with open(FIXTURES / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_forexfactory_production_fixture_preserves_parser_contract() -> None:
    payload = _load("forexfactory_api_anonymized.json")
    events = scraper_ig._parse_ff_events(payload)

    assert len(events) == len(payload) == 5
    assert events[0].source == CalendarSource.FOREXFACTORY
    assert events[0].country == "USA"
    assert events[0].impact == ImpactLevel.HIGH
    assert events[0].time == "12:30"
    assert events[0].date == "12/08/2026"
    assert events[0].utc_dt == "2026-08-12T12:30:00+00:00"
    assert events[2].country == "AUD"
    assert events[3].country == "JPN"


def test_fxstreet_production_fixture_preserves_parser_contract() -> None:
    payload = _load("fxstreet_api_anonymized.json")
    events = scraper_fxstreet._parse_api_events(payload)

    assert len(events) == len(payload) == 3
    assert events[0].source == CalendarSource.FXSTREET
    assert events[0].country == "CHF"
    assert events[0].impact == ImpactLevel.MID
    assert events[0].actual == "-0.1%"
    assert events[0].forecast == "-0.2%"
    assert events[0].previous == "0.1%"
    assert events[0].deviation == "0.44543"
    assert events[1].impact == ImpactLevel.HIGH
    assert events[2].country == "EUR"
    assert events[2].forecast == ""
