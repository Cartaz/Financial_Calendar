"""Impostazioni utente persistenti in formato JSON.

Le impostazioni sono salvate nella directory XDG appropriata conforme
alla specifica Freedesktop. Ogni modifica emette un evento config_changed
tramite l'event bus (se disponibile).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any

from config.constants import CalendarDefaults, PathConfig

logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    """Schema delle impostazioni utente con valori predefiniti.

    Attributes:
        ig_column_order: Ordine delle colonne IG (lista di indici).
        fxstreet_column_order: Ordine delle colonne FXStreet.
        selected_region: Regione filtro selezionata.
        selected_impact: Livello impatto filtro selezionato.
        last_refresh_ig: Timestamp ultimo aggiornamento IG.
        last_refresh_fxstreet: Timestamp ultimo aggiornamento FXStreet.
    """

    ig_column_order: list[int] = field(
        default_factory=lambda: list(range(len(CalendarDefaults.IG_COLUMNS)))
    )
    fxstreet_column_order: list[int] = field(
        default_factory=lambda: list(range(len(CalendarDefaults.FXSTREET_COLUMNS)))
    )
    selected_region: str = "ALL"
    selected_impact: str = "ALL"
    last_refresh_ig: str = ""
    last_refresh_fxstreet: str = ""


class Settings:
    """Gestore delle impostazioni utente con persistenza JSON.

    Fornisce caricamento, salvataggio e accesso thread-safe alle
    impostazioni. Ogni modifica emette un evento config_changed
    tramite l'event bus (se disponibile).
    """

    def __init__(self) -> None:
        """Inizializza il gestore impostazioni con valori predefiniti."""
        self._data = UserSettings()

    def load(self) -> None:
        """Carica le impostazioni dal file JSON.

        Se il file non esiste o è corrotto, mantiene i valori predefiniti
        e logga un avviso.
        """
        try:
            if PathConfig.SETTINGS_FILE.exists():
                with open(PathConfig.SETTINGS_FILE, "r", encoding="utf-8") as fh:
                    raw: dict[str, Any] = json.load(fh)
                self._data = UserSettings(**raw)
                logger.info("Impostazioni caricate da %s", PathConfig.SETTINGS_FILE)
            else:
                logger.info("Nessun file impostazioni trovato, uso valori predefiniti")
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("File impostazioni corrotto, uso valori predefiniti: %s", exc)
            self._data = UserSettings()

    def save(self) -> None:
        """Salva le impostazioni correnti nel file JSON."""
        PathConfig.ensure_dirs()
        try:
            with open(PathConfig.SETTINGS_FILE, "w", encoding="utf-8") as fh:
                json.dump(asdict(self._data), fh, indent=2, ensure_ascii=False)
            logger.info("Impostazioni salvate in %s", PathConfig.SETTINGS_FILE)
        except OSError as exc:
            logger.error("Errore nel salvataggio delle impostazioni: %s", exc)

    def get(self, key: str) -> Any:
        """Recupera il valore di un'impostazione per chiave.

        Args:
            key: Nome dell'attributo in UserSettings.

        Returns:
            Il valore dell'impostazione richiesta.

        Raises:
            AttributeError: Se la chiave non esiste nello schema.
        """
        return getattr(self._data, key)

    def set(self, key: str, value: Any) -> None:
        """Imposta il valore di un'impostazione e salva.

        Dopo il salvataggio, emette un evento config_changed tramite
        l'event bus con la chiave e il nuovo valore.

        Args:
            key: Nome dell'attributo in UserSettings.
            value: Nuovo valore da assegnare.

        Raises:
            AttributeError: Se la chiave non esiste nello schema.
        """
        setattr(self._data, key, value)
        self.save()
        self._emit_config_changed(key, value)

    def _emit_config_changed(self, key: str, value: Any) -> None:
        """Emette l'evento config_changed tramite l'event bus.

        Usa un import differito per evitare dipendenze circolari
        a livello di modulo.

        Args:
            key: Chiave dell'impostazione modificata.
            value: Nuovo valore assegnato.
        """
        try:
            from core.event_bus import EventBus
            bus = EventBus()
            bus.emit("config_changed", {"key": key, "value": str(value)})
            logger.debug("Evento config_changed emesso: %s=%s", key, value)
        except Exception as exc:
            logger.debug("Impossibile emettere config_changed: %s", exc)

    def reset(self) -> None:
        """Ripristina tutte le impostazioni ai valori predefiniti."""
        self._data = UserSettings()
        self.save()
        logger.info("Impostazioni ripristinate ai valori predefiniti")
