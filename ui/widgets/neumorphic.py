"""Helper per applicare effetti neumorphism ai widget Qt.

Qt QSS non supporta nativamente `box-shadow` (né inset né outset).
Per ottenere l'effetto neumorphic vero — ombre chiare in alto-sinistra
e scure in basso-destra — usiamo `QGraphicsDropShadowEffect` con due
offset opposti. Per l'effetto inset sui campi di testo ricadiamo invece
su QSS con `border` colorati (vedi NeumorphicStyle).

Le funzioni qui esposte sono riusabili su qualsiasi QWidget e mantengono
i token di ThemeShadow/ThemeColors come unica fonte di verità.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from config.theme import ThemeColors, ThemeShadow


def _make_shadow(
    color_hex: str,
    offset: tuple[int, int],
    blur: int,
    alpha: int,
) -> QGraphicsDropShadowEffect:
    """Crea un singolo QGraphicsDropShadowEffect dai parametri.

    Args:
        color_hex: Colore dell'ombra in formato #RRGGBB.
        offset: Tupla (dx, dy) dell'offset dell'ombra.
        blur: Raggio di sfumatura in pixel.
        alpha: Opacità 0-255.

    Returns:
        QGraphicsDropShadowEffect configurato.
    """
    eff = QGraphicsDropShadowEffect()
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)
    eff.setColor(QColor(r, g, b, alpha))
    eff.setOffset(offset[0], offset[1])
    eff.setBlurRadius(blur)
    return eff


def apply_extrude(
    widget: QWidget,
    *,
    blur: int = ThemeShadow.EXTRUDE_BLUR,
    alpha: int = ThemeShadow.EXTRUDE_ALPHA,
) -> None:
    """Applica l'effetto estruso (ombra esterna) a un widget.

    L'effetto neumorphic classico per bottoni e card: una coppia di
    ombre soft, chiara in alto-sinistra e scura in basso-destra.

    Nota: QGraphicsDropShadowEffect supporta una sola ombra per effect,
    quindi applichiamo quella scura (più visibile). La componente chiara
    viene simulata dal QSS di base (vedi NeumorphicStyle) tramite un
    sottile border-top/left chiaro.

    Args:
        widget: Widget a cui applicare l'effetto (tipicamente QPushButton, Card).
        blur: Raggio di sfumatura dell'ombra.
        alpha: Opacità dell'ombra.
    """
    # Ombra scura principale (basso-destra) — visibile e profonda
    widget.setGraphicsEffect(
        _make_shadow(
            ThemeColors.SHADOW_DARK,
            ThemeShadow.EXTRUDE_DARK_OFFSET,
            blur,
            alpha,
        )
    )


def apply_extrude_soft(
    widget: QWidget,
    *,
    blur: int = ThemeShadow.EXTRUDE_SOFT_BLUR,
    alpha: int = ThemeShadow.EXTRUDE_SOFT_ALPHA,
) -> None:
    """Applica l'effetto estruso morbido per card e contenitori.

    Variante più larga e meno opaca di `apply_extrude`, ideale per
    superfici grandi (card, pannelli) dove un'ombra troppo marcata
    risulterebbe pesante.

    Args:
        widget: Widget a cui applicare l'effetto (tipicamente Card, pannelli).
        blur: Raggio di sfumatura dell'ombra.
        alpha: Opacità dell'ombra.
    """
    widget.setGraphicsEffect(
        _make_shadow(
            ThemeColors.SHADOW_DARK_SOFT,
            ThemeShadow.EXTRUDE_SOFT_DARK_OFFSET,
            blur,
            alpha,
        )
    )


def apply_press_inset(widget: QWidget) -> None:
    """Applica l'effetto incavato temporaneo per stato premuto.

    Le ombre si invertono (chiara in basso-destra, scura in alto-sinistra)
    per simulare la pressione fisica del pulsante dentro la superficie.

    Args:
        widget: Widget a cui applicare l'effetto (tipicamente QPushButton).
    """
    # Invertito: ombra scura in alto-sinistra → sembra "premuto dentro"
    widget.setGraphicsEffect(
        _make_shadow(
            ThemeColors.SHADOW_DARK,
            (
                -ThemeShadow.PRESS_DARK_OFFSET[0],
                -ThemeShadow.PRESS_DARK_OFFSET[1],
            ),
            ThemeShadow.PRESS_BLUR,
            ThemeShadow.PRESS_ALPHA,
        )
    )


def clear_effect(widget: QWidget) -> None:
    """Rimuove qualsiasi effetto grafico applicato al widget.

    Utile per ripristinare lo stato neutro prima di applicare un nuovo
    effetto (ad esempio al rilascio del mouse).

    Args:
        widget: Widget da pulire.
    """
    widget.setGraphicsEffect(None)
