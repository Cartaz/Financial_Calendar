from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


def test_frontend_uses_required_design_tokens_without_surface_gradients() -> None:
    css = (UI / "styles.css").read_text(encoding="utf-8")

    assert "--surface: rgb(20, 20, 20);" in css
    assert "--accent: rgb(255, 102, 0);" in css
    assert "--shadow-raised:" in css
    assert "--shadow-inset:" in css
    assert "--shadow-active-inset-glow:" in css
    assert "background: var(--surface);" in css
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css


def test_frontend_is_semantic_and_wired_to_qwebchannel() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    javascript = (UI / "app.js").read_text(encoding="utf-8")

    assert '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>' in html
    assert "<header" in html
    assert "<nav" in html
    assert "<main" in html
    assert "<table" in html
    assert "<label" in html
    assert "<button" in html
    assert "new QWebChannel(qt.webChannelTransport" in javascript
    assert "refreshSource" in javascript
    assert "saveFilters" in javascript
    assert "saveColumnOrder" in javascript
    assert "React" not in javascript
    assert "Vue" not in javascript


def test_frontend_uses_iana_timezone_and_exposes_cached_state() -> None:
    javascript = (UI / "app.js").read_text(encoding="utf-8")
    bridge = (UI / "bridge.py").read_text(encoding="utf-8")

    assert "resolvedOptions().timeZone" in javascript
    assert '"getEventsInTimezone"' in javascript
    assert "Europe/Rome" in javascript
    assert "Dati salvati" in javascript
    assert "Dati aggiornati" in javascript
    assert "Errore · nessun dato" in javascript
    assert "def getEventsInTimezone" in bridge
    assert '"data_origin"' in bridge
    assert '"last_refresh_iso"' in bridge


def test_runtime_owns_timers_and_window_geometry_remains_native() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    javascript = (UI / "app.js").read_text(encoding="utf-8")
    bridge = (UI / "bridge.py").read_text(encoding="utf-8")
    runtime = (UI / "runtime.py").read_text(encoding="utf-8")
    window = (UI / "window.py").read_text(encoding="utf-8")
    ux_css = (UI / "ux.css").read_text(encoding="utf-8")

    assert 'id="auto-refresh"' in html
    assert 'id="freshness-label"' in html
    assert 'class="source-freshness"' in html
    assert 'href="ux.css"' in html
    assert '"saveUiState"' in javascript
    assert '"saveSort"' in javascript
    assert "sourceFreshnessSummary" in javascript
    assert "startFreshnessClock" in javascript
    assert "auto_refresh_options" in bridge
    assert "QTimer" not in bridge
    assert "QTimer" in runtime
    assert "auto_refresh_timer" in runtime
    assert "notification_timer" in runtime
    assert "saveGeometry" in window
    assert "restoreGeometry" in window
    assert "window_geometry" in window
    assert ".auto-refresh-field" in ux_css
    assert ".source-status.is-stale" in ux_css


def test_frontend_has_accessibility_and_reduced_motion_guards() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    css = (UI / "styles.css").read_text(encoding="utf-8")

    assert "aria-live" in html
    assert "aria-pressed" in html
    assert ":focus-visible" in css
    assert "prefers-reduced-motion: reduce" in css


def test_frontend_is_constrained_to_window_and_table_owns_scrolling() -> None:
    css = (UI / "viewport.css").read_text(encoding="utf-8")
    window = (UI / "window.py").read_text(encoding="utf-8")

    assert "_install_viewport_styles" in window
    assert 'ui_dir / "viewport.css"' in window
    assert "height: 100vh;" in css
    assert "max-height: 100vh;" in css
    assert "overflow: hidden;" in css
    assert ".table-shell {" in css
    assert "flex: 1 1 0;" in css
    assert ".table-scroll {" in css
    assert "max-height: none;" in css
    assert "overflow: auto;" in css


def test_windowed_layout_compacts_before_table_space_is_exhausted() -> None:
    css = (UI / "viewport.css").read_text(encoding="utf-8")

    assert "@media (max-height: 900px)" in css
    assert "@media (max-height: 720px)" in css
    assert ".source-tab small:not(.source-freshness)" in css
    assert "min-height: 44px;" in css
    assert "height: 36px;" in css
    assert "height: 38px;" in css
    assert ".app-description," in css
    assert ".panel-description" in css


def test_redundant_header_copy_is_hidden_without_breaking_js_hooks() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    css = (UI / "viewport.css").read_text(encoding="utf-8")

    assert 'id="app-name"' in html
    assert 'id="app-description"' in html
    assert 'id="connection-state"' in html
    assert 'id="refresh-all"' in html
    assert 'id="source-title"' in html
    assert 'id="source-description"' in html
    assert (
        ".topbar h1,\n.app-description,\n.topbar-actions {\n  display: none !important;"
        in css
    )
    assert (
        ".panel-heading h2,\n.panel-description {\n  display: none !important;"
        in css
    )
    assert ".topbar .eyebrow" in css
    assert ".panel-heading .eyebrow" in css


def test_system_tray_integration_is_removed() -> None:
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    window = (UI / "window.py").read_text(encoding="utf-8")
    bridge = (UI / "bridge.py").read_text(encoding="utf-8")

    assert not (UI / "tray.py").exists()
    assert "TrayIconManager" not in main
    assert "tray_available" not in window
    assert "tray_available" not in bridge
    assert "def closeEvent" in window
    assert "app.quit()" in window


def test_repository_layout_and_installer_are_minimal() -> None:
    visible_dirs = {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "__pycache__"
    }
    installer = (ROOT / "install.sh").read_text(encoding="utf-8")

    assert visible_dirs == {"assets", "config", "core", "tests", "ui"}
    assert not (ROOT / "web").exists()
    assert not (ROOT / "web_ui").exists()
    assert not (ROOT / "pyproject.toml").exists()
    assert not (ROOT / "requirements-dev.txt").exists()
    assert 'VENV_DIR="${SCRIPT_DIR}/.venv"' in installer
    assert 'pip install -r "${SCRIPT_DIR}/requirements.txt"' in installer
    assert 'echo "Avvio: .venv/bin/python main.py"' in installer
    assert "WRAPPER_SCRIPT" not in installer
    assert ".desktop" not in installer
