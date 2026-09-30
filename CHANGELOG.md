# Changelog

## [1.1.0] - 2026-09-08

### UI QML nativa
- QApplication e QQmlApplicationEngine; eliminati WebEngine, WebChannel e frontend web dopo confronto di parità su 81 combinazioni.
- Tabella e log virtualizzati, tema neumorfico compatto condiviso, Noto Sans incluso, controlli accessibili e navigazione da tastiera.
- Conservati sorgenti, filtri, ricerca, intervalli, ordinamento e riordino colonne, export, cache, notifiche, log, scorciatoie e geometria.

### Audit desktop del 29 settembre 2026
- Corrette race nel completamento refresh, modifiche involontarie alla data relative al focus, JSON eccessivamente annidati, overflow cache e avvio prematuro di processi HTTP.
- Notifiche sempre asincrone, risposta D-Bus UINT32 validata e servizio dei test corretto; riordino colonne con gesto QML interno e persistenza Python.
- Superfici uniformi, ombre calibrate nel tema, background controlli condivisi e navigazione tabella da tastiera.
- Audit documentato in `AUDIT_QML.md`; 81 test locali e 9 interazioni OpenGL passate, avvio e chiusura verificati con entrambi i feed reali.

### Affidabilità
- Query, matching, salvataggi, export e notifiche fuori dal thread GUI; export dalla vista canonica Python.
- Refresh protetto fino al completamento della persistenza, errori per sorgente e disponibilità parziale esplicita.
- HTTP con scadenza totale, annullamento, limite alla risposta e Retry-After; consegna D-Bus (Jeepney) con timeout.
- Validazione robusta di fusi, minuti e timestamp; conteggio ICS effettivo, protezione CSV, notifiche confermate solo dopo consegna e memoria della policy potata.
- Timer non rimandati dagli aggiornamenti della vista; installer ripara pip e verifica QML.
- CI con compileall, Ruff, QML lint/load, RHI OpenGL, interazioni Qt e trasporto D-Bus reale su Python 3.12/3.14.

## [1.0.1] - 2026-08-25

Release di manutenzione strategica successiva alla chiusura della roadmap 1.0.

### Architettura
- stato operativo reso canonico e privato al controller tramite snapshot immutabili per sorgente;
- query combinate, matching dei probabili duplicati e policy notifiche consolidati in moduli Python dedicati;
- `CalendarBridge` riportato al ruolo di adattatore QWebChannel, senza ownership di timer o regole di dominio;
- rimosso l'EventBus globale e sostituito il flusso controller→UI con dipendenze esplicite;
- presentation HTML/CSS/JavaScript confinata in `ui/web/`, senza monkey patching o duplicate detection nel frontend;
- integrazioni native Qt/D-Bus e file dialog separate dal core.

### Affidabilità e sicurezza
- export risolto contro i dati canonici Python, accettando dal frontend solo identità e data/ora di presentazione validate;
- WebEngine reso local-only, con navigazioni HTTP(S) inoltrate al browser di sistema;
- `install.sh` rafforzato con verifica Python 3.12+, riparazione della `.venv` e controllo degli import critici;
- test riallineati alle interfacce pubbliche e aggiunta copertura per matching, notification policy ed export boundary.

### Manutenzione
- rimossa duplicazione e dead code residuo emersi dal secondo audit strategico;
- nessuna nuova feature o modifica intenzionale al comportamento utente della release 1.0.0.

## [1.0.0] - 2026-08-21

Prima release pubblica stabile di Financial Calendar.

### Dati e affidabilità
- calendari ForexFactory/Faireconomy e FXStreet, aggiornabili in modo indipendente;
- cache persistente dell'ultimo dataset valido per sorgente e avvio offline;
- conversione timezone DST-safe tramite zone IANA;
- gestione parziale quando una sorgente fallisce e l'altra rimane disponibile;
- metriche di refresh, retry e warning sul tasso di record scartati dai parser;
- fixture anonimizzate dei feed e copertura automatica dei contratti API.

### Interfaccia
- frontend HTML/CSS/JavaScript ospitato in Qt WebEngine tramite QWebChannel;
- dark neumorphism `#141414` con accent `#FF6600`;
- layout compatto automatico per finestre non massimizzate;
- ricerca locale, filtri rapidi Oggi/Domani/Prossime 24h e countdown;
- evidenziazione del prossimo evento HIGH e attenuazione degli eventi trascorsi;
- persistenza di sorgente, filtri, timezone, ordinamento, colonne e geometria finestra.

### Operatività
- vista combinata delle due sorgenti con indicazione non distruttiva dei probabili duplicati;
- notifiche desktop opzionali per eventi HIGH via Freedesktop D-Bus;
- export CSV e ICS degli eventi visibili;
- auto-refresh configurabile Manuale / 5 / 15 / 30 / 60 minuti.

### Qualità
- nessun server HTTP locale, database o framework JavaScript aggiuntivo;
- installazione locale tramite `install.sh` e `.venv`;
- CI su Python 3.12 e 3.14 con compile check, Ruff, JavaScript syntax check e suite Qt/WebEngine.
