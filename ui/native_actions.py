"""Native desktop actions used by the WebChannel transport layer."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Mapping

from PySide6.QtWidgets import QApplication, QFileDialog

from core.exporters import write_export

logger = logging.getLogger(__name__)


class NativeActions:
    """Keep file dialogs and other desktop integration outside the bridge."""

    def export_events(
        self,
        export_format: str,
        events: list[Mapping[str, object]],
    ) -> dict[str, object]:
        export_format = export_format.lower().strip()
        if export_format not in {"csv", "ics"}:
            return {"ok": False, "error": "Formato export non supportato"}

        extension = f".{export_format}"
        default_name = (
            f"financial-calendar-{datetime.now().strftime('%Y%m%d-%H%M')}{extension}"
        )
        file_filter = (
            "CSV (*.csv)" if export_format == "csv" else "Calendario iCalendar (*.ics)"
        )
        parent = QApplication.activeWindow()
        path, _ = QFileDialog.getSaveFileName(
            parent,
            "Esporta calendario",
            default_name,
            file_filter,
        )
        if not path:
            return {"ok": False, "cancelled": True}
        if not path.lower().endswith(extension):
            path += extension

        try:
            count = write_export(Path(path), export_format, events)
        except (OSError, ValueError) as exc:
            logger.error("Export %s fallito: %s", export_format, exc)
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "path": path, "count": count}
