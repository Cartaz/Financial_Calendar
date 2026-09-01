"""Funzioni di utilità condivise dagli scraper.

Contiene funzioni di pulizia dei dati, formattazione dei valori
e salvataggio dei JSON di debug.
"""

from __future__ import annotations

import json
import logging

from config.constants import PathConfig

logger = logging.getLogger(__name__)


def save_debug_json(data: object, name: str) -> None:
    """Salva il JSON grezzo per debug nella directory dati applicativa."""
    try:
        debug_dir = PathConfig.APP_DATA_DIR / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        out_file = debug_dir / f"{name}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        logger.debug("Debug JSON salvato: %s", out_file)
    except OSError as exc:
        logger.debug("Impossibile salvare debug JSON: %s", exc)


def clean_string(value: object) -> str:
    """Pulisce un valore dall'API restituendo una stringa vuota se nullo."""
    if value is None:
        return ""
    s = str(value).strip()
    if s in ("None", "null", "N/A", "-"):
        return ""
    return s


def format_value(value: float | int | None, unit: str | None = None) -> str:
    """Formatta un valore numerico per la visualizzazione."""
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        formatted = str(int(value))
    else:
        formatted = str(value)
    if unit:
        formatted = f"{formatted}{unit}"
    return formatted
