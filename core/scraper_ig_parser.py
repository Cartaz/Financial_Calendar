"""Parser date per i dati del calendario IG.

Contiene la funzione parse_ig_date usata dallo scraper IG per
convertire i timestamp ISO del JSON di ForexFactory nei tre
formati richiesti da CalendarEvent (ora, data display, utc_dt).
"""

from __future__ import annotations

from datetime import datetime


def parse_ig_date(date_str: str) -> tuple[str, str, str]:
    """Analizza una stringa data IG restituendo (ora, data_display, utc_dt).

    Supporta formati ISO con/senza timezone e date semplici.

    Args:
        date_str: Stringa data dal JSON IG.

    Returns:
        Tupla (time_str, date_display, utc_dt_str).
    """
    if not date_str:
        return ("", "", "")
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (dt.strftime("%H:%M"), dt.strftime("%d/%m/%Y"),
                date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        pass
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return ("", dt.strftime("%d/%m/%Y"), "")
    except (ValueError, TypeError):
        return ("", "", "")
