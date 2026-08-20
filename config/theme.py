"""Token di colore e tipografia semantici per il tema Neumorphism.

Questo modulo definisce tutti i colori dell'applicazione come costanti
semantiche ispirate alle linee guida neumorphism (palette scura con
unico accento arancione #FF6600, ombre chiare e scure contrapposte).
Nessun componente UI deve contenere valori hex al di fuori di ThemeColors.
"""

from __future__ import annotations


class ThemeColors:
    """Token di colore centralizzati per il tema Neumorphism.

    La palette è costruita attorno a un unico colore di sfondo (#121213)
    dal quale nascono tutte le superfici tramite ombre contrapposte
    (chiara in alto a sinistra, scura in basso a destra). L'accento
    arancione (#FF6600) è riservato a stati attivi, link, focus e
    indicatori di stato — mai per riempire intere superfici.
    """

    # --- Sfondo e ombre (neumorphism) ---
    BG_MAIN = "#121213"           # Sfondo applicazione
    BG_FLAT = "#121213"           # Sfondo piatto (stesso materiale)
    SHADOW_LIGHT = "#1e1e21"      # Ombra chiara (alto-sinistra)
    SHADOW_LIGHT_SOFT = "#1a1a1d"  # Variante morbida
    SHADOW_DARK = "#000000"       # Ombra scura (basso-destra)
    SHADOW_DARK_SOFT = "#030304"  # Variante morbida

    # --- Testo ---
    TEXT_PRIMARY = "#ededee"      # Testo principale (rapporto > 14:1 sullo sfondo)
    TEXT_SECONDARY = "#97979b"    # Testo secondario / label
    TEXT_FAINT = "#616166"        # Testo debole / hint / placeholder
    TEXT_DISABLED = "#4a4a4e"     # Testo disabilitato

    # --- Bordi e separatori ---
    BORDER = "#1e1e21"            # Bordo sottile (uguale a shadow-light)
    DIVIDER = "rgba(255, 255, 255, 0.07)"  # Separatore sottile

    # --- Accento primario — Arancione ---
    PRIMARY = "#ff6600"           # Accento attivo / link / focus
    PRIMARY_SOFT = "#ff8c3d"      # Variante chiara (anelli focus)
    PRIMARY_DARK = "#cc5200"      # Variante scura (pressed)

    # --- Stato / feedback ---
    GOOD = "#55c98f"              # Successo / impatto basso positivo
    BAD = "#e56a65"               # Errore / impatto alto critico
    WARNING = "#f59e0b"           # Avviso / impatto medio

    # Indicatori di stato (per StatusIndicator)
    STATUS_RUNNING = "#ff6600"    # In corso: accento pulsante
    STATUS_ERROR = "#e56a65"      # Errore: rosso soft
    STATUS_STOPPED = "#616166"    # Fermato: grigio neutro
    STATUS_PAUSED = "#f59e0b"     # In pausa: ambra

    # --- Tooltip e selezione ---
    BG_TOOLTIP = "#1a1a1d"
    BG_SELECTION = "#ff6600"
    TEXT_SELECTION = "#121213"

    # --- Colori impatto eventi ---
    IMPACT_HIGH = "#e56a65"       # Alto: rosso soft
    IMPACT_MEDIUM = "#f59e0b"     # Medio: ambra
    IMPACT_LOW = "#616166"        # Basso: grigio

    # --- Surface tonali per le card (mai veri e propri colori) ---
    # Le card nel neumorphism devono essere dello stesso colore dello sfondo;
    # usiamo questi token solo come alias di compatibilità per componenti
    # che si aspettano BG_CARD.
    BG_CARD = "#121213"


class ThemeFonts:
    """Token tipografici centralizzati per il tema Neumorphism.

    Le linee guida neumorphism raccomandano:
    - Sora per i titoli (geometrica, moderna)
    - Inter per il corpo del testo (alta leggibilità su sfondo scuro)
    - JetBrains Mono per codice, etichette e badge (mono spaziale)

    Fallback a Noto Sans / Sarasa Mono SC se i font non sono installati,
    per garantire il rendering su tutti i sistemi.
    """

    FAMILY_DISPLAY = "Sora, Noto Sans, DejaVu Sans, sans-serif"
    FAMILY_MAIN = "Inter, Noto Sans, DejaVu Sans, sans-serif"
    FAMILY_MONO = "JetBrains Mono, Sarasa Mono SC, DejaVu Sans Mono, monospace"

    SIZE_DISPLAY = 22       # Titoli principali (hero, h1)
    SIZE_H2 = 18            # Sottotitoli / sezioni
    SIZE_H3 = 15            # Intestazioni card
    SIZE_CARD_HEADER = 12   # Etichette in maiuscoletto (section label)
    SIZE_BUTTON_LABEL = 13  # Etichette pulsanti
    SIZE_BODY = 13          # Testo corpo
    SIZE_SMALL = 12         # Testo piccolo
    SIZE_SHORTCUT_BADGE = 10  # Badge scorciatoia

    WEIGHT_BOLD = 700
    WEIGHT_SEMIBOLD = 600
    WEIGHT_MEDIUM = 500
    WEIGHT_NORMAL = 400


class ThemeRadius:
    """Raggi di arrotondamento coerenti con le linee guida (12/16/24)."""

    RADIUS_SM = 12   # Badge, chip, piccoli elementi
    RADIUS_MD = 16   # Pulsanti, campi di testo
    RADIUS_LG = 24   # Card, pannelli grandi, hero


class ThemeShadow:
    """Offset delle ombre neumorphic per effet­to estruso/incavato.

    Coordinate con unica fonte di luce virtuale in alto a sinistra:
    - ombra CHIARA (light) in alto a sinistra → offset negativo
    - ombra SCURA (dark) in basso a destra → offset positivo

    Per gli effetti inset (campi), gli stessi valori vanno invertiti.
    """

    # Estruso (bottoni, card) — ombra esterna
    EXTRUDE_LIGHT_OFFSET = (-6, -6)   # (dx, dy) ombra chiara
    EXTRUDE_DARK_OFFSET = (6, 6)      # (dx, dy) ombra scura
    EXTRUDE_BLUR = 14
    EXTRUDE_ALPHA = 200

    # Estruso morbido (card)
    EXTRUDE_SOFT_LIGHT_OFFSET = (-8, -8)
    EXTRUDE_SOFT_DARK_OFFSET = (8, 8)
    EXTRUDE_SOFT_BLUR = 20
    EXTRUDE_SOFT_ALPHA = 160

    # Incavato (campi) — simulato via QSS border (nessun offset QGraphicsEffect)
    INSET_BORDER_LIGHT = 1   # px bordo chiaro (top/left)
    INSET_BORDER_DARK = 1    # px bordo scuro (bottom/right)

    # Pressed (click) — ombra inset
    PRESS_LIGHT_OFFSET = (4, 4)
    PRESS_DARK_OFFSET = (-4, -4)
    PRESS_BLUR = 10
    PRESS_ALPHA = 220
