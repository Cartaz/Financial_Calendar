"""Selettore globale del fuso orario.

Fornisce un widget con QComboBox per selezionare il fuso orario
globale dell'applicazione. Quando l'utente cambia fuso, tutte
le tabelle del calendario vengono aggiornate con gli orari
convertiti. Include rilevamento automatico del fuso locale.
"""

from __future__ import annotations

import logging
import time

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from config.theme import ThemeColors, ThemeFonts

logger = logging.getLogger(__name__)

# Fusi orari comuni con offset da UTC in ore
# Include offset con mezz'ore per India (UTC+5:30), Afghanistan, ecc.
TIMEZONE_OFFSETS: list[tuple[str, float]] = [
    ("UTC-12:00", -12.0),
    ("UTC-11:00", -11.0),
    ("UTC-10:00", -10.0),
    ("UTC-09:00", -9.0),
    ("UTC-08:00 (PST)", -8.0),
    ("UTC-07:00 (MST)", -7.0),
    ("UTC-06:00 (CST)", -6.0),
    ("UTC-05:00 (EST)", -5.0),
    ("UTC-04:00", -4.0),
    ("UTC-03:00 (BRT)", -3.0),
    ("UTC-02:00", -2.0),
    ("UTC-01:00", -1.0),
    ("UTC+00:00 (GMT)", 0.0),
    ("UTC+01:00 (CET)", 1.0),
    ("UTC+02:00 (CEST)", 2.0),
    ("UTC+03:00 (MSK)", 3.0),
    ("UTC+03:30 (IRST)", 3.5),
    ("UTC+04:00 (GST)", 4.0),
    ("UTC+05:00 (PKT)", 5.0),
    ("UTC+05:30 (IST)", 5.5),
    ("UTC+06:00 (BST)", 6.0),
    ("UTC+07:00 (ICT)", 7.0),
    ("UTC+08:00 (CST/SGT)", 8.0),
    ("UTC+09:00 (JST/KST)", 9.0),
    ("UTC+09:30 (ACST)", 9.5),
    ("UTC+10:00 (AEST)", 10.0),
    ("UTC+11:00", 11.0),
    ("UTC+12:00 (NZST)", 12.0),
    ("UTC+13:00", 13.0),
    ("UTC+14:00", 14.0),
]


class TimezoneToolbar(QWidget):
    """Barra degli strumenti con selettore globale del fuso orario.

    Permette all'utente di selezionare il fuso orario che viene
    applicato globalmente a tutti i calendari. Rileva automaticamente
    il fuso locale all'avvio.

    Signals:
        timezone_changed: Emesso quando il fuso orario cambia,
            con il nuovo offset in ore (float).
    """

    timezone_changed = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Inizializza la barra del fuso orario.

        Args:
            parent: Widget genitore.
        """
        super().__init__(parent)
        self._tz_offset: float = 0.0
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura il layout della barra con label e combo box."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        tz_label = QLabel("FUSO ORARIO", self)
        tz_label.setStyleSheet(
            f"color: {ThemeColors.TEXT_FAINT}; "
            f"font-weight: {ThemeFonts.WEIGHT_MEDIUM}; "
            f"font-size: {ThemeFonts.SIZE_CARD_HEADER}px; "
            f"font-family: '{ThemeFonts.FAMILY_MONO}'; "
            f"letter-spacing: 0.12em; "
            f"background-color: transparent;"
        )
        layout.addWidget(tz_label)

        self._tz_combo = QComboBox(self)
        tz_display = [label for label, _ in TIMEZONE_OFFSETS]
        self._tz_combo.addItems(tz_display)
        self._auto_detect_timezone()
        self._tz_combo.currentIndexChanged.connect(self._on_timezone_changed)
        # Lo stile QSS globale già fornisce aspetto neumorphic incavato.
        # Aggiungiamo solo il min-width per evitare che la combo sia troppo stretta.
        self._tz_combo.setStyleSheet(
            f"QComboBox {{ min-width: 220px; }}"
        )
        layout.addWidget(self._tz_combo)

        self._tz_info_label = QLabel("", self)
        self._tz_info_label.setStyleSheet(
            f"color: {ThemeColors.TEXT_SECONDARY}; "
            f"font-size: {ThemeFonts.SIZE_SHORTCUT_BADGE}px; "
            f"font-family: '{ThemeFonts.FAMILY_MONO}'; "
            f"background-color: transparent;"
        )
        self._update_tz_info_label()
        layout.addWidget(self._tz_info_label)

        layout.addStretch()

    def _auto_detect_timezone(self) -> None:
        """Rileva il fuso orario locale e preseleziona nel combo."""
        local_offset = -time.timezone if time.daylight == 0 else -time.altzone
        offset_hours = local_offset / 3600.0

        best_idx = 0
        best_diff = abs(TIMEZONE_OFFSETS[0][1] - offset_hours)
        for i, (_, tz_offset) in enumerate(TIMEZONE_OFFSETS):
            diff = abs(tz_offset - offset_hours)
            if diff < best_diff:
                best_diff = diff
                best_idx = i

        self._tz_combo.setCurrentIndex(best_idx)
        self._tz_offset = TIMEZONE_OFFSETS[best_idx][1]
        logger.info(
            "Fuso orario locale rilevato: UTC%+.1f, selezionato: %s",
            offset_hours, TIMEZONE_OFFSETS[best_idx][0],
        )

    def _on_timezone_changed(self, index: int) -> None:
        """Gestisce il cambio di fuso orario dal combo.

        Args:
            index: Indice della voce selezionata.
        """
        if 0 <= index < len(TIMEZONE_OFFSETS):
            label, offset = TIMEZONE_OFFSETS[index]
            self._tz_offset = offset
            logger.info("Fuso orario cambiato: %s (offset=%+.1f)", label, offset)
            self._update_tz_info_label()
            self.timezone_changed.emit(offset)

    def _update_tz_info_label(self) -> None:
        """Aggiorna l'etichetta informativa del fuso orario."""
        if self._tz_offset == 0.0:
            self._tz_info_label.setText("Orari in UTC")
            return
        sign = "+" if self._tz_offset > 0 else ""
        hours = int(self._tz_offset)
        mins = int((abs(self._tz_offset) % 1) * 60)
        suffix = f":{mins:02d}" if mins else ""
        self._tz_info_label.setText(f"Orari convertiti: UTC{sign}{hours}{suffix}")

    @property
    def tz_offset(self) -> float:
        """Offset corrente dal fuso UTC in ore.

        Returns:
            Offset in ore (es. 2.0 per CEST).
        """
        return self._tz_offset
