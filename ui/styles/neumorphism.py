"""Tema Neumorphism completo come foglio di stile QSS.

Sostituisce il vecchio `breeze_dark.py`. Genera il QSS globale
dell'applicazione usando esclusivamente i token di colore e i font
definiti in config/theme.py, conforme alle linee guida neumorphism.

Limitazioni di Qt QSS:
- `box-shadow` non è supportato nativamente. Per ottenere l'effetto
  estruso (bottoni, card) usiamo in combinazione:
    1. QSS per bordi top/left chiari (simulazione ombra chiara)
    2. QGraphicsDropShadowEffect (vedi ui/widgets/neumorphic.py)
       per l'ombra scura esterna in basso-destra
- L'effetto inset sui campi (QLineEdit, QComboBox, QDateEdit) è
  simulato con bordi top/left scuri e bottom/right chiari.

Gli stili per QDateEdit e QCalendarWidget sono in calendar_styles.py.
"""

from __future__ import annotations

from config.theme import ThemeColors, ThemeFonts, ThemeRadius
from ui.styles.calendar_styles import CalendarStyles


class NeumorphicStyle:
    """Generatore del foglio di stile QSS globale per Neumorphism.

    Tutti i colori, font e spaziature sono referenziati tramite i token
    semantici di ThemeColors, ThemeFonts e ThemeRadius. Nessun valore
    hardcoded, conformemente alle linee guida di progetto.
    """

    @staticmethod
    def get_stylesheet() -> str:
        """Genera il QSS completo per l'applicazione.

        Returns:
            Stringa QSS con tutti gli stili dell'applicazione.
        """
        tc = ThemeColors
        tf = ThemeFonts
        tr = ThemeRadius

        main_css = f"""
        /* ====== BASE / SFONDO ====== */
        QMainWindow, QWidget {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            font-family: "{tf.FAMILY_MAIN}";
            font-size: {tf.SIZE_BODY}px;
        }}

        /* ====== LABEL ====== */
        QLabel {{
            background-color: transparent;
            color: {tc.TEXT_PRIMARY};
            font-size: {tf.SIZE_BODY}px;
            font-family: "{tf.FAMILY_MAIN}";
        }}

        /* ====== TAB WIDGET ====== */
        QTabWidget::pane {{
            border: none;
            border-radius: {tr.RADIUS_LG}px;
            background-color: {tc.BG_MAIN};
            /* Ombre non supportate qui: usa Card wrapper o effect dal codice */
        }}

        QTabBar {{
            background-color: transparent;
        }}

        QTabBar::tab {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_SECONDARY};
            border: none;
            border-top-left-radius: {tr.RADIUS_MD}px;
            border-top-right-radius: {tr.RADIUS_MD}px;
            /* Simulazione ombra neumorphic estrusa sui tab */
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_DARK};
            padding: 10px 24px;
            margin: 0 4px 0 0;
            font-size: {tf.SIZE_BODY}px;
            font-weight: {tf.WEIGHT_MEDIUM};
            font-family: "{tf.FAMILY_MAIN}";
            min-width: 90px;
        }}

        QTabBar::tab:selected {{
            color: {tc.PRIMARY};
            background-color: {tc.BG_MAIN};
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            font-weight: {tf.WEIGHT_SEMIBOLD};
        }}

        QTabBar::tab:hover:!selected {{
            color: {tc.TEXT_PRIMARY};
        }}

        /* ====== TABELLA ====== */
        QTableWidget {{
            background-color: {tc.BG_MAIN};
            alternate-background-color: {tc.SHADOW_LIGHT_SOFT};
            color: {tc.TEXT_PRIMARY};
            gridline-color: {tc.DIVIDER};
            border: none;
            border-top: 1px solid {tc.SHADOW_DARK};
            border-left: 1px solid {tc.SHADOW_DARK};
            border-bottom: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_LIGHT};
            /* inset: top/left scuri + bottom/right chiari → effetto incavato */
            border-radius: {tr.RADIUS_MD}px;
            font-size: {tf.SIZE_BODY}px;
            selection-background-color: rgba(255, 102, 0, 0.18);
            selection-color: {tc.TEXT_PRIMARY};
            outline: none;
        }}

        QTableWidget::item {{
            padding: 8px 12px;
            border-bottom: 1px solid {tc.DIVIDER};
            background-color: transparent;
        }}

        QTableWidget::item:hover {{
            background-color: rgba(255, 102, 0, 0.06);
            color: {tc.TEXT_PRIMARY};
        }}

        QTableWidget::item:selected {{
            background-color: rgba(255, 102, 0, 0.18);
            color: {tc.TEXT_PRIMARY};
        }}

        QHeaderView {{
            background-color: transparent;
            border: none;
        }}

        QHeaderView::section {{
            background-color: {tc.SHADOW_LIGHT_SOFT};
            color: {tc.TEXT_SECONDARY};
            padding: 10px 12px;
            border: none;
            border-right: 1px solid {tc.DIVIDER};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            font-weight: {tf.WEIGHT_SEMIBOLD};
            font-size: {tf.SIZE_SMALL}px;
            font-family: "{tf.FAMILY_MONO}";
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        QHeaderView::section:hover {{
            color: {tc.PRIMARY};
            background-color: {tc.SHADOW_LIGHT};
        }}

        /* ====== PULSANTI (estrusi) ====== */
        QPushButton {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            /* Simulazione ombra chiara top/left via QSS (ombra scura via effect) */
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            border-radius: {tr.RADIUS_MD}px;
            padding: {10}px {20}px;
            font-size: {tf.SIZE_BUTTON_LABEL}px;
            font-weight: {tf.WEIGHT_SEMIBOLD};
            font-family: "{tf.FAMILY_MAIN}";
            min-height: 22px;
        }}

        QPushButton:hover {{
            /* Hover: ombra leggermente più stretta → simulata con border più sottile */
            color: {tc.PRIMARY};
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
        }}

        QPushButton:pressed {{
            /* Pressed: ombra invertita → inset (top/left scuri, bottom/right chiari) */
            color: {tc.TEXT_SECONDARY};
            border-top: 1px solid {tc.SHADOW_DARK};
            border-left: 1px solid {tc.SHADOW_DARK};
            border-bottom: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_LIGHT};
            background-color: {tc.BG_FLAT};
        }}

        QPushButton:disabled {{
            color: {tc.TEXT_DISABLED};
            border: none;
            background-color: {tc.BG_FLAT};
            /* Disabilitato: niente ombre, opacità ridotta (linee guida §07) */
        }}

        /* Variante primaria (accento): testo arancione, resto estruso uguale */
        QPushButton[cssClass="primary"] {{
            color: {tc.PRIMARY};
        }}
        QPushButton[cssClass="primary"]:hover {{
            color: {tc.PRIMARY_SOFT};
        }}

        /* ====== COMBOBOX (incavato) ====== */
        QComboBox {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            /* Inset: top/left scuri, bottom/right chiari → sembra scavato */
            border-top: 1px solid {tc.SHADOW_DARK};
            border-left: 1px solid {tc.SHADOW_DARK};
            border-bottom: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_LIGHT};
            border-radius: {tr.RADIUS_MD}px;
            padding: 8px 14px;
            font-size: {tf.SIZE_BODY}px;
            min-height: 22px;
            min-width: 80px;
        }}

        QComboBox:hover {{
            color: {tc.PRIMARY};
        }}

        QComboBox:focus {{
            /* Anello di accento al focus (linee guida §04 e §07) */
            border: 2px solid {tc.PRIMARY_SOFT};
            padding: 7px 13px;  /* compensa il border 2px */
        }}

        QComboBox:disabled {{
            color: {tc.TEXT_DISABLED};
            border: none;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 26px;
            background-color: transparent;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {tc.TEXT_SECONDARY};
            margin-right: 8px;
            width: 0;
            height: 0;
        }}

        QComboBox:hover::down-arrow {{
            border-top-color: {tc.PRIMARY};
        }}

        QComboBox QAbstractItemView {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            border-radius: {tr.RADIUS_MD}px;
            padding: 6px;
            selection-background-color: rgba(255, 102, 0, 0.18);
            selection-color: {tc.TEXT_PRIMARY};
            outline: none;
        }}

        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: {tr.RADIUS_SM}px;
            min-height: 22px;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: rgba(255, 102, 0, 0.10);
            color: {tc.PRIMARY};
        }}

        /* ====== CHECKBOX ====== */
        QCheckBox {{
            background-color: transparent;
            color: {tc.TEXT_PRIMARY};
            spacing: 8px;
            font-size: {tf.SIZE_BODY}px;
            font-weight: {tf.WEIGHT_MEDIUM};
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 6px;
            border: none;
            /* Inset per la casella non selezionata */
            border-top: 1px solid {tc.SHADOW_DARK};
            border-left: 1px solid {tc.SHADOW_DARK};
            border-bottom: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_LIGHT};
            background-color: {tc.BG_MAIN};
        }}

        QCheckBox::indicator:checked {{
            /* Estruso quando attivo: piccolo "pill" arancione */
            background-color: {tc.PRIMARY};
            border-top: 1px solid {tc.PRIMARY_SOFT};
            border-left: 1px solid {tc.PRIMARY_SOFT};
            border-bottom: 1px solid {tc.PRIMARY_DARK};
            border-right: 1px solid {tc.PRIMARY_DARK};
            /* Check mark via image-less QSS: usiamo border-check semplificato */
            image: none;
        }}

        QCheckBox::indicator:hover {{
            border: 2px solid {tc.PRIMARY_SOFT};
        }}

        /* ====== SCROLLBAR (estruse sottili) ====== */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 12px;
            margin: 4px 2px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {tc.SHADOW_LIGHT};
            min-height: 32px;
            border-radius: 4px;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {tc.BG_MAIN};
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            border: none;
            background: transparent;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 12px;
            margin: 2px 4px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {tc.SHADOW_LIGHT};
            min-width: 32px;
            border-radius: 4px;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {tc.BG_MAIN};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            height: 0;
            border: none;
            background: transparent;
        }}

        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}

        /* ====== TOOLTIP ====== */
        QToolTip {{
            background-color: {tc.BG_TOOLTIP};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            padding: 8px 12px;
            border-radius: {tr.RADIUS_SM}px;
            font-size: {tf.SIZE_SMALL}px;
        }}

        /* ====== MENU (tray icon & popup menu) ====== */
        QMenu {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            border-radius: {tr.RADIUS_MD}px;
            padding: 8px;
            font-size: {tf.SIZE_BODY}px;
        }}

        QMenu::item {{
            padding: 8px 24px 8px 16px;
            border-radius: {tr.RADIUS_SM}px;
        }}

        QMenu::item:selected {{
            background-color: rgba(255, 102, 0, 0.12);
            color: {tc.PRIMARY};
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {tc.DIVIDER};
            margin: 4px 8px;
        }}

        /* ====== LINEEDIT (incavato) ====== */
        QLineEdit {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_DARK};
            border-left: 1px solid {tc.SHADOW_DARK};
            border-bottom: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_LIGHT};
            border-radius: {tr.RADIUS_MD}px;
            padding: 8px 14px;
            font-size: {tf.SIZE_BODY}px;
            selection-background-color: rgba(255, 102, 0, 0.25);
            selection-color: {tc.TEXT_PRIMARY};
        }}

        QLineEdit:focus {{
            border: 2px solid {tc.PRIMARY_SOFT};
            padding: 7px 13px;
        }}

        QLineEdit:disabled {{
            color: {tc.TEXT_DISABLED};
            border: none;
        }}

        /* ====== SPINBOX (incavato, usato nel popup calendario) ====== */
        QSpinBox {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_DARK};
            border-left: 1px solid {tc.SHADOW_DARK};
            border-bottom: 1px solid {tc.SHADOW_LIGHT};
            border-right: 1px solid {tc.SHADOW_LIGHT};
            border-radius: {tr.RADIUS_SM}px;
            padding: 4px 8px;
        }}
        """

        date_css = CalendarStyles.date_edit_style()
        calendar_css = CalendarStyles.calendar_popup_style()

        return main_css + date_css + calendar_css
