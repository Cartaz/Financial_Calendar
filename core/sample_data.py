"""Dati di esempio per gli scraper IG e FXStreet.

Fornisce eventi di fallback quando le API non sono raggiungibili.
Questi dati sono generati dinamicamente con la data/ora corrente.
"""

from __future__ import annotations

from datetime import datetime

from core.models import CalendarEvent, CalendarSource, ImpactLevel


def sample_ig_events() -> list[CalendarEvent]:
    """Genera eventi di esempio per IG quando l'API fallisce.

    Returns:
        Lista di CalendarEvent di esempio.
    """
    now = datetime.now()
    today = now.strftime("%d/%m/%Y")
    time_now = now.strftime("%H:%M")
    return [
        CalendarEvent(
            time=time_now, date=today, country="EUR", impact=ImpactLevel.HIGH,
            event_name="Tasso di interesse BCE", actual="4.50%",
            forecast="4.50%", previous="4.50%",
            source=CalendarSource.IG,
        ),
        CalendarEvent(
            time=time_now, date=today, country="USA", impact=ImpactLevel.HIGH,
            event_name="Non-Farm Payrolls", actual="216K",
            forecast="170K", previous="187K",
            source=CalendarSource.IG,
        ),
        CalendarEvent(
            time=time_now, date=today, country="JPN", impact=ImpactLevel.MID,
            event_name="Indice produzione industriale", actual="-0.1%",
            forecast="0.2%", previous="0.3%",
            source=CalendarSource.IG,
        ),
        CalendarEvent(
            time=time_now, date=today, country="GBP", impact=ImpactLevel.HIGH,
            event_name="Decisione tasso Bank of England", actual="5.25%",
            forecast="5.25%", previous="5.25%",
            source=CalendarSource.IG,
        ),
        CalendarEvent(
            time=time_now, date=today, country="EUR", impact=ImpactLevel.MID,
            event_name="PMI manifatturiero", actual="44.2",
            forecast="44.1", previous="43.8",
            source=CalendarSource.IG,
        ),
        CalendarEvent(
            time=time_now, date=today, country="USA", impact=ImpactLevel.LOW,
            event_name="Richieste sussidi disoccupazione", actual="220K",
            forecast="218K", previous="221K",
            source=CalendarSource.IG,
        ),
    ]


def sample_fxstreet_events() -> list[CalendarEvent]:
    """Genera eventi di esempio per FXStreet quando l'API fallisce.

    Returns:
        Lista di CalendarEvent di esempio.
    """
    now = datetime.now()
    today = now.strftime("%d/%m/%Y")
    time_now = now.strftime("%H:%M")
    return [
        CalendarEvent(
            time=time_now, date=today, country="USA", impact=ImpactLevel.HIGH,
            event_name="CPI YoY", actual="3.2%",
            forecast="3.3%", previous="3.4%",
            deviation="-0.1", source=CalendarSource.FXSTREET,
        ),
        CalendarEvent(
            time=time_now, date=today, country="EUR", impact=ImpactLevel.HIGH,
            event_name="German ZEW Economic Sentiment", actual="12.8",
            forecast="9.5", previous="8.6",
            deviation="3.3", source=CalendarSource.FXSTREET,
        ),
        CalendarEvent(
            time=time_now, date=today, country="JPN", impact=ImpactLevel.MID,
            event_name="Trade Balance", actual="-662.5B",
            forecast="-540.0B", previous="-566.5B",
            deviation="-122.5", source=CalendarSource.FXSTREET,
        ),
    ]
