from __future__ import annotations

import logging

from core.scraper_metrics import ScrapeMetrics, response_retry_count


def test_scrape_metrics_logs_counts_origin_and_warning(caplog) -> None:
    metrics = ScrapeMetrics(
        source="TestSource",
        raw_count=10,
        valid_count=7,
        skipped_count=3,
        duration_ms=123,
        retries=2,
        origin="network",
    )

    with caplog.at_level(logging.INFO):
        metrics.log(logging.getLogger("test.metrics"))

    text = caplog.text
    assert "duration_ms=123" in text
    assert "raw=10" in text
    assert "valid=7" in text
    assert "skipped=3" in text
    assert "retries=2" in text
    assert "origin=network" in text
    assert "30.0% degli eventi raw sono stati scartati" in text


def test_discard_warning_requires_minimum_sample(caplog) -> None:
    metrics = ScrapeMetrics(
        source="TinySource",
        raw_count=4,
        valid_count=2,
        skipped_count=2,
        duration_ms=1,
    )

    with caplog.at_level(logging.INFO):
        metrics.log(logging.getLogger("test.metrics.tiny"))

    assert "refresh metrics" in caplog.text
    assert "parser warning" not in caplog.text


def test_response_retry_count_reads_urllib3_history_shape() -> None:
    class Retries:
        history = (object(), object())

    class Raw:
        retries = Retries()

    class Response:
        raw = Raw()

    assert response_retry_count(Response()) == 2
    assert response_retry_count(object()) == 0
