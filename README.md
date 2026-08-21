# Financial Calendar

Applicazione desktop Python per i calendari economici **ForexFactory/Faireconomy** e **FXStreet**, con interfaccia HTML/CSS/JavaScript ospitata in Qt WebEngine.

La UI usa superfici `#141414` e `#FF6600` come unico colore accent.

## Requisiti

- Python 3.12+
- Linux desktop
- accesso a Internet per installare le dipendenze e aggiornare i calendari

Dopo almeno un refresh riuscito, l'app può riaprire l'ultimo calendario valido anche temporaneamente senza rete grazie alla cache locale persistente.

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
core/         Modelli, controller, cache e scraper
tests/        Test automatici
ui/           Finestra Qt, bridge QWebChannel e frontend HTML/CSS/JS

install.sh    Installazione locale nella .venv
main.py       Entry point
requirements.txt
ROADMAP.md    Piano di evoluzione del programma
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

Non viene avviato alcun server HTTP locale e non è richiesto alcun browser esterno. Python gestisce rete, cache, persistenza, filtri e lavoro in background; il frontend gestisce esclusivamente la presentazione.

## Funzioni principali

- calendari ForexFactory/Faireconomy e FXStreet
- refresh asincrono
- cache persistente dell'ultimo calendario valido per sorgente
- avvio con dati salvati prima del refresh di rete
- mantenimento degli ultimi dati reali se un refresh fallisce
- timestamp di refresh interni in ISO-8601 UTC
- filtri indipendenti per data, area e impatto
- conversione timezone DST-safe tramite zone IANA, con offset UTC fissi ancora disponibili
- stato sorgente distinto tra dati aggiornati, dati salvati e assenza di dati
- ordinamento e riordino persistente delle colonne
- bandiere dei paesi
- errori leggibili mantenendo visibili gli ultimi dati reali
- log applicativo integrato
- chiusura diretta con la X della finestra
- UI contenuta nella finestra con scroll interno della tabella

## Roadmap

Lo sviluppo pianificato è tracciato in `ROADMAP.md`, con checklist per affidabilità, auto-refresh, persistenza UX, ricerca, notifiche ed export.

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
