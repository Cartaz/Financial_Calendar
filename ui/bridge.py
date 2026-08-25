"""QWebChannel transport bridge between the local frontend and Python services."""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot

from config.constants import AppMeta, CalendarDefaults
from config.settings import Settings
from core.app_controller import AppController
from core.calendar_queries import CalendarQueryService
from core.event_matching import build_duplicate_groups, event_identity
from core.models import CalendarEvent, CalendarSource
from ui.native_actions import NativeActions
from ui.runtime import CalendarRuntime

logger = logging.getLogger(__name__)

_SOURCE_BY_KEY: dict[str, CalendarSource] = {
    "ig": CalendarSource.FOREXFACTORY,
    "fxstreet": CalendarSource.FXSTREET,
}
_SOURCE_KEYS = {"ig", "fxstreet", "combined"}
_PREFIX_BY_KEY = {"ig": "ig", "fxstreet": "fxstreet", "combined": "combined"}
_COLUMN_KEYS: dict[str, list[str]] = {
    "ig": ["date", "time", "country", "impact", "event_name", "actual", "forecast", "previous"],
    "fxstreet": [
        "date", "time", "country", "event_name", "impact", "actual", "deviation", "forecast", "previous"
    ],
    "combined": [
        "date", "time", "country", "impact", "event_name", "source", "actual", "forecast", "previous", "deviation"
    ],
}
_COLUMN_LABELS: dict[str, list[str]] = {
    "ig": list(CalendarDefaults.IG_COLUMNS),
    "fxstreet": list(CalendarDefaults.FXSTREET_COLUMNS),
    "combined": [
        "Data", "Ora", "Paese", "Impatto", "Evento", "Sorgente", "Attuale", "Previsione", "Precedente", "Dev"
    ],
}


def _display_refresh_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return value
    return parsed.astimezone().strftime("%d/%m/%Y %H:%M:%S")


class CalendarBridge(QObject):
    """Expose a deliberately small presentation API to JavaScript."""

    backendEvent = Signal(str, "QVariantMap")
    logMessage = Signal("QVariantMap")
    _controller_event = Signal(str, object)
    _log_event = Signal(object)

    def __init__(
        self,
        controller: AppController,
        settings: Settings,
        runtime: CalendarRuntime,
        *,
        debug: bool = False,
        native_actions: NativeActions | None = None,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._settings = settings
        self._runtime = runtime
        self._queries = CalendarQueryService(controller)
        self._native_actions = native_actions or NativeActions()
        self._debug = debug
        self._logs: deque[dict[str, str]] = deque(maxlen=250)
        self._controller_event.connect(self._forward_controller_event)
        self._log_event.connect(self._forward_log_event)
        self._controller.set_notification_callback(self._receive_controller_event)

    def _receive_controller_event(self, event_name: str, payload: dict) -> None:
        self._controller_event.emit(event_name, dict(payload))

    @Slot(str, object)
    def _forward_controller_event(self, event_name: str, payload: object) -> None:
        data = dict(payload) if isinstance(payload, dict) else {}
        if event_name in {"calendar_refreshed", "calendar_refresh_error"}:
            source_key = str(data.get("source", ""))
            source = _SOURCE_BY_KEY.get(source_key)
            if source is not None:
                timestamp = self._controller.get_last_refresh(source)
                data["last_refresh"] = _display_refresh_timestamp(timestamp)
                data["last_refresh_iso"] = timestamp
                data["data_origin"] = self._controller.get_data_origin(source)
            data["combined_state"] = self._source_state("combined")
        self.backendEvent.emit(event_name, data)
        if event_name == "calendar_refreshed":
            self._runtime.check_notifications()

    def enqueue_log(self, payload: dict[str, str]) -> None:
        self._log_event.emit(dict(payload))

    @Slot(object)
    def _forward_log_event(self, payload: object) -> None:
        data = dict(payload) if isinstance(payload, dict) else {}
        self._logs.append(data)
        self.logMessage.emit(data)

    @staticmethod
    def _validate_source_key(source_key: str) -> str:
        if source_key not in _SOURCE_KEYS:
            raise ValueError(f"Sorgente non valida: {source_key}")
        return source_key

    @staticmethod
    def _source(source_key: str) -> CalendarSource:
        try:
            return _SOURCE_BY_KEY[source_key]
        except KeyError as exc:
            raise ValueError(f"Sorgente reale non valida: {source_key}") from exc

    @classmethod
    def _sources(cls, source_key: str) -> tuple[CalendarSource, ...]:
        cls._validate_source_key(source_key)
        if source_key == "combined":
            return (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET)
        return (cls._source(source_key),)

    @staticmethod
    def _event_to_map(event: CalendarEvent, duplicate_group: str = "") -> dict[str, str]:
        return {
            "date": event.date,
            "time": event.time,
            "country": event.country,
            "impact": event.impact.value,
            "event_name": event.event_name,
            "actual": event.actual,
            "forecast": event.forecast,
            "previous": event.previous,
            "deviation": event.deviation,
            "source": event.source.value,
            "utc_dt": event.utc_dt,
            "duplicate_group": duplicate_group,
        }

    def _serialize_events(self, source_key: str, events: list[CalendarEvent]) -> list[dict[str, str]]:
        groups = build_duplicate_groups(events) if source_key == "combined" else {}
        return [self._event_to_map(event, groups.get(event_identity(event), "")) for event in events]

    def _source_state(self, source_key: str) -> dict:
        self._validate_source_key(source_key)
        prefix = _PREFIX_BY_KEY[source_key]
        if source_key == "combined":
            timestamp, origin, refreshing = self._queries.combined_status()
            name = "Tutti"
            description = "Vista combinata ForexFactory + FXStreet"
        else:
            source = self._source(source_key)
            timestamp = self._controller.get_last_refresh(source)
            origin = self._controller.get_data_origin(source)
            refreshing = self._controller.is_refreshing(source)
            name = "ForexFactory" if source_key == "ig" else "FXStreet"
            description = "Feed Faireconomy / ForexFactory" if source_key == "ig" else "Calendario economico FXStreet"
        columns = [
            {"key": key, "label": label}
            for key, label in zip(_COLUMN_KEYS[source_key], _COLUMN_LABELS[source_key], strict=True)
        ]
        return {
            "key": source_key,
            "name": name,
            "description": description,
            "columns": columns,
            "column_order": self._settings.get(f"{prefix}_column_order"),
            "selected_region": self._settings.get(f"{prefix}_selected_region"),
            "selected_impact": self._settings.get(f"{prefix}_selected_impact"),
            "sort_key": self._settings.get(f"{prefix}_sort_key"),
            "sort_direction": self._settings.get(f"{prefix}_sort_direction"),
            "last_refresh": _display_refresh_timestamp(timestamp),
            "last_refresh_iso": timestamp,
            "refreshing": refreshing,
            "data_origin": origin,
        }

    @Slot(result="QVariantMap")
    def getInitialState(self) -> dict:
        return {
            "app": {"name": AppMeta.DISPLAY_NAME, "version": AppMeta.VERSION, "description": AppMeta.DESCRIPTION},
            "sources": [self._source_state(key) for key in ("ig", "fxstreet", "combined")],
            "regions": list(CalendarDefaults.REGIONS),
            "impacts": ["ALL", *CalendarDefaults.IMPACT_LEVELS],
            "auto_refresh_options": [0, 5, 15, 30, 60],
            "notification_lead_options": [0, 5, 15, 30, 60],
            "ui_state": {
                "active_source": self._settings.get("active_source"),
                "timezone_name": self._settings.get("timezone_name"),
                "selected_date": self._settings.get("selected_date"),
                "auto_refresh_minutes": self._settings.get("auto_refresh_minutes"),
                "high_notification_minutes": self._settings.get("high_notification_minutes"),
            },
            "flag_codes": dict(CalendarDefaults.FLAG_CODES),
            "debug": self._debug,
        }

    def _query_maps(
        self,
        source_key: str,
        region: str,
        impact: str,
        date: str,
        *,
        tz_offset_hours: float = 0.0,
        timezone_name: str = "",
    ) -> list[dict[str, str]]:
        events = self._queries.query(
            self._sources(source_key),
            region=region,
            impact=impact,
            date=date,
            tz_offset_hours=tz_offset_hours,
            timezone_name=timezone_name,
        )
        return self._serialize_events(source_key, events)

    @Slot(str, str, str, str, float, result="QVariantList")
    def getEvents(self, source_key: str, region: str, impact: str, date: str, tz_offset_hours: float) -> list[dict[str, str]]:
        return self._query_maps(source_key, region, impact, date, tz_offset_hours=tz_offset_hours)

    @Slot(str, str, str, str, str, result="QVariantList")
    def getEventsInTimezone(self, source_key: str, region: str, impact: str, date: str, timezone_name: str) -> list[dict[str, str]]:
        return self._query_maps(source_key, region, impact, date, timezone_name=timezone_name)

    @Slot(str, str, str, result=bool)
    def saveFilters(self, source_key: str, region: str, impact: str) -> bool:
        self._validate_source_key(source_key)
        prefix = _PREFIX_BY_KEY[source_key]
        try:
            return bool(self._settings.set_many({f"{prefix}_selected_region": region, f"{prefix}_selected_impact": impact}))
        except (TypeError, ValueError):
            return False

    @Slot(str, str, result=bool)
    def saveColumnOrder(self, source_key: str, order_json: str) -> bool:
        self._validate_source_key(source_key)
        try:
            order = json.loads(order_json)
            return bool(self._settings.set(f"{_PREFIX_BY_KEY[source_key]}_column_order", order))
        except (json.JSONDecodeError, TypeError, ValueError):
            return False

    @Slot(str, str, str, result=bool)
    def saveSort(self, source_key: str, sort_key: str, direction: str) -> bool:
        self._validate_source_key(source_key)
        prefix = _PREFIX_BY_KEY[source_key]
        try:
            return bool(self._settings.set_many({f"{prefix}_sort_key": sort_key, f"{prefix}_sort_direction": direction}))
        except (TypeError, ValueError):
            return False

    @Slot(str, str, str, int, result=bool)
    def saveUiState(self, active_source: str, timezone_name: str, selected_date: str, auto_refresh_minutes: int) -> bool:
        try:
            saved = self._settings.set_many({
                "active_source": active_source,
                "timezone_name": timezone_name,
                "selected_date": selected_date,
                "auto_refresh_minutes": auto_refresh_minutes,
            })
        except (TypeError, ValueError):
            return False
        if saved:
            self._runtime.configure_auto_refresh()
        return bool(saved)

    @Slot(int, result=bool)
    def saveNotificationLead(self, minutes: int) -> bool:
        try:
            saved = self._settings.set("high_notification_minutes", minutes)
        except (TypeError, ValueError):
            return False
        if saved:
            self._runtime.configure_notifications()
            self._runtime.check_notifications()
        return bool(saved)

    @Slot(str)
    def refreshSource(self, source_key: str) -> None:
        self._validate_source_key(source_key)
        if source_key == "combined":
            self._controller.refresh_all()
        elif self._source(source_key) == CalendarSource.FXSTREET:
            self._controller.refresh_fxstreet()
        else:
            self._controller.refresh_ig()

    @Slot()
    def refreshAll(self) -> None:
        self._controller.refresh_all()

    @Slot(str, str, result="QVariantMap")
    def exportEvents(self, export_format: str, events_json: str) -> dict:
        """Resolve visible identities against current Python-owned state before export."""
        try:
            raw = json.loads(events_json)
        except json.JSONDecodeError:
            return {"ok": False, "error": "Dati export non validi"}
        if not isinstance(raw, list) or len(raw) > 20_000:
            return {"ok": False, "error": "Dati export non validi"}

        identities: set[tuple[str, str, str, str]] = set()
        for item in raw:
            if not isinstance(item, dict):
                return {"ok": False, "error": "Dati export non validi"}
            identity = (
                str(item.get("source", "")),
                str(item.get("utc_dt", "")),
                str(item.get("country", "")),
                str(item.get("event_name", "")),
            )
            if not all(identity):
                return {"ok": False, "error": "Dati export non validi"}
            identities.add(identity)

        source_key = self._validate_source_key(str(self._settings.get("active_source")))
        timezone_name = str(self._settings.get("timezone_name"))
        if timezone_name == "local":
            timezone_name = "UTC"
        events = self._queries.resolve_identities(
            self._sources(source_key),
            identities,
            timezone_name=timezone_name,
        )
        if not events:
            return {"ok": False, "error": "Nessun evento corrente da esportare"}
        return self._native_actions.export_events(
            export_format,
            self._serialize_events(source_key, events),
        )

    @Slot()
    def start(self) -> None:
        self._runtime.start()

    @Slot(result="QVariantList")
    def getRecentLogs(self) -> list[dict[str, str]]:
        return list(self._logs)


class WebLogHandler(logging.Handler):
    """Forward standard Python log records to the frontend without replacing logging."""

    def __init__(self, bridge: CalendarBridge) -> None:
        super().__init__()
        self._bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = {
                "time": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
            }
            self._bridge.enqueue_log(payload)
        except Exception:
            self.handleError(record)
