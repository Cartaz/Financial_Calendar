"""Application controller coordinating background refresh and filtering."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

from config.constants import CalendarDefaults
from config.timezones import resolve_timezone
from core.cache import CalendarCache
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_fxstreet import scrape_fxstreet_calendar
from core.scraper_ig import scrape_ig_calendar
from core.time_utils import try_parse_utc

logger = logging.getLogger(__name__)

_SOURCES = (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET)


class AppController:
    """Own the canonical per-source calendar snapshots and their refreshes."""

    def __init__(self, *, debug: bool = False) -> None:
        self._debug = debug
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scraper")
        self._notification_callback: Callable[[str, dict], None] | None = None

        self._state_lock = threading.RLock()
        self._data_lock = threading.RLock()
        self._shutting_down = threading.Event()
        self._shutdown_complete = False

        self._refreshing = {source: threading.Event() for source in _SOURCES}
        self._events: dict[CalendarSource, tuple[CalendarEvent, ...]] = {
            source: () for source in _SOURCES
        }
        self._origin = {source: "empty" for source in _SOURCES}
        self._timestamp = {source: "" for source in _SOURCES}
        self._errors = {source: "" for source in _SOURCES}

        self._cache = CalendarCache()
        self._load_cached_events()

    def _replace_source_state(
        self,
        source: CalendarSource,
        events: Iterable[CalendarEvent],
        *,
        origin: str,
        timestamp: str,
    ) -> None:
        """Atomically replace one source snapshot and its freshness metadata."""
        snapshot = tuple(events)
        with self._data_lock:
            self._events[source] = snapshot
            self._origin[source] = origin
            self._timestamp[source] = timestamp

    def _load_cached_events(self) -> None:
        for source in _SOURCES:
            snapshot = self._cache.load(source)
            if snapshot is not None:
                self._replace_source_state(
                    source,
                    snapshot.events,
                    origin="cache",
                    timestamp=snapshot.refreshed_at,
                )

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
        return self._refreshing[source].is_set()

    def refresh(self, source: CalendarSource) -> None:
        """Start one background refresh unless it is already running."""
        refreshing = self._refreshing[source]
        with self._state_lock:
            if self._shutting_down.is_set():
                logger.debug("%s: refresh ignorato durante shutdown", source.value)
                return
            if refreshing.is_set():
                logger.debug("%s: refresh già in corso", source.value)
                return
            refreshing.set()

        logger.info("%s: avvio refresh", source.value)
        self._notify("calendar_refresh_started", {"source": source.value})
        try:
            # Completion runs inside the worker so persistence never lands on
            # the caller's (GUI) thread, even when the work finishes instantly.
            self._executor.submit(self._run_refresh, source)
        except RuntimeError as exc:
            refreshing.clear()
            self._notify(
                "calendar_refresh_error", {"source": source.value, "error": str(exc)}
            )

    def refresh_all(self) -> None:
        for source in _SOURCES:
            self.refresh(source)

    def _scrape(self, source: CalendarSource) -> list[CalendarEvent]:
        scraper = (
            scrape_ig_calendar
            if source == CalendarSource.FOREXFACTORY
            else scrape_fxstreet_calendar
        )
        return scraper(debug=self._debug, cancel_event=self._shutting_down)

    def _run_refresh(self, source: CalendarSource) -> None:
        try:
            events = self._scrape(source)
        except Exception as exc:
            self._complete_refresh(source, error=exc)
        else:
            self._complete_refresh(source, events=events)

    def _complete_refresh(
        self,
        source: CalendarSource,
        *,
        events: list[CalendarEvent] | None = None,
        error: BaseException | None = None,
    ) -> None:
        name = "calendar_refresh_error"
        payload: dict = {"source": source.value}
        try:
            if self._shutting_down.is_set():
                return
            if error is not None:
                raise error
            if not events:
                raise ValueError("La sorgente non ha restituito eventi validi")
            refreshed_at = datetime.now(timezone.utc).isoformat()
            self._replace_source_state(
                source, events, origin="network", timestamp=refreshed_at
            )
            if not self._cache.save(source, list(events), refreshed_at):
                logger.warning(
                    "%s: impossibile aggiornare la cache persistente", source.value
                )
            with self._data_lock:
                self._errors[source] = ""
            name = "calendar_refreshed"
            payload.update(
                count=len(events), timestamp=refreshed_at, data_origin="network"
            )
            logger.info("%s: refresh completato, %d eventi", source.value, len(events))
        except Exception as exc:
            logger.error("%s: errore refresh", source.value, exc_info=exc)
            with self._data_lock:
                self._errors[source] = str(exc)
            payload.update(error=str(exc), data_origin=self.get_data_origin(source))
        finally:
            self._refreshing[source].clear()
        self._notify(name, payload)

    def filter_events(
        self,
        source: CalendarSource,
        region: str = "ALL",
        impact: str = "ALL",
        date: str = "",
        timezone_name: str = "UTC",
    ) -> list[CalendarEvent]:
        with self._data_lock:
            events = list(self._events[source])

        events = self._filter_past_events(events)
        events = self._convert_events_timezone(events, timezone_name)

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
        parsed = try_parse_utc(event.utc_dt)
        if parsed is None:
            logger.warning(
                "Timestamp non valido o naive ignorato per %s: %s",
                event.event_name,
                event.utc_dt,
            )
        return parsed

    @staticmethod
    def _filter_past_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=CalendarDefaults.PAST_EVENT_CUTOFF_HOURS
        )
        return [
            event
            for event in events
            if (dt_utc := AppController._parse_event_utc(event)) is None
            or dt_utc >= cutoff
        ]

    @staticmethod
    def _convert_events_timezone(
        events: list[CalendarEvent],
        timezone_name: str,
    ) -> list[CalendarEvent]:
        target_tz = resolve_timezone(timezone_name or "UTC")
        converted: list[CalendarEvent] = []
        for event in events:
            dt_utc = AppController._parse_event_utc(event)
            if dt_utc is None:
                converted.append(event)
                continue
            dt_local = dt_utc.astimezone(target_tz)
            converted.append(
                replace(
                    event,
                    time=dt_local.strftime("%H:%M"),
                    date=dt_local.strftime("%d/%m/%Y"),
                )
            )
        return converted

    def get_source_error(self, source: CalendarSource) -> str:
        with self._data_lock:
            return self._errors[source]

    def get_last_refresh(self, source: CalendarSource) -> str:
        """UTC timestamp of the data currently shown (network or cache), or ""."""
        with self._data_lock:
            return self._timestamp[source]

    def get_data_origin(self, source: CalendarSource) -> str:
        with self._data_lock:
            return self._origin[source]

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
        for refreshing in self._refreshing.values():
            refreshing.clear()
        logger.info("Controller arrestato")
