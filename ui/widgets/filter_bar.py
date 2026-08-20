"""Barra dei filtri per data, regione e impatto.

Fornisce controlli per filtrare gli eventi del calendario per
data, regione geografica (EUR, USA, JPN, ecc.) e livello di
impatto (HIGH, MID, LOW). Emette segnali quando i filtri cambiano.
Include una checkbox per abilitare/disabilitare il filtro data.

Nel tema Neumorphism la barra è una superficie estrusa morbida che
racchiude i campi incavati al suo interno (date edit, combo box).
"""

from __future__ import annotations

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from config.constants import CalendarDefaults
from config.theme import ThemeColors, ThemeFonts
from ui.styles.components import ComponentStyles
from ui.widgets.neumorphic import apply_extrude_soft

# "Tutti" → "ALL"; gli altri mantengono il proprio valore.
_REGION_VALUES: list[str] = ["ALL"] + [r for r in CalendarDefaults.REGIONS if r != "ALL"]
_REGION_LABELS: list[str] = ["Tutte"] + [r for r in CalendarDefaults.REGIONS if r != "ALL"]
_IMPACT_VALUES: list[str] = ["ALL", "HIGH", "MID", "LOW"]
_IMPACT_LABELS: list[str] = ["Tutti", "ALTO", "MEDIO", "BASSO"]


class FilterBar(QWidget):
    """Barra dei filtri con controlli per data, regione e impatto.

    Fornisce tre controlli di filtro:
    - Selettore data (QDateEdit) con checkbox per abilitare/disabilitare
    - Selettore regione (QComboBox con le regioni definite in CalendarDefaults)
    - Selettore impatto (QComboBox con HIGH, MID, LOW, ALL)

    Signals:
        filters_changed: Emesso quando uno qualsiasi dei filtri cambia,
            con un dict contenente i valori correnti dei filtri.
    """

    filters_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Inizializza la barra dei filtri con tutti i controlli.

        Args:
            parent: Widget genitore.
        """
        super().__init__(parent)
        self._setup_ui()
        # Applica ombra estrusa morbida alla barra (contenitore)
        apply_extrude_soft(self)

    def _setup_ui(self) -> None:
        """Configura il layout e i controlli della barra filtri."""
        self.setStyleSheet(ComponentStyles.filter_bar_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        label_style = (
            f"color: {ThemeColors.TEXT_SECONDARY}; "
            f"font-weight: {ThemeFonts.WEIGHT_MEDIUM}; "
            f"font-size: {ThemeFonts.SIZE_SMALL}px; "
            f"font-family: '{ThemeFonts.FAMILY_MONO}'; "
            f"letter-spacing: 0.06em; "
            f"background-color: transparent;"
        )

        # Checkbox per abilitare il filtro data
        self._date_checkbox = QCheckBox("Filtra per data:", self)
        self._date_checkbox.setChecked(False)
        self._date_checkbox.setStyleSheet(label_style)
        self._date_checkbox.toggled.connect(self._on_date_filter_toggled)
        layout.addWidget(self._date_checkbox)

        self._date_edit = QDateEdit(self)
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.dateChanged.connect(self._emit_filters)
        self._date_edit.setEnabled(False)  # Disabilitato finché checkbox non è attivo
        self._date_edit.setMinimumWidth(140)
        layout.addWidget(self._date_edit)

        layout.addSpacing(20)

        region_label = QLabel("Regione:", self)
        region_label.setStyleSheet(label_style)
        layout.addWidget(region_label)

        self._region_combo = QComboBox(self)
        self._region_combo.addItems(_REGION_LABELS)
        self._region_combo.currentIndexChanged.connect(self._emit_filters)
        self._region_combo.setMinimumWidth(120)
        layout.addWidget(self._region_combo)

        layout.addSpacing(20)

        impact_label = QLabel("Impatto:", self)
        impact_label.setStyleSheet(label_style)
        layout.addWidget(impact_label)

        self._impact_combo = QComboBox(self)
        self._impact_combo.addItems(_IMPACT_LABELS)
        self._impact_combo.currentIndexChanged.connect(self._emit_filters)
        self._impact_combo.setMinimumWidth(120)
        layout.addWidget(self._impact_combo)

        layout.addStretch()

    def _on_date_filter_toggled(self, checked: bool) -> None:
        """Abilita o disabilita il selettore data quando la checkbox cambia.

        Args:
            checked: True se la checkbox è attiva.
        """
        self._date_edit.setEnabled(checked)
        self._emit_filters()

    def _current_filters(self) -> dict[str, str | bool]:
        """Calcola i filtri correnti leggendo lo stato dei widget.

        Returns:
            Dict con chiavi 'date', 'date_enabled', 'region', 'impact'.
        """
        region_idx = self._region_combo.currentIndex()
        impact_idx = self._impact_combo.currentIndex()
        date_enabled = self._date_checkbox.isChecked()

        return {
            "date": self._date_edit.date().toString("dd/MM/yyyy") if date_enabled else "",
            "date_enabled": date_enabled,
            "region": _REGION_VALUES[region_idx] if region_idx < len(_REGION_VALUES) else "ALL",
            "impact": _IMPACT_VALUES[impact_idx] if impact_idx < len(_IMPACT_VALUES) else "ALL",
        }

    def _emit_filters(self) -> None:
        """Emette il segnale filters_changed con i valori correnti."""
        self.filters_changed.emit(self._current_filters())

    def get_current_filters(self) -> dict[str, str]:
        """Restituisce i valori correnti dei filtri.

        Returns:
            Dict con chiavi 'date', 'date_enabled', 'region', 'impact'.
        """
        return self._current_filters()

    def set_filters(self, region: str = "ALL", impact: str = "ALL") -> None:
        """Imposta i valori dei filtri programmaticamente.

        Args:
            region: Codice regione o "ALL".
            impact: Livello impatto o "ALL".
        """
        if region in _REGION_VALUES:
            self._region_combo.setCurrentIndex(_REGION_VALUES.index(region))
        if impact in _IMPACT_VALUES:
            self._impact_combo.setCurrentIndex(_IMPACT_VALUES.index(impact))
