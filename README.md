# Financial Calendar

Desktop financial-calendar aggregator for **ForexFactory/Faireconomy** and **FXStreet**, written in Python with a native **HTML, CSS and JavaScript** frontend hosted by Qt WebEngine.

The interface follows a dark monochrome neumorphic design system with an exact `#141414` surface and `#FF6600` as the only primary accent.

## Requirements

- Python 3.12+
- PySide6 6.9+ (including Qt WebEngine and Qt WebChannel)
- requests 2.32+
- Linux desktop environment; KDE Plasma is the primary target

## Quick start

```bash
git clone https://github.com/Cartaz/Financial_Calendar.git
cd Financial_Calendar
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

For a local desktop/menu installation on Arch/CachyOS:

```bash
./install.sh
```

## Architecture

```text
Python business logic
    ↓
AppController / Settings / scrapers
    ↓
QWebChannel bridge
    ↓
Qt WebEngine
    ↓
HTML + CSS + JavaScript
```

No local HTTP server, external browser or JavaScript framework is required. The frontend is loaded from local application files; Python remains responsible for network access, persistence, filtering and background work.

## Features

- ForexFactory/Faireconomy and FXStreet economic calendars
- background refresh through the existing thread pool
- independent date, region and impact filters
- local/UTC/fixed-offset timezone conversion
- sortable event table
- draggable and persisted column order per source
- country flags
- source-specific refresh plus refresh-all
- readable backend error state while retaining previous real data
- collapsible application log viewer
- system-tray integration when supported by the desktop environment
- atomically persisted XDG settings
- responsive dark-neumorphic HTML interface
- visible keyboard focus and reduced-motion support

## Keyboard shortcuts

- `Ctrl+R` — refresh ForexFactory
- `Ctrl+F` — refresh FXStreet
- `Ctrl+M` — hide the main window when a system tray is available
- `Ctrl+Q` — quit

## Data-integrity rules

Production refreshes never substitute fabricated sample data. Network, schema, or parsing failures keep the previous real data visible and put the affected source into an error state. Accepted event timestamps must contain an explicit timezone and are normalized to UTC before filtering or display conversion.

## Project structure

```text
main.py              Application bootstrap
config/              Constants and persisted settings
core/                Models, event bus, scrapers and application controller
web_ui/              Qt WebEngine window, QWebChannel bridge and tray
web/                  HTML, CSS and JavaScript frontend
assets/               Icons and country flags
install.sh            Local XDG/KDE installation helper
tests/                Backend, bridge, frontend and WebEngine smoke tests
```

## Design system

The frontend tokens are centralized in `web/styles.css`.

- all visible surfaces: `rgb(20, 20, 20)` / `#141414`
- accent: `rgb(255, 102, 0)` / `#FF6600`
- neutral text/details: grayscale only
- raised elements: paired lower-right dark and upper-left soft-light shadows
- recessed elements: paired inset shadows
- selected elements: orange content, thin orange border and restrained glow
- no surface gradients, glassmorphism or alternate card background colors

## Configuration

Settings are stored under the XDG config directory, normally:

```text
~/.config/financial_calendar/settings.json
```

Runtime data directories are created under the corresponding XDG paths.

## Debug logging

```bash
.venv/bin/python main.py --debug
```

Raw API payloads are saved to the XDG debug directory only when `--debug` is enabled. Recent application log records are also available in the collapsible **Attività** section of the UI.

## Development

```bash
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m compileall -q main.py config core web_ui tests
.venv/bin/ruff check main.py config core web_ui tests
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --no-sandbox" \
  .venv/bin/pytest -q
```

CI runs the same Python compilation, linting and test suite on Python 3.12 and 3.14, including an offscreen Qt WebEngine startup smoke test.
