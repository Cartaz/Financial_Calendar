"""Date parser for the legacy ``ig`` source key (ForexFactory feed)."""

from __future__ import annotations

from core.time_utils import normalize_iso_to_utc


def parse_ig_date(date_str: str) -> tuple[str, str, str]:
    """Return the event timestamp normalized to UTC.

    The public ForexFactory/Faireconomy feed normally includes explicit
    offsets (for example ``-04:00``).  Those offsets are converted to UTC
    here, so every downstream consumer sees the same time basis.
    """
    dt_utc = normalize_iso_to_utc(date_str, "ForexFactory date")
    return (
        dt_utc.strftime("%H:%M"),
        dt_utc.strftime("%d/%m/%Y"),
        dt_utc.isoformat(),
    )
