# Analisi Financial Calendar — 20 novembre 2026

Audit su `main` @ `ba7a42c` (release 1.1.0). Nessun file del progetto è stato modificato tranne la creazione di questo report. Installazione, test e avvio sono stati eseguiti su una **copia** del repository in una cartella temporanea, con `XDG_CONFIG_HOME`/`XDG_DATA_HOME` temporanei: le impostazioni e la cache reali non sono state toccate.

Legenda: **[V]** = verificato (eseguito o letto riga per riga), **[S]** = sospetto, non riprodotto.

## Riassunto

1. Il progetto è **in buono stato**: si installa, si avvia, scarica dati reali da entrambe le sorgenti e i test (81) passano. Non ci sono segreti né dipendenze vulnerabili.
2. Il core Python (scraper, cache, impostazioni, export, matching) è solido e ben difeso; la UI QML è piccola e leggibile.
3. I problemi reali sono pochi: un **bug di ordinamento numerico**, una **race sul cambio sorgente** mascherata dalla UI, un limite delle fonti non documentato.
4. Il debito vero è il **residuo delle tre riscritture della UI** (QWidget → WebEngine → QML): nomi `ig` per ForexFactory, codice morto, due meccanismi per riordinare le colonne, definizioni delle colonne in tre posti.
5. Verdetto: **da tenere e sistemare**. Non serve riscrivere niente. Con 1–2 giorni di pulizia mirata diventa coerente.

## Cosa ho eseguito

| Passo | Esito |
| --- | --- |
| `install.sh` (Python 3.14.10, venv nuovo) | **[V] OK.** PySide6 6.11.3, requests 2.34.2, jeepney 0.9.0. Import, qmllint e caricamento QML superati |
| `compileall` | [V] OK |
| `ruff` con le regole della CI (`E4,E7,E9,F`) | [V] nessun errore |
| `ruff` con regole estese (B, SIM, UP, PL, RUF) | 67 segnalazioni, quasi tutte stilistiche (`timezone.utc` → `UTC`, magic number). Nessuna indica un bug |
| `pyside6-qmllint ui/qml/*.qml` | [V] nessun warning |
| `python -m ui.validate` (software) | [V] `QML load: OK` |
| `pytest` sotto `dbus-run-session` | [V] **81 passed**, 0 skipped, 3,5 s |
| Avvio reale `main.py` offscreen con rete | [V] ForexFactory 125 eventi, FXStreet 217 eventi, 0 scarti, cache e settings scritti |
| `pip-audit -r requirements.txt` | [V] nessuna vulnerabilità nota |
| Scansione della cronologia git (117 commit) per segreti | [V] nessun segreto: solo `${{ github.token }}` nella CI |
| `vulture` (codice morto) | Vedi sezione 2 |

**Cosa non ho potuto verificare:** il controllo RHI/OpenGL (`--require-rhi`) perché `xvfb-run` non è installato; la resa visiva reale su KWin/Wayland; la comparsa effettiva della notifica sul tuo demone. La CI su GitHub è verde sull'ultimo merge, quindi questi controlli lì passano.

## Il progetto in breve

App desktop Linux che mostra in una finestra QML i calendari economici ForexFactory (feed JSON Faireconomy) e FXStreet (API pubblica). Ci sono filtri, ricerca, una vista combinata con i probabili duplicati segnalati, una cache offline, l'export CSV/ICS e notifiche D-Bus per gli eventi HIGH.

- **Stack:** Python ≥ 3.12, PySide6 6.11 (QML), requests, jeepney.
- **Struttura:** `core/` (dominio, senza Qt), `config/` (impostazioni e fusi), `ui/` (adapter Qt, modelli, runtime, QML), `tests/`.
- **Avvio:** `./install.sh` e poi `.venv/bin/python main.py`.
- **Dimensione:** circa 3.900 righe di codice di produzione e 1.700 di test.

---

## 1. Bug e comportamenti errati

### 1.1 L'ordinamento delle colonne numeriche è sbagliato — **media** [V]
`core/calendar_view.py:97-101` e `:289-296`. Le colonne Attuale, Previsione, Precedente e Dev vengono ordinate con un "natural sort" testuale, che ignora il segno e tratta le cifre decimali come un intero separato. Riprodotto con valori reali:

```
input:  0.3%  0.25%  -0.5%  -1.2%  1.0%  10K  9.5K  -0.1%
asc  →  0.3%, 0.25%, 1.0%, 9.5K, 10K, -0.1%, -0.5%, -1.2%
```

Quindi 0,3 viene prima di 0,25 e i negativi finiscono dopo i positivi, in ordine inverso. Per un calendario economico è proprio l'ordinamento che serve.
**Correzione:** per quelle colonne, estrarre il numero con una regex (`[+-]?\d+(?:[.,]\d+)?`) e ordinare per `(valore numerico, testo)`, mettendo i valori vuoti o non numerici in fondo. Aggiungere un test.

### 1.2 Race: un filtro può essere salvato sulla sorgente sbagliata — **bassa** (mascherata) [V]
`ui/adapters.py:277-281`, `:289-300`. `change()`, `moveColumn()` e `setColumnPositions()` leggono la sorgente attiva da `self._view`, cioè dall'ultimo snapshot **ricevuto**, non da quello in coda. Riprodotto con uno script sugli adapter reali: `selectSource("fxstreet")` seguito subito da `setFilter("region","USA")` salva `ig_selected_region = USA` e la vista FXStreet resta su `ALL`.
Nella UI attuale il problema non emerge perché tutti i controlli sono disabilitati quando `busy` è attivo (vedi 1.5), ma la protezione dipende da quel workaround.
**Correzione:** lasciare che sia `CalendarViewService.change()` a leggere `active_source` dalle impostazioni, dentro il worker seriale, invece di riceverlo dall'adapter.

### 1.3 Orizzonti diversi tra le sorgenti, non documentati — **media** [V]
`core/scraper_ig.py:24` usa `ff_calendar_thisweek.json`. Nel fetch reale di oggi (venerdì) l'ultimo evento ForexFactory è alle 17:15 UTC di oggi, mentre FXStreet copre fino al 27/11. Quindi da venerdì sera a domenica ForexFactory non ha eventi futuri, e nella vista "Tutti" la prossima settimana arriva da una sola fonte. Non esiste un feed pubblico `nextweek`: ho verificato che `ff_calendar_nextweek.json` risponde 404.
**Correzione:** documentarlo nel README e mostrarlo nella UI (ad esempio "ForexFactory: copertura fino a dom 22/11"). Non serve altro codice.

### 1.4 L'orario della notifica ignora il fuso scelto — **bassa** [V]
`ui/runtime.py:102`: `event_dt.astimezone()` usa il fuso del sistema, non `timezone_name` delle impostazioni. Se hai impostato `UTC` o un fuso IANA diverso, la tabella e la notifica mostrano orari diversi.
**Correzione:** usare `resolve_timezone(settings.get("timezone_name"))`.

### 1.5 I controlli si disabilitano a ogni lavoro in coda — **bassa** [V lettura, S effetto visivo]
`ui/qml/Main.qml:62,76,83,93,134,143`: tutti i controlli usano `enabled: !root.calendar.busy`. `busy` diventa vero per **ogni** job in coda: il ricaricamento ogni 30 s (`ui/adapters.py:209-212`), ogni refresh completato e il salvataggio della geometria. I job durano pochi millisecondi, ma un click che cade in quel momento viene perso e i controlli lampeggiano a opacità 0,4.
**Correzione:** dopo la 1.2 la disabilitazione non serve più. Toglierla oppure limitarla alle operazioni lunghe (l'export).

### 1.6 La geometria massimizzata perde la dimensione normale — **bassa** [S]
`ui/window.py:131-140` salva `root.geometry()` anche quando la finestra è massimizzata. Al ripristino la finestra "normale" avrà le dimensioni dello schermo intero. Non l'ho riprodotto su un desktop reale.

### 1.7 Nessuna chiusura ordinata su SIGTERM/SIGINT — **bassa** [V]
`main.py`: con `timeout -s TERM` il processo muore senza log di shutdown e senza salvare la geometria. Ctrl+C dal terminale ha lo stesso effetto. Alla chiusura normale dalla finestra il problema non si presenta.
**Correzione:** gestire `signal.signal(SIGTERM/SIGINT)` e chiamare `app.quit()`, oppure usare un `QSocketNotifier`.

---

## 2. Codice morto e residui delle migrazioni

Tutti i casi sono **[V]** con grep sul codice di produzione e sui test.

| # | Dove | Cosa | Gravità |
| --- | --- | --- | --- |
| 2.1 | `core/calendar_queries.py:50-94` | `resolve_identities()` e `combined_status()`: servivano all'export e allo stato del vecchio bridge WebEngine. Non hanno chiamanti. `combined_status` duplica anche la logica di stato che oggi vive in `CalendarView.snapshot()` | media (crea confusione: due logiche di stato) |
| 2.2 | `core/app_controller.py:241,250-251,330-336` + `core/calendar_queries.py:28,39` | Parametro `tz_offset_hours` e `_convert_events_tz`: il vecchio fuso espresso come offset numerico. In produzione si passa sempre `timezone_name`. È ancora testato in `tests/test_timezones.py` | media |
| 2.3 | `ui/qml/Main.qml:126,175-196`, `ui/adapters.py:295-300`, `core/calendar_view.py:180-186` | **Secondo meccanismo di riordino colonne** (`onColumnMoved` → `orderDelay` → `setColumnPositions`). Con `movableColumns: false` l'utente non può attivarlo: lo usa solo un test che chiama `table.moveColumn()` per codice. Il riordino reale passa da `DragHandler`/Alt+freccia → `moveColumn`. Restano anche `clearColumnReordering`, `resettingOrder` e `forceLayout` in `onAccepted` | media |
| 2.4 | `config/constants.py:13,14,99` | `AppMeta.AUTHOR`, `AppMeta.DESCRIPTION`, `PathConfig.DESKTOP_FILE`: non usati (il file `.desktop` veniva dal PKGBUILD, ora rimosso) | bassa |
| 2.5 | `config/settings.py:336` | `Settings.reset()` non usato, nemmeno nei test | bassa |
| 2.6 | `core/exceptions.py:48-58` | `ConfigError` e `ConfigValidationError` non sono mai sollevate né catturate. `AppError.details` viene impostato ma mai mostrato | bassa |
| 2.7 | `core/__init__.py`, `config/__init__.py` | Re-export di package che nessuno usa. `core/__init__` importa `AppController`, quindi `import core.models` carica tutto il controller e gli scraper | bassa |
| 2.8 | `core/models.py:17` + `app_controller.py:105,355` | Alias enum `CalendarSource.IG` (è lo stesso oggetto di `FOREXFACTORY`): `source in (IG, FOREXFACTORY)` è ridondante. La docstring parla di "bridge bindings", che non esistono più | bassa |
| 2.9 | `ui/qml/Theme.qml:8` | Token `subdued` non usato | bassa |
| 2.10 | `AUDIT_QML.md` | Report storico della PR #18 nella root, citato dal CHANGELOG. Va bene come archivio, ma in root si confonde con la documentazione corrente | bassa |

---

## 3. Duplicazioni e approcci diversi allo stesso problema

### 3.1 Le colonne sono definite in tre posti — **media** [V]
- `config/constants.py:19-38`: `IG_COLUMNS` e `FXSTREET_COLUMNS` (etichette italiane, con "Importanza" al posto di "Impatto"). Servono solo a `len()` in `settings.py`.
- `config/settings.py:21-54`: `_IG_SORT_KEYS`, `_FXSTREET_SORT_KEYS`, `_COMBINED_SORT_KEYS`. Il `10` della vista combinata è scritto a mano in `:68` e `:142`.
- `core/calendar_view.py:18-70`: `COLUMNS` e `LABELS`, cioè quelle usate davvero.

Per aggiungere una colonna bisogna modificare tre file. Se se ne dimentica uno, le impostazioni salvate vengono scartate come "permutazione non valida".
**Correzione:** tenere solo `COLUMNS`/`LABELS` (in un modulo di `core` senza dipendenze) e far derivare da lì le chiavi di ordinamento e le lunghezze in `settings.py`.

### 3.2 La lista delle regioni è duplicata in QML — **bassa** [V]
`ui/qml/Main.qml:74` riscrive a mano `CalendarDefaults.REGIONS` (`config/constants.py:44`), con `ALL` in un'altra posizione. Andrebbe esposta dall'adapter.

### 3.3 Scrittura JSON atomica copiata tre volte — **bassa** [V]
`config/settings.py:269-290`, `core/cache.py:175-198` e `core/exporters.py:187-203` contengono lo stesso schema tempfile + fsync + `os.replace` + cleanup, con piccole differenze nella gestione degli errori. Si può estrarre una funzione `atomic_write_text()`.

### 3.4 Timestamp dell'ultimo refresh salvato due volte — **bassa** [V]
`core/app_controller.py:212-218` riscrive `settings.json` (con fsync) a ogni refresh per `last_refresh_ig`/`last_refresh_fxstreet`, ma lo stesso valore è già in `refreshed_at` della cache. Il valore delle impostazioni si legge solo quando la cache manca (`:346-358`), e in quel caso lo stato è comunque "Nessun dato".
**Correzione:** eliminare le due chiavi e usare solo la cache.

### 3.5 Codice gemello per sorgente nel controller — **bassa** [V]
`core/app_controller.py:42-43,110-128,175-187`: coppie `_refreshing_ig`/`_refreshing_fxstreet`, `refresh_ig`/`refresh_fxstreet` e `_on_*_refresh_done`. Basterebbe un dizionario indicizzato per sorgente. Anche il `Future` creato a mano in `refresh_and_complete` (`:150-158`) serve solo ad adattare la firma e si può togliere.

---

## 4. Nomi fuorvianti

### 4.1 `ig` significa ForexFactory — **media** (crea confusione) [V]
La sorgente originale era IG ed è stata sostituita da ForexFactory, ma la chiave `ig` è rimasta ovunque: `scraper_ig.py`, `scraper_ig_parser.py`, `parse_ig_date`, `scrape_ig_calendar`, `refresh_ig`, le chiavi `ig_*` in `settings.json`, il file `calendar_ig.json` in cache e `IG_COLUMNS`. Chi legge il codice per la prima volta pensa a una terza sorgente.
**Correzione:** rinominare nel codice (`forexfactory`/`ff`). Le chiavi persistite si possono lasciare come sono, oppure migrare una volta in `Settings.load()` con il fallback già usato per `selected_region`. È la parte più invasiva della pulizia: va fatta per ultima e con i test.

### 4.2 `scraper_ig_parser.py` è un file di 20 righe — **bassa**
Contiene un'unica funzione usata solo da `scraper_ig.py`. Va accorpata.

---

## 5. Complessità da valutare (non sono bug)

- **Un processo Python per ogni richiesta HTTP** (`core/http_client.py`, `core/http_transport.py`) e **uno per ogni notifica** (`ui/desktop_notifications.py`). Danno una scadenza totale e un annullamento garantiti allo shutdown, sono testati e funzionano. Costano circa 100–200 ms di avvio dell'interprete per richiesta, che con refresh ogni 15 minuti è irrilevante. **Consiglio di tenerli.** Unica nota [V]: se il figlio stampa un output non JSON, `json.loads` (`core/http_client.py:50`) solleva `ValueError` e non `requests.RequestException`. Lo scraper non lo traduce in `ScraperConnectionError`, ma il controller lo cattura comunque come errore generico: niente crash, solo un messaggio meno chiaro.
- **Tre code di lavoro** (executor degli scraper, `WorkQueue` della vista, `WorkQueue` delle notifiche) con lo shutdown in due fasi (`stop`/`shutdown`, `begin_shutdown`). La struttura è corretta, ma è più complessa di quanto serva a un'app con due feed. Non la toccherei senza un motivo concreto.

---

## 6. Sicurezza

- **[V] Nessun segreto** nel codice o nella cronologia git.
- **[V] Input validati:** le impostazioni sono normalizzate chiave per chiave, la cache è validata record per record, le dimensioni HTTP sono limitate (8 MiB), il CSV è protetto dalla formula injection e l'escape ICS è corretto. I processi figli partono senza shell e ricevono i dati su stdin.
- **[V]** Il file delle impostazioni e la cache sono creati con permessi `0600`.
- Nessun problema da segnalare.

## 7. Dipendenze

- **[V]** `pip-audit` non trova vulnerabilità. PySide6 è vincolato a `<6.12`, mentre la 6.12.0 è già uscita: aggiornarla è una scelta, non un'urgenza.
- **[V]** Le dipendenze di sviluppo (`pytest`, `ruff`) sono scritte a mano due volte, nel README e in `ci.yml`. `requirements-dev.txt` e `pyproject.toml` sono stati cancellati in passato.
- **[V]** `AppMeta.ICON_NAME` è passato alle notifiche e `setDesktopFileName("financial_calendar")` è impostato, ma l'installer non installa né l'icona nel tema né il file `.desktop`. Probabilmente notifiche e taskbar Wayland mostrano un'icona generica **[S]**.

## 8. Test

- **[V] I test sono reali, non finti:** caricano il vero QML, simulano drag del mouse e tasti, usano un vero bus D-Bus privato e veri processi HTTP con scadenza e annullamento, e lavorano su fixture anonimizzate di payload reali. Nessun test fa richieste di rete.
- **Lacune:**
  - nessun test sull'ordinamento dei valori numerici (bug 1.1);
  - nessun test sulla sorgente con comandi in coda (1.2);
  - nessun test sull'orario delle notifiche (1.4).
- **Organizzazione:** i file prendono il nome dalla storia (`test_audit_regressions`, `test_migration_regressions`, `test_strategic_hardening`) invece che dalla funzionalità, quindi è difficile trovare dove è testato qualcosa. L'helper che isola i percorsi XDG è copiato in molti file perché non c'è un `conftest.py`.
- **Test su codice morto:** `test_timezones.py` testa `_convert_events_tz` (2.2) e `test_qml_migration.py:182` testa il percorso di riordino che l'utente non può usare (2.3). Vanno aggiornati insieme alla rimozione.
- La CI usa ruff solo con `E4,E7,E9,F`. È accettabile; aggiungere `B` porterebbe pochi avvisi utili.

## 9. Documentazione

| Dove | Problema | Gravità |
| --- | --- | --- |
| README | Non dice che ForexFactory copre solo la settimana corrente (1.3) | media |
| README "CSV e ICS … nell'ordine visibile" | Vale per le righe. Le colonne del CSV hanno un ordine fisso (`CSV_COLUMNS`) e non seguono il riordino dell'utente | bassa |
| README, Architettura | Riporta la storia della migrazione ("confronto su 81 combinazioni"), che appartiene al CHANGELOG | bassa |
| CHANGELOG `[1.1.0] - 2026-09-08` | Include l'audit del 29/09 e la release è del 30/09: la data non torna | bassa |
| `core/models.py:12-14` | La docstring cita i "bridge bindings" WebEngine, rimossi | bassa |

---

## Piano di pulizia

Le fasi sono ordinate dalla più sicura e utile alla più invasiva. Ognuna si chiude con la suite completa verde (`pytest`, qmllint, `ui.validate`).

### Fase 1 — Bug con impatto per l'utente (≈ 2–3 h, rischio basso)
- 1.1 ordinamento numerico, con test.
- 1.4 orario delle notifiche nel fuso scelto, con test.
- 1.3 documentare la copertura di ForexFactory nel README (e, se vuoi, aggiungere un'indicazione nella UI).

### Fase 2 — Rimozione del codice morto (≈ 2 h, rischio basso)
- 2.1, 2.2, 2.4–2.9, aggiornando i test che usano `_convert_events_tz`.
- Spostare `AUDIT_QML.md` in `docs/` e correggere la data nel CHANGELOG e la docstring di `models.py`.

### Fase 3 — Un solo meccanismo per colonne e comandi (≈ 3–4 h, rischio medio)
- 2.3: rimuovere il percorso `onColumnMoved`/`setColumnPositions` e riscrivere il test con Alt+freccia o con il drag.
- 1.2: far leggere la sorgente attiva al servizio, poi 1.5: togliere `enabled: !busy` dai controlli, con un test della race.
- 3.1: un'unica definizione delle colonne; 3.2: esporre le regioni dall'adapter.

### Fase 4 — Consolidamento interno (≈ 2–3 h, rischio basso-medio)
- 3.3 helper `atomic_write_text`; 3.4 togliere `last_refresh_*` dalle impostazioni; 3.5 controller indicizzato per sorgente.
- 1.7 gestione di SIGTERM/SIGINT; 1.6 salvare la geometria normale quando la finestra è massimizzata.
- `conftest.py` con la fixture di isolamento XDG; `requirements-dev.txt` usato sia da README sia da CI.

### Fase 5 — Rinomina `ig` → ForexFactory (≈ 3–4 h, rischio medio-alto)
- 4.1 e 4.2: rinominare moduli, funzioni ed enum. Migrare una volta le chiavi di `settings.json` e il nome del file di cache, oppure lasciarli invariati e documentarlo. Va fatta per ultima perché tocca quasi tutti i file e i dati persistiti.

### Facoltativo
- Installare il file `.desktop` e l'icona dall'installer (sez. 7).
- Rinominare i file di test per funzionalità.
- Aggiornare PySide6 a 6.12 dopo un giro completo di test.

**Totale stimato: 1,5–2 giornate** per le fasi 1–5.

---

## Esito della pulizia (branch `cleanup/audit-phases`)

Le fasi 1–5 sono state eseguite in ordine. I riferimenti di riga qui sopra valgono per `ba7a42c`.

| Fase | Fatto | Prova |
| --- | --- | --- |
| 1 | 1.1 ordinamento numerico; 1.4 fuso delle notifiche; 1.3 copertura documentata nel README | `tests/test_sorting.py`, `test_notification_time_uses_the_configured_timezone` (fallisce senza correzione) |
| 2 | Rimossi 2.1, 2.2, 2.4–2.9; `AUDIT_QML.md` → `docs/`; data del CHANGELOG | suite completa |
| 3 | 2.3 un solo riordino; 1.2 sorgente letta nel worker e spostamenti per chiave; 1.5 controlli non più disabilitati; 3.1 colonne in `config/constants.py`; 3.2 regioni e impatti esposti dall'adapter | `test_commands_queued_after_a_source_switch_apply_to_the_new_source`, test del drag sull'intestazione |
| 4 | 3.3 `config/storage.atomic_write_text`; 3.4 niente `last_refresh_*`; 3.5 controller per sorgente; 1.7 SIGTERM/SIGINT; 1.6 geometria massimizzata; `tests/conftest.py`; `requirements-dev.txt` | `kill -TERM` → exit 0 e geometria salvata; `test_maximized_window_keeps_its_normal_geometry` (fallisce senza correzione) |
| 5 | 4.1 `ig` → `forexfactory` con migrazione di impostazioni e cache; UID ICS invariati; 4.2 parser accorpato | `tests/test_legacy_migration.py`; avvio reale su una copia dei dati utente in formato `ig` |

Emersi durante il lavoro, corretti nella stessa PR:
- Il flag `maximized` veniva letto a finestra già nascosta, quindi era sempre `false`.
- Il ripristino di una finestra massimizzata veniva annullato da `show()`.

Non fatti, di proposito:
- Installazione di `.desktop` e icona: scrive fuori dal repository.
- Rinomina dei file di test per funzionalità: molto rumore nel diff, poco valore.
- Aggiornamento a PySide6 6.12.
- Aumento della versione: il CHANGELOG ha una sezione `[Unreleased]` così il merge non pubblica una release.
