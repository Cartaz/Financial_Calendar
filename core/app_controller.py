"""Application controller coordinating background refresh and filtering."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config.constants import CalendarDefaults
from config.settings import Settings
from core.cache import CalendarCache
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_fxstreet import scrape_fxstreet_calendar
from core.scraper_ig import scrape_ig_calendar

logger = logging.getLogger(__name__)


class AppController:
    """Coordinate scrapers, persisted state and UI notifications."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        debug: bool = False,
    ) -> None:
        self.settings = settings or Settings()
        self.events_ig: list[CalendarEvent] = []
        self.events_fxstreet: list[CalendarEvent] = []

        self._debug = debug
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scraper")
        self._notification_callback: Callable[[str, dict], None] | None = None

        self._refreshing_ig = threading.Event()
        self._refreshing_fxstreet = threading.Event()
        self._state_lock = threading.RLock()
        self._data_lock = threading.RLock()
        self._shutting_down = threading.Event()
        self._shutdown_complete = False

        self._cache = CalendarCache()
        self._data_origin: dict[str, str] = {"ig": "empty", "fxstreet": "empty"}
        self._data_timestamp: dict[str, str] = {"ig": "", "fxstreet": ""}
        self._load_cached_events()

    def _load_cached_events(self) -> None:
        for source in (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET):
            snapshot = self._cache.load(source)
            if snapshot is None:
                continue

            with self._data_lock:
                if source == CalendarSource.FXSTREET:
                    self.events_fxstreet = list(snapshot.events)
                else:
                    self.events_ig = list(snapshot.events)
                self._data_origin[source.value] = "cache"
                self._data_timestamp[source.value] = snapshot.refreshed_at

    def set_notification_callback(
        self,
        callback: Callable[[str, dict], None] | None,
    ) -> None:
        with self._state_lock:
            self._notification_callback = callback

    def _notify(self, event_name: str, payload: dict) -> None:
        if self._shutting_down.is_set():
            return
        with self._state_lock:
            callback = self._notification_callback
        if callback is not None:
            callback(event_name, payload)

    def is_refreshing(self, source: CalendarSource) -> bool:
        event = (
            self._refreshing_ig
            if source in (CalendarSource.IG, CalendarSource.FOREXFACTORY)
            else self._refreshing_fxstreet
        )
        return event.is_set()

    def refresh_ig(self) -> None:
        self._start_refresh(
            CalendarSource.FOREXFACTORY,
            self._refreshing_ig,
            lambda: scrape_ig_calendar(debug=self._debug),
            self._on_ig_refresh_done,
        )

    def refresh_fxstreet(self) -> None:
        self._start_refresh(
            CalendarSource.FXSTREET,
            self._refreshing_fxstreet,
            lambda: scrape_fxstreet_calendar(debug=self._debug),
            self._on_fxstreet_refresh_done,
        )

    def _start_refresh(
        self,
        source: CalendarSource,
        refreshing_flag: threading.Event,
        scraper: Callable[[], list[CalendarEvent]],
        done_callback: Callable[[Future], None],
    ) -> None:
        source_key = source.value
        with self._state_lock:
            if self._shutting_down.is_set():
                logger.debug("%s: refresh ignorato durante shutdown", source_key)
                return
            if refreshing_flag.is_set():
                logger.debug("%s: refresh già in corso", source_key)
                return
            refreshing_flag.set()

        logger.info("%s: avvio refresh", source_key)
        self._notify("calendar_refresh_started", {"source": source_key})
        try:
            future = self._executor.submit(scraper)
        except RuntimeError as exc:
            refreshing_flag.clear()
            if not self._shutting_down.is_set():
                self._notify(
                    "calendar_refresh_error",
                    {"source": source_key, "error": str(exc)},
                )
            return
        future.add_done_callback(done_callback)

    def refresh_all(self) -> None:
        self.refresh_ig()
        self.refresh_fxstreet()

    def _on_ig_refresh_done(self, future: Future) -> None:
        self._complete_refresh(
            future,
            CalendarSource.FOREXFACTORY,
            self._refreshing_ig,
        )

    def _on_fxstreet_refresh_done(self, future: Future) -> None:
        self._complete_refresh(
            future,
            CalendarSource.FXSTREET,
            self._refreshing_fxstreet,
        )

    def _complete_refresh(
        self,
        future: Future,
        source: CalendarSource,
        refreshing_flag: threading.Event,
    ) -> None:
        refreshing_flag.clear()
        if self._shutting_down.is_set():
            return

        source_key = source.value
        try:
            events = future.result()
        except Exception as exc:
            logger.error("%s: errore refresh: %s", source_key, exc)
            self._notify(
                "calendar_refresh_error",
                {
                    "source": source_key,
                    "error": str(exc),
                    "data_origin": self.get_data_origin(source),
                },
            )
            return

        refreshed_at = datetime.now(timezone.utc).isoformat()

        with self._data_lock:
            if source in (CalendarSource.IG, CalendarSource.FOREXFACTORY):
                self.events_ig = list(events)
                refresh_key = "last_refresh_ig"
            else:
                self.events_fxstreet = list(events)
                refresh_key = "last_refresh_fxstreet"
            self._data_origin[source_key] = "network"
            self._data_timestamp[source_key] = refreshed_at

        if not self._cache.save(source, list(events), refreshed_at):
            logger.warning("%s: impossibile aggiornare la cache persistente", source_key)

        if not self.settings.set(refresh_key, refreshed_at):
            logger.warning("%s: impossibile persistere last refresh", source_key)

        logger.info("%s: refresh completato, %d eventi", source_key, len(events))
        self._notify(
            "calendar_refreshed",
            {
                "source": source_key,
                "count": len(events),
                "timestamp": refreshed_at,
                "data_origin": "network",
            },
        )

    def filter_events(
        self,
        source: CalendarSource,
        region: str = "ALL",
        impact: str = "ALL",
        date: str = "",
        tz_offset_hours: float = 0.0,
        timezone_name: str = "",
    ) -> list[CalendarEvent]:
        with self._data_lock:
            source_events = (
                self.events_ig
                if source in (CalendarSource.IG, CalendarSource.FOREXFACTORY)
                else self.events_fxstreet
            )
            events = list(source_events)

        events = self._filter_past_events(events)
        if timezone_name:
            events = self._convert_events_timezone(events, timezone_name)
        else:
            events = self._convert_events_tz(events, tz_offset_hours)

        if date:
            events = [event for event in events if event.date == date]
        if region != "ALL":
            events = [event for event in events if event.country == region]
        if impact != "ALL":
            try:
                wanted_impact = ImpactLevel(impact)
            except ValueError:
                logger.warning("Filtro impatto non valido ignorato: %s", impact)
            else:
                events = [event for event in events if event.impact == wanted_impact]
        return events

    @staticmethod
    def _parse_event_utc(event: CalendarEvent) -> datetime | None:
        if not event.utc_dt:
            return None
        try:
            parsed = datetime.fromisoformat(event.utc_dt.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            logger.debug("Timestamp non valido per %s: %r", event.event_name, event.utc_dt)
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            logger.warning(
                "Timestamp naive ignorato per %s: %s",
                event.event_name,
                event.utc_dt,
            )
            return None
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _filter_past_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=CalendarDefaults.PAST_EVENT_CUTOFF_HOURS
        )
        kept: list[CalendarEvent] = []
        for event in events:
            dt_utc = AppController._parse_event_utc(event)
            if dt_utc is None or dt_utc >= cutoff:
                kept.append(event)
        return kept

    @staticmethod
    def _timezone_from_spec(timezone_name: str) -> tzinfo:
        text = timezone_name.strip()
        if not text or text.upper() == "UTC":
            return timezone.utc

        upper = text.upper()
        if upper.startswith("UTC") and len(text) > 3:
            suffix = text[3:]
            sign = 1
            if suffix.startswith("+"):
                suffix = suffix[1:]
            elif suffix.startswith("-"):
                sign = -1
                suffix = suffix[1:]
            else:
                logger.warning("Timezone offset non valido %r, uso UTC", timezone_name)
                return timezone.utc

            try:
                hours_text, minutes_text = suffix.split(":", 1)
                hours = int(hours_text)
                minutes = int(minutes_text)
            except (TypeError, ValueError):
                logger.warning("Timezone offset non valido %r, uso UTC", timezone_name)
                return timezone.utc

            if hours > 14 or minutes < 0 or minutes >= 60 or (hours == 14 and minutes):
                logger.warning("Timezone offset fuori intervallo %r, uso UTC", timezone_name)
                return timezone.utc
            return timezone(sign * timedelta(hours=hours, minutes=minutes))

        try:
            return ZoneInfo(text)
        except ZoneInfoNotFoundError:
            logger.warning("Timezone IANA sconosciuta %r, uso UTC", timezone_name)
            return timezone.utc

    @staticmethod
    def _convert_events_to_zone(
        events: list[CalendarEvent],
        target_tz: tzinfo,
    ) -> list[CalendarEvent]:
        converted: list[CalendarEvent] = []

        for event in events:
            dt_utc = AppController._parse_event_utc(event)
            if dt_utc is None:
                converted.append(event)
                continue

            dt_local = dt_utc.astimezone(target_tz)
            converted.append(
                CalendarEvent(
                    time=dt_local.strftime("%H:%M"),
                    country=event.country,
                    impact=event.impact,
                    event_name=event.event_name,
                    actual=event.actual,
                    forecast=event.forecast,
                    previous=event.previous,
                    date=dt_local.strftime("%d/%m/%Y"),
                    utc_dt=event.utc_dt,
                    deviation=event.deviation,
                    source=event.source,
                )
            )
        return converted

    @staticmethod
    def _convert_events_tz(
        events: list[CalendarEvent],
        offset_hours: float,
    ) -> list[CalendarEvent]:
        target_tz = timezone(timedelta(hours=offset_hours))
        return AppController._convert_events_to_zone(events, target_tz)

    @staticmethod
    def _convert_events_timezone(
        events: list[CalendarEvent],
        timezone_name: str,
    ) -> list[CalendarEvent]:
        target_tz = AppController._timezone_from_spec(timezone_name)
        return AppController._convert_events_to_zone(events, target_tz)

    def get_last_refresh(self, source: CalendarSource) -> str:
        source_key = source.value
        with self._data_lock:
            timestamp = self._data_timestamp.get(source_key, "")
        if timestamp:
            return timestamp

        key = (
            "last_refresh_ig"
            if source in (CalendarSource.IG, CalendarSource.FOREXFACTORY)
            else "last_refresh_fxstreet"
        )
        return str(self.settings.get(key))

    def get_data_origin(self, source: CalendarSource) -> str:
        with self._data_lock:
            return self._data_origin.get(source.value, "empty")

    def begin_shutdown(self) -> None:
        """Stop accepting work and prevent callbacks into a closing UI."""
        if self._shutting_down.is_set():
            return
        self._shutting_down.set()
        with self._state_lock:
            self._notification_callback = None
        logger.info("Controller: shutdown richiesto")

    def shutdown(self) -> None:
        """Deterministically finish/cancel executor work and release threads."""
        with self._state_lock:
            if self._shutdown_complete:
                return
            self._shutdown_complete = True

        self.begin_shutdown()
        self._executor.shutdown(wait=True, cancel_futures=True)
        self._refreshing_ig.clear()
        self._refreshing_fxstreet.clear()
        logger.info("Controller arrestato")
