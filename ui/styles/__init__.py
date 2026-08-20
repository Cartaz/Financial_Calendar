"""Stili e fogli di stile QSS per l'applicazione."""

from ui.styles.neumorphism import NeumorphicStyle
from ui.styles.calendar_styles import CalendarStyles
from ui.styles.components import ComponentStyles

# Mantieni alias per retrocompatibilità con codice esistente
# che fa riferimento a BreezeDarkStyle.
BreezeDarkStyle = NeumorphicStyle

__all__ = [
    "NeumorphicStyle",
    "BreezeDarkStyle",  # alias deprecato — usare NeumorphicStyle
    "CalendarStyles",
    "ComponentStyles",
]
