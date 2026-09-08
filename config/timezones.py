"""One strict timezone contract shared by settings and calendar queries."""

from __future__ import annotations

import os
import re
from datetime import timedelta, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_timezone(value: str) -> tzinfo:
    text = str(value).strip()
    if text == "local":
        name = os.environ.get("TZ", "").removeprefix(":")
        if name:
            try:
                return ZoneInfo(name)
            except (ValueError, ZoneInfoNotFoundError) as exc:
                raise ValueError(f"Fuso locale TZ non valido: {name}") from exc
        try:
            with Path("/etc/localtime").open("rb") as handle:
                return ZoneInfo.from_file(handle, key="local")
        except (OSError, ValueError) as exc:
            raise ValueError(
                "Fuso locale non disponibile; selezionare una zona IANA"
            ) from exc
    if text == "UTC":
        return timezone.utc
    match = re.fullmatch(r"UTC([+-])(\d{2}):(\d{2})", text)
    if match:
        hours, minutes = int(match[2]), int(match[3])
        if hours > 14 or minutes > 59 or (hours == 14 and minutes):
            raise ValueError("Offset UTC fuori intervallo")
        return timezone(
            timedelta(minutes=(hours * 60 + minutes) * (1 if match[1] == "+" else -1))
        )
    try:
        return ZoneInfo(text)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValueError(f"Fuso orario non valido: {text}") from exc


def validate_timezone(value: object) -> str:
    text = str(value).strip() or "local"
    if len(text) > 128 or any(ord(char) < 32 for char in text):
        raise ValueError("Fuso orario non valido")
    if text != "local":
        resolve_timezone(text)
    return text
