# Risorse statiche dell'applicazione

Questa directory contiene le risorse statiche dell'applicazione
Calendario Finanziario. I percorsi sono calcolati dinamicamente
tramite `pathlib.Path` e non sono mai hardcoded nel codice.

- `icons/` — Icona dell'applicazione (PNG 256x256)
- `flags/` — Bandiere nazionali SVG (formato ISO 3166-1 alpha-2 lowercase,
  es. `us.svg`, `eu.svg`). Scaricate da [flagcdn.com](https://flagcdn.com)
  tramite `scripts/download_flags.py`. Sono vettoriali, pesano ~1-3 KB
  ciascuna e scalano perfettamente a qualsiasi dimensione. La mappa
  regione → ISO2 è in `config/constants.py::CalendarDefaults.FLAG_CODES`.
- `sounds/` — Suoni di notifica (riservato futuro)
- `images/` — Immagini statiche (riservato futuro)

