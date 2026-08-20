"""Semantic sorting helpers for the QML calendar table models."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Callable

from core.models import CalendarEvent, ImpactLevel


def extract_numeric_sort_key(text: str) -> float | str:
    if not text:
        return float("inf")

    cleaned = text.strip().replace(",", ".")
    multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    for suffix, mult in multipliers.items():
        if cleaned.upper().endswith(suffix):
            try:
                return float(cleaned[:-1].rstrip()) * mult
            except ValueError:
                break

    match = re.match(r"^([+-]?[\d.]+)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return text


def date_sort_key(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y%m%d")
    except ValueError:
        return date_str


def impact_sort_key(impact: ImpactLevel) -> int:
    return {ImpactLevel.HIGH: 3, ImpactLevel.MID: 2, ImpactLevel.LOW: 1}.get(impact, 0)


_SORT_KEY_MAP: dict[str, dict[int, Callable[[str, CalendarEvent], object]]] = {
    "ig": {
        0: lambda value, _ev: date_sort_key(value),
        3: lambda _value, ev: impact_sort_key(ev.impact),
        4: lambda value, _ev: value.lower(),
    },
    "fxstreet": {
        0: lambda value, _ev: date_sort_key(value),
        3: lambda value, _ev: value.lower(),
        4: lambda _value, ev: impact_sort_key(ev.impact),
    },
}


def compute_sort_key(
    source_type: str, col_idx: int, value: str, event: CalendarEvent
) -> object:
    source_map = _SORT_KEY_MAP.get(source_type, {})
    key_fn = source_map.get(col_idx)
    if key_fn is not None:
        return key_fn(value, event)
    if col_idx in (1, 2):
        return value
    return extract_numeric_sort_key(value)
