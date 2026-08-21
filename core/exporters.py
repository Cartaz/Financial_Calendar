"""Pure export helpers for filtered economic-calendar events."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


CSV_COLUMNS = [
    "source",
    "date",
    "time",
    "country",
    "impact",
    "event_name",
    "actual",
    "forecast",
    "previous",
    "deviation",
    "utc_dt",
    "duplicate_group",
]


def _text(value: object) -> str:
    return "" if value is None else str(value)


def render_csv(events: Iterable[Mapping[str, object]]) -> str:
    """Render events as a UTF-8 CSV document."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for event in events:
        writer.writerow({key: _text(event.get(key, "")) for key in CSV_COLUMNS})
    return output.getvalue()


def _parse_utc(value: object) -> datetime | None:
    text = _text(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _ics_escape(value: object) -> str:
    text = _text(value)
    return (
        text.replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _fold_ics_line(line: str) -> list[str]:
    """Fold an iCalendar content line without splitting UTF-8 code points."""
    if len(line.encode("utf-8")) <= 75:
        return [line]

    folded: list[str] = []
    current = ""
    limit = 75
    for char in line:
        candidate = current + char
        if current and len(candidate.encode("utf-8")) > limit:
            folded.append(current)
            current = " " + char
            limit = 75
        else:
            current = candidate
    if current:
        folded.append(current)
    return folded


def _event_uid(event: Mapping[str, object], dt_utc: datetime) -> str:
    stable = "|".join(
        [
            _text(event.get("source")),
            dt_utc.isoformat(),
            _text(event.get("country")),
            _text(event.get("event_name")),
        ]
    )
    digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32]
    return f"{digest}@financial-calendar"


def render_ics(
    events: Iterable[Mapping[str, object]],
    *,
    generated_at: datetime | None = None,
) -> str:
    """Render timestamped events as an RFC 5545 compatible calendar."""
    stamp = generated_at or datetime.now(timezone.utc)
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    stamp = stamp.astimezone(timezone.utc)
    stamp_text = stamp.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Financial Calendar//Cartaz//IT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for event in events:
        dt_utc = _parse_utc(event.get("utc_dt"))
        if dt_utc is None:
            continue

        title = _text(event.get("event_name")) or "Evento economico"
        country = _text(event.get("country"))
        impact = _text(event.get("impact"))
        source = _text(event.get("source"))
        description_parts = [part for part in [country, impact, source] if part]
        description = " · ".join(description_parts)

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_event_uid(event, dt_utc)}",
                f"DTSTAMP:{stamp_text}",
                f"DTSTART:{dt_utc.strftime('%Y%m%dT%H%M%SZ')}",
                "DURATION:PT15M",
                f"SUMMARY:{_ics_escape(title)}",
                f"DESCRIPTION:{_ics_escape(description)}",
            ]
        )
        duplicate_group = _text(event.get("duplicate_group"))
        if duplicate_group:
            lines.append(f"X-FINANCIAL-CALENDAR-DUPLICATE-GROUP:{_ics_escape(duplicate_group)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    folded = [part for line in lines for part in _fold_ics_line(line)]
    return "\r\n".join(folded) + "\r\n"


def write_export(
    path: str | Path,
    export_format: str,
    events: Iterable[Mapping[str, object]],
) -> int:
    """Atomically write an export and return the number of supplied events."""
    event_list = [dict(event) for event in events]
    export_format = export_format.lower().strip()
    if export_format == "csv":
        content = render_csv(event_list)
    elif export_format == "ics":
        content = render_ics(event_list)
    else:
        raise ValueError(f"Formato export non supportato: {export_format}")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, destination)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
    return len(event_list)
