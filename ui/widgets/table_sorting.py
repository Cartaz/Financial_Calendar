"""Funzioni di ordinamento per la tabella del calendario.

Fornisce chiavi di ordinamento personalizzate per date, livelli
di impatto e valori numerici con unità di misura. Usate da
SortableItem e CalendarTable per un ordinamento semanticamente
corretto.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Callable

from core.models import CalendarEvent, ImpactLevel


def extract_numeric_sort_key(text: str) -> float | str:
    """Estrae una chiave numerica da un testo per l'ordinamento.

    Gestisce valori come "3.2%", "-0.1", "216K", "662.5B", ecc.
    Se il testo non contiene un numero, restituisce il testo stesso.

    Args:
        text: Testo da cui estrarre il valore numerico.

    Returns:
        Valore numerico float o stringa originale.
    """
    if not text:
        return float("inf")

    cleaned = text.strip().replace(",", ".")

    multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    for suffix, mult in multipliers.items():
        if cleaned.upper().endswith(suffix):
            num_part = cleaned[:-1].rstrip()
            try:
                return float(num_part) * mult
            except ValueError:
                break

    match = re.match(r"^([+-]?[\d.]+)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return text


def date_sort_key(date_str: str) -> str:
    """Converte una data dd/mm/yyyy in chiave YYYYMMDD per ordinamento.

    Args:
        date_str: Data in formato dd/mm/yyyy.

    Returns:
        Stringa YYYYMMDD per ordinamento cronologico, o stringa vuota.
    """
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y%m%d")
    except ValueError:
        return date_str


def impact_sort_key(impact: ImpactLevel) -> int:
    """Converte un livello di impatto in chiave numerica.

    HIGH=3, MID=2, LOW=1 per ordinamento per importanza.

    Args:
        impact: Livello di impatto.

    Returns:
        Intero per ordinamento.
    """
    return {ImpactLevel.HIGH: 3, ImpactLevel.MID: 2, ImpactLevel.LOW: 1}.get(impact, 0)


# Mappa (source_type → col_idx → funzione sort_key).
# Colonne non elencate usano extract_numeric_sort_key come fallback.
_SORT_KEY_MAP: dict[str, dict[int, Callable[[str, CalendarEvent], object]]] = {
    "ig": {
        0: lambda value, _ev: date_sort_key(value),
        3: lambda _value, ev: impact_sort_key(ev.impact),
        4: lambda value, _ev: value.lower(),
    },
    "fxstreet": {
        0: lambda value, _ev: date_sort_key(value),
        3: lambda value, _ev: value.lower(),
        4: lambda _value, ev: impact_sort_key(ev.impact),
    },
}


def compute_sort_key(
    source_type: str, col_idx: int, value: str, event: CalendarEvent
) -> object:
    """Calcola la chiave di ordinamento per una cella della tabella.

    Ogni tipo di colonna ha una chiave appropriata per un
    ordinamento semanticamente corretto.

    Args:
        source_type: 'ig' o 'fxstreet'.
        col_idx: Indice della colonna.
        value: Testo visualizzato nella cella.
        event: CalendarEvent di riferimento.

    Returns:
        Chiave di ordinamento (stringa, numero, ecc.).
    """
    source_map = _SORT_KEY_MAP.get(source_type, {})
    key_fn = source_map.get(col_idx)
    if key_fn is not None:
        return key_fn(value, event)
    # Colonne Paese (2 per IG, 2 per FXStreet) e Ora (1 per entrambe)
    # usano il testo così com'è, in modo che l'ordinamento sia lessicografico.
    if col_idx in (1, 2):
        return value
    return extract_numeric_sort_key(value)
