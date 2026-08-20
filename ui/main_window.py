"""Finestra principale dell'applicazione con tab IG e FXStreet.

Contiene due tab per i calendari IG e FXStreet, ciascuno con
barra filtri, tabella e pulsante di aggiornamento. Include un
selettore globale del fuso orario delegato a TimezoneToolbar.

Il closeEvent chiude completamente l'applicazione (QApplication.quit)
conforme alla specifica §3.5. La minimizzazione nel tray è
disponibile tramite Ctrl+M.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QKeySequence, QIcon, QShortcut
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from config.constants import UIConstraints
from config.theme import ThemeColors, ThemeFonts
from core.app_controller import AppController
from core.models import CalendarSource
from ui.timezone_toolbar import TimezoneToolbar
from ui.widgets.action_button import ActionButton
from ui.widgets.calendar_table import CalendarTable
from ui.widgets.filter_bar import FilterBar
from ui.widgets.neumorphic import apply_extrude_soft
from ui.widgets.shortcut_badge import ShortcutBadge
from ui.widgets.status_indicator import StatusIndicator

logger = logging.getLogger(__name__)

_ICON_PATH = Path(__file__).parent.parent / "assets" / "icons" / "financial-calendar.png"


class MainWindow(QMainWindow):
    """Finestra principale con tab per calendari IG e FXStreet.

    Gestisce due tab indipendenti, ciascuno con barra filtri,
    tabella eventi e pulsante aggiornamento. Il closeEvent
    chiude completamente l'app (conforme §3.5).

    Signals:
        refresh_started_sig: Segnale thread-safe per inizio refresh.
        refresh_completed_sig: Segnale thread-safe per completamento refresh.
        refresh_error_sig: Segnale thread-safe per errore di refresh.
    """

    refresh_started_sig = Signal(str)
    refresh_completed_sig = Signal(str, str, int)
    refresh_error_sig = Signal(str, str)

    def __init__(self, controller: AppController) -> None:
        """Inizializza la finestra principale con il controller.

        Args:
            controller: Controller principale dell'applicazione.
        """
        super().__init__()
        self._controller = controller
        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self) -> None:
        """Configura le proprietà della finestra principale."""
        self.setWindowTitle("Calendario Finanziario")
        self.setMinimumSize(UIConstraints.WINDOW_MIN_WIDTH, UIConstraints.WINDOW_MIN_HEIGHT)
        self.resize(UIConstraints.WINDOW_DEFAULT_WIDTH, UIConstraints.WINDOW_DEFAULT_HEIGHT)
        if _ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))

    def _setup_ui(self) -> None:
        """Configura il layout completo della finestra."""
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Barra globale con selettore fuso orario
        self._tz_toolbar = TimezoneToolbar(self)
        self._tz_toolbar.timezone_changed.connect(self._on_timezone_changed)
        main_layout.addWidget(self._tz_toolbar)

        # Scorciatoia Ctrl+M per minimizzazione nel tray
        minimize_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        minimize_shortcut.activated.connect(self._minimize_to_tray)

        # Inizializza i dizionari PRIMA di creare i tab
        self._status_indicators: dict[CalendarSource, StatusIndicator] = {}
        self._last_refresh_labels: dict[CalendarSource, QLabel] = {}
        self._filter_bars: dict[CalendarSource, FilterBar] = {}
        self._calendar_tables: dict[CalendarSource, CalendarTable] = {}
        self._refresh_buttons: dict[CalendarSource, ActionButton] = {}

        self._tab_widget = QTabWidget(self)
        # Il tab widget stesso non riceve ombra (sarebbe in conflitto con i tab);
        # applichiamo ombra morbida al pane via effect sulla tab page.
        self._tab_ig = self._create_calendar_tab(CalendarSource.IG)
        self._tab_fxstreet = self._create_calendar_tab(CalendarSource.FXSTREET)
        self._tab_widget.addTab(self._tab_ig, "IG Economic Calendar")
        self._tab_widget.addTab(self._tab_fxstreet, "FXStreet Economic Calendar")

        main_layout.addWidget(self._tab_widget)

    def closeEvent(self, event) -> None:
        """Chiude completamente l'applicazione (conforme §3.5).

        Il pulsante X invoca QApplication.quit(), non minimizza.
        Per minimizzare nel tray, usare Ctrl+M.

        Args:
            event: Evento di chiusura.
        """
        event.accept()
        QApplication.quit()

    def _minimize_to_tray(self) -> None:
        """Minimizza la finestra nel tray (scorciatoia Ctrl+M)."""
        self.hide()

    def _on_timezone_changed(self, offset: float) -> None:
        """Gestisce il cambio di fuso orario globale.

        Args:
            offset: Nuovo offset UTC in ore.
        """
        self._update_table(CalendarSource.IG)
        self._update_table(CalendarSource.FXSTREET)

    def _create_calendar_tab(self, source: CalendarSource) -> QWidget:
        """Crea un tab del calendario con filtri, tabella e controlli.

        Args:
            source: Fonte del calendario (IG o FXStreet).

        Returns:
            Widget contenente il tab completo.
        """
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(14)

        shortcut = "Ctrl+R" if source == CalendarSource.IG else "Ctrl+F"
        refresh_btn = ActionButton("Aggiorna", shortcut, self)
        refresh_btn.action_requested.connect(
            lambda checked=False, s=source: self._on_refresh_clicked(s)
        )

        indicator = StatusIndicator(self)
        indicator.set_state(StatusIndicator.State.STOPPED)
        self._status_indicators[source] = indicator

        from ui.styles.components import ComponentStyles
        last_refresh_label = QLabel("Ultimo aggiornamento: --", self)
        last_refresh_label.setStyleSheet(ComponentStyles.last_refresh_label_style())
        self._last_refresh_labels[source] = last_refresh_label

        shortcut_badge = ShortcutBadge(shortcut, self)
        toolbar_layout.addWidget(refresh_btn)
        toolbar_layout.addWidget(indicator)
        toolbar_layout.addWidget(last_refresh_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(shortcut_badge)
        layout.addLayout(toolbar_layout)

        filter_bar = FilterBar(self)
        filter_bar.filters_changed.connect(
            lambda filters, s=source: self._on_filters_changed(s, filters)
        )
        self._filter_bars[source] = filter_bar
        layout.addWidget(filter_bar)

        calendar_table = CalendarTable(source, self)
        self._calendar_tables[source] = calendar_table
        layout.addWidget(calendar_table)

        self._refresh_buttons[source] = refresh_btn
        return tab

    def _connect_signals(self) -> None:
        """Connette i segnali Qt per comunicazione thread-safe."""
        self.refresh_started_sig.connect(self._handle_refresh_started)
        self.refresh_completed_sig.connect(self._handle_refresh_completed)
        self.refresh_error_sig.connect(self._handle_refresh_error)
        self._controller.set_notification_callback(self._on_controller_notify)

    def _on_controller_notify(self, event_name: str, payload: dict) -> None:
        """Callback dal controller — emette segnali Qt thread-safe.

        Args:
            event_name: Nome dell'evento.
            payload: Dati associati all'evento.
        """
        source = payload.get("source", "ig")
        logger.debug("Controller notify: event=%s source=%s", event_name, source)
        if event_name == "calendar_refresh_started":
            self.refresh_started_sig.emit(source)
        elif event_name == "calendar_refreshed":
            self.refresh_completed_sig.emit(
                source, payload.get("timestamp", ""), payload.get("count", 0),
            )
        elif event_name == "calendar_refresh_error":
            self.refresh_error_sig.emit(source, payload.get("error", ""))

    @Slot(str)
    def _handle_refresh_started(self, source_key: str) -> None:
        """Gestisce l'inizio del refresh sul thread principale."""
        source = CalendarSource.IG if source_key == "ig" else CalendarSource.FXSTREET
        indicator = self._status_indicators.get(source)
        if indicator:
            indicator.set_state(StatusIndicator.State.RUNNING)
        btn = self._refresh_buttons.get(source)
        if btn:
            btn.set_enabled(False)

    @Slot(str, str, int)
    def _handle_refresh_completed(self, source_key: str, timestamp: str, count: int) -> None:
        """Gestisce il completamento del refresh sul thread principale."""
        source = CalendarSource.IG if source_key == "ig" else CalendarSource.FXSTREET
        indicator = self._status_indicators.get(source)
        if indicator:
            indicator.set_state(StatusIndicator.State.STOPPED)
        label = self._last_refresh_labels.get(source)
        if label and timestamp:
            label.setText(f"Ultimo aggiornamento: {timestamp}")
        btn = self._refresh_buttons.get(source)
        if btn:
            btn.set_enabled(True)
        self._update_table(source)

    @Slot(str, str)
    def _handle_refresh_error(self, source_key: str, error: str) -> None:
        """Gestisce gli errori di refresh sul thread principale."""
        source = CalendarSource.IG if source_key == "ig" else CalendarSource.FXSTREET
        logger.error("UI: errore refresh %s: %s", source_key, error)
        indicator = self._status_indicators.get(source)
        if indicator:
            indicator.set_state(StatusIndicator.State.ERROR)
        btn = self._refresh_buttons.get(source)
        if btn:
            btn.set_enabled(True)

    def _on_refresh_clicked(self, source: CalendarSource) -> None:
        """Gestisce il clic sul pulsante di aggiornamento."""
        if source == CalendarSource.IG:
            self._controller.refresh_ig()
        else:
            self._controller.refresh_fxstreet()

    def _on_filters_changed(self, source: CalendarSource, filters: dict) -> None:
        """Gestisce il cambio dei filtri aggiornando la tabella."""
        self._update_table(source)

    def _update_table(self, source: CalendarSource) -> None:
        """Aggiorna la tabella con filtri correnti e fuso orario."""
        filter_bar = self._filter_bars.get(source)
        table = self._calendar_tables.get(source)
        if not filter_bar or not table:
            return
        filters = filter_bar.get_current_filters()
        date_filter = filters.get("date", "") if filters.get("date_enabled", False) else ""
        events = self._controller.filter_events(
            source,
            region=filters.get("region", "ALL"),
            impact=filters.get("impact", "ALL"),
            date=date_filter,
            tz_offset_hours=self._tz_toolbar.tz_offset,
        )
        table.populate(events)

    def load_initial_data(self) -> None:
        """Carica i dati iniziali per entrambi i calendari."""
        self._controller.refresh_all()
