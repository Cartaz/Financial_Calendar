"""QWebChannel bridge between the HTML frontend and the Python backend."""

from __future__ import annotations

import json
import logging
import re
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QFileDialog

from config.constants import AppMeta, CalendarDefaults
from config.settings import Settings
from core.app_controller import AppController
from core.exporters import write_export
from core.models import CalendarEvent, CalendarSource
from core.notifications import DesktopNotifier

logger = logging.getLogger(__name__)

_SOURCE_BY_KEY: dict[str, CalendarSource] = {
    "ig": CalendarSource.FOREXFACTORY,
    "fxstreet": CalendarSource.FXSTREET,
}
_SOURCE_KEYS = {"ig", "fxstreet", "combined"}
_PREFIX_BY_KEY = {"ig": "ig", "fxstreet": "fxstreet", "combined": "combined"}

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
    "combined": [
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
    ],
}

_COLUMN_LABELS: dict[str, list[str]] = {
    "ig": list(CalendarDefaults.IG_COLUMNS),
    "fxstreet": list(CalendarDefaults.FXSTREET_COLUMNS),
    "combined": [
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
    ],
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


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _oldest_timestamp(values: list[str]) -> str:
    parsed = [(item, _parse_utc(item)) for item in values if item]
    valid = [(item, dt) for item, dt in parsed if dt is not None]
    if not valid:
        return next((item for item in values if item), "")
    return min(valid, key=lambda item: item[1])[0]


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
        notifier: DesktopNotifier | None = None,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._settings = settings
        self._debug = debug
        self._started = False
        self._logs: deque[dict[str, str]] = deque(maxlen=250)
        self._notifier = notifier or DesktopNotifier()
        self._notified_keys: set[str] = set()
        self._notified_events: list[tuple[CalendarEvent, datetime]] = []

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setSingleShot(False)
        self._auto_refresh_timer.timeout.connect(self._controller.refresh_all)

        self._notification_timer = QTimer(self)
        self._notification_timer.setSingleShot(False)
        self._notification_timer.setInterval(30_000)
        self._notification_timer.timeout.connect(self._check_high_notifications)

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
            data["combined_state"] = self._source_state("combined")
        self.backendEvent.emit(event_name, data)
        if event_name == "calendar_refreshed":
            self._check_high_notifications()

    def enqueue_log(self, payload: dict[str, str]) -> None:
        """Queue a formatted logging record for the frontend."""
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

    def _combined_status(self) -> tuple[str, str, bool]:
        real_sources = [CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET]
        timestamps = [self._controller.get_last_refresh(source) for source in real_sources]
        origins = [self._controller.get_data_origin(source) for source in real_sources]
        refreshing = any(self._controller.is_refreshing(source) for source in real_sources)
        if not any(origin != "empty" for origin in origins):
            origin = "empty"
        elif any(origin == "cache" for origin in origins):
            origin = "cache"
        else:
            origin = "network"
        return _oldest_timestamp(timestamps), origin, refreshing

    def _source_state(self, source_key: str) -> dict:
        self._validate_source_key(source_key)
        prefix = _PREFIX_BY_KEY[source_key]
        if source_key == "combined":
            timestamp, origin, refreshing = self._combined_status()
            name = "Tutti"
            description = "Vista combinata ForexFactory + FXStreet"
        else:
            source = self._source(source_key)
            timestamp = self._controller.get_last_refresh(source)
            origin = self._controller.get_data_origin(source)
            refreshing = self._controller.is_refreshing(source)
            name = "ForexFactory" if source_key == "ig" else "FXStreet"
            description = (
                "Feed Faireconomy / ForexFactory"
                if source_key == "ig"
                else "Calendario economico FXStreet"
            )

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
            "app": {
                "name": AppMeta.DISPLAY_NAME,
                "version": AppMeta.VERSION,
                "description": AppMeta.DESCRIPTION,
            },
            "sources": [
                self._source_state("ig"),
                self._source_state("fxstreet"),
                self._source_state("combined"),
            ],
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

    def _query_events(
        self,
        source_key: str,
        region: str,
        impact: str,
        date: str,
        *,
        tz_offset_hours: float = 0.0,
        timezone_name: str = "",
    ) -> list[CalendarEvent]:
        self._validate_source_key(source_key)
        source_keys = ["ig", "fxstreet"] if source_key == "combined" else [source_key]
        events: list[CalendarEvent] = []
        for key in source_keys:
            events.extend(
                self._controller.filter_events(
                    self._source(key),
                    region=region,
                    impact=impact,
                    date=date,
                    tz_offset_hours=tz_offset_hours,
                    timezone_name=timezone_name,
                )
            )
        events.sort(key=lambda event: (_parse_utc(event.utc_dt) or datetime.max.replace(tzinfo=timezone.utc)))
        return events

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
        events = self._query_events(
            source_key,
            region,
            impact,
            date,
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
        events = self._query_events(
            source_key,
            region,
            impact,
            date,
            timezone_name=timezone_name,
        )
        return [self._event_to_map(event) for event in events]

    @Slot(str, str, str, result=bool)
    def saveFilters(self, source_key: str, region: str, impact: str) -> bool:
        self._validate_source_key(source_key)
        prefix = _PREFIX_BY_KEY[source_key]
        try:
            return bool(
                self._settings.set_many(
                    {
                        f"{prefix}_selected_region": region,
                        f"{prefix}_selected_impact": impact,
                    }
                )
            )
        except (TypeError, ValueError):
            return False

    @Slot(str, str, result=bool)
    def saveColumnOrder(self, source_key: str, order_json: str) -> bool:
        self._validate_source_key(source_key)
        try:
            order = json.loads(order_json)
        except json.JSONDecodeError:
            return False
        prefix = _PREFIX_BY_KEY[source_key]
        try:
            return bool(self._settings.set(f"{prefix}_column_order", order))
        except (TypeError, ValueError):
            return False

    @Slot(str, str, str, result=bool)
    def saveSort(self, source_key: str, sort_key: str, direction: str) -> bool:
        self._validate_source_key(source_key)
        prefix = _PREFIX_BY_KEY[source_key]
        try:
            return bool(
                self._settings.set_many(
                    {
                        f"{prefix}_sort_key": sort_key,
                        f"{prefix}_sort_direction": direction,
                    }
                )
            )
        except (TypeError, ValueError):
            return False

    @Slot(str, str, str, int, result=bool)
    def saveUiState(
        self,
        active_source: str,
        timezone_name: str,
        selected_date: str,
        auto_refresh_minutes: int,
    ) -> bool:
        try:
            saved = self._settings.set_many(
                {
                    "active_source": active_source,
                    "timezone_name": timezone_name,
                    "selected_date": selected_date,
                    "auto_refresh_minutes": auto_refresh_minutes,
                }
            )
        except (TypeError, ValueError):
            return False
        if saved:
            self._configure_auto_refresh(self._settings.get("auto_refresh_minutes"))
        return bool(saved)

    @Slot(int, result=bool)
    def saveNotificationLead(self, minutes: int) -> bool:
        try:
            saved = self._settings.set("high_notification_minutes", minutes)
        except (TypeError, ValueError):
            return False
        if saved:
            self._configure_notification_timer()
            self._check_high_notifications()
        return bool(saved)

    def _configure_auto_refresh(self, minutes: int) -> None:
        self._auto_refresh_timer.stop()
        if not self._started or minutes <= 0:
            return
        self._auto_refresh_timer.start(int(minutes) * 60 * 1000)
        logger.info("Auto-refresh configurato ogni %d minuti", minutes)

    def _configure_notification_timer(self) -> None:
        self._notification_timer.stop()
        minutes = int(self._settings.get("high_notification_minutes"))
        if not self._started or minutes <= 0:
            return
        self._notification_timer.start()
        logger.info("Notifiche HIGH configurate con anticipo di %d minuti", minutes)

    @staticmethod
    def _event_tokens(event: CalendarEvent) -> set[str]:
        normalized = re.sub(r"[^a-z0-9]+", " ", event.event_name.casefold())
        return {token for token in normalized.split() if len(token) >= 3}

    @classmethod
    def _probably_same_event(
        cls,
        left: CalendarEvent,
        left_dt: datetime,
        right: CalendarEvent,
        right_dt: datetime,
    ) -> bool:
        if left.country != right.country:
            return False
        if abs((left_dt - right_dt).total_seconds()) > 15 * 60:
            return False
        left_tokens = cls._event_tokens(left)
        right_tokens = cls._event_tokens(right)
        if not left_tokens or not right_tokens:
            return False
        overlap = len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
        return overlap >= 0.6

    def _check_high_notifications(self) -> None:
        lead_minutes = int(self._settings.get("high_notification_minutes"))
        if lead_minutes <= 0 or not self._started:
            return

        now = datetime.now(timezone.utc)
        candidates: list[tuple[CalendarEvent, datetime]] = []
        for source in (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET):
            for event in self._controller.filter_events(
                source,
                region="ALL",
                impact="HIGH",
                timezone_name="UTC",
            ):
                dt_utc = _parse_utc(event.utc_dt)
                if dt_utc is None:
                    continue
                remaining = (dt_utc - now).total_seconds()
                if 0 < remaining <= lead_minutes * 60:
                    candidates.append((event, dt_utc))

        candidates.sort(key=lambda item: item[1])
        for event, dt_utc in candidates:
            key = "|".join([event.source.value, event.utc_dt, event.country, event.event_name])
            if key in self._notified_keys:
                continue
            self._notified_keys.add(key)

            if any(
                self._probably_same_event(event, dt_utc, previous, previous_dt)
                for previous, previous_dt in self._notified_events
            ):
                continue

            remaining_minutes = max(1, int((dt_utc - now).total_seconds() // 60) + 1)
            title = f"Evento HIGH tra {remaining_minutes} min"
            body = f"{event.country} · {event.event_name} · {dt_utc.astimezone().strftime('%H:%M')}"
            self._notifier.notify(title, body)
            self._notified_events.append((event, dt_utc))

    @Slot(str)
    def refreshSource(self, source_key: str) -> None:
        self._validate_source_key(source_key)
        if source_key == "combined":
            self._controller.refresh_all()
            return
        source = self._source(source_key)
        if source == CalendarSource.FXSTREET:
            self._controller.refresh_fxstreet()
        else:
            self._controller.refresh_ig()

    @Slot()
    def refreshAll(self) -> None:
        self._controller.refresh_all()

    @Slot(str, str, result="QVariantMap")
    def exportEvents(self, export_format: str, events_json: str) -> dict:
        export_format = export_format.lower().strip()
        if export_format not in {"csv", "ics"}:
            return {"ok": False, "error": "Formato export non supportato"}
        try:
            raw = json.loads(events_json)
        except json.JSONDecodeError:
            return {"ok": False, "error": "Dati export non validi"}
        if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
            return {"ok": False, "error": "Dati export non validi"}
        if len(raw) > 20_000:
            return {"ok": False, "error": "Troppi eventi da esportare"}

        extension = f".{export_format}"
        default_name = f"financial-calendar-{datetime.now().strftime('%Y%m%d-%H%M')}{extension}"
        file_filter = "CSV (*.csv)" if export_format == "csv" else "Calendario iCalendar (*.ics)"
        parent = QApplication.activeWindow()
        path, _ = QFileDialog.getSaveFileName(parent, "Esporta calendario", default_name, file_filter)
        if not path:
            return {"ok": False, "cancelled": True}
        if not path.lower().endswith(extension):
            path += extension

        try:
            count = write_export(Path(path), export_format, raw)
        except (OSError, ValueError) as exc:
            logger.error("Export %s fallito: %s", export_format, exc)
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "path": path, "count": count}

    @Slot()
    def start(self) -> None:
        """Start the first data refresh once the WebChannel client is ready."""
        if self._started:
            return
        self._started = True
        self._configure_auto_refresh(self._settings.get("auto_refresh_minutes"))
        self._configure_notification_timer()
        self._controller.refresh_all()
        self._check_high_notifications()

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
