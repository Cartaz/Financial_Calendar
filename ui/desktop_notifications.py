"""Freedesktop QtDBus notifications, bounded and invoked on the worker queue."""

import json
import logging
from pathlib import Path
import subprocess
import sys
from config.constants import AppMeta

logger = logging.getLogger(__name__)


class DesktopNotifier:
    def notify(self, title: str, body: str, *, timeout_ms: int = 7000) -> bool:
        if not sys.platform.startswith("linux"):
            return False
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("notification_transport.py")),
                ],
                input=json.dumps(
                    [
                        AppMeta.DISPLAY_NAME,
                        AppMeta.ICON_NAME,
                        str(title),
                        str(body),
                        int(timeout_ms),
                    ]
                ),
                text=True,
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            logger.warning("Notifica desktop non consegnata", exc_info=True)
            return False
        if result.returncode:
            logger.warning("Notifica desktop non consegnata: %s", result.stderr.strip())
            return False
        return True
