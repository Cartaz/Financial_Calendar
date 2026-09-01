# Financial Calendar — Campagna approfondita di bug hunting

## Scopo

Questo documento definisce una campagna di bug hunting ripetibile per Financial Calendar. L'obiettivo non è soltanto trovare crash evidenti, ma verificare che l'applicazione resti corretta quando dati, rete, cache, timezone, filesystem, WebEngine e lifecycle Qt si comportano in condizioni realistiche o degradate.

La campagna deve cercare in particolare:

- perdita o corruzione dello stato canonico Python;
- divergenze tra UI e backend;
- dati economici mostrati con data/ora, sorgente, impatto o valori errati;
- errori silenziosi negli scraper;
- regressioni offline/cache;
- race condition durante refresh e shutdown;
- problemi di persistenza o recovery;
- errori di sicurezza nel confine WebEngine/QWebChannel;
- regressioni di accessibilità e usabilità desktop.

Un test è considerato superato solo quando il comportamento osservato coincide con quello atteso e non compaiono eccezioni, warning anomali, dati inventati, perdita di dati validi o stato incoerente.

---

## 1. Preparazione dell'ambiente

Usare una copia pulita della repository e l'installazione canonica:

```bash
chmod +x install.sh
./install.sh
.venv/bin/python main.py
```

Prima della campagna eseguire anche:

```bash
.venv/bin/python -m compileall -q main.py config core ui tests
.venv/bin/ruff check --target-version py312 --select E4,E7,E9,F main.py config core ui tests
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests -q
```

Se disponibili, ripetere i test almeno su Python 3.12 e sulla versione Python più recente supportata dalla CI.

Per evitare che cache e configurazioni pregresse nascondano difetti, eseguire parte della campagna con directory XDG temporanee:

```bash
export XDG_CONFIG_HOME="$(mktemp -d)"
export XDG_DATA_HOME="$(mktemp -d)"
.venv/bin/python main.py
```

Annotare per ogni sessione:

- commit SHA;
- versione Python;
- versione PySide6/Qt;
- sistema operativo e sessione grafica;
- timezone di sistema;
- presenza/assenza di rete;
- stato iniziale di config e cache.

---

## 2. Classificazione dei bug

### Severità

| Livello | Criterio |
| --- | --- |
| **S0 - Critico** | perdita/corruzione dati persistenti, comportamento pericoloso, esecuzione non autorizzata, crash sistematico all'avvio |
| **S1 - Alto** | dati economici sostanzialmente errati, refresh che distrugge dati validi, deadlock, freeze UI, export errato, errore di timezone rilevante |
| **S2 - Medio** | funzione importante non disponibile, stato UI/backend divergente, recovery difettoso, notifica errata, problema significativo di accessibilità |
| **S3 - Basso** | difetto visuale, messaggio poco chiaro, problema minore di layout o UX senza perdita di correttezza |

### Priorità di correzione

1. S0 immediatamente;
2. S1 prima di qualsiasi nuova feature;
3. S2 nella milestone corrente se tocca il codice modificato;
4. S3 solo dopo aver escluso cause architetturali più profonde.

---

## 3. Regola di riproducibilità

Ogni bug deve avere una scheda minima:

```text
ID:
Titolo:
Severità:
Commit:
Ambiente:
Precondizioni:
Passi per riprodurre:
Risultato osservato:
Risultato atteso:
Frequenza: sempre / intermittente / una volta
Log rilevanti:
File coinvolti sospetti:
Screenshot/video se utile:
```

Prima di correggere un bug intermittente, tentare almeno 10 riproduzioni controllate. Per problemi di concorrenza, aumentare a 50-100 cicli quando praticabile.

---

# CAMPAGNA A — Avvio, installazione e lifecycle

## A1. Installazione pulita

- [ ] Eseguire `./install.sh` da root repository.
- [ ] Eseguirlo da una directory diversa usando il path assoluto allo script.
- [ ] Rieseguirlo con `.venv` già valida.
- [ ] Simulare `.venv` corrotta/non valida e verificare recovery chiaro.
- [ ] Verificare errore comprensibile con Python < 3.12.
- [ ] Verificare errore comprensibile se il modulo `venv` manca.
- [ ] Verificare gli import critici di PySide6, WebEngine e QWebChannel.
- [ ] Controllare che non vengano creati file di build/config non previsti nella repository.

## A2. Avvio pulito

- [ ] Avvio senza file settings.
- [ ] Avvio senza cache.
- [ ] Avvio senza rete.
- [ ] Avvio con cache valida ma rete assente.
- [ ] Avvio con settings JSON vuoto.
- [ ] Avvio con settings JSON troncato.
- [ ] Avvio con settings di schema vecchio.
- [ ] Avvio con dati XDG non scrivibili.

**Atteso:** la GUI non deve bloccarsi; configurazioni invalide devono degradare verso default sicuri; la mancanza di rete non deve cancellare dati validi già disponibili.

## A3. Shutdown

Ripetere almeno 25 volte:

- [ ] chiusura immediata dopo l'avvio;
- [ ] chiusura durante refresh ForexFactory;
- [ ] chiusura durante refresh FXStreet;
- [ ] chiusura durante refresh simultaneo;
- [ ] chiusura mentre sono attivi i timer automatici;
- [ ] chiusura dopo apertura dialog export;
- [ ] chiusura dopo una failure di rete.

Controllare:

- [ ] nessun processo Python orfano;
- [ ] nessuna callback tardiva che modifica UI/stato dopo `begin_shutdown`;
- [ ] nessuna eccezione `QObject deleted`, timer su oggetti distrutti o callback su WebEngine già chiuso;
- [ ] settings salvati una sola volta in modo coerente;
- [ ] shutdown idempotente.

---

# CAMPAGNA B — Scraper e rete

## B1. Risposte valide

Per entrambe le sorgenti:

- [ ] payload reale normale;
- [ ] evento LOW/MID/HIGH;
- [ ] campi opzionali vuoti;
- [ ] caratteri Unicode;
- [ ] nomi evento lunghi;
- [ ] valori numerici con segno;
- [ ] timestamp con offset positivo e negativo;
- [ ] più eventi con stesso timestamp.

## B2. Payload degradati

Iniettare o riprodurre:

- [ ] lista vuota;
- [ ] JSON non-lista;
- [ ] elemento `null` nella lista;
- [ ] elemento stringa invece di object;
- [ ] record con campi obbligatori mancanti;
- [ ] timestamp invalido;
- [ ] timestamp naive;
- [ ] codice paese sconosciuto;
- [ ] livello impatto sconosciuto;
- [ ] valori estremamente lunghi;
- [ ] dati Unicode strani/control characters.

**Atteso:** record realmente malformati vengono scartati e loggati; errori di programmazione inattesi devono emergere e non essere mascherati come semplice dato sporco.

## B3. Failure di rete

- [ ] DNS failure;
- [ ] connection refused;
- [ ] timeout connect;
- [ ] timeout read;
- [ ] HTTP 429;
- [ ] HTTP 500/502/503;
- [ ] risposta HTML al posto di JSON;
- [ ] connessione interrotta a metà risposta;
- [ ] rete che cade durante refresh;
- [ ] rete che torna disponibile dopo un fallimento.

Verificare:

- [ ] retry limitati;
- [ ] nessun loop infinito;
- [ ] GUI sempre responsiva;
- [ ] vecchi dati validi preservati;
- [ ] stato sorgente coerente;
- [ ] messaggio errore conciso in UI;
- [ ] diagnostica completa nei log.

## B4. Refresh concorrenti

Eseguire 50-100 cicli automatizzati/manuali dove possibile:

- [ ] refresh ripetuto della stessa sorgente mentre è già in corso;
- [ ] `refresh_all()` seguito subito da refresh singolo;
- [ ] refresh singolo seguito da `refresh_all()`;
- [ ] una sorgente riesce mentre l'altra fallisce;
- [ ] entrambe falliscono;
- [ ] entrambe riescono con ordine di completamento invertito.

**Invariante:** ogni sorgente mantiene un solo snapshot canonico coerente; il completamento tardivo non deve sovrascrivere stato non pertinente o produrre duplicazioni.

---

# CAMPAGNA C — Cache e persistenza dati

## C1. Cache valida

- [ ] salvataggio dopo refresh riuscito;
- [ ] riavvio offline e caricamento cache;
- [ ] timestamp/origin corretti;
- [ ] eventi identici a quelli salvati;
- [ ] nessun evento inventato.

## C2. Cache corrotta

Testare file:

- [ ] JSON troncato;
- [ ] JSON sintatticamente valido ma schema errato;
- [ ] versione cache sconosciuta;
- [ ] sorgente dichiarata diversa dal file;
- [ ] timestamp invalido;
- [ ] lista eventi non valida;
- [ ] evento singolo corrotto;
- [ ] file vuoto;
- [ ] file enorme ma formalmente valido.

**Atteso:** niente crash; cache non affidabile ignorata; nessun fallback con dati fittizi.

## C3. Atomicità

Simulare dove possibile:

- [ ] errore prima del flush;
- [ ] errore durante `fsync`;
- [ ] errore su `os.replace`;
- [ ] directory non scrivibile;
- [ ] spazio disco insufficiente;
- [ ] file temporaneo già presente.

Controllare che l'ultimo snapshot valido non venga distrutto.

---

# CAMPAGNA D — Settings e stato UI persistente

## D1. Valori validi

Verificare persistenza e riavvio di:

- [ ] sorgente attiva;
- [ ] timezone;
- [ ] data selezionata;
- [ ] filtri regione/impatto;
- [ ] ordine colonne;
- [ ] ordinamento e direzione;
- [ ] intervallo auto-refresh;
- [ ] lead time notifiche;
- [ ] geometria finestra.

## D2. Valori invalidi

Provare manualmente a scrivere nel JSON settings:

- [ ] sorgente inesistente;
- [ ] timezone inesistente;
- [ ] data non ISO;
- [ ] colonne mancanti/duplicate;
- [ ] intervalli refresh fuori range;
- [ ] sort key sconosciuta;
- [ ] direzione sort invalida;
- [ ] geometria malformata;
- [ ] stringhe con control characters;
- [ ] tipi sbagliati (`null`, list, object dove attesa stringa/int).

**Atteso:** default sicuri e nessun crash.

## D3. Failure di salvataggio

- [ ] filesystem read-only;
- [ ] permission denied;
- [ ] directory rimossa durante save;
- [ ] errore atomico simulato.

Controllare che:

- [ ] il backend non consideri persistito uno stato non scritto;
- [ ] la UI non resti permanentemente divergente dal valore canonico;
- [ ] il vecchio settings file valido rimanga recuperabile.

---

# CAMPAGNA E — Date, timezone e DST

Questa è una delle aree a rischio più alto perché un errore può mostrare un evento economico nell'ora o nel giorno sbagliato.

## E1. Parsing UTC

- [ ] `Z`;
- [ ] `+00:00`;
- [ ] offset positivo;
- [ ] offset negativo;
- [ ] timestamp naive;
- [ ] timestamp invalido;
- [ ] stringa vuota;
- [ ] valori non-stringa nei boundary tolleranti.

## E2. Europe/Rome

Verificare eventi attorno ai cambi DST:

- [ ] ultima domenica di marzo, prima del cambio;
- [ ] istante del cambio CET → CEST;
- [ ] subito dopo il cambio;
- [ ] ultima domenica di ottobre, prima del cambio;
- [ ] ora ripetuta CEST → CET;
- [ ] subito dopo il cambio.

## E3. Altre zone

- [ ] America/New_York nelle settimane in cui USA ed Europa hanno DST disallineato;
- [ ] Asia/Tokyo senza DST;
- [ ] UTC;
- [ ] offset fisso positivo;
- [ ] offset fisso negativo.

## E4. Confini di giornata

- [ ] evento 23:59 UTC che diventa giorno successivo localmente;
- [ ] evento 00:01 UTC che diventa giorno precedente in America;
- [ ] Today/Tomorrow vicino a mezzanotte;
- [ ] Next 24h attraverso mezzanotte;
- [ ] Next 24h attraverso transizione DST.

**Invariante:** il timestamp UTC canonico non cambia; cambia solo la rappresentazione locale.

---

# CAMPAGNA F — Filtri, ricerca, sorting e navigazione

## F1. Filtri

Provare tutte le combinazioni ragionevoli:

- [ ] ogni regione;
- [ ] ALL;
- [ ] LOW/MID/HIGH singoli;
- [ ] più impatti;
- [ ] nessun impatto;
- [ ] data con eventi;
- [ ] data senza eventi;
- [ ] combinato + filtri.

## F2. Ricerca locale

- [ ] nome evento esatto;
- [ ] sottostringa;
- [ ] case insensitive;
- [ ] paese;
- [ ] impatto;
- [ ] valori actual/forecast/previous;
- [ ] stringhe Unicode;
- [ ] spazi iniziali/finali;
- [ ] query vuota;
- [ ] query che non produce risultati.

## F3. Sorting

Per ogni colonna ordinabile:

- [ ] ascending;
- [ ] descending;
- [ ] valori vuoti;
- [ ] valori uguali;
- [ ] eventi di sorgenti differenti;
- [ ] sort persistito dopo riavvio.

Controllare che sorting e filtri non modifichino lo stato canonico degli eventi.

---

# CAMPAGNA G — Vista combinata e duplicate matching

Costruire coppie controllate:

- [ ] stesso evento, nomi quasi identici, orari entro 15 min;
- [ ] stesso evento, nome leggermente diverso;
- [ ] nome uguale ma paese diverso;
- [ ] nome uguale ma sorgente uguale;
- [ ] eventi oltre la finestra temporale;
- [ ] nomi molto corti;
- [ ] accenti/Unicode;
- [ ] catene di tre eventi A~B, B~C;
- [ ] eventi simultanei realmente distinti.

Verificare:

- [ ] nessun falso merge distruttivo: entrambe le righe restano visibili;
- [ ] duplicate group stabile;
- [ ] stesso algoritmo usato dalle notifiche dove previsto;
- [ ] matching indipendente dall'ordine di input.

---

# CAMPAGNA H — Notifiche desktop

## H1. Timing

Per lead time 5/15/30/60 min:

- [ ] evento appena fuori finestra;
- [ ] evento esattamente sulla soglia;
- [ ] evento appena dentro finestra;
- [ ] evento già passato;
- [ ] evento HIGH futuro;
- [ ] evento MID/LOW futuro.

## H2. Deduplicazione

- [ ] stesso evento controllato più volte dal timer;
- [ ] probabile duplicato cross-source;
- [ ] riavvio applicazione;
- [ ] cambio timezone mentre l'evento è prossimo.

## H3. Backend notifiche non disponibile

- [ ] ambiente senza servizio Freedesktop Notifications;
- [ ] errore D-Bus;
- [ ] servizio che scompare a runtime.

**Atteso:** nessun crash e nessun fallback a subprocess esterni non previsti.

---

# CAMPAGNA I — Export CSV / ICS

## I1. CSV

- [ ] un evento;
- [ ] molti eventi;
- [ ] vista filtrata;
- [ ] vista combinata;
- [ ] virgole nei testi;
- [ ] virgolette;
- [ ] newline nei testi;
- [ ] Unicode;
- [ ] campi vuoti;
- [ ] ordine eventi coerente con la vista esportata.

Aprire il file con almeno due parser/applicazioni differenti se possibile.

## I2. ICS

- [ ] `DTSTART` UTC corretto;
- [ ] UID stabile;
- [ ] escaping di `,`, `;`, backslash e newline;
- [ ] line folding UTF-8;
- [ ] evento con timestamp invalido escluso senza corrompere il calendario;
- [ ] import in almeno un client calendario reale.

## I3. Boundary di sicurezza

Tentare dal frontend di alterare:

- [ ] nome evento;
- [ ] paese;
- [ ] sorgente;
- [ ] impact;
- [ ] valori economici;
- [ ] timestamp canonico.

**Atteso:** l'export deve risolvere l'identità contro lo stato canonico Python e non fidarsi dei dati arbitrari forniti dal DOM/JS.

## I4. Filesystem

- [ ] percorso valido;
- [ ] file esistente;
- [ ] directory read-only;
- [ ] nome Unicode;
- [ ] annullamento QFileDialog;
- [ ] errore durante scrittura atomica.

---

# CAMPAGNA J — QWebChannel e bridge

## J1. Input invalidi

Per ogni slot esposto:

- [ ] tipo corretto;
- [ ] `null`;
- [ ] stringa vuota;
- [ ] tipo errato;
- [ ] valori fuori dominio;
- [ ] array enormi dove applicabile;
- [ ] stringhe molto lunghe;
- [ ] oggetti JS inattesi.

Verificare che il bridge:

- [ ] validi/converta;
- [ ] non implementi regole di dominio duplicate;
- [ ] non esponga filesystem o comandi arbitrari;
- [ ] restituisca valori serializzabili semplici;
- [ ] non propaghi eccezioni non gestite verso WebChannel per input utente prevedibilmente invalidi.

## J2. Segnali Python → JS

- [ ] refresh started;
- [ ] refresh completed;
- [ ] refresh failed;
- [ ] log forwarding;
- [ ] cambio sorgente/stato;
- [ ] segnali durante shutdown.

Cercare doppie emissioni, emissioni tardive e handler JS registrati più volte.

---

# CAMPAGNA K — WebEngine security boundary

Provare navigazioni verso:

- [ ] file locale previsto;
- [ ] qrc Qt WebChannel previsto;
- [ ] `https://example.com`;
- [ ] `http://example.com`;
- [ ] `data:text/html,...`;
- [ ] `javascript:`;
- [ ] custom scheme;
- [ ] URL trascinato nella finestra;
- [ ] popup/window.open;

Verificare:

- [ ] contenuto HTTP(S) non caricato nel WebEngine dell'app;
- [ ] link esterni aperti solo nel browser di sistema;
- [ ] `LocalContentCanAccessRemoteUrls` disabilitato;
- [ ] unknown URL schemes rifiutati;
- [ ] navigation-on-drop disabilitata;
- [ ] DNS prefetch disabilitato;
- [ ] nessuna esecuzione di JavaScript non fidato.

---

# CAMPAGNA L — UI, layout e accessibilità

## L1. Dimensioni finestra

Testare almeno:

- [ ] 1920×1080;
- [ ] 1366×768;
- [ ] 1280×720;
- [ ] altezza appena sopra 900 px;
- [ ] altezza appena sotto 900 px;
- [ ] altezza appena sopra 720 px;
- [ ] altezza appena sotto 720 px;
- [ ] dimensione minima consentita;
- [ ] monitor HiDPI / scaling 125%, 150%, 200% se disponibile.

Controllare overflow, clipping, scroll annidati, footer irraggiungibile e controlli sovrapposti.

## L2. Tastiera

Senza mouse:

- [ ] attraversare tutti i controlli con Tab/Shift+Tab;
- [ ] attivare pulsanti con tastiera;
- [ ] usare filtri;
- [ ] cambiare sorgente;
- [ ] usare ricerca;
- [ ] cambiare quick range;
- [ ] avviare export;
- [ ] verificare focus sempre visibile.

**Nota di bug hunting:** il riordino colonne tramite drag-and-drop è un'area già identificata da verificare esplicitamente per accessibilità da tastiera.

## L3. Semantica e feedback

- [ ] `aria-live` per messaggi dinamici importanti;
- [ ] `aria-pressed` coerente;
- [ ] label associate ai controlli;
- [ ] tabella semanticamente corretta;
- [ ] contrasto leggibile;
- [ ] stato selezionato distinguibile senza affidarsi solo al colore;
- [ ] `prefers-reduced-motion` rispettato.

---

# CAMPAGNA M — Stress e soak test

## M1. Refresh prolungato

Lasciare l'app aperta per 4-8 ore con auto-refresh attivo.

Ogni 30-60 minuti controllare:

- [ ] memoria RSS;
- [ ] numero thread;
- [ ] responsività UI;
- [ ] log duplicati;
- [ ] timer duplicati;
- [ ] crescita non limitata dello stato notifiche;
- [ ] crescita anomala della cache/debug data;
- [ ] correttezza degli eventi dopo molti refresh.

## M2. Interazione rapida

Durante refresh:

- [ ] cambiare sorgente rapidamente 20-50 volte;
- [ ] cambiare filtri;
- [ ] cambiare timezone;
- [ ] cambiare sorting;
- [ ] usare ricerca;
- [ ] aprire/chiudere dialog export;
- [ ] ridimensionare continuamente la finestra.

Cercare freeze, race, dati provenienti dalla sorgente sbagliata o DOM non sincronizzato.

## M3. Dataset grande

Con fixture sintetiche solo nei test, non nella produzione:

- [ ] 1.000 eventi;
- [ ] 5.000 eventi;
- [ ] 20.000 eventi al boundary export;
- [ ] molti duplicati probabili;
- [ ] molte stringhe lunghe.

Misurare tempi di:

- filtering;
- sorting;
- matching;
- serializzazione bridge;
- rendering;
- export.

Segnalare qualsiasi operazione che blocchi sensibilmente il GUI thread.

---

# CAMPAGNA N — Fault injection mirata

Usare monkeypatch nei test per forzare failure difficili da riprodurre manualmente.

Target raccomandati:

- [ ] `requests.Session.get`;
- [ ] parser timestamp;
- [ ] `Path.mkdir`;
- [ ] `Path.write_text`/file open;
- [ ] `os.replace`;
- [ ] `os.fsync`;
- [ ] notifier D-Bus;
- [ ] QFileDialog/native export action;
- [ ] callback future del controller;
- [ ] settings save;
- [ ] cache save/load.

Per ogni fault verificare tre proprietà:

1. l'errore è osservabile nei log;
2. lo stato precedente valido resta valido;
3. l'applicazione può continuare o chiudersi deterministicamente.

---

# CAMPAGNA O — Caccia alle inconsistenze architetturali

Durante il bug hunting non limitarsi al sintomo. Per ogni difetto chiedere:

- [ ] esistono due fonti di verità per lo stesso stato?
- [ ] una regola di dominio è duplicata tra Python e JavaScript?
- [ ] il bridge sta prendendo decisioni che spettano al core?
- [ ] una callback dipende implicitamente dall'ordine temporale?
- [ ] una modifica richiede toccare troppi moduli per una responsabilità semplice?
- [ ] un `except` troppo ampio sta nascondendo bug?
- [ ] una failure viene convertita in successo apparente?
- [ ] un test verifica dettagli d'implementazione invece di un comportamento?
- [ ] la correzione proposta aggiunge un caso speciale invece di rimuovere la causa?

Se la risposta indica un problema strutturale, correggere il design prima di aggiungere workaround.

---

# CAMPAGNA P — Revisione dei log

Eseguire almeno una sessione completa con logging DEBUG.

Cercare:

- [ ] traceback inattesi;
- [ ] warning ripetuti;
- [ ] retry non limitati;
- [ ] errori salvati solo in UI ma non nei log;
- [ ] errori salvati solo nei log senza feedback UI quando necessario;
- [ ] dati sensibili/non necessari nei log;
- [ ] refresh completati senza metriche coerenti;
- [ ] sorgenti indicate con nome errato;
- [ ] timestamp naive;
- [ ] callback dopo shutdown.

---

# CAMPAGNA Q — Regression test dopo ogni bug trovato

Per ogni bug confermato:

1. creare prima un test che lo riproduca quando possibile;
2. verificare che il test fallisca sulla versione difettosa;
3. correggere la causa nel layer appropriato;
4. verificare che il nuovo test passi;
5. eseguire la suite completa;
6. cercare duplicazioni o complessità introdotte dalla fix;
7. aggiornare questo documento se il bug rivela una nuova classe di rischio.

Una fix non è completa se corregge soltanto il caso manuale senza protezione automatica ragionevole.

---

# Exit criteria della campagna

La campagna può essere considerata conclusa quando:

- [ ] compileall è verde;
- [ ] Ruff è verde;
- [ ] syntax check JavaScript è verde;
- [ ] pytest è interamente verde;
- [ ] nessun S0/S1 resta aperto;
- [ ] ogni S2 rimasto ha un defer esplicito e giustificato;
- [ ] startup online e offline sono verificati;
- [ ] refresh di entrambe le sorgenti è verificato;
- [ ] partial-source failure è verificata;
- [ ] cache corrotta è verificata;
- [ ] settings corrotti sono verificati;
- [ ] DST e confini di giornata sono verificati;
- [ ] export CSV e ICS sono aperti con software reale;
- [ ] notifiche sono testate sia disponibili sia indisponibili;
- [ ] WebEngine security boundary è verificato;
- [ ] shutdown durante lavoro asincrono è verificato;
- [ ] soak test non mostra crescita anomala o freeze;
- [ ] nessun bug trovato è stato chiuso con workaround tattico non documentato;
- [ ] viene svolto un ultimo strategic review dell'intero progetto.

---

# Report finale consigliato

Alla fine produrre una tabella di sintesi:

| ID | Area | Severità | Riproducibile | Test automatico | Stato | Root cause | Fix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BH-001 | esempio | S2 | sì | sì | corretto | ... | ... |

Aggiungere poi:

- totale scenari eseguiti;
- totale bug trovati per severità;
- bug corretti;
- bug deferiti con motivazione;
- nuovi test aggiunti;
- test rimossi o razionalizzati;
- eventuali aree non verificabili nell'ambiente usato;
- risultato finale di CI;
- strategic review conclusivo.

Il risultato desiderato non è “nessun bug trovato”, ma evidenza credibile che le aree a rischio sono state attaccate intenzionalmente, che i fault importanti degradano in modo controllato e che ogni correzione mantiene semplice l'architettura.
