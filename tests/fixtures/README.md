# Scraper fixtures

Queste fixture sono snapshot minimali e anonimizzati della **struttura realmente osservata** nei feed di produzione usati dall'applicazione.

- `forexfactory_api_anonymized.json`: forma del feed pubblico Faireconomy/ForexFactory `ff_calendar_thisweek.json`, campionata da un payload di agosto 2026.
- `fxstreet_api_anonymized.json`: forma dell'endpoint pubblico FXStreet `eventDates`, basata su record restituiti dall'API reale.

Per ridurre l'accoppiamento a record editoriali specifici, nomi e identificatori degli eventi sono stati sostituiti. Sono invece mantenuti campi, tipi, timezone, valori nullabili, unità e livelli di volatilità necessari a verificare il contratto di parsing.

Le fixture non sono fallback runtime e non vengono mai mostrate all'utente: esistono esclusivamente per i test di regressione.
