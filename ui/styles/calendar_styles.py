"""Stili QSS per il widget calendario QCalendarWidget.

Genera il foglio di stile per il popup del calendario usato da
QDateEdit, usando esclusivamente i token ThemeColors, ThemeFonts e
ThemeRadius. Separato da neumorphism.py per rispettare il limite
di 300 righe per file di stile.
"""

from __future__ import annotations

from config.theme import ThemeColors, ThemeFonts, ThemeRadius


class CalendarStyles:
    """Stili QSS per il widget QCalendarWidget e QDateEdit.

    Tutti i colori, font e spaziature sono referenziati tramite i token
    semantici di ThemeColors, ThemeFonts e ThemeRadius.
    """

    @staticmethod
    def date_edit_style() -> str:
        """Stile completo per QDateEdit con dropdown e freccia.

        Il widget QDateEdit è trattato come un campo incavato (inset),
        coerentemente con gli altri campi editabili.

        Returns:
            Stringa QSS per QDateEdit e i suoi sub-controls.
        """
        tc = ThemeColors
        tf = ThemeFonts
        tr = ThemeRadius
        return f"""
        QDateEdit {{
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
            min-height: 22px;
        }}
        QDateEdit:hover {{
            color: {tc.PRIMARY};
        }}
        QDateEdit:focus {{
            border: 2px solid {tc.PRIMARY_SOFT};
            padding: 7px 13px;
        }}
        QDateEdit:disabled {{
            color: {tc.TEXT_DISABLED};
            border: none;
        }}
        QDateEdit::drop-down {{
            border: none;
            width: 26px;
            background-color: transparent;
        }}
        QDateEdit::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {tc.TEXT_SECONDARY};
            margin-right: 8px;
            width: 0;
            height: 0;
        }}
        QDateEdit:hover::down-arrow {{
            border-top-color: {tc.PRIMARY};
        }}
        QDateEdit:disabled::down-arrow {{
            border-top-color: {tc.TEXT_DISABLED};
        }}
        """

    @staticmethod
    def calendar_popup_style() -> str:
        """Stile completo per il popup QCalendarWidget.

        Returns:
            Stringa QSS per QCalendarWidget e tutti i suoi sub-elementi.
        """
        tc = ThemeColors
        tf = ThemeFonts
        tr = ThemeRadius
        return f"""
        QCalendarWidget {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            border-radius: {tr.RADIUS_LG}px;
        }}
        QCalendarWidget QWidget {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
        }}
        QCalendarWidget QToolButton {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            border-radius: {tr.RADIUS_SM}px;
            padding: 6px 10px;
            font-size: {tf.SIZE_BODY}px;
            font-weight: {tf.WEIGHT_MEDIUM};
        }}
        QCalendarWidget QToolButton:hover {{
            color: {tc.PRIMARY};
        }}
        QCalendarWidget QMenu {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            border: none;
            border-top: 1px solid {tc.SHADOW_LIGHT};
            border-left: 1px solid {tc.SHADOW_LIGHT};
            border-bottom: 1px solid {tc.SHADOW_DARK};
            border-right: 1px solid {tc.SHADOW_DARK};
            border-radius: {tr.RADIUS_MD}px;
            padding: 6px;
        }}
        QCalendarWidget QMenu::item {{
            padding: 6px 16px;
            border-radius: {tr.RADIUS_SM}px;
        }}
        QCalendarWidget QMenu::item:selected {{
            background-color: rgba(255, 102, 0, 0.18);
            color: {tc.PRIMARY};
        }}
        QCalendarWidget QAbstractItemView {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
            selection-background-color: rgba(255, 102, 0, 0.25);
            selection-color: {tc.TEXT_PRIMARY};
            border: none;
        }}
        QCalendarWidget QSpinBox {{
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
        QCalendarWidget QSpinBox::up-button,
        QCalendarWidget QSpinBox::down-button {{
            background-color: transparent;
            border: none;
            width: 16px;
        }}
        #qt_calendar_navigationbar {{
            background-color: {tc.BG_MAIN};
        }}
        #qt_calendar_navigationbar QToolButton {{
            background-color: {tc.BG_MAIN};
            color: {tc.TEXT_PRIMARY};
        }}
        #qt_calendar_navigationbar QToolButton:hover {{
            color: {tc.PRIMARY};
        }}
        #qt_calendar_prevmonth, #qt_calendar_nextmonth {{
            background-color: transparent;
            border: none;
            color: {tc.TEXT_SECONDARY};
            font-size: 18px;
            padding: 4px 8px;
            border-radius: {tr.RADIUS_SM}px;
        }}
        #qt_calendar_prevmonth:hover, #qt_calendar_nextmonth:hover {{
            color: {tc.PRIMARY};
            background-color: rgba(255, 102, 0, 0.08);
        }}
        #qt_calendar_monthbutton, #qt_calendar_yearbutton {{
            background-color: transparent;
            color: {tc.TEXT_PRIMARY};
            font-weight: {tf.WEIGHT_SEMIBOLD};
            padding: 4px 10px;
            border-radius: {tr.RADIUS_SM}px;
        }}
        #qt_calendar_monthbutton:hover, #qt_calendar_yearbutton:hover {{
            color: {tc.PRIMARY};
            background-color: rgba(255, 102, 0, 0.08);
        }}
        #qt_calendar_calendarview {{
            background-color: {tc.BG_MAIN};
            alternate-background-color: {tc.SHADOW_LIGHT_SOFT};
            selection-background-color: {tc.PRIMARY};
            selection-color: {tc.BG_MAIN};
        }}
        """
