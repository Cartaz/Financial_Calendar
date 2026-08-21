"""Shared observability helpers for calendar scrapers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import monotonic
from typing import Any


DISCARD_WARNING_RATIO = 0.20
DISCARD_WARNING_MIN_RAW = 5


@dataclass(frozen=True, slots=True)
class ScrapeMetrics:
    """Metrics for one source refresh/parsing pass."""

    source: str
    raw_count: int
    valid_count: int
    skipped_count: int
    duration_ms: int
    retries: int = 0
    origin: str = "network"

    @property
    def discard_ratio(self) -> float:
        if self.raw_count <= 0:
            return 0.0
        return self.skipped_count / self.raw_count

    def log(self, target: logging.Logger) -> None:
        target.info(
            "%s refresh metrics: duration_ms=%d raw=%d valid=%d skipped=%d "
            "retries=%d origin=%s discard_pct=%.1f",
            self.source,
            self.duration_ms,
            self.raw_count,
            self.valid_count,
            self.skipped_count,
            self.retries,
            self.origin,
            self.discard_ratio * 100.0,
        )
        if (
            self.raw_count >= DISCARD_WARNING_MIN_RAW
            and self.discard_ratio >= DISCARD_WARNING_RATIO
        ):
            target.warning(
                "%s parser warning: %.1f%% degli eventi raw sono stati scartati "
                "(%d/%d; soglia %.0f%%)",
                self.source,
                self.discard_ratio * 100.0,
                self.skipped_count,
                self.raw_count,
                DISCARD_WARNING_RATIO * 100.0,
            )


class RefreshTimer:
    """Monotonic timer used to keep scraper timing deterministic and testable."""

    def __init__(self) -> None:
        self._started = monotonic()

    def elapsed_ms(self) -> int:
        return max(0, round((monotonic() - self._started) * 1000))


def response_retry_count(response: Any) -> int:
    """Return urllib3 retry-history length when requests exposes it."""
    raw = getattr(response, "raw", None)
    retries = getattr(raw, "retries", None)
    history = getattr(retries, "history", ())
    try:
        return len(history or ())
    except TypeError:
        return 0
