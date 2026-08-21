from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_uses_required_design_tokens_without_surface_gradients() -> None:
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

    assert "--surface: rgb(20, 20, 20);" in css
    assert "--accent: rgb(255, 102, 0);" in css
    assert "--shadow-raised:" in css
    assert "--shadow-inset:" in css
    assert "--shadow-active-inset-glow:" in css
    assert "background: var(--surface);" in css
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css


def test_frontend_is_semantic_and_wired_to_qwebchannel() -> None:
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "web" / "app.js").read_text(encoding="utf-8")

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


def test_frontend_has_accessibility_and_reduced_motion_guards() -> None:
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")

    assert "aria-live" in html
    assert "aria-pressed" in html
    assert ":focus-visible" in css
    assert "prefers-reduced-motion: reduce" in css



def test_frontend_is_constrained_to_window_and_table_owns_scrolling() -> None:
    css = (ROOT / "web" / "viewport.css").read_text(encoding="utf-8")
    window = (ROOT / "web_ui" / "window.py").read_text(encoding="utf-8")

    assert "_install_viewport_styles" in window
    assert 'web_dir / "viewport.css"' in window
    assert "height: 100vh;" in css
    assert "max-height: 100vh;" in css
    assert "overflow: hidden;" in css
    assert ".table-shell {" in css
    assert "flex: 1 1 0;" in css
    assert ".table-scroll {" in css
    assert "max-height: none;" in css
    assert "overflow: auto;" in css


def test_system_tray_integration_is_removed() -> None:
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    window = (ROOT / "web_ui" / "window.py").read_text(encoding="utf-8")
    bridge = (ROOT / "web_ui" / "bridge.py").read_text(encoding="utf-8")

    assert not (ROOT / "web_ui" / "tray.py").exists()
    assert "TrayIconManager" not in main
    assert "tray_available" not in window
    assert "tray_available" not in bridge
    assert "def closeEvent" in window
    assert "app.quit()" in window
