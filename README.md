# Financial Calendar

Calendari economici **ForexFactory/Faireconomy** e **FXStreet** in una finestra desktop QML nativa. Versione **1.1.0**.

## Installazione e avvio

Richiede Linux desktop, Python 3.12+, Qt/PySide6 6.11 e librerie di sistema OpenGL/EGL. Su Ubuntu: `sudo apt install python3-venv libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri`. Per le notifiche serve un session bus D-Bus con servizio Freedesktop Notifications.

```bash
chmod +x install.sh
./install.sh
.venv/bin/python main.py
```

L'installer crea o ripara `.venv`, ripristina pip quando manca, installa `requirements.txt`, esegue il lint QML e carica la finestra con configurazione temporanea senza rete. `main.py --debug` abilita il logging dettagliato.

## Funzioni

- Sorgenti separate e vista **Tutti**, con indicazione dei probabili duplicati senza eliminare eventi.
- Filtri per paese, impatto e data; ricerca; Oggi, Domani e Prossime 24 ore. I fusi `local`, `UTC`, IANA (es. `Europe/Rome`) e offset (es. `UTC+02:00`) sono risolti in Python, anche attraverso cambi DST.
- Ordinamento cliccando le intestazioni; trascinamento delle colonne oppure **Alt+← / Alt+→** sull'intestazione selezionata. Filtri, ordinamento e colonne sono salvati per sorgente.
- Refresh indipendente, freschezza per sorgente, cache persistente, avvio offline e dati precedenti conservati in caso di errore. La vista combinata segnala la disponibilità parziale.
- Auto-refresh a 5/15/30/60 minuti; 0 disattiva. **Ctrl+R** aggiorna ForexFactory, **Ctrl+F** FXStreet.
- Countdown e prossimo evento HIGH. Notifiche HIGH facoltative a 5/15/30/60 minuti: un evento viene registrato come notificato soltanto dopo una consegna riuscita.
- CSV e ICS della vista Python effettivamente mostrata, nell'ordine visibile. CSV protegge le formule mantenendo i valori economici; ICS comunica il numero effettivo di eventi scritti.
- Log consultabile e copiabile, limitato a 250 messaggi; geometria della finestra persistente. **X** e **Ctrl+Q** terminano l'applicazione; nessuna tray.

## Architettura

`main.py` collega `QApplication`, impostazioni, controller e finestra. `QQmlApplicationEngine` carica `ui/qml/Main.qml`.

| Cartella | Responsabilità |
| --- | --- |
| `core/` | Dominio indipendente da Qt, scraper, cache, query, ordinamento, matching, export e policy notifiche |
| `config/` | Validazione e persistenza atomica delle impostazioni; risoluzione dei fusi |
| `ui/` | Modelli Qt, adapter mirati, runtime, lavoro asincrono, finestre native e shell |
| `ui/qml/` | Presentazione, controlli semantici e tema condiviso |
| `assets/` | Icone, bandiere e Noto Sans con licenza OFL |
| `tests/` | Fixture dei feed, test di dominio, regressioni e interazione QML |

Il dataset resta nei modelli `QAbstractTableModel`/`QAbstractListModel`; QML riceve solo una piccola proiezione delle preferenze. Query, persistenza, matching, export e consegna notifiche lavorano fuori dal thread GUI. Le richieste HTTP sono isolate in processi brevi con scadenza totale di 35 secondi, risposta massima di 8 MiB, Retry-After limitato e annullamento alla chiusura. Il trasporto QtDBus è isolato con scadenza di 5 secondi. I processi vengono terminati e raccolti, senza shell.

`Theme.qml` centralizza superficie `#141414`, accento `#ff6600`, testo, font e raggi 28/22/16/12. `RaisedSurface` usa `RectangularShadow` con `cached: false`; `InsetSurface` compone bordi interni. Non ci sono shader personalizzati da compilare: quelli di Qt accompagnano la stessa versione PySide6. Le celle non hanno effetti individuali. La tabella e il log virtualizzano e riutilizzano i delegate.

Le impostazioni e la cache mantengono i percorsi XDG precedenti. La geometria QWidget esistente viene importata una volta nel nuovo formato QML. Il frontend WebEngine è stato rimosso dopo un confronto su 81 combinazioni di sorgenti, filtri e fusi.

## Verifiche

```bash
.venv/bin/python -m pip install 'pytest>=8.3,<9' 'ruff>=0.12,<1'
.venv/bin/python -m compileall -q main.py config core ui tests
.venv/bin/ruff check --target-version py312 --select E4,E7,E9,F main.py config core ui tests
.venv/bin/pyside6-qmllint ui/qml/*.qml
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software .venv/bin/python -m ui.validate
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=rhi QSG_RHI_BACKEND=opengl LIBGL_ALWAYS_SOFTWARE=1 .venv/bin/python -m ui.validate --require-rhi
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software dbus-run-session -- .venv/bin/python -m pytest tests -q
```

La CI esegue questi controlli su Python 3.12 e 3.14, incluso un vero servizio D-Bus privato e il caricamento con OpenGL. Il test D-Bus viene saltato solo quando non esiste una sessione di test. La verifica software non certifica ombre o accelerazione grafica: per questo esiste il controllo RHI separato. La pubblicazione della release su main dipende dal successo dei test.
