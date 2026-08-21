# Financial Calendar

Applicazione desktop Python per i calendari economici **ForexFactory/Faireconomy** e **FXStreet**, con interfaccia HTML/CSS/JavaScript ospitata in Qt WebEngine.

La UI usa superfici `#141414` e `#FF6600` come unico colore accent.

## Requisiti

- Python 3.12+
- Linux desktop
- accesso a Internet per installare le dipendenze e aggiornare i calendari

## Installazione

Dalla root della repository:

```bash
chmod +x install.sh
./install.sh
```

Lo script crea la `.venv` locale e installa esclusivamente le dipendenze di `requirements.txt`.

## Avvio

```bash
.venv/bin/python main.py
```

Per il logging di debug:

```bash
.venv/bin/python main.py --debug
```

## Struttura

```text
assets/       Icone e bandiere
config/       Costanti e impostazioni persistenti
core/         Modelli, controller e scraper
tests/        Test automatici
ui/           Finestra Qt, bridge QWebChannel e frontend HTML/CSS/JS

install.sh    Installazione locale nella .venv
main.py       Entry point
requirements.txt
```

Le cartelle applicative principali sono quindi `core`, `config`, `assets`, `tests` e `ui`.

## Architettura

```text
core / config
    ↓
AppController
    ↓
ui.bridge / QWebChannel
    ↓
ui.window / Qt WebEngine
    ↓
HTML + CSS + JavaScript
```

Non viene avviato alcun server HTTP locale e non è richiesto alcun browser esterno. Python gestisce rete, persistenza, filtri e lavoro in background; il frontend gestisce esclusivamente la presentazione.

## Funzioni principali

- calendari ForexFactory/Faireconomy e FXStreet
- refresh asincrono
- filtri indipendenti per data, area e impatto
- conversione del fuso orario
- ordinamento e riordino persistente delle colonne
- bandiere dei paesi
- errori leggibili mantenendo visibili gli ultimi dati reali
- log applicativo integrato
- chiusura diretta con la X della finestra
- UI contenuta nella finestra con scroll interno della tabella

## Sviluppo e test

Le dipendenze di sviluppo non sono mantenute in file di configurazione aggiuntivi. Per eseguire i controlli locali:

```bash
.venv/bin/python -m pip install "pytest>=8.3,<9" "ruff>=0.12,<1"
.venv/bin/python -m compileall -q main.py config core ui tests
.venv/bin/ruff check --target-version py312 --select E4,E7,E9,F main.py config core ui tests
node --check ui/app.js
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --no-sandbox" \
  .venv/bin/python -m pytest tests -q
```

Non sono necessari `pyproject.toml`, package metadata o altri sistemi di packaging Python.
