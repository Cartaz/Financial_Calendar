"""Card con intestazione in maiuscoletto.

Widget contenitore con superficie neumorphic estrusa (ombra morbida
esterna) e intestazione in maiuscoletto. Lo stesso colore dello
sfondo applica per elemento e contenitore: la profondità nasce
dall'ombra, non dal colore.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from config.theme import ThemeFonts
from ui.styles.components import ComponentStyles
from ui.widgets.neumorphic import apply_extrude_soft


class Card(QWidget):
    """Card con intestazione in maiuscoletto e area contenuto.

    Implementa una superficie neumorphic estrusa: stesso colore
    dello sfondo, ombra esterna morbida (radius-lg = 24px),
    padding interno generoso. L'intestazione usa il font mono
    in maiuscoletto, colore faint, letter-spacing ampio.

    Args:
        title: Titolo dell'intestazione della card.
        parent: Widget genitore.
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        """Inizializza la card con il titolo indicato.

        Args:
            title: Titolo dell'intestazione della card.
            parent: Widget genitore.
        """
        super().__init__(parent)
        self._title = title
        self._setup_ui(title)
        # Applica ombra estrusa morbida (variante card)
        apply_extrude_soft(self)

    def _setup_ui(self, title: str) -> None:
        """Configura il layout della card con intestazione e area contenuto.

        Args:
            title: Titolo dell'intestazione.
        """
        self.setStyleSheet(ComponentStyles.card_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        self._header_label = QLabel(title.upper(), self)
        header_font = QFont(ThemeFonts.FAMILY_MONO, ThemeFonts.SIZE_CARD_HEADER)
        header_font.setWeight(ThemeFonts.WEIGHT_MEDIUM)
        header_font.setCapitalization(QFont.Capitalization.AllUppercase)
        # Letter-spacing non supportato nativamente da QFont su tutti i backend;
        # è gestito via QSS in ComponentStyles.card_header_style.
        self._header_label.setFont(header_font)
        self._header_label.setStyleSheet(ComponentStyles.card_header_style())
        self._header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self._header_label)

        self._content_widget = QWidget(self)
        # Il content widget deve essere trasparente per non coprire la card
        self._content_widget.setStyleSheet("background-color: transparent;")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)

        layout.addWidget(self._content_widget)

    def content_layout(self) -> QVBoxLayout:
        """Restituisce il layout dell'area contenuto della card.

        Returns:
            QVBoxLayout dove aggiungere widget figli.
        """
        return self._content_layout

    def set_title(self, title: str) -> None:
        """Aggiorna il titolo dell'intestazione della card.

        Args:
            title: Nuovo titolo.
        """
        self._header_label.setText(title.upper())
