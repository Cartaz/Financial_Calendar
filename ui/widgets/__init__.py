"""Widget personalizzati riutilizzabili per l'interfaccia utente."""

from ui.widgets.status_indicator import StatusIndicator
from ui.widgets.shortcut_badge import ShortcutBadge
from ui.widgets.action_button import ActionButton
from ui.widgets.card import Card
from ui.widgets.calendar_table import CalendarTable
from ui.widgets.draggable_header import DraggableHeaderView
from ui.widgets.filter_bar import FilterBar
from ui.widgets.neumorphic import (
    apply_extrude,
    apply_extrude_soft,
    apply_press_inset,
    clear_effect,
)
from ui.widgets.table_sorting import (
    extract_numeric_sort_key,
    date_sort_key,
    impact_sort_key,
    compute_sort_key,
)

__all__ = [
    "StatusIndicator",
    "ShortcutBadge",
    "ActionButton",
    "Card",
    "CalendarTable",
    "DraggableHeaderView",
    "FilterBar",
    "apply_extrude",
    "apply_extrude_soft",
    "apply_press_inset",
    "clear_effect",
    "extract_numeric_sort_key",
    "date_sort_key",
    "impact_sort_key",
    "compute_sort_key",
]
