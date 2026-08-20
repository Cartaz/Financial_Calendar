"""Funzioni di utilità condivise dagli scraper.

Contiene funzioni di pulizia dei dati, formattazione dei valori
e salvataggio dei JSON di debug.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def save_debug_json(data: object, name: str) -> None:
    """Salva il JSON grezzo per debug in XDG_DATA_HOME.

    Args:
        data: Dati JSON da salvare.
        name: Nome del file (senza estensione).
    """
    try:
        xdg_data = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        debug_dir = xdg_data / "financial_calendar" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        out_file = debug_dir / f"{name}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        logger.debug("Debug JSON salvato: %s", out_file)
    except Exception as exc:
        logger.debug("Impossibile salvare debug JSON: %s", exc)


def clean_string(value: object) -> str:
    """Pulisce un valore dall'API restituendo una stringa vuota se nullo.

    Args:
        value: Valore dall'API (stringa, None, ecc.).

    Returns:
        Stringa pulita o stringa vuota.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if s in ("None", "null", "N/A", "-"):
        return ""
    return s


def format_value(value: float | int | None, unit: str | None = None) -> str:
    """Formatta un valore numerico per la visualizzazione.

    L'API FXStreet restituisce valori numerici (float/null).
    Se presente, aggiunge l'unità di misura.

    Args:
        value: Valore numerico o None.
        unit: Unità di misura opzionale (es. '%', 'B', 'M').

    Returns:
        Stringa formattata del valore.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        formatted = str(int(value))
    else:
        formatted = str(value)
    if unit:
        formatted = f"{formatted}{unit}"
    return formatted
