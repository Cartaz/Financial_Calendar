"""Canonical cross-source matching for economic-calendar events."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone

from core.models import CalendarEvent

_DUPLICATE_WINDOW_SECONDS = 15 * 60
_DUPLICATE_DICE_THRESHOLD = 0.72


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_like = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", ascii_like.casefold())).strip()


def _bigram_dice(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if len(left) < 2 or len(right) < 2:
        return 0.0

    counts: dict[str, int] = {}
    for index in range(len(left) - 1):
        pair = left[index : index + 2]
        counts[pair] = counts.get(pair, 0) + 1

    matches = 0
    for index in range(len(right) - 1):
        pair = right[index : index + 2]
        available = counts.get(pair, 0)
        if available > 0:
            matches += 1
            counts[pair] = available - 1

    return (2 * matches) / (len(left) + len(right) - 2)


def events_probably_duplicate(left: CalendarEvent, right: CalendarEvent) -> bool:
    """Return whether two events from different feeds likely describe one release."""
    if left.source == right.source or left.country != right.country:
        return False

    left_dt = _parse_utc(left.utc_dt)
    right_dt = _parse_utc(right.utc_dt)
    if left_dt is None or right_dt is None:
        return False
    if abs((left_dt - right_dt).total_seconds()) > _DUPLICATE_WINDOW_SECONDS:
        return False

    left_name = _normalized_name(left.event_name)
    right_name = _normalized_name(right.event_name)
    if not left_name or not right_name:
        return False
    if left_name == right_name:
        return True

    shorter, longer = sorted((left_name, right_name), key=len)
    if len(shorter) >= 8 and shorter in longer:
        return True
    return _bigram_dice(left_name, right_name) >= _DUPLICATE_DICE_THRESHOLD


def event_identity(event: CalendarEvent) -> tuple[str, str, str, str]:
    """Return a stable in-memory identity used to annotate duplicate groups."""
    return (event.source.value, event.utc_dt, event.country, event.event_name)


def build_duplicate_groups(events: list[CalendarEvent]) -> dict[tuple[str, str, str, str], str]:
    """Group probable cross-source duplicates without dropping any event."""
    if len(events) < 2:
        return {}

    parents = list(range(len(events)))

    def find(index: int) -> int:
        current = index
        while parents[current] != current:
            parents[current] = parents[parents[current]]
            current = parents[current]
        return current

    def unite(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parents[root_right] = root_left

    for left_index, left in enumerate(events):
        for right_index in range(left_index + 1, len(events)):
            if events_probably_duplicate(left, events[right_index]):
                unite(left_index, right_index)

    members: dict[int, list[CalendarEvent]] = {}
    for index, event in enumerate(events):
        members.setdefault(find(index), []).append(event)

    result: dict[tuple[str, str, str, str], str] = {}
    serial = 1
    for group_events in members.values():
        if len(group_events) < 2:
            continue
        group_name = f"D{serial}"
        serial += 1
        for event in group_events:
            result[event_identity(event)] = group_name
    return result
