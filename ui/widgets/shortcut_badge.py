"""Badge scorciatoia tastiera.

Mostra una scorciatoia tastiera in un piccolo badge con sfondo
semi-trasparente e bordo sottile. Il testo è centrato e usa il
font monospace definito in ThemeFonts.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ui.styles.components import ComponentStyles


class ShortcutBadge(QLabel):
    """Badge visivo per una scorciatoia tastiera.

    Mostra la combinazione di tasti (es. "Ctrl+R") in un badge
    piccolo con sfondo semi-trasparente e bordo sottile.
    Il testo è centrato e usa il font monospace.

    Args:
        shortcut: Stringa della scorciatoia (es. "Ctrl+R").
        parent: Widget genitore.
    """

    def __init__(self, shortcut: str, parent: object | None = None) -> None:
        """Inizializza il badge con la scorciatoia indicata.

        Args:
            shortcut: Stringa della scorciatoia (es. "Ctrl+R").
            parent: Widget genitore.
        """
        super().__init__(shortcut, parent)
        self._shortcut_text = shortcut
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(ComponentStyles.shortcut_badge_style())

    def get_shortcut_text(self) -> str:
        """Restituisce il testo della scorciatoia.

        Returns:
            Stringa della scorciatoia.
        """
        return self._shortcut_text
