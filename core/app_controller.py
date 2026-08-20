"""Controller principale dell'applicazione.

Orchestra lo scraping, la gestione dei dati e la comunicazione
con il livello UI tramite notification callback. Non importa mai da ui/.

I callback dei futures vengono eseguiti nel thread pool. Per
aggiornare la UI in modo sicuro, il controller usa un
notification_callback che l'UI deve impostare per marshalling
cross-thread tramite segnali Qt.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Callable

from core.event_bus import EventBus
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from core.scraper_ig import scrape_ig_calendar
from core.scraper_fxstreet import scrape_fxstreet_calendar
from config.constants import CalendarDefaults
from config.settings import Settings

logger = logging.getLogger(__name__)


class AppController:
    """Controller principale che coordina la logica di business.

    Gestisce lo scraping in background, il filtraggio degli eventi
    e la comunicazione con l'UI tramite notification_callback.

    Attributes:
        settings: Gestore delle impostazioni utente.
        events_ig: Lista eventi IG correnti.
        events_fxstreet: Lista eventi FXStreet correnti.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Inizializza il controller con impostazioni e event bus.

        Args:
            settings: Istanza Settings; se None, crea una nuova.
        """
        self._bus = EventBus()
        self.settings = settings or Settings()
        self.events_ig: list[CalendarEvent] = []
        self.events_fxstreet: list[CalendarEvent] = []
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scraper")
        self._notification_callback: Callable[[str, dict], None] | None = None
        self._refreshing_ig = threading.Event()
        self._refreshing_fxstreet = threading.Event()

    def set_notification_callback(self, callback: Callable[[str, dict], None]) -> None:
        """Imposta il callback per notifiche thread-safe verso la UI.

        Args:
            callback: Funzione (event_name: str, payload: dict) -> None.
        """
        self._notification_callback = callback

    def _notify(self, event_name: str, payload: dict) -> None:
        """Invia una notifica tramite il callback thread-safe.

        Args:
            event_name: Nome dell'evento.
            payload: Dati associati all'evento.
        """
        if self._notification_callback is not None:
            self._notification_callback(event_name, payload)
        else:
            self._bus.emit(event_name, payload)

    def subscribe(self, event: str, handler: Callable) -> None:
        """Iscrive un handler a un evento dell'event bus."""
        self._bus.subscribe(event, handler)

    def is_refreshing(self, source: CalendarSource) -> bool:
        """Verifica se un refresh è in corso.

        Args:
            source: Fonte del calendario.

        Returns:
            True se un refresh è in corso.
        """
        return (
            self._refreshing_ig.is_set()
            if source == CalendarSource.IG
            else self._refreshing_fxstreet.is_set()
        )

    def refresh_ig(self) -> None:
        """Aggiorna il calendario IG in background."""
        if self._refreshing_ig.is_set():
            logger.debug("IG: refresh già in corso, richiesta ignorata")
            return
        self._refreshing_ig.set()
        logger.info("IG: avvio refresh")
        self._notify("calendar_refresh_started", {"source": "ig"})
        future = self._executor.submit(scrape_ig_calendar)
        future.add_done_callback(self._on_ig_refresh_done)

    def refresh_fxstreet(self) -> None:
        """Aggiorna il calendario FXStreet in background."""
        if self._refreshing_fxstreet.is_set():
            logger.debug("FXStreet: refresh già in corso, richiesta ignorata")
            return
        self._refreshing_fxstreet.set()
        logger.info("FXStreet: avvio refresh")
        self._notify("calendar_refresh_started", {"source": "fxstreet"})
        future = self._executor.submit(scrape_fxstreet_calendar)
        future.add_done_callback(self._on_fxstreet_refresh_done)

    def refresh_all(self) -> None:
        """Aggiorna entrambi i calendari in parallelo."""
        self.refresh_ig()
        self.refresh_fxstreet()

    def _on_ig_refresh_done(self, future: Future) -> None:
        """Callback completamento IG (thread pool).

        Args:
            future: Future con il risultato dello scraping.
        """
        self._refreshing_ig.clear()
        try:
            self.events_ig = future.result()
            ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.settings.set("last_refresh_ig", ts)
            logger.info("IG: refresh completato, %d eventi", len(self.events_ig))
            self._notify("calendar_refreshed", {"source": "ig", "count": len(self.events_ig), "timestamp": ts})
        except Exception as exc:
            logger.error("IG: errore nel refresh: %s", exc)
            self._notify("calendar_refresh_error", {"source": "ig", "error": str(exc)})

    def _on_fxstreet_refresh_done(self, future: Future) -> None:
        """Callback completamento FXStreet (thread pool).

        Args:
            future: Future con il risultato dello scraping.
        """
        self._refreshing_fxstreet.clear()
        try:
            self.events_fxstreet = future.result()
            ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.settings.set("last_refresh_fxstreet", ts)
            logger.info("FXStreet: refresh completato, %d eventi", len(self.events_fxstreet))
            self._notify("calendar_refreshed", {"source": "fxstreet", "count": len(self.events_fxstreet), "timestamp": ts})
        except Exception as exc:
            logger.error("FXStreet: errore nel refresh: %s", exc)
            self._notify("calendar_refresh_error", {"source": "fxstreet", "error": str(exc)})

    def filter_events(
        self, source: CalendarSource, region: str = "ALL",
        impact: str = "ALL", date: str = "", tz_offset_hours: float = 0.0,
    ) -> list[CalendarEvent]:
        """Filtra gli eventi per data, regione e impatto con conversione fuso.

        Args:
            source: Fonte del calendario.
            region: Codice regione o "ALL".
            impact: Livello impatto o "ALL".
            date: Data in formato dd/mm/yyyy o stringa vuota.
            tz_offset_hours: Offset dal fuso UTC in ore.

        Returns:
            Lista di CalendarEvent filtrati con orari convertiti.
        """
        events = self.events_ig if source == CalendarSource.IG else self.events_fxstreet
        events = self._filter_past_events(events)
        if tz_offset_hours != 0.0:
            events = self._convert_events_tz(events, tz_offset_hours)
        if date:
            events = [e for e in events if e.date == date]
        if region != "ALL":
            events = [e for e in events if e.country == region]
        if impact != "ALL":
            events = [e for e in events if e.impact == ImpactLevel(impact)]
        return events

    @staticmethod
    def _filter_past_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Rimuove gli eventi più vecchi di PAST_EVENT_CUTOFF_HOURS da ora.

        Confronta l'utc_dt di ciascun evento con (now - cutoff) in UTC.
        Gli eventi senza utc_dt (es. dati di esempio o parsing fallito)
        sono mantenuti: non potendoli datare, non possiamo filtrarli.

        Args:
            events: Lista di CalendarEvent da filtrare.

        Returns:
            Lista di CalendarEvent con solo eventi recenti/futuri.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=CalendarDefaults.PAST_EVENT_CUTOFF_HOURS
        )
        kept: list[CalendarEvent] = []
        filtered_out = 0
        for ev in events:
            if not ev.utc_dt:
                kept.append(ev)
                continue
            try:
                dt_utc = datetime.fromisoformat(ev.utc_dt)
            except (ValueError, TypeError):
                kept.append(ev)
                continue
            if dt_utc >= cutoff:
                kept.append(ev)
            else:
                filtered_out += 1
        if filtered_out:
            logger.debug(
                "Filtrati %d eventi più vecchi di %dh (cutoff UTC=%s)",
                filtered_out, CalendarDefaults.PAST_EVENT_CUTOFF_HOURS,
                cutoff.isoformat(),
            )
        return kept

    @staticmethod
    def _convert_events_tz(events: list[CalendarEvent], offset_hours: float) -> list[CalendarEvent]:
        """Converte gli orari UTC degli eventi nel fuso specificato.

        Args:
            events: Lista di CalendarEvent con orari UTC.
            offset_hours: Offset dal fuso UTC in ore.

        Returns:
            Lista di CalendarEvent con date e ore convertite.
        """
        offset = timedelta(hours=offset_hours)
        converted: list[CalendarEvent] = []
        for ev in events:
            if not ev.utc_dt:
                converted.append(ev)
                continue
            try:
                dt_utc = datetime.fromisoformat(ev.utc_dt)
                dt_local = dt_utc + offset
                converted.append(CalendarEvent(
                    time=dt_local.strftime("%H:%M"), country=ev.country,
                    impact=ev.impact, event_name=ev.event_name,
                    actual=ev.actual, forecast=ev.forecast, previous=ev.previous,
                    date=dt_local.strftime("%d/%m/%Y"), utc_dt=ev.utc_dt,
                    deviation=ev.deviation, source=ev.source,
                ))
            except (ValueError, TypeError) as exc:
                logger.debug("Impossibile convertire fuso per %s: %s", ev.event_name, exc)
                converted.append(ev)
        return converted

    def get_last_refresh(self, source: CalendarSource) -> str:
        """Recupera il timestamp dell'ultimo aggiornamento.

        Args:
            source: Fonte del calendario.

        Returns:
            Stringa con data/ora dell'ultimo aggiornamento.
        """
        key = "last_refresh_ig" if source == CalendarSource.IG else "last_refresh_fxstreet"
        return self.settings.get(key)

    def shutdown(self) -> None:
        """Arresta il controller e il thread pool."""
        self._executor.shutdown(wait=False)
        logger.info("Controller arrestato")
