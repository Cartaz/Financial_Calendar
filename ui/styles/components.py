"""Stili specifici per i componenti widget dell'applicazione.

Fornisce stili QSS aggiuntivi per widget personalizzati come
card, indicatori di stato, badge scorciatoia e barre filtro,
conformi alle linee guida neumorphism. Usa esclusivamente i token
di ThemeColors, ThemeFonts, ThemeRadius e ThemeShadow.
"""

from __future__ import annotations

from config.theme import ThemeColors, ThemeFonts, ThemeRadius


class ComponentStyles:
    """Stili QSS per widget personalizzati dell'applicazione.

    Ogni metodo restituisce una stringa QSS per uno specifico widget,
    usando solo i token centralizzati. Nessun valore hardcoded.
    """

    @staticmethod
    def card_style() -> str:
        """Stile per le card con intestazione.

        Nel neumorphism la card è una superficie estrusa: stesso colore
        dello sfondo, ombra morbida esterna (applicata via
        QGraphicsDropShadowEffect in Card._setup_ui), niente bordo
        colorato. Il raggio è radius-lg (24px).

        Returns:
            Stringa QSS per il widget card.
        """
        tc = ThemeColors
        tr = ThemeRadius
        return (
            f"background-color: {tc.BG_MAIN}; "
            f"border: none; "
            f"border-radius: {tr.RADIUS_LG}px; "
            f"padding: 24px; "
            f"margin: 4px;"
        )

    @staticmethod
    def card_header_style() -> str:
        """Stile per l'intestazione delle card in maiuscoletto.

        Ispirato al "section-label" delle linee guida: font mono,
        lettere maiuscole, colore faint, letter-spacing ampio.

        Returns:
            Stringa QSS per l'header della card.
        """
        tc = ThemeColors
        tf = ThemeFonts
        return (
            f"color: {tc.TEXT_FAINT}; "
            f"font-size: {tf.SIZE_CARD_HEADER}px; "
            f"font-weight: {tf.WEIGHT_MEDIUM}; "
            f"letter-spacing: 0.12em; "
            f"padding-left: 4px; "
            f"padding-bottom: 4px; "
            f"font-family: '{tf.FAMILY_MONO}';"
        )

    @staticmethod
    def status_indicator_style(color: str) -> str:
        """Stile per l'indicatore di stato (punto colorato).

        Nel neumorphism l'indicatore mantiene un piccolo estruso
        per essere visibile anche sulle superfici a basso contrasto.

        Args:
            color: Colore dell'indicatore dal token semantico.

        Returns:
            Stringa QSS per l'indicatore di stato.
        """
        from config.constants import UIConstraints
        d = UIConstraints.INDICATOR_DIAMETER
        tc = ThemeColors
        return (
            f"background-color: {color}; "
            f"border: none; "
            f"border-top: 1px solid {tc.SHADOW_LIGHT}; "
            f"border-left: 1px solid {tc.SHADOW_LIGHT}; "
            f"border-bottom: 1px solid {tc.SHADOW_DARK}; "
            f"border-right: 1px solid {tc.SHADOW_DARK}; "
            f"border-radius: {d // 2}px; "
            f"min-width: {d}px; "
            f"max-width: {d}px; "
            f"min-height: {d}px; "
            f"max-height: {d}px;"
        )

    @staticmethod
    def shortcut_badge_style() -> str:
        """Stile per il badge scorciatoia tastiera.

        Piccolo chip estruso che riporta la combinazione di tasti.
        Font monospace, testo secondario, raggio radius-sm.

        Returns:
            Stringa QSS per il badge scorciatoia.
        """
        tc = ThemeColors
        tf = ThemeFonts
        tr = ThemeRadius
        return (
            f"background-color: {tc.BG_MAIN}; "
            f"color: {tc.TEXT_SECONDARY}; "
            f"border: none; "
            f"border-top: 1px solid {tc.SHADOW_LIGHT}; "
            f"border-left: 1px solid {tc.SHADOW_LIGHT}; "
            f"border-bottom: 1px solid {tc.SHADOW_DARK}; "
            f"border-right: 1px solid {tc.SHADOW_DARK}; "
            f"border-radius: {tr.RADIUS_SM}px; "
            f"padding: 4px 10px; "
            f"font-size: {tf.SIZE_SHORTCUT_BADGE}px; "
            f"font-family: '{tf.FAMILY_MONO}'; "
            f"font-weight: {tf.WEIGHT_MEDIUM}; "
            f"letter-spacing: 0.04em;"
        )

    @staticmethod
    def filter_bar_style() -> str:
        """Stile per la barra dei filtri.

        Trattata come una card estrusa morbida per racchiudere i filtri
        in un'unica area visiva coerente. L'ombra esterna è applicata
        via QGraphicsDropShadowEffect in FilterBar.

        Returns:
            Stringa QSS per la barra filtri.
        """
        tc = ThemeColors
        tr = ThemeRadius
        return (
            f"background-color: {tc.BG_MAIN}; "
            f"border: none; "
            f"border-radius: {tr.RADIUS_LG}px; "
            f"padding: 16px 20px;"
        )

    @staticmethod
    def section_label_style() -> str:
        """Stile per le etichette di sezione (es. "01 — PRINCIPIO").

        Returns:
            Stringa QSS per l'etichetta di sezione.
        """
        tc = ThemeColors
        tf = ThemeFonts
        return (
            f"color: {tc.TEXT_FAINT}; "
            f"font-size: {tf.SIZE_CARD_HEADER}px; "
            f"font-family: '{tf.FAMILY_MONO}'; "
            f"font-weight: {tf.WEIGHT_MEDIUM}; "
            f"letter-spacing: 0.12em;"
        )

    @staticmethod
    def heading_style(size: int = None, weight: int = None) -> str:
        """Stile per i titoli (Sora display font).

        Args:
            size: Dimensione font in px (default ThemeFonts.SIZE_H2).
            weight: Peso font (default ThemeFonts.WEIGHT_SEMIBOLD).

        Returns:
            Stringa QSS per il titolo.
        """
        tc = ThemeColors
        tf = ThemeFonts
        s = size if size is not None else tf.SIZE_H2
        w = weight if weight is not None else tf.WEIGHT_SEMIBOLD
        return (
            f"color: {tc.TEXT_PRIMARY}; "
            f"font-size: {s}px; "
            f"font-weight: {w}; "
            f"font-family: '{tf.FAMILY_DISPLAY}'; "
            f"background-color: transparent;"
        )

    @staticmethod
    def last_refresh_label_style() -> str:
        """Stile per l'etichetta "Ultimo aggiornamento: ...".

        Returns:
            Stringa QSS per l'etichetta.
        """
        tc = ThemeColors
        tf = ThemeFonts
        return (
            f"color: {tc.TEXT_SECONDARY}; "
            f"font-size: {tf.SIZE_SMALL}px; "
            f"font-family: '{tf.FAMILY_MONO}'; "
            f"font-weight: {tf.WEIGHT_NORMAL}; "
            f"background-color: transparent;"
        )
