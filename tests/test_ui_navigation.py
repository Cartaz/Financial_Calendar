from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "ui" / "web"


def test_navigation_controls_are_wired_without_frameworks() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    javascript = (WEB / "navigation.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")

    assert 'id="event-search"' in html
    assert 'data-quick-range="today"' in html
    assert 'data-quick-range="tomorrow"' in html
    assert 'data-quick-range="next24"' in html
    assert '<script src="web/navigation.js" defer></script>' in html
    assert "const FinancialCalendarNavigation" in javascript
    assert "function filterEvents" in javascript
    assert 'quickRange === "next24"' in javascript
    assert "event.event_name" in javascript
    assert "event.country" in javascript
    assert "FinancialCalendarNavigation.filterEvents" in app
    assert "React" not in javascript
    assert "Vue" not in javascript


def test_navigation_uses_real_utc_timestamps_for_timing() -> None:
    javascript = (WEB / "navigation.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")

    assert "event.utc_dt" in javascript
    assert "eventUtcDate" in javascript
    assert "24 * 60 * 60 * 1000" in javascript
    assert "formatCountdown" in javascript
    assert "nextHighEvent" in javascript
    assert 'event.impact === "HIGH"' in javascript
    assert 'row.classList.add("is-past")' in app
    assert 'row.classList.add("is-next-high")' in app


def test_frontend_extensions_do_not_monkey_patch_base_functions() -> None:
    navigation = (WEB / "navigation.js").read_text(encoding="utf-8")
    operations = (WEB / "operations.js").read_text(encoding="utf-8")

    forbidden = [
        "sortedEvents = function",
        "makeCell = function",
        "renderBody = function",
        "bindControls = function",
        "bootstrap = async function",
    ]
    for pattern in forbidden:
        assert pattern not in navigation
        assert pattern not in operations


def test_navigation_styles_preserve_dark_neumorphic_language() -> None:
    css = (WEB / "navigation.css").read_text(encoding="utf-8")

    assert "var(--surface)" in css
    assert "var(--accent)" in css
    assert "var(--shadow-active-inset-glow)" in css
    assert ".event-countdown" in css
    assert "tr.is-past" in css
    assert "tr.is-next-high" in css
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css
