"""Indicatore di stato — punto colorato animato.

Mostra lo stato di un processo tramite un punto colorato estruso.
Supporta gli stati RUNNING, ERROR, STOPPED e PAUSED con colori
semanticamente definiti in ThemeColors. Il diametro (10px) e i bordi
esterni sono studiati per rimanere visibili sulle superfici neumorphic
a basso contrasto (linee guida §07 accessibilità).
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel

from config.theme import ThemeColors
from config.constants import UIConstraints
from ui.styles.components import ComponentStyles


class StatusIndicator(QLabel):
    """Indicatore visivo dello stato di un processo.

    Mostra un punto colorato estruso (10px) con animazione pulsante
    per lo stato RUNNING. Gli stati possibili sono definiti
    nell'enum State.

    Attributes:
        state: Stato corrente dell'indicatore.
    """

    class State(Enum):
        """Stati possibili dell'indicatore."""

        RUNNING = "running"
        ERROR = "error"
        STOPPED = "stopped"
        PAUSED = "paused"

    _STATE_COLORS = {
        State.RUNNING: ThemeColors.STATUS_RUNNING,
        State.ERROR: ThemeColors.STATUS_ERROR,
        State.STOPPED: ThemeColors.STATUS_STOPPED,
        State.PAUSED: ThemeColors.STATUS_PAUSED,
    }

    def __init__(self, parent: object | None = None) -> None:
        """Inizializza l'indicatore con stato STOPPED.

        Args:
            parent: Widget genitore.
        """
        super().__init__(parent)
        self.state = self.State.STOPPED
        self._opacity = 1.0
        self._pulse_direction = -1

        self._timer = QTimer(self)
        self._timer.setInterval(75)
        self._timer.timeout.connect(self._animate_pulse)

        self.setFixedSize(UIConstraints.INDICATOR_DIAMETER, UIConstraints.INDICATOR_DIAMETER)
        self._update_style()

    def set_state(self, state: State) -> None:
        """Aggiorna lo stato visivo dell'indicatore.

        Attiva l'animazione pulsante per RUNNING, la disattiva
        per tutti gli altri stati.

        Args:
            state: Nuovo stato dell'indicatore.
        """
        self.state = state
        self._opacity = 1.0
        self._pulse_direction = -1

        if state == self.State.RUNNING:
            self._timer.start()
        else:
            self._timer.stop()
            self._update_style()

    def _animate_pulse(self) -> None:
        """Animazione pulsante: opacity oscillante tra 0.5 e 1.0."""
        self._opacity += self._pulse_direction * 0.05
        if self._opacity <= 0.5:
            self._opacity = 0.5
            self._pulse_direction = 1
        elif self._opacity >= 1.0:
            self._opacity = 1.0
            self._pulse_direction = -1
        self._update_style()

    def _update_style(self) -> None:
        """Aggiorna lo stile QSS in base allo stato e all'opacity."""
        color = self._STATE_COLORS.get(self.state, ThemeColors.STATUS_STOPPED)
        if self.state == self.State.RUNNING and self._opacity < 1.0:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            color = f"rgba({r}, {g}, {b}, {self._opacity:.2f})"
        self.setStyleSheet(ComponentStyles.status_indicator_style(color))
