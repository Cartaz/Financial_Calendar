"""Tabella del calendario con drag-and-drop e ordinamento click.

Visualizza gli eventi del calendario in una QTableWidget con header
trascinabile. Supporta la colorazione dell'impatto, il riordino
delle colonne tramite drag-and-drop, e l'ordinamento cliccando
sull'header della colonna. La colonna Paese mostra anche la bandiera
nazionale (SVG in assets/flags/).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from config.constants import CalendarDefaults, PathConfig
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from config.theme import ThemeColors
from ui.widgets.draggable_header import DraggableHeaderView
from ui.widgets.table_sorting import compute_sort_key

logger = logging.getLogger(__name__)

# Indice della colonna "Paese" in entrambe le tabelle (IG e FXStreet).
_COUNTRY_COLUMN_INDEX = 2
# Dimensione dell'icona bandiera nelle celle della tabella.
_FLAG_ICON_SIZE = QSize(20, 14)


class SortableItem(QTableWidgetItem):
    """Item di tabella con chiave di ordinamento personalizzata.

    Memorizza una chiave di ordinamento in Qt.ItemDataRole.UserRole
    per consentire un confronto corretto tra valori di tipo diverso.
    """

    def __init__(self, text: str, sort_key: object = None) -> None:
        """Inizializza l'item con testo e chiave di ordinamento.

        Args:
            text: Testo da visualizzare nella cella.
            sort_key: Chiave per l'ordinamento. Se None, si usa il testo.
        """
        super().__init__(text)
        self._sort_key = sort_key

    def __lt__(self, other: object) -> bool:
        """Confronta usando la chiave di ordinamento.

        Args:
            other: Altro item da confrontare.

        Returns:
            True se questo item è minore dell'altro.
        """
        if not isinstance(other, SortableItem):
            return super().__lt__(other)
        if self._sort_key is not None and other._sort_key is not None:
            try:
                return self._sort_key < other._sort_key  # type: ignore[operator]
            except TypeError:
                return str(self._sort_key) < str(other._sort_key)
        return super().__lt__(other)


class CalendarTable(QWidget):
    """Tabella del calendario con colonne trascinabili e ordinamento.

    Mostra gli eventi in una tabella con header trascinabile per
    riordinare le colonne. Cliccando sull'header si ordina per
    quella colonna. La colonna Paese mostra la bandiera nazionale.

    Args:
        source: Fonte del calendario (IG o FXStreet).
        parent: Widget genitore.

    Signals:
        column_order_changed: Emesso quando l'ordine colonne cambia.
    """

    def __init__(self, source: CalendarSource, parent: QWidget | None = None) -> None:
        """Inizializza la tabella del calendario.

        Args:
            source: Fonte del calendario (IG o FXStreet).
            parent: Widget genitore.
        """
        super().__init__(parent)
        self._source = source
        self._events: list[CalendarEvent] = []
        self._sort_column: int = -1
        self._sort_order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
        # Cache region → QIcon: le SVG vengono caricate una sola volta.
        self._flag_icons: dict[str, QIcon] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if source == CalendarSource.IG:
            headers = ["Data", "Ora", "Paese", "Importanza", "Evento",
                        "Attuale", "Previsione", "Precedente"]
        else:
            headers = ["Data", "Ora", "Paese", "Evento", "Impatto",
                        "Attuale", "Dev", "Consensus", "Precedente"]

        self._headers = headers
        self._table = QTableWidget(0, len(headers), self)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        # Larghezza minima per la colonna Paese, così bandiera + codice
        # stanno comodi anche con resizeColumnsToContents().
        self._table.horizontalHeader().setMinimumSectionSize(60)

        self._draggable_header = DraggableHeaderView(Qt.Orientation.Horizontal, self._table)
        self._table.setHorizontalHeader(self._draggable_header)
        self._table.setHorizontalHeaderLabels(headers)
        self._draggable_header.column_order_changed.connect(self._on_column_order_changed)
        self._draggable_header.sort_requested.connect(self._on_sort_requested)

        layout.addWidget(self._table)

    def populate(self, events: list[CalendarEvent]) -> None:
        """Popola la tabella con gli eventi del calendario.

        Args:
            events: Lista di CalendarEvent da visualizzare.
        """
        self._events = list(events)
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        source_key = "ig" if self._source == CalendarSource.IG else "fxstreet"

        for row_idx, event in enumerate(events):
            self._table.insertRow(row_idx)
            row_data = (
                event.to_ig_row() if self._source == CalendarSource.IG
                else event.to_fxstreet_row()
            )
            for col_idx, value in enumerate(row_data):
                sort_key = compute_sort_key(source_key, col_idx, value, event)
                item = SortableItem(value, sort_key)

                if col_idx == _COUNTRY_COLUMN_INDEX:
                    # Colonna Paese: icona bandiera + codice, allineata a sx.
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                    )
                    flag_icon = self._get_flag_icon(event.country)
                    if flag_icon is not None:
                        item.setIcon(flag_icon)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if self._source == CalendarSource.IG:
                    self._style_ig_cell(item, col_idx, event)
                else:
                    self._style_fxstreet_cell(item, col_idx, event)

                self._table.setItem(row_idx, col_idx, item)

        self._table.resizeColumnsToContents()
        if self._sort_column >= 0:
            self._apply_sort()

    def _get_flag_icon(self, region: str) -> QIcon | None:
        """Restituisce l'icona della bandiera per una regione (con cache).

        Args:
            region: Codice regione (es. "EUR", "USA", "JPN").

        Returns:
            QIcon della bandiera, o None se non disponibile.
        """
        if region in self._flag_icons:
            return self._flag_icons[region]

        iso2 = CalendarDefaults.FLAG_CODES.get(region)
        if iso2 is None:
            self._flag_icons[region] = None
            return None

        svg_path = PathConfig.FLAGS_DIR / f"{iso2}.svg"
        if not svg_path.exists():
            logger.debug("Bandiera mancante per %s: %s", region, svg_path)
            self._flag_icons[region] = None
            return None

        icon = QIcon(str(svg_path))
        if icon.isNull():
            logger.warning("SVG non valida per %s: %s", region, svg_path)
            self._flag_icons[region] = None
            return None

        self._flag_icons[region] = icon
        return icon

    def _on_sort_requested(self, logical_index: int) -> None:
        """Gestisce la richiesta di ordinamento.

        Args:
            logical_index: Indice logico della colonna cliccata.
        """
        if logical_index < 0:
            return
        if self._sort_column == logical_index:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = logical_index
            self._sort_order = Qt.SortOrder.AscendingOrder
        self._apply_sort()

    def _apply_sort(self) -> None:
        """Applica l'ordinamento corrente alla tabella."""
        if self._sort_column < 0:
            return
        self._draggable_header.setSortIndicator(self._sort_column, self._sort_order)
        self._table.sortItems(self._sort_column, self._sort_order)

    def _style_ig_cell(self, item: QTableWidgetItem, col_idx: int, event: CalendarEvent) -> None:
        """Applica lo stile alla cella IG.

        Args:
            item: Item della cella.
            col_idx: Indice della colonna.
            event: Evento di riferimento.
        """
        if col_idx == 3:
            self._apply_impact_style(item, event.impact)

    def _style_fxstreet_cell(self, item: QTableWidgetItem, col_idx: int, event: CalendarEvent) -> None:
        """Applica lo stile alla cella FXStreet.

        Args:
            item: Item della cella.
            col_idx: Indice della colonna.
            event: Evento di riferimento.
        """
        if col_idx == 4:
            self._apply_impact_style(item, event.impact)

    def _apply_impact_style(self, item: QTableWidgetItem, impact: ImpactLevel) -> None:
        """Applica lo stile dell'impatto all'item.

        Args:
            item: Item della cella.
            impact: Livello di impatto.
        """
        color_map = {
            ImpactLevel.HIGH: ThemeColors.IMPACT_HIGH,
            ImpactLevel.MID: ThemeColors.IMPACT_MEDIUM,
            ImpactLevel.LOW: ThemeColors.IMPACT_LOW,
        }
        color = color_map.get(impact, ThemeColors.IMPACT_LOW)
        item.setForeground(QColor(color))
        font = item.font()
        font.setBold(impact in (ImpactLevel.HIGH, ImpactLevel.MID))
        item.setFont(font)

    def _on_column_order_changed(self, new_order: list[int]) -> None:
        """Gestisce il cambio di ordine delle colonne.

        Args:
            new_order: Lista di indici logici nel nuovo ordine.
        """
        logger.info("Ordine colonne cambiato per %s: %s", self._source.value, new_order)

    def get_column_order(self) -> list[int]:
        """Restituisce l'ordine corrente delle colonne.

        Returns:
            Lista di indici logici nell'ordine visuale corrente.
        """
        return self._draggable_header.current_order()

    def set_column_order(self, order: list[int]) -> None:
        """Imposta l'ordine delle colonne.

        Args:
            order: Lista di indici logici nell'ordine desiderato.
        """
        self._draggable_header.set_column_order(order)
