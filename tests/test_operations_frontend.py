from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


def test_release_15_controls_and_assets_are_wired() -> None:
    html = (UI / "index.html").read_text(encoding="utf-8")
    operations = (UI / "operations.js").read_text(encoding="utf-8")
    css = (UI / "operations.css").read_text(encoding="utf-8")
    bridge = (UI / "bridge.py").read_text(encoding="utf-8")

    assert 'data-source="combined"' in html
    assert 'id="notification-lead"' in html
    assert 'id="export-csv"' in html
    assert 'id="export-ics"' in html
    assert 'href="operations.css"' in html
    assert 'src="operations.js"' in html

    assert "eventsProbablyDuplicate" in operations
    assert "buildDuplicateGroups" in operations
    assert 'bridgeCall("exportEvents"' in operations
    assert 'bridgeCall("saveNotificationLead"' in operations
    assert "duplicate_group" in operations
    assert "Possibile duplicato" in operations

    assert "grid-template-columns: repeat(3" in css
    assert ".duplicate-badge" in css
    assert ".is-probable-duplicate" in css
    assert "linear-gradient" not in css
    assert "radial-gradient" not in css

    assert "def exportEvents" in bridge
    assert "def saveNotificationLead" in bridge
    assert "DesktopNotifier" in bridge
    assert "combined_state" in bridge


def test_release_15_does_not_reintroduce_tray_or_external_notification_processes() -> None:
    notifier = (ROOT / "core" / "notifications.py").read_text(encoding="utf-8")
    bridge = (UI / "bridge.py").read_text(encoding="utf-8")

    assert "QtDBus" in notifier
    assert "org.freedesktop.Notifications" in notifier
    assert "notify-send" not in notifier
    assert "QSystemTrayIcon" not in notifier
    assert "QSystemTrayIcon" not in bridge
