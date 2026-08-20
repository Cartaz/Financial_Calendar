"""Modelli dati per gli eventi del calendario finanziario.

Definisce le strutture dati usate per rappresentare gli eventi
economici provenienti da IG e FXStreet. Usa dataclass per
immutabilità e type safety.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CalendarSource(Enum):
    """Fonte del calendario economico."""

    IG = "ig"
    FXSTREET = "fxstreet"


class ImpactLevel(Enum):
    """Livello di impatto dell'evento economico."""

    HIGH = "HIGH"
    MID = "MID"
    LOW = "LOW"


@dataclass(frozen=True)
class CalendarEvent:
    """Evento singolo del calendario economico.

    Attributes:
        time: Orario dell'evento (formattato per visualizzazione).
        country: Codice paese/regione (es. EUR, USA, JPN).
        impact: Livello di impatto (HIGH, MID, LOW).
        event_name: Nome descrittivo dell'evento.
        actual: Valore attuale rilevato.
        forecast: Valore previsto (IG) o consensus (FXStreet).
        previous: Valore precedente.
        date: Data dell'evento (formattata per visualizzazione).
        utc_dt: Stringa ISO 8601 della data/ora UTC originale
            (es. "2026-05-13T14:30:00+00:00"). Usata per la
            conversione di fuso orario. Se vuota, la conversione
            non è disponibile per questo evento.
        deviation: Deviazione dal consensus (solo FXStreet).
        source: Fonte del calendario (IG o FXStreet).
    """

    time: str
    country: str
    impact: ImpactLevel
    event_name: str
    actual: str
    forecast: str
    previous: str
    date: str = ""
    utc_dt: str = ""
    deviation: str = ""
    source: CalendarSource = CalendarSource.IG

    def to_ig_row(self) -> list[str]:
        """Converte l'evento in riga per tabella IG.

        Returns:
            Lista di valori [Data, Ora, Paese, Importanza, Evento,
            Attuale, Previsione, Precedente].
        """
        impact_map = {
            ImpactLevel.HIGH: "ALTO",
            ImpactLevel.MID: "MEDIO",
            ImpactLevel.LOW: "BASSO",
        }
        return [
            self.date,
            self.time,
            self.country,
            impact_map.get(self.impact, "BASSO"),
            self.event_name,
            self.actual,
            self.forecast,
            self.previous,
        ]

    def to_fxstreet_row(self) -> list[str]:
        """Converte l'evento in riga per tabella FXStreet.

        Returns:
            Lista di valori [Data, Ora, Paese, Evento, Impatto, Attuale,
            Dev, Consensus, Precedente].
        """
        return [
            self.date,
            self.time,
            self.country,
            self.event_name,
            self.impact.value,
            self.actual,
            self.deviation,
            self.forecast,
            self.previous,
        ]
