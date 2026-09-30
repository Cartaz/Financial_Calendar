"""Canonical view queries shared by presentation and export, independent of Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import re

from config.constants import CalendarDefaults
from config.timezones import resolve_timezone
from core.calendar_queries import CalendarQueryService
from core.event_matching import build_duplicate_groups, event_identity
from core.models import CalendarSource
from core.time_utils import try_parse_utc

SOURCES = {"ig": "ForexFactory", "fxstreet": "FXStreet", "combined": "Tutti"}
COLUMNS = {
    "ig": (
        "date",
        "time",
        "country",
        "impact",
        "event_name",
        "actual",
        "forecast",
        "previous",
    ),
    "fxstreet": (
        "date",
        "time",
        "country",
        "event_name",
        "impact",
        "actual",
        "deviation",
        "forecast",
        "previous",
    ),
    "combined": (
        "date",
        "time",
        "country",
        "impact",
        "event_name",
        "source",
        "actual",
        "forecast",
        "previous",
        "deviation",
    ),
}
LABELS = dict(
    zip(
        COLUMNS["combined"],
        (
            "Data",
            "Ora",
            "Paese",
            "Impatto",
            "Evento",
            "Sorgente",
            "Attuale",
            "Previsione",
            "Precedente",
            "Dev",
        ),
        strict=True,
    )
)


@dataclass(frozen=True)
class CalendarView:
    rows: tuple[dict, ...]
    columns: tuple[str, ...]
    state: dict
    sources: tuple[dict, ...]
    summary: str
    status: str
    error: str


def countdown(seconds: float) -> str:
    if seconds <= 0:
        return ""
    minutes = math.ceil(seconds / 60)
    if minutes < 60:
        return f"tra {minutes} min"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"tra {hours} h" + (f" {minutes} min" if minutes else "")
    days, hours = divmod(hours, 24)
    return f"tra {days} g" + (f" {hours} h" if hours else "")


def _natural(value: str):
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.split(r"(\d+)", value)
    )


class CalendarViewService:
    """Single owner of session query state; Settings owns persisted preferences.

    Methods are serialized by the UI worker. Returned views are read-only snapshots.
    """

    def __init__(self, controller, settings):
        self.controller = controller
        self.settings = settings
        self.queries = CalendarQueryService(controller)
        self.search = ""
        self.quick_range = "manual" if settings.get("selected_date") else "all"
        self._matching_events = None
        self._matching_groups = {}

    def change(self, key: str, value, *, source: str = "") -> CalendarView:
        if key == "search":
            self.search = str(value)[:1000]
        elif key == "range":
            if value not in {"all", "today", "tomorrow", "next24"}:
                raise ValueError("Intervallo non valido")
            if not self.settings.set("selected_date", ""):
                raise OSError("Impossibile salvare la data")
            self.quick_range = value
        else:
            if key in {"region", "impact", "column_order", "sort"}:
                if source not in SOURCES:
                    raise ValueError("Sorgente non valida")
                if key == "sort":
                    if value not in COLUMNS[source]:
                        raise ValueError("Colonna non valida")
                    direction = (
                        "desc"
                        if self.settings.get(f"{source}_sort_key") == value
                        and self.settings.get(f"{source}_sort_direction") == "asc"
                        else "asc"
                    )
                    values = {
                        f"{source}_sort_key": value,
                        f"{source}_sort_direction": direction,
                    }
                else:
                    suffix = {
                        "region": "selected_region",
                        "impact": "selected_impact",
                        "column_order": "column_order",
                    }[key]
                    if key == "region" and value not in CalendarDefaults.REGIONS:
                        raise ValueError("Area non valida")
                    if key == "impact" and value not in {
                        "ALL",
                        *CalendarDefaults.IMPACT_LEVELS,
                    }:
                        raise ValueError("Impatto non valido")
                    values = {f"{source}_{suffix}": value}
            elif key in {
                "active_source",
                "timezone_name",
                "selected_date",
                "auto_refresh_minutes",
                "high_notification_minutes",
                "window_geometry",
            }:
                if key == "active_source" and value not in SOURCES:
                    raise ValueError("Sorgente non valida")
                values = {key: value}
            else:
                raise ValueError("Preferenza non valida")
            if not self.settings.set_many(values):
                raise OSError(
                    "Impossibile salvare la modifica; valore precedente conservato"
                )
            if key == "selected_date":
                self.quick_range = "manual" if value else "all"
        return self.snapshot()

    def set_column_positions(self, source: str, positions: list[int]) -> CalendarView:
        order = self.settings.get(f"{source}_column_order")
        if any(type(i) is not int for i in positions) or sorted(positions) != list(
            range(len(order))
        ):
            raise ValueError("Ordine colonne non valido")
        return self.change("column_order", [order[i] for i in positions], source=source)

    def move_column(self, source: str, old: int, new: int) -> CalendarView:
        if source not in SOURCES:
            raise ValueError("Sorgente non valida")
        order = self.settings.get(f"{source}_column_order")
        if not 0 <= old < len(order) or not 0 <= new < len(order):
            raise ValueError("Posizione colonna non valida")
        order.insert(new, order.pop(old))
        return self.change("column_order", order, source=source)

    def snapshot(self, *, now: datetime | None = None) -> CalendarView:
        now = now or datetime.now(timezone.utc)
        active = self.settings.get("active_source")
        zone_name = self.settings.get("timezone_name")
        zone = resolve_timezone(zone_name)
        date = self.settings.get("selected_date")
        if self.quick_range in {"today", "tomorrow"}:
            date = (
                now.astimezone(zone).date()
                + timedelta(days=self.quick_range == "tomorrow")
            ).isoformat()
        region = self.settings.get(f"{active}_selected_region")
        impact = self.settings.get(f"{active}_selected_impact")
        sources = tuple(
            CalendarSource(key)
            for key in ("ig", "fxstreet")
            if active == "combined" or key == active
        )
        events = self.queries.query(
            sources,
            region=region,
            impact=impact,
            date=datetime.fromisoformat(date).strftime("%d/%m/%Y") if date else "",
            timezone_name=zone_name,
        )
        if active == "combined":
            match_events = tuple(events)
            if self._matching_events != match_events:
                self._matching_groups = build_duplicate_groups(events)
                self._matching_events = match_events
            groups = self._matching_groups
        else:
            groups = {}
        rows = []
        for event in events:
            dt = try_parse_utc(event.utc_dt)
            seconds = (dt - now).total_seconds() if dt else None
            if self.quick_range == "next24" and (
                seconds is None or not 0 <= seconds <= 86400
            ):
                continue
            if (
                self.search.strip().casefold()
                not in " ".join(
                    (
                        event.event_name,
                        event.country,
                        event.impact.value,
                        event.actual,
                        event.forecast,
                        event.previous,
                        event.deviation,
                    )
                ).casefold()
            ):
                continue
            row = {
                key: getattr(event, key)
                for key in (
                    "date",
                    "time",
                    "country",
                    "event_name",
                    "actual",
                    "forecast",
                    "previous",
                    "deviation",
                    "utc_dt",
                )
            }
            row.update(
                source=event.source.value,
                impact=event.impact.value,
                duplicate_group=groups.get(event_identity(event), ""),
                countdown=countdown(seconds or 0),
                past=seconds is not None and seconds < 0,
                next_high=False,
            )
            rows.append(row)
        next_high = next(
            (row for row in rows if row["impact"] == "HIGH" and row["countdown"]), None
        )
        summary = "Nessun evento HIGH imminente"
        if next_high is not None:
            next_high["next_high"] = True
            summary = (
                f"Prossimo HIGH: {next_high['event_name']} · {next_high['countdown']}"
            )
        sort_key = self.settings.get(f"{active}_sort_key")
        direction = self.settings.get(f"{active}_sort_direction")
        if sort_key:

            def key(row):
                if sort_key == "impact":
                    return {"HIGH": 3, "MID": 2, "LOW": 1}[row["impact"]]
                if sort_key == "date":
                    return tuple(reversed(row["date"].split("/")))
                return _natural(str(row[sort_key]))

            rows.sort(key=key, reverse=direction == "desc")
        order = self.settings.get(f"{active}_column_order")
        state = {
            key: self.settings.get(key)
            for key in (
                "active_source",
                "timezone_name",
                "auto_refresh_minutes",
                "high_notification_minutes",
                "selected_date",
            )
        }
        state.update(
            region=region,
            impact=impact,
            date=date,
            search=self.search,
            quick_range=self.quick_range,
            sort_key=sort_key,
            sort_direction=direction,
        )
        statuses = []
        for key, label in SOURCES.items():
            selected = (
                (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET)
                if key == "combined"
                else (CalendarSource(key),)
            )
            errors = [
                f"{SOURCES[source.value]}: {self.controller.get_source_error(source)}"
                for source in selected
                if self.controller.get_source_error(source)
            ]
            missing = [
                SOURCES[source.value]
                for source in selected
                if self.controller.get_data_origin(source) == "empty"
            ]
            refreshing = any(
                self.controller.is_refreshing(source) for source in selected
            )
            stamps = [
                try_parse_utc(self.controller.get_last_refresh(source))
                for source in selected
            ]
            valid = [stamp for stamp in stamps if stamp is not None]
            stamp = min(valid) if valid else None
            age = max(0, int((now - stamp).total_seconds() / 60)) if stamp else None
            freshness = (
                "mai" if age is None else ("adesso" if age == 0 else f"{age} min fa")
            )
            if refreshing:
                status = "Aggiornamento…"
            elif len(missing) == len(selected):
                status = "Nessun dato"
            elif missing or errors:
                status = (
                    "Dati parziali" if key == "combined" else "Errore · dati precedenti"
                )
            elif any(
                self.controller.get_data_origin(source) == "cache"
                for source in selected
            ):
                status = "Dati salvati"
            elif age is not None and age > max(
                15, state["auto_refresh_minutes"] * 2 or 60
            ):
                status = "Dati non recenti"
            else:
                status = "Dati aggiornati"
            detail = "\n".join(
                errors
                or ([f"Sorgenti senza dati: {', '.join(missing)}"] if missing else [])
            )
            statuses.append(
                dict(
                    key=key,
                    label=label,
                    status=status,
                    freshness=freshness,
                    error=detail,
                    refreshing=refreshing,
                )
            )
        current = next(item for item in statuses if item["key"] == active)
        return CalendarView(
            tuple(rows),
            tuple(COLUMNS[active][i] for i in order),
            state,
            tuple(statuses),
            summary,
            f"{current['status']} · {current['freshness']}",
            current["error"],
        )
