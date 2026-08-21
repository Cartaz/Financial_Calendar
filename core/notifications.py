"""Linux desktop notifications through the standard Freedesktop D-Bus API."""

from __future__ import annotations

import logging
import sys

from config.constants import AppMeta

logger = logging.getLogger(__name__)


class DesktopNotifier:
    """Best-effort KDE/Linux notifier without introducing tray semantics."""

    def notify(self, title: str, body: str, *, timeout_ms: int = 7000) -> bool:
        if not sys.platform.startswith("linux"):
            logger.debug("Notifiche desktop non supportate su questa piattaforma")
            return False

        try:
            from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage
        except ImportError:
            logger.warning("QtDBus non disponibile: notifica desktop ignorata")
            return False

        bus = QDBusConnection.sessionBus()
        if not bus.isConnected():
            logger.warning("Session bus D-Bus non disponibile: notifica ignorata")
            return False

        interface = QDBusInterface(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            bus,
        )
        if not interface.isValid():
            logger.warning("Servizio org.freedesktop.Notifications non disponibile")
            return False

        reply = interface.call(
            "Notify",
            AppMeta.DISPLAY_NAME,
            0,
            AppMeta.ICON_NAME,
            str(title),
            str(body),
            [],
            {},
            int(timeout_ms),
        )
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            logger.warning("Notifica desktop fallita: %s", reply.errorMessage())
            return False
        return True
