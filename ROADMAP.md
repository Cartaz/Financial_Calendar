# Financial Calendar — Roadmap

Questa roadmap raccoglie gli sviluppi pianificati dopo la stabilizzazione della UI HTML dark-neumorphic.

## 1.2 — Affidabilità dei dati

- [x] Cache persistente dell'ultimo calendario valido per ogni sorgente.
- [x] Avvio offline con caricamento immediato degli ultimi dati reali disponibili.
- [x] Mantenimento dei dati precedenti quando un refresh fallisce.
- [x] Timestamp dei nuovi refresh salvati in formato ISO-8601 UTC.
- [x] Stato UI che distingue dati da rete, dati salvati e assenza di dati.
- [ ] Conversione timezone DST-safe basata su timezone IANA invece di un singolo offset numerico.
- [ ] Test di regressione sui cambi ora legale/solare.

Criterio di completamento: il programma deve essere utilizzabile anche senza rete dopo almeno un refresh riuscito e deve mostrare orari corretti attraverso transizioni DST.

## 1.3 — Aggiornamento e persistenza UX

- [ ] Auto-refresh configurabile: Manuale / 5 / 15 / 30 / 60 minuti.
- [ ] Indicatore di freschezza per sorgente.
- [ ] Persistenza della sorgente attiva.
- [ ] Persistenza della timezone scelta.
- [ ] Persistenza della data selezionata.
- [ ] Persistenza di ordinamento colonna e direzione.
- [ ] Persistenza opzionale di dimensione/posizione finestra.

Criterio di completamento: alla riapertura l'app deve ripristinare lo stato operativo precedente e aggiornarsi senza intervento manuale quando richiesto.

## 1.4 — Navigazione del calendario

- [ ] Ricerca testuale locale degli eventi.
- [ ] Filtri rapidi Oggi / Domani / Prossime 24h.
- [ ] Countdown per eventi futuri.
- [ ] Evidenziazione discreta del prossimo evento importante.
- [ ] Attenuazione visuale degli eventi già trascorsi.

Criterio di completamento: trovare e contestualizzare un evento imminente deve richiedere pochi secondi anche con molti eventi in tabella.

## 1.5 — Funzioni operative

- [ ] Notifiche desktop opzionali prima degli eventi HIGH.
- [ ] Intervallo di anticipo notifiche configurabile.
- [ ] Vista combinata ForexFactory + FXStreet.
- [ ] Identificazione non distruttiva dei probabili duplicati tra sorgenti.
- [ ] Export CSV degli eventi filtrati.
- [ ] Export ICS degli eventi selezionati/filtrati.

Criterio di completamento: il calendario deve poter diventare uno strumento operativo senza perdere la semplicità dell'interfaccia corrente.

## Hardening continuo

- [ ] Fixture reali anonimizzate per entrambe le API.
- [ ] Soglia di warning quando cresce la percentuale di eventi scartati dal parser.
- [ ] Metriche di refresh nel log: durata, raw, validi, scartati, origine cache/rete.
- [ ] Test avvio offline.
- [ ] Test cache corrotta.
- [ ] Test una sorgente disponibile e una indisponibile.
- [ ] Test shutdown durante richieste attive.
- [ ] Test persistenza completa della UI.

## Principi da mantenere

- Nessun server HTTP locale.
- Nessun framework JavaScript aggiuntivo salvo necessità concreta.
- Nessun database se file JSON atomici restano sufficienti.
- Nessun `pyproject.toml` o sistema di packaging Python aggiuntivo.
- Installazione: `chmod +x install.sh` seguito da `./install.sh`.
- Avvio: `.venv/bin/python main.py`.
- Nuove funzioni sempre accompagnate da test e senza dati di fallback inventati.
