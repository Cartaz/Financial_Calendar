# Financial Calendar

Applicazione desktop Python per i calendari economici **ForexFactory/Faireconomy** e **FXStreet**, con interfaccia HTML/CSS/JavaScript ospitata in Qt WebEngine.

**Release stabile: 1.0.0**

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
core/         Modelli, controller, cache, export, notifiche e scraper
tests/        Test automatici e fixture anonimizzate dei feed
ui/           Finestra Qt, bridge QWebChannel e frontend HTML/CSS/JS

install.sh    Installazione locale nella .venv
main.py       Entry point
requirements.txt
CHANGELOG.md  Cronologia delle release pubbliche
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

Non viene avviato alcun server HTTP locale e non è richiesto alcun browser esterno. Python gestisce rete, cache, persistenza, timer, notifiche desktop, export e osservabilità dei refresh; il frontend gestisce presentazione e navigazione locale del dataset già ricevuto.

## Funzioni principali

- calendari ForexFactory/Faireconomy e FXStreet
- vista combinata `Tutti` con filtri, colonne e ordinamento persistenti indipendenti
- indicazione non distruttiva dei probabili duplicati tra le due sorgenti, senza eliminare righe
- refresh asincrono e indipendente per sorgente
- auto-refresh configurabile: Manuale / 5 / 15 / 30 / 60 minuti
- indicatore di freschezza indipendente per ciascuna sorgente
- cache persistente dell'ultimo calendario valido per sorgente
- avvio con dati salvati prima del refresh di rete
- mantenimento degli ultimi dati reali se un refresh fallisce
- funzionamento parziale quando una sorgente è disponibile e l'altra è in errore
- timestamp di refresh interni in ISO-8601 UTC
- metriche di refresh nel log: durata, raw, validi, scartati, retry e origine cache/rete
- warning automatico quando almeno il 20% di un campione di almeno 5 record raw viene scartato dal parser
- fixture anonimizzate basate sulla struttura reale dei payload di entrambe le API
- filtri indipendenti per data, area e impatto
- ricerca testuale locale su evento, paese, impatto e valori economici
- filtri rapidi Tutti / Oggi / Domani / Prossime 24h
- filtro Prossime 24h basato sui timestamp UTC reali, anche attraverso mezzanotte e cambi DST
- countdown locale per gli eventi futuri
- indicazione del prossimo evento HIGH e sua evidenziazione discreta
- attenuazione degli eventi già trascorsi
- notifiche desktop opzionali per eventi HIGH, configurabili a 5 / 15 / 30 / 60 minuti prima
- notifiche Linux tramite lo standard Freedesktop D-Bus, senza modalità tray e senza processi `notify-send`
- export CSV degli eventi attualmente visibili dopo filtri, ricerca e intervallo rapido
- export ICS degli eventi visibili con timestamp UTC e UID stabili
- conversione timezone DST-safe tramite zone IANA, con offset UTC fissi ancora disponibili
- stato sorgente distinto tra dati aggiornati, dati salvati, dati non recenti e assenza di dati
- ripristino della sorgente attiva, data, timezone, intervallo auto-refresh e preferenza notifiche
- ordinamento e riordino persistente delle colonne, separato per sorgente e vista combinata
- ripristino di dimensione e posizione della finestra
- bandiere dei paesi
- errori leggibili mantenendo visibili gli ultimi dati reali
- log applicativo integrato
- chiusura diretta con la X della finestra
- UI contenuta nella finestra con scroll interno della tabella

## Release

La cronologia delle release pubbliche è mantenuta in `CHANGELOG.md`. La release `v1.0.0` rappresenta la prima versione pubblica stabile del progetto.

## Sviluppo e test

Le dipendenze di sviluppo non sono mantenute in file di configurazione aggiuntivi. Per eseguire i controlli locali:

```bash
.venv/bin/python -m pip install "pytest>=8.3,<9" "ruff>=0.12,<1"
.venv/bin/python -m compileall -q main.py config core ui tests
.venv/bin/ruff check --target-version py312 --select E4,E7,E9,F main.py config core ui tests
node --check ui/app.js
node --check ui/navigation.js
node --check ui/operations.js
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --no-sandbox" \
  .venv/bin/python -m pytest tests -q
```

Le fixture dei feed usate dai test sono in `tests/fixtures/` e non vengono mai usate come dati di fallback runtime.

Non sono necessari `pyproject.toml`, package metadata o altri sistemi di packaging Python.
