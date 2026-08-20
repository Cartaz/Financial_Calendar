# Financial Calendar

Desktop financial-calendar aggregator for **ForexFactory/Faireconomy** and **FXStreet**, written in Python with a **Qt Quick/QML** frontend.

The interface uses a dark neumorphic design system with an exact `#141414` application background, neutral grayscale surfaces, and `#FF6600` as the primary accent.

## Requirements

- Python 3.12+
- PySide6 6.9+
- requests 2.31+
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

## Keyboard shortcuts

- `Ctrl+R` — refresh ForexFactory while the first tab is active
- `Ctrl+F` — refresh FXStreet while the FXStreet tab is active
- `Ctrl+M` — hide the main window when a system tray is available
- `Ctrl+Q` — quit

## Features

- ForexFactory/Faireconomy and FXStreet economic calendars
- background refresh through a thread pool
- date, region and impact filters
- timezone conversion from normalized UTC timestamps
- semantic column sorting
- draggable and persisted QML table headers
- country flags
- system-tray integration
- atomically persisted XDG settings
- dark neumorphic QML design system

## Data-integrity rules

Production refreshes never substitute fabricated sample data. Network, schema, or parsing failures keep the previous real data visible and put the affected source into an error state. All accepted event timestamps must contain an explicit timezone and are normalized to UTC before filtering or display conversion.

## Project structure

```text
main.py              Application bootstrap
config/              Constants and persisted settings
core/                Models, event bus, scrapers and application controller
qml/                 Qt Quick UI and visual design system
ui_qml/              Python/QML bridge, sorting and tray integration
assets/               Icons and country flags
install.sh            Local XDG/KDE installation helper
```

## Design system

The QML theme is centralized in `qml/Theme.js`.

- background: `#141414`
- accent: `#FF6600`
- neutral surfaces: grayscale only
- raised elements: paired upper-left light / lower-right dark `RectangularShadow`
- recessed elements: compact internal falloff gradients

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

Raw API payloads are saved to the XDG debug directory only when `--debug` is enabled.

## Development

```bash
.venv/bin/pip install -r requirements-dev.txt
ruff check .
pytest -q
```

CI additionally performs Python compilation, selected QML linting, and an offscreen QML startup smoke test.
