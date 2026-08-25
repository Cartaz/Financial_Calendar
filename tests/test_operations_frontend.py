from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"
WEB = UI / "web"


def test_release_15_controls_and_assets_are_wired() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")
    operations = (WEB / "operations.js").read_text(encoding="utf-8")
    css = (WEB / "operations.css").read_text(encoding="utf-8")
    bridge = (UI / "bridge.py").read_text(encoding="utf-8")
    matching = (ROOT / "core" / "event_matching.py").read_text(encoding="utf-8")

    assert 'data-source="combined"' in html
    assert 'id="notification-lead"' in html
    assert 'id="export-csv"' in html
    assert 'id="export-ics"' in html
    assert 'href="web/operations.css"' in html
    assert 'src="web/operations.js"' in html

    assert "eventsProbablyDuplicate" not in operations
    assert "bigramDice" not in operations
    assert "duplicate_group" in operations
    assert "FinancialCalendarOperations.duplicateGroup" in app
    assert 'bridgeCall("exportEvents"' in app
    assert 'bridgeCall("saveNotificationLead"' in app
    assert "Possibile duplicato" in app

    assert "events_probably_duplicate" in matching
    assert "build_duplicate_groups" in matching

    assert "grid-template-columns: repeat(3" in css
    assert ".duplicate-badge" in css
    assert ".is-probable-duplicate" in css
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css

    assert "def exportEvents" in bridge
    assert "def saveNotificationLead" in bridge
    assert "DesktopNotifier" not in bridge
    assert "QTimer" not in bridge


def test_release_15_does_not_reintroduce_tray_or_external_notification_processes() -> None:
    notifier = (UI / "desktop_notifications.py").read_text(encoding="utf-8")
    runtime = (UI / "runtime.py").read_text(encoding="utf-8")

    assert "QtDBus" in notifier
    assert "org.freedesktop.Notifications" in notifier
    assert "notify-send" not in notifier
    assert "QSystemTrayIcon" not in notifier
    assert "from ui.desktop_notifications import DesktopNotifier" in runtime
    assert not (ROOT / "core" / "notifications.py").exists()
