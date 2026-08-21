from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


def test_navigation_controls_are_wired_without_frameworks() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    javascript = (UI / "navigation.js").read_text(encoding="utf-8")

    assert 'id="event-search"' in html
    assert 'data-quick-range="today"' in html
    assert 'data-quick-range="tomorrow"' in html
    assert 'data-quick-range="next24"' in html
    assert '<script src="navigation.js" defer></script>' in html
    assert "navigationFilteredEvents" in javascript
    assert "state.navigation.quickRange === \"next24\"" in javascript
    assert "event.event_name" in javascript
    assert "event.country" in javascript
    assert "Date.now()" in javascript
    assert "React" not in javascript
    assert "Vue" not in javascript


def test_navigation_uses_real_utc_timestamps_for_timing() -> None:
    javascript = (UI / "navigation.js").read_text(encoding="utf-8")

    assert "event.utc_dt" in javascript
    assert "eventUtcDate" in javascript
    assert "24 * 60 * 60 * 1000" in javascript
    assert "formatCountdown" in javascript
    assert "nextHighEvent" in javascript
    assert 'event.impact === "HIGH"' in javascript
    assert 'row.classList.add("is-past")' in javascript
    assert 'row.classList.add("is-next-high")' in javascript


def test_navigation_styles_preserve_dark_neumorphic_language() -> None:
    css = (UI / "navigation.css").read_text(encoding="utf-8")

    assert "var(--surface)" in css
    assert "var(--accent)" in css
    assert "var(--shadow-active-inset-glow)" in css
    assert ".event-countdown" in css
    assert "tr.is-past" in css
    assert "tr.is-next-high" in css
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css
