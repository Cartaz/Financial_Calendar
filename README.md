# Financial Calendar

Desktop financial-calendar aggregator for **IG** and **FXStreet**, written in Python with a **Qt Quick/QML** frontend.

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

- `Ctrl+R` — refresh IG while the IG tab is active
- `Ctrl+F` — refresh FXStreet while the FXStreet tab is active
- `Ctrl+M` — hide the main window
- `Ctrl+Q` — quit

## Features

- IG and FXStreet economic calendars
- background refresh through a thread pool
- date, region and impact filters
- timezone conversion
- semantic column sorting
- draggable QML table headers
- country flags
- system-tray integration
- XDG-compatible persisted settings
- dark neumorphic QML design system

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

The previous Qt Widgets/QSS presentation layer has been removed. There is now one frontend implementation: QML.

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

## Development notes

The business layer does not import the frontend. `AppController` communicates with `ui_qml.bridge.CalendarBridge` through notification callbacks marshalled into the Qt event loop.

When changing QML, keep the application geometry and workflow stable unless a functional change explicitly requires otherwise.
