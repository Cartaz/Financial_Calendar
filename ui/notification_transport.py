"""Isolated QtDBus call: typed Notify arguments and no GUI or tray."""

import json
import sys
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt, Q_ARG, Q_RETURN_ARG
from PySide6.QtDBus import QDBusConnection, QDBusInterface


def main():
    app = QCoreApplication([])
    name, icon, title, body, timeout = json.load(sys.stdin)
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        raise RuntimeError("Session bus D-Bus non disponibile")
    interface = QDBusInterface(
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications",
        "org.freedesktop.Notifications",
        bus,
    )
    if not interface.isValid():
        raise RuntimeError(interface.lastError().message())
    interface.setTimeout(3000)
    QMetaObject.invokeMethod(
        interface,
        "Notify",
        Qt.DirectConnection,
        Q_RETURN_ARG("uint"),
        Q_ARG(str, name),
        Q_ARG("uint", 0),
        Q_ARG(str, icon),
        Q_ARG(str, title),
        Q_ARG(str, body),
        Q_ARG("QStringList", []),
        Q_ARG("QVariantMap", {}),
        Q_ARG(int, timeout),
    )
    if interface.lastError().isValid():
        raise RuntimeError(interface.lastError().message())
    del app


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
