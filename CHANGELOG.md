# Changelog

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
