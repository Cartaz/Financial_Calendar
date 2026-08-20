"""Header trascinabile per il riordino delle colonne della tabella.

Permette all'utente di trascinare le intestazioni delle colonne a
destra o sinistra per riordinare le sezioni del calendario. Le
nuove posizioni vengono comunicate tramite il signal column_order_changed.

Distingue tra clic (per ordinamento) e trascinamento (per riordino):
se il mouse si muove meno di 5 pixel tra pressione e rilascio,
viene interpretato come clic per ordinare la colonna.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import QHeaderView


logger = logging.getLogger(__name__)

# Soglia pixel: se il mouse si muove meno di questo valore, è un clic
_CLICK_THRESHOLD = 5


class DraggableHeaderView(QHeaderView):
    """Header di tabella con supporto al drag-and-drop e ordinamento click.

    Permette all'utente di trascinare le intestazioni delle colonne
    per riordinarle. Distingue tra clic (ordinamento) e drag (riordino).
    Le nuove posizioni vengono comunicate tramite il signal
    column_order_changed, le richieste di ordinamento tramite sort_requested.

    Signals:
        column_order_changed: Emesso quando l'ordine delle colonne
            cambia, con la lista dei nuovi indici logici.
        sort_requested: Emesso quando l'utente clicca su una colonna
            per ordinare, con l'indice logico della colonna.
    """

    column_order_changed = Signal(list)
    sort_requested = Signal(int)

    def __init__(self, orientation: Qt.Orientation, parent: object | None = None) -> None:
        """Inizializza l'header trascinabile.

        Args:
            orientation: Orientamento dell'header (orizzontale o verticale).
            parent: Widget genitore.
        """
        super().__init__(orientation, parent)
        self._dragging = False
        self._drag_section = -1
        self._press_pos = QPoint()
        self.setSectionsMovable(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QHeaderView.DragDropMode.InternalMove)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setHighlightSections(True)
        self.setSortIndicatorShown(True)
        self.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Registra la posizione di partenza per distinguere clic da drag.

        Args:
            event: Evento del mouse.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            section = self.logicalIndexAt(pos)
            if section >= 0:
                self._dragging = True
                self._drag_section = section
                self._press_pos = pos
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Gestisce il rilascio: clic (ordinamento) o drag (riordino).

        Se il mouse si è mosso meno di _CLICK_THRESHOLD pixel, viene
        interpretato come clic per ordinare la colonna. Altrimenti
        viene trattato come completamento del drag-and-drop.

        Args:
            event: Evento del mouse.
        """
        if self._dragging:
            self._dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

            release_pos = event.position().toPoint()
            delta = release_pos - self._press_pos
            distance = (delta.x() ** 2 + delta.y() ** 2) ** 0.5

            if distance < _CLICK_THRESHOLD:
                # È un clic: richiedi ordinamento
                logger.debug("Clic su colonna %d, richiedo ordinamento", self._drag_section)
                self.sort_requested.emit(self._drag_section)
            else:
                # È un drag: notifica il nuovo ordine
                new_order = self.current_order()
                self.column_order_changed.emit(new_order)
                logger.debug("Ordine colonne cambiato: %s", new_order)

        super().mouseReleaseEvent(event)

    def current_order(self) -> list[int]:
        """Restituisce l'ordine corrente delle colonne logiche.

        Returns:
            Lista di indici logici nell'ordine visuale corrente.
        """
        count = self.count()
        return [self.logicalIndex(i) for i in range(count)]

    def set_column_order(self, order: list[int]) -> None:
        """Imposta l'ordine delle colonne in base alla lista di indici.

        Args:
            order: Lista di indici logici nell'ordine desiderato.
        """
        for visual_index, logical_index in enumerate(order):
            current_visual = self.visualIndex(logical_index)
            if current_visual != visual_index:
                self.moveSection(current_visual, visual_index)
