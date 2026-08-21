"""QWebChannel bridge between the HTML frontend and the Python backend."""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot

from config.constants import AppMeta, CalendarDefaults
from config.settings import Settings
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource

_SOURCE_BY_KEY: dict[str, CalendarSource] = {
    "ig": CalendarSource.FOREXFACTORY,
    "fxstreet": CalendarSource.FXSTREET,
}

_COLUMN_KEYS: dict[str, list[str]] = {
    "ig": [
        "date",
        "time",
        "country",
        "impact",
        "event_name",
        "actual",
        "forecast",
        "previous",
    ],
    "fxstreet": [
        "date",
        "time",
        "country",
        "event_name",
        "impact",
        "actual",
        "deviation",
        "forecast",
        "previous",
    ],
}

_COLUMN_LABELS: dict[str, list[str]] = {
    "ig": list(CalendarDefaults.IG_COLUMNS),
    "fxstreet": list(CalendarDefaults.FXSTREET_COLUMNS),
}


def _display_refresh_timestamp(value: str) -> str:
    """Render new ISO UTC timestamps locally while accepting legacy strings."""
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
        *,
        debug: bool = False,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._settings = settings
        self._debug = debug
        self._started = False
        self._logs: deque[dict[str, str]] = deque(maxlen=250)

        self._controller_event.connect(self._forward_controller_event)
        self._log_event.connect(self._forward_log_event)
        self._controller.set_notification_callback(self._receive_controller_event)

    def _receive_controller_event(self, event_name: str, payload: dict) -> None:
        """Accept controller callbacks from worker threads and queue them to Qt."""
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
        self.backendEvent.emit(event_name, data)

    def enqueue_log(self, payload: dict[str, str]) -> None:
        """Queue a formatted logging record for the frontend."""
        self._log_event.emit(dict(payload))

    @Slot(object)
    def _forward_log_event(self, payload: object) -> None:
        data = dict(payload) if isinstance(payload, dict) else {}
        self._logs.append(data)
        self.logMessage.emit(data)

    @staticmethod
    def _source(source_key: str) -> CalendarSource:
        try:
            return _SOURCE_BY_KEY[source_key]
        except KeyError as exc:
            raise ValueError(f"Sorgente non valida: {source_key}") from exc

    @staticmethod
    def _event_to_map(event: CalendarEvent) -> dict[str, str]:
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
        }

    def _source_state(self, source_key: str) -> dict:
        source = self._source(source_key)
        prefix = "ig" if source_key == "ig" else "fxstreet"
        timestamp = self._controller.get_last_refresh(source)
        columns = [
            {"key": key, "label": label}
            for key, label in zip(
                _COLUMN_KEYS[source_key],
                _COLUMN_LABELS[source_key],
                strict=True,
            )
        ]
        return {
            "key": source_key,
            "name": "ForexFactory" if source_key == "ig" else "FXStreet",
            "description": (
                "Feed Faireconomy / ForexFactory"
                if source_key == "ig"
                else "Calendario economico FXStreet"
            ),
            "columns": columns,
            "column_order": self._settings.get(f"{prefix}_column_order"),
            "selected_region": self._settings.get(f"{prefix}_selected_region"),
            "selected_impact": self._settings.get(f"{prefix}_selected_impact"),
            "last_refresh": _display_refresh_timestamp(timestamp),
            "last_refresh_iso": timestamp,
            "refreshing": self._controller.is_refreshing(source),
            "data_origin": self._controller.get_data_origin(source),
        }

    @Slot(result="QVariantMap")
    def getInitialState(self) -> dict:
        return {
            "app": {
                "name": AppMeta.DISPLAY_NAME,
                "version": AppMeta.VERSION,
                "description": AppMeta.DESCRIPTION,
            },
            "sources": [self._source_state("ig"), self._source_state("fxstreet")],
            "regions": list(CalendarDefaults.REGIONS),
            "impacts": ["ALL", *CalendarDefaults.IMPACT_LEVELS],
            "flag_codes": dict(CalendarDefaults.FLAG_CODES),
            "debug": self._debug,
        }

    @Slot(str, str, str, str, float, result="QVariantList")
    def getEvents(
        self,
        source_key: str,
        region: str,
        impact: str,
        date: str,
        tz_offset_hours: float,
    ) -> list[dict[str, str]]:
        """Compatibility query using a fixed UTC offset."""
        source = self._source(source_key)
        events = self._controller.filter_events(
            source,
            region=region,
            impact=impact,
            date=date,
            tz_offset_hours=tz_offset_hours,
        )
        return [self._event_to_map(event) for event in events]

    @Slot(str, str, str, str, str, result="QVariantList")
    def getEventsInTimezone(
        self,
        source_key: str,
        region: str,
        impact: str,
        date: str,
        timezone_name: str,
    ) -> list[dict[str, str]]:
        """Query events using an IANA timezone or an explicit UTC offset spec."""
        source = self._source(source_key)
        events = self._controller.filter_events(
            source,
            region=region,
            impact=impact,
            date=date,
            timezone_name=timezone_name,
        )
        return [self._event_to_map(event) for event in events]

    @Slot(str, str, str, result=bool)
    def saveFilters(self, source_key: str, region: str, impact: str) -> bool:
        self._source(source_key)
        prefix = "ig" if source_key == "ig" else "fxstreet"
        region_ok = self._settings.set(f"{prefix}_selected_region", region)
        impact_ok = self._settings.set(f"{prefix}_selected_impact", impact)
        return bool(region_ok and impact_ok)

    @Slot(str, str, result=bool)
    def saveColumnOrder(self, source_key: str, order_json: str) -> bool:
        self._source(source_key)
        try:
            order = json.loads(order_json)
        except json.JSONDecodeError:
            return False
        prefix = "ig" if source_key == "ig" else "fxstreet"
        try:
            return bool(self._settings.set(f"{prefix}_column_order", order))
        except (TypeError, ValueError):
            return False

    @Slot(str)
    def refreshSource(self, source_key: str) -> None:
        source = self._source(source_key)
        if source == CalendarSource.FXSTREET:
            self._controller.refresh_fxstreet()
        else:
            self._controller.refresh_ig()

    @Slot()
    def refreshAll(self) -> None:
        self._controller.refresh_all()

    @Slot()
    def start(self) -> None:
        """Start the first data refresh once the WebChannel client is ready."""
        if self._started:
            return
        self._started = True
        self._controller.refresh_all()

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
