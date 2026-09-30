# Audit Financial Calendar — 29 settembre 2026

Audit della migrazione QML della PR #18, partendo da `3524d66b3dfdd6d6b736228e60c034d8086e43fd`. `main` all'inizio dell'audit era ancora la versione WebEngine (`e0524f4bf09b3ddc7e64efc5693ef30e723baf63`). Il riferimento è lo standard Cartaz Desktop Application — QML Compact.

## Architettura e responsabilità

| Area | Proprietario e verifica |
| --- | --- |
| Avvio | `main.py`: logging, QApplication, settings, controller e wiring della finestra; nessuna logica di dominio |
| Dati e refresh | `AppController`: snapshot immutabili per sorgente, lock, refresh indipendenti, cancellazione e persistenza |
| Query | `CalendarViewService` / `CalendarQueryService`: filtri, ricerca, intervalli, fusi, ordinamento, duplicati e vista canonica per export |
| Persistenza | `Settings` e `CalendarCache`: percorsi XDG, validazione, sostituzione atomica, rollback delle preferenze su errore |
| Confine Qt | `CalendarAdapter`, `PreferencesAdapter`, `ExportAdapter`: slot tipizzati, segnali e proiezioni UI; modello tabellare e modelli lista Qt |
| Presentazione | `QQmlApplicationEngine` e QML; tabella/log virtualizzati; nessun WebEngine, WebChannel, DOM o dataset JS duplicato |
| Integrazione nativa | QApplication, finestra QML, QFileDialog non bloccante, clipboard, notifiche D-Bus e scorciatoie; nessuna tray |
| Concorrenza | Executor scraper, code seriali per vista/persistenza e notifiche; HTTP e D-Bus isolati in processi con scadenze |
| Lifecycle | Stop dei timer e dei callback, annullamento HTTP, attesa dei worker e raccolta dei subprocess; salvataggio geometria |

Sono stati letti entry point, installer, configurazione, servizi core, adapter, modelli, componenti QML, notifiche e controlli CI. Il core sano è stato mantenuto; non è stato introdotto un nuovo stack UI.

## Problemi riprodotti e correzioni

| Problema | Correzione e prova |
| --- | --- |
| Un Future già terminato eseguiva il callback di refresh sul chiamante, portando la persistenza sul thread GUI | Completamento incluso nel lavoro dell'executor; regressione forza un Future già completato e verifica il thread del salvataggio |
| Dare e togliere focus alla data trasformava `Oggi` in una data fissa | Data persistita distinta dalla data relativa derivata; salvataggio solo dopo modifica dell'utente. Test focus, input invalido e input valido |
| JSON locale eccessivamente annidato sollevava RecursionError durante l'avvio | Settings torna ai default e cache viene ignorata; test su entrambi i file corrotti |
| Timestamp estremo causava OverflowError nel salvataggio cache | Rifiuto esplicito senza eccezione non gestita; test con anno 1 e offset +14:00 |
| Opzioni HTTP non serializzabili avviavano un figlio prima dell'errore, lasciandolo in attesa su stdin | Serializzazione prima dell'avvio; regressione verifica che nessun figlio venga creato |
| Il servizio del test D-Bus restituiva un array di variant invece di UINT32, bloccando la CI | Servizio di prova con risposta wire tipizzata; verifica di risposta valida, variant, intero signed ed errore sul vero bus privato |
| Il trasporto notifiche accettava anche risposte con tipo wire sbagliato | Verifica di method_return, firma `u` e singolo identificatore intero |
| CalendarRuntime senza coda esplicita consegnava le notifiche in modo sincrono | Coda sempre presente, proprietà e shutdown espliciti; test con notifier bloccante verifica il thread e la chiusura |
| Gerarchia delle superfici e ombre non allineata al contratto | Pannello principale strong raised; superficie uniforme; stato selezionato con testo arancione e bordi inset leggeri; token ombre centralizzati e background controlli condiviso |

Il riordino è stato inoltre consolidato: il percorso precedente dipendeva da un drag nativo QDrag e il gesto QTest non produceva un ordine persistito, mentre `moveColumn()` programmatico passava. Questo, da solo, non certificava un difetto su un desktop fisico. È ora usato un DragHandler interno che invia una richiesta tipizzata a Python al rilascio: nessun ordine persistente è posseduto dai delegate. I test verificano il gesto mouse, l'assenza di sort accidentale, Alt+freccia, persistenza e ritorno alla sorgente precedente, sia software sia OpenGL.

## Verifiche osservate

Ambiente locale: Linux, Python 3.12.14, PySide6/Qt 6.11.2. Test grafici su display Xvfb con RHI OpenGL Mesa software (`LIBGL_ALWAYS_SOFTWARE=1`).

- Installazione iniziale tramite `bash install.sh`: riuscita, inclusi import, QML lint e caricamento.
- `compileall`, Ruff (regole CI E4/E7/E9/F), `bash -n install.sh`, `pyside6-qmllint`: passati.
- Caricamento QML software e `ui.validate --require-rhi` con OpenGL: passati.
- Suite completa su bus D-Bus privato: **81 passed**, nessun test saltato.
- Interazioni QML sul renderer OpenGL: **9 passed**.
- Copertura mantenuta: scraper/fixture degradate, timezone e DST, filtri, ordinamento e duplicati, cache/offline e disponibilità parziale, export CSV/ICS, rollback impostazioni, timer, deadline HTTP, annullamento e raccolta subprocess, lifecycle e geometria.
- Avvio del vero `main.main()` con impostazioni XDG temporanee e rete reale: ForexFactory **141 eventi validi** e FXStreet **387**, zero scarti e zero retry; **521 eventi** nella vista combinata dopo il cutoff degli eventi passati (134 + 387).
- Finestra ispezionata a **1360×820** e **820×560**: layout visibile e tabella con scroll interno; nessun warning QML.
- Chiusura attraverso il normale event loop: codice **0**, executor arrestati e geometria salvata.
- PSS da `/proc/self/smaps_rollup` nella vista combinata: **241090 kB**. È una singola misura su Mesa software, non un confronto prestazionale né una previsione per la GPU dell'utente.

## Scelte e limiti

Le superfici inset usano il componente leggero a bordi interni, non uno shader SDF: deviazione estetica dichiarata rispetto a un inset con blur perfetto, senza introdurre effetti costosi nei delegate. Le ombre raised/glow sono quelle Qt della stessa versione PySide6, con `cached: false`; non esistono shader custom da compilare con qsb.

Il test locale non certifica KWin/Wayland, la GPU AMD reale, il file picker del desktop dell'utente né la comparsa della notifica sul suo daemon. D-Bus è stato verificato con un vero bus privato e servizio di test tipizzato. Non è stato eseguito un soak test di ore. I feed e i conteggi descrivono il campione del 29 settembre, non garantiscono la disponibilità futura delle API.

La CI della PR deve completare compile/lint, load software, OpenGL e suite con D-Bus su Python 3.12 e 3.14 prima del merge. Lo stato effettivo finale è visibile nella PR; questo documento non anticipa il risultato della CI. Non sono rimasti fallimenti riproducibili nei controlli locali descritti, senza affermare che ogni possibile bug sia escluso.

## Fonti

- Repository e PR: https://github.com/Cartaz/Financial_Calendar/pull/18
- Qt ListView e riuso dei delegate: https://doc.qt.io/qt-6/qml-qtquick-listview.html
- Qt HorizontalHeaderView: https://doc.qt.io/qt-6/qml-qtquick-controls-horizontalheaderview.html
- Qt RectangularShadow: https://doc.qt.io/qt-6/qml-qtquick-effects-rectangularshadow.html
- Specifica Freedesktop Notifications: https://specifications.freedesktop.org/notification/latest-single/
- Implementazione ufficiale Qt del drag nativo: https://github.com/qt/qtdeclarative/blob/v6.11.2/src/quick/items/qquicktableview.cpp
