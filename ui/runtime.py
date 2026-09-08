"""Qt runtime coordination kept separate from the QML presentation."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer

from config.settings import Settings
from core.app_controller import AppController
from core.models import CalendarSource
from core.notification_policy import NotificationPolicy
from ui.desktop_notifications import DesktopNotifier

logger = logging.getLogger(__name__)


class CalendarRuntime(QObject):
    """Own Qt timers and native notification integration for the application."""

    def __init__(
        self,
        controller: AppController,
        settings: Settings,
        *,
        notifier: DesktopNotifier | None = None,
        queue=None,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._settings = settings
        self._notifier = notifier or DesktopNotifier()
        self._notification_policy = NotificationPolicy()
        self._started = False
        self._queue = queue
        self._checking = False

        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.setSingleShot(False)
        self.auto_refresh_timer.timeout.connect(self._controller.refresh_all)

        self.notification_timer = QTimer(self)
        self.notification_timer.setSingleShot(False)
        self.notification_timer.setInterval(30_000)
        self.notification_timer.timeout.connect(self.check_notifications)

    @property
    def started(self) -> bool:
        return self._started

    def configure_auto_refresh(self) -> None:
        minutes = int(self._settings.get("auto_refresh_minutes"))
        if (
            self._started
            and self.auto_refresh_timer.isActive()
            and self.auto_refresh_timer.interval() == minutes * 60000
        ):
            return
        self.auto_refresh_timer.stop()
        if not self._started or minutes <= 0:
            return
        self.auto_refresh_timer.start(minutes * 60 * 1000)
        logger.info("Auto-refresh configurato ogni %d minuti", minutes)

    def configure_notifications(self) -> None:
        minutes = int(self._settings.get("high_notification_minutes"))
        if self._started and minutes > 0 and self.notification_timer.isActive():
            return
        self.notification_timer.stop()
        if not self._started or minutes <= 0:
            return
        self.notification_timer.start()
        logger.info("Notifiche HIGH configurate con anticipo di %d minuti", minutes)

    def check_notifications(self) -> None:
        if not self._started:
            return
        lead_minutes = int(self._settings.get("high_notification_minutes"))
        if lead_minutes <= 0:
            return

        if self._checking:
            return
        self._checking = True

        def work():
            events = []
            for source in (CalendarSource.FOREXFACTORY, CalendarSource.FXSTREET):
                events.extend(
                    self._controller.filter_events(
                        source, region="ALL", impact="HIGH", timezone_name="UTC"
                    )
                )
            for event, event_dt, remaining in self._notification_policy.due_events(
                events, lead_minutes, commit=False
            ):
                if not self._started:
                    break
                title = f"Evento HIGH tra {remaining} min"
                body = f"{event.country} · {event.event_name} · {event_dt.astimezone().strftime('%H:%M')}"
                if self._notifier.notify(title, body):
                    self._notification_policy.mark_delivered(event)

        def done(value, error):
            self._checking = False

        if self._queue is not None:
            self._queue.submit(work, done)
        else:
            # Standalone compatibility for non-window consumers; shell always queues.
            try:
                work()
            finally:
                done(None, None)

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self.configure_auto_refresh()
        self.configure_notifications()
        self._controller.refresh_all()
        self.check_notifications()

    def stop(self) -> None:
        """Idempotently stop all Qt timers owned by the runtime."""
        self._started = False
        self.auto_refresh_timer.stop()
        self.notification_timer.stop()
