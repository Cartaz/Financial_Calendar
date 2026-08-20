"""Event bus singleton per la comunicazione tra moduli.

Implementa un canale di comunicazione asincrona tra tutti i moduli
dell'applicazione. Supporta registrazione, emissione e deregistrazione
di eventi. I nomi degli eventi seguono il pattern modulo_azione_stato.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """Canale di comunicazione centrale tra moduli.

    Implementa il pattern singleton per garantire un'unica istanza
    condivisa in tutta l'applicazione. Gli handler vengono eseguiti
    sincronamente nel thread dell'emittente.
    """

    _instance: EventBus | None = None
    _handlers: dict[str, list[EventHandler]]

    def __new__(cls) -> EventBus:
        """Crea o restituisce l'istanza singleton dell'event bus."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = defaultdict(list)
        return cls._instance

    def subscribe(self, event: str, handler: EventHandler) -> None:
        """Registra un handler per un tipo di evento.

        Args:
            event: Nome dell'evento (es. 'calendar_refreshed').
            handler: Funzione callback che riceve il payload dell'evento.
        """
        self._handlers[event].append(handler)
        logger.debug("Handler iscritto all'evento '%s': %s", event, handler.__name__)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        """Deregistra un handler per un tipo di evento.

        Args:
            event: Nome dell'evento.
            handler: Funzione callback da rimuovere.
        """
        if event in self._handlers:
            try:
                self._handlers[event].remove(handler)
                logger.debug("Handler rimosso dall'evento '%s': %s", event, handler.__name__)
            except ValueError:
                logger.warning("Handler non trovato per l'evento '%s'", event)

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Emette un evento notificando tutti gli handler registrati.

        Args:
            event: Nome dell'evento da emettere.
            payload: Dati associati all'evento.
        """
        data = payload or {}
        handlers = self._handlers.get(event, [])
        logger.debug("Evento '%s' emesso con %d handler", event, len(handlers))
        for handler in handlers:
            try:
                handler(data)
            except Exception as exc:
                logger.error(
                    "Errore nell'handler %s per l'evento '%s': %s",
                    handler.__name__,
                    event,
                    exc,
                )

    @classmethod
    def reset(cls) -> None:
        """Resetta l'istanza singleton (solo per testing)."""
        cls._instance = None
