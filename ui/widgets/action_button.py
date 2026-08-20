"""Pulsante d'azione con indicatore di stato e badge scorciatoia.

Combina un pulsante d'azione, un badge scorciatoia e un indicatore
di stato in un'unica unità visiva coerente con il tema Neumorphism.
Il pulsante è un elemento estruso (ombra esterna) che al click viene
incavato per simulare la pressione fisica.
La scorciatoia è registrata nel sistema globale tramite QShortcut.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from config.constants import UIConstraints
from ui.widgets.neumorphic import apply_extrude, clear_effect
from ui.widgets.shortcut_badge import ShortcutBadge
from ui.widgets.status_indicator import StatusIndicator


class ActionButton(QWidget):
    """Pulsante d'azione con indicatore di stato e badge scorciatoia.

    L'indicatore di stato animato mostra visivamente lo stato del
    processo. Il badge scorciatoia registra la combinazione di tasti
    nel sistema globale. Il pulsante applica l'effetto neumorphic
    estruso (ombra esterna) e lo inverte al click per simulare
    la pressione fisica.

    Args:
        label: Testo del pulsante.
        shortcut: Scorciatoia tastiera (es. "Ctrl+R").
        parent: Widget genitore.

    Signals:
        action_requested: Emesso quando l'utente clicca il pulsante
            o preme la scorciatoia.
    """

    action_requested = Signal()

    def __init__(
        self,
        label: str,
        shortcut: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """Inizializza il pulsante d'azione con tutti i componenti.

        Args:
            label: Testo del pulsante.
            shortcut: Scorciatoia tastiera (es. "Ctrl+R").
            parent: Widget genitore.
        """
        super().__init__(parent)
        self._setup_ui(label, shortcut)

    def _setup_ui(self, label: str, shortcut: str) -> None:
        """Configura il layout del widget con pulsante, indicatore e badge.

        Args:
            label: Testo del pulsante.
            shortcut: Scorciatoia tastiera.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._indicator = StatusIndicator(self)

        self._button = QPushButton(label, self)
        # Lo stile QSS globale (NeumorphicStyle) già fornisce:
        # - estrusione via border top/left chiari + bottom/right scuri
        # - hover (color: PRIMARY)
        # - pressed (border invertiti → inset)
        # Aggiungiamo qui solo l'ombra esterna vera via QGraphicsEffect.
        self._button.setCursor(self._button.cursor())
        # Padding coerente con le linee guida (più aria di Breeze)
        self._button.setStyleSheet(
            f"padding: {UIConstraints.BUTTON_PADDING_V}px "
            f"{UIConstraints.BUTTON_PADDING_H}px;"
        )
        # Applica ombra estrusa (via QGraphicsDropShadowEffect)
        apply_extrude(self._button)

        self._button.pressed.connect(self._on_pressed)
        self._button.released.connect(self._on_released)
        self._button.clicked.connect(self.action_requested.emit)

        layout.addWidget(self._indicator)
        layout.addWidget(self._button)

        if shortcut:
            self._badge = ShortcutBadge(shortcut, self)
            layout.addWidget(self._badge)
            self._shortcut = QShortcut(QKeySequence(shortcut), self)
            self._shortcut.activated.connect(self.action_requested.emit)

    def _on_pressed(self) -> None:
        """Gestisce la pressione: rimuove ombra esterna per simulare l'inset.

        Il QSS `:pressed` già inverte i border (top/left scuri,
        bottom/right chiari); rimuoviamo anche l'effetto grafico esterno
        così il pulsante "affonda" davvero nel materiale.
        """
        clear_effect(self._button)

    def _on_released(self) -> None:
        """Gestisce il rilascio: ripristina l'ombra estrusa."""
        apply_extrude(self._button)

    def set_status(self, state: StatusIndicator.State) -> None:
        """Aggiorna lo stato visivo dell'indicatore.

        Args:
            state: Nuovo stato del processo.
        """
        self._indicator.set_state(state)

    def set_enabled(self, enabled: bool) -> None:
        """Abilita o disabilita il pulsante.

        Quando disabilitato, l'ombra estrusa viene rimossa per ridurre
        l'evidenza visiva (linee guida §07: ridurre opacità e rimuovere
        le ombre, non solo attenuarle).

        Args:
            enabled: True per abilitare, False per disabilitare.
        """
        self._button.setEnabled(enabled)
        if enabled:
            apply_extrude(self._button)
        else:
            clear_effect(self._button)
