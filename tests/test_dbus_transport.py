"""Real session-bus integration. CI runs under dbus-run-session."""

import json
import os
from pathlib import Path
import sys
import pytest
from PySide6.QtCore import QCoreApplication, QProcess
from PySide6.QtDBus import QDBusConnection, QDBusVirtualObject
from PySide6.QtTest import QTest


def test_notify_has_freedesktop_signature_and_delivery_reply():
    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        pytest.skip("Requires a private D-Bus session; CI runs dbus-run-session")
    app = QCoreApplication.instance()
    if app is None:
        from PySide6.QtWidgets import QApplication

        app = QApplication([])
    received = []

    class Receiver(QDBusVirtualObject):
        def introspect(self, path):
            return '<interface name="org.freedesktop.Notifications"><method name="Notify"><arg type="s" direction="in"/><arg type="u" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="as" direction="in"/><arg type="a{sv}" direction="in"/><arg type="i" direction="in"/><arg type="u" direction="out"/></method></interface>'

        def handleMessage(self, message, connection):
            if message.member() == "Notify":
                received.append((message.signature(), message.arguments()))
                connection.send(message.createReply([1]))
                return True
            return False

    bus = QDBusConnection.sessionBus()
    receiver = Receiver()
    assert bus.registerService("org.freedesktop.Notifications")
    assert bus.registerVirtualObject("/org/freedesktop/Notifications", receiver)
    process = QProcess()
    process.setProgram(sys.executable)
    process.setArguments(
        [str(Path(__file__).parents[1] / "ui" / "notification_transport.py")]
    )
    try:
        process.start()
        process.write(json.dumps(["Calendar", "icon", "Test", "Body", 7000]).encode())
        process.closeWriteChannel()
        for _ in range(600):
            app.processEvents()
            if process.state() == QProcess.NotRunning:
                break
            QTest.qWait(10)
        assert process.state() == QProcess.NotRunning
        assert received and received[0][0] == "susssasa{sv}i"
        assert received[0][1][3:5] == ["Test", "Body"]
        assert process.exitCode() == 0, bytes(process.readAllStandardError()).decode()
    finally:
        if process.state() != QProcess.NotRunning:
            process.kill()
            process.waitForFinished(1000)
        bus.unregisterObject("/org/freedesktop/Notifications")
        bus.unregisterService("org.freedesktop.Notifications")
