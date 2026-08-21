# Financial Calendar — Roadmap

Questa roadmap raccoglie gli sviluppi pianificati dopo la stabilizzazione della UI HTML dark-neumorphic.

## 1.2 — Affidabilità dei dati

- [x] Cache persistente dell'ultimo calendario valido per ogni sorgente.
- [x] Avvio offline con caricamento immediato degli ultimi dati reali disponibili.
- [x] Mantenimento dei dati precedenti quando un refresh fallisce.
- [x] Timestamp dei nuovi refresh salvati in formato ISO-8601 UTC.
- [x] Stato UI che distingue visivamente dati da rete, dati salvati e assenza di dati.
- [x] Conversione timezone DST-safe basata su timezone IANA invece di un singolo offset numerico.
- [x] Test di regressione sui cambi ora legale/solare.

Criterio di completamento: il programma deve essere utilizzabile anche senza rete dopo almeno un refresh riuscito e deve mostrare orari corretti attraverso transizioni DST.

## 1.3 — Aggiornamento e persistenza UX

- [x] Auto-refresh configurabile: Manuale / 5 / 15 / 30 / 60 minuti.
- [x] Indicatore di freschezza per sorgente.
- [x] Persistenza della sorgente attiva.
- [x] Persistenza della timezone scelta.
- [x] Persistenza della data selezionata.
- [x] Persistenza di ordinamento colonna e direzione.
- [x] Persistenza di dimensione/posizione finestra.

Criterio di completamento: alla riapertura l'app deve ripristinare lo stato operativo precedente e aggiornarsi senza intervento manuale quando richiesto.

## 1.4 — Navigazione del calendario

- [x] Ricerca testuale locale degli eventi.
- [x] Filtri rapidi Oggi / Domani / Prossime 24h.
- [x] Countdown per eventi futuri.
- [x] Evidenziazione discreta del prossimo evento importante.
- [x] Attenuazione visuale degli eventi già trascorsi.

Criterio di completamento: trovare e contestualizzare un evento imminente deve richiedere pochi secondi anche con molti eventi in tabella.

## 1.5 — Funzioni operative

- [x] Notifiche desktop opzionali prima degli eventi HIGH.
- [x] Intervallo di anticipo notifiche configurabile.
- [x] Vista combinata ForexFactory + FXStreet.
- [x] Identificazione non distruttiva dei probabili duplicati tra sorgenti.
- [x] Export CSV degli eventi filtrati.
- [x] Export ICS degli eventi selezionati/filtrati.

Criterio di completamento: il calendario deve poter diventare uno strumento operativo senza perdere la semplicità dell'interfaccia corrente.

## Hardening continuo

- [x] Fixture reali anonimizzate per entrambe le API.
- [x] Soglia di warning quando cresce la percentuale di eventi scartati dal parser.
- [x] Metriche di refresh nel log: durata, raw, validi, scartati, origine cache/rete.
- [x] Test avvio offline.
- [x] Test cache corrotta.
- [x] Test una sorgente disponibile e una indisponibile.
- [x] Test shutdown durante richieste attive.
- [x] Test persistenza completa della UI.

Criterio di completamento: i contratti dei feed devono essere coperti da fixture realistiche, le degradazioni dei parser devono emergere nei log e il fallimento di una sorgente non deve compromettere i dati validi dell'altra.

## Stato

**Roadmap completata.** Tutte le milestone e le attività di hardening pianificate in questo documento sono implementate e coperte da test automatici.

## Principi da mantenere

- Nessun server HTTP locale.
- Nessun framework JavaScript aggiuntivo salvo necessità concreta.
- Nessun database se file JSON atomici restano sufficienti.
- Nessun `pyproject.toml` o sistema di packaging Python aggiuntivo.
- Installazione: `chmod +x install.sh` seguito da `./install.sh`.
- Avvio: `.venv/bin/python main.py`.
- Nuove funzioni sempre accompagnate da test e senza dati di fallback inventati.
