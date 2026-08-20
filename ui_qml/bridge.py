"""Bridge between the Python controller and the Qt Quick/QML frontend."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    Property,
    QUrl,
    Qt,
    Signal,
    Slot,
)

from config.constants import CalendarDefaults, PathConfig
from core.app_controller import AppController
from core.models import CalendarEvent, CalendarSource, ImpactLevel
from ui_qml.sorting import compute_sort_key


TIMEZONE_OFFSETS: list[tuple[str, float]] = [
    ("UTC-12:00", -12.0), ("UTC-11:00", -11.0), ("UTC-10:00", -10.0),
    ("UTC-09:00", -9.0), ("UTC-08:00 (PST)", -8.0),
    ("UTC-07:00 (MST)", -7.0), ("UTC-06:00 (CST)", -6.0),
    ("UTC-05:00 (EST)", -5.0), ("UTC-04:00", -4.0),
    ("UTC-03:00 (BRT)", -3.0), ("UTC-02:00", -2.0),
    ("UTC-01:00", -1.0), ("UTC+00:00 (GMT)", 0.0),
    ("UTC+01:00 (CET)", 1.0), ("UTC+02:00 (CEST)", 2.0),
    ("UTC+03:00 (MSK)", 3.0), ("UTC+03:30 (IRST)", 3.5),
    ("UTC+04:00 (GST)", 4.0), ("UTC+05:00 (PKT)", 5.0),
    ("UTC+05:30 (IST)", 5.5), ("UTC+06:00 (BST)", 6.0),
    ("UTC+07:00 (ICT)", 7.0), ("UTC+08:00 (CST/SGT)", 8.0),
    ("UTC+09:00 (JST/KST)", 9.0), ("UTC+09:30 (ACST)", 9.5),
    ("UTC+10:00 (AEST)", 10.0), ("UTC+11:00", 11.0),
    ("UTC+12:00 (NZST)", 12.0), ("UTC+13:00", 13.0),
    ("UTC+14:00", 14.0),
]

_COLUMN_WIDTHS = {
    "ig": [100, 66, 82, 108, 300, 90, 104, 104],
    "fxstreet": [100, 66, 82, 290, 92, 90, 82, 104, 104],
}


def nearest_timezone_index(offset_hours: float) -> int:
    return min(
        range(len(TIMEZONE_OFFSETS)),
        key=lambda idx: abs(TIMEZONE_OFFSETS[idx][1] - offset_hours),
    )


def local_utc_offset_hours(moment: datetime | None = None) -> float:
    current = moment if moment is not None else datetime.now().astimezone()
    if current.tzinfo is None:
        current = current.astimezone()
    offset = current.utcoffset()
    return 0.0 if offset is None else offset.total_seconds() / 3600.0


class CalendarTableModel(QAbstractTableModel):
    """Read-only calendar model consumed by QML TableView."""

    ForegroundRole = int(Qt.ItemDataRole.UserRole) + 1
    FlagRole = ForegroundRole + 1

    sortChanged = Signal()

    def __init__(self, source: CalendarSource, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._source = source
        self._events: list[CalendarEvent] = []
        self._sort_column = -1
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._headers = (
            CalendarDefaults.IG_COLUMNS
            if source in (CalendarSource.IG, CalendarSource.FOREXFACTORY)
            else CalendarDefaults.FXSTREET_COLUMNS
        )

    def roleNames(self) -> dict[int, bytes]:
        return {
            int(Qt.ItemDataRole.DisplayRole): b"display",
            self.ForegroundRole: b"foreground",
            self.FlagRole: b"flagUrl",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._events)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._headers)

    def _row_for(self, event: CalendarEvent) -> list[str]:
        if self._source in (CalendarSource.IG, CalendarSource.FOREXFACTORY):
            return event.to_forexfactory_row()
        return event.to_fxstreet_row()

    def data(
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._events)):
            return None

        event = self._events[index.row()]
        row = self._row_for(event)
        if not (0 <= index.column() < len(row)):
            return None

        if role == int(Qt.ItemDataRole.DisplayRole):
            return row[index.column()]

        impact_col = (
            3
            if self._source in (CalendarSource.IG, CalendarSource.FOREXFACTORY)
            else 4
        )
        if role == self.ForegroundRole:
            if index.column() != impact_col:
                return "#E6E6E6"
            return {
                ImpactLevel.HIGH: "#FF6A66",
                ImpactLevel.MID: "#FFB000",
                ImpactLevel.LOW: "#858585",
            }.get(event.impact, "#858585")

        if role == self.FlagRole and index.column() == 2:
            iso2 = CalendarDefaults.FLAG_CODES.get(event.country)
            if iso2:
                path = PathConfig.FLAGS_DIR / f"{iso2}.svg"
                if path.exists():
                    return QUrl.fromLocalFile(str(path)).toString()
            return ""

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if role != int(Qt.ItemDataRole.DisplayRole):
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section] if 0 <= section < len(self._headers) else None
        return section + 1

    @Property(int, notify=sortChanged)
    def sortColumnIndex(self) -> int:
        return self._sort_column

    @Property(bool, notify=sortChanged)
    def sortAscending(self) -> bool:
        return self._sort_order == Qt.SortOrder.AscendingOrder

    def _sort_key(self, column: int, event: CalendarEvent) -> Any:
        source_key = (
            "ig"
            if self._source in (CalendarSource.IG, CalendarSource.FOREXFACTORY)
            else "fxstreet"
        )
        row = self._row_for(event)
        raw = compute_sort_key(source_key, column, row[column], event)
        if isinstance(raw, (int, float)):
            return (0, raw)
        return (1, str(raw).lower())

    def _sort_events(self) -> None:
        if self._sort_column < 0:
            return
        self._events.sort(
            key=lambda event: self._sort_key(self._sort_column, event),
            reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
        )

    def set_events(self, events: list[CalendarEvent]) -> None:
        self.beginResetModel()
        self._events = list(events)
        self._sort_events()
        self.endResetModel()

    @Slot(int)
    def sortColumn(self, column: int) -> None:
        if not (0 <= column < len(self._headers)):
            return

        if self._sort_column == column:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = column
            self._sort_order = Qt.SortOrder.AscendingOrder

        self.beginResetModel()
        self._sort_events()
        self.endResetModel()
        self.sortChanged.emit()


class CalendarBridge(QObject):
    """Thread-safe QObject exposed to QML as ``bridge``."""

    igStatusChanged = Signal()
    fxStatusChanged = Signal()
    igLastRefreshChanged = Signal()
    fxLastRefreshChanged = Signal()
    igErrorChanged = Signal()
    fxErrorChanged = Signal()
    timezoneIndexChanged = Signal()
    timezoneInfoChanged = Signal()

    _controllerNotification = Signal(str, "QVariantMap")

    def __init__(self, controller: AppController, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._settings = controller.settings
        self._ig_model = CalendarTableModel(CalendarSource.FOREXFACTORY, self)
        self._fx_model = CalendarTableModel(CalendarSource.FXSTREET, self)

        self._ig_status = "stopped"
        self._fx_status = "stopped"
        self._ig_error = ""
        self._fx_error = ""
        self._ig_last_refresh = controller.get_last_refresh(CalendarSource.FOREXFACTORY) or "--"
        self._fx_last_refresh = controller.get_last_refresh(CalendarSource.FXSTREET) or "--"

        self._filters = {
            "ig": {
                "region": str(self._settings.get("ig_selected_region")),
                "impact": str(self._settings.get("ig_selected_impact")),
                "date_enabled": False,
                "date": "",
            },
            "fxstreet": {
                "region": str(self._settings.get("fxstreet_selected_region")),
                "impact": str(self._settings.get("fxstreet_selected_impact")),
                "date_enabled": False,
                "date": "",
            },
        }

        self._timezone_index = nearest_timezone_index(local_utc_offset_hours())
        self._tz_offset = TIMEZONE_OFFSETS[self._timezone_index][1]

        self._controllerNotification.connect(self._handle_controller_notification)
        self._controller.set_notification_callback(
            lambda name, payload: self._controllerNotification.emit(name, payload)
        )

    @Property(QObject, constant=True)
    def igModel(self) -> QObject:
        return self._ig_model

    @Property(QObject, constant=True)
    def fxModel(self) -> QObject:
        return self._fx_model

    @Property("QStringList", constant=True)
    def timezoneOptions(self) -> list[str]:
        return [label for label, _ in TIMEZONE_OFFSETS]

    @Property("QStringList", constant=True)
    def regionOptions(self) -> list[str]:
        return ["Tutte"] + [item for item in CalendarDefaults.REGIONS if item != "ALL"]

    @Property("QStringList", constant=True)
    def impactOptions(self) -> list[str]:
        return ["Tutti", "ALTO", "MEDIO", "BASSO"]

    @Property(int, notify=timezoneIndexChanged)
    def timezoneIndex(self) -> int:
        return self._timezone_index

    @Property(str, notify=timezoneInfoChanged)
    def timezoneInfo(self) -> str:
        if self._tz_offset == 0:
            return "Orari in UTC"
        sign = "+" if self._tz_offset > 0 else "-"
        absolute = abs(self._tz_offset)
        hours = int(absolute)
        minutes = int(round((absolute % 1) * 60))
        suffix = f":{minutes:02d}" if minutes else ""
        return f"Orari convertiti: UTC{sign}{hours}{suffix}"

    @Property(str, notify=igStatusChanged)
    def igStatus(self) -> str:
        return self._ig_status

    @Property(str, notify=fxStatusChanged)
    def fxStatus(self) -> str:
        return self._fx_status

    @Property(str, notify=igLastRefreshChanged)
    def igLastRefresh(self) -> str:
        return self._ig_last_refresh

    @Property(str, notify=fxLastRefreshChanged)
    def fxLastRefresh(self) -> str:
        return self._fx_last_refresh

    @Property(str, notify=igErrorChanged)
    def igError(self) -> str:
        return self._ig_error

    @Property(str, notify=fxErrorChanged)
    def fxError(self) -> str:
        return self._fx_error

    @Slot()
    def refreshAll(self) -> None:
        self._controller.refresh_all()

    @Slot(str)
    def refresh(self, source: str) -> None:
        if source == "ig":
            self._controller.refresh_ig()
        elif source == "fxstreet":
            self._controller.refresh_fxstreet()

    @Slot()
    def beginShutdown(self) -> None:
        self._controller.begin_shutdown()

    @Slot(int)
    def setTimezoneIndex(self, index: int) -> None:
        if not (0 <= index < len(TIMEZONE_OFFSETS)) or index == self._timezone_index:
            return
        self._timezone_index = index
        self._tz_offset = TIMEZONE_OFFSETS[index][1]
        self.timezoneIndexChanged.emit()
        self.timezoneInfoChanged.emit()
        self._refresh_model("ig")
        self._refresh_model("fxstreet")

    def _option_index(self, source: str, kind: str) -> int:
        cfg = self._filters.get(source)
        if cfg is None:
            return 0
        value = str(cfg[kind])
        values = (
            ["ALL"] + [item for item in CalendarDefaults.REGIONS if item != "ALL"]
            if kind == "region"
            else ["ALL", "HIGH", "MID", "LOW"]
        )
        try:
            return values.index(value)
        except ValueError:
            return 0

    @Slot(str, result=int)
    def filterRegionIndex(self, source: str) -> int:
        return self._option_index(source, "region")

    @Slot(str, result=int)
    def filterImpactIndex(self, source: str) -> int:
        return self._option_index(source, "impact")

    @Slot(str, int, int, bool, str)
    def setFilters(
        self,
        source: str,
        region_index: int,
        impact_index: int,
        date_enabled: bool,
        date_text: str,
    ) -> None:
        if source not in self._filters:
            return

        region_values = ["ALL"] + [
            item for item in CalendarDefaults.REGIONS if item != "ALL"
        ]
        impact_values = ["ALL", "HIGH", "MID", "LOW"]
        region = (
            region_values[region_index]
            if 0 <= region_index < len(region_values)
            else "ALL"
        )
        impact = (
            impact_values[impact_index]
            if 0 <= impact_index < len(impact_values)
            else "ALL"
        )

        self._filters[source] = {
            "region": region,
            "impact": impact,
            "date_enabled": bool(date_enabled),
            "date": date_text if date_enabled else "",
        }

        prefix = "ig" if source == "ig" else "fxstreet"
        self._settings.set(f"{prefix}_selected_region", region)
        self._settings.set(f"{prefix}_selected_impact", impact)
        self._refresh_model(source)

    @Slot(str, int)
    def sortColumn(self, source: str, column: int) -> None:
        if source == "ig":
            self._ig_model.sortColumn(column)
        elif source == "fxstreet":
            self._fx_model.sortColumn(column)

    @Slot(str, result="QVariantList")
    def getColumnOrder(self, source: str) -> list[int]:
        key = "ig_column_order" if source == "ig" else "fxstreet_column_order"
        if source not in {"ig", "fxstreet"}:
            return []
        return list(self._settings.get(key))

    @Slot(str, int, int, int)
    def columnMoved(
        self,
        source: str,
        logical_index: int,
        old_visual_index: int,
        new_visual_index: int,
    ) -> None:
        if source not in {"ig", "fxstreet"}:
            return
        key = "ig_column_order" if source == "ig" else "fxstreet_column_order"
        order = list(self._settings.get(key))
        if logical_index not in order:
            return
        if not (0 <= new_visual_index < len(order)):
            return

        order.remove(logical_index)
        order.insert(new_visual_index, logical_index)
        self._settings.set(key, order)

    @Slot(str, int, result=int)
    def preferredColumnWidth(self, source: str, logical_column: int) -> int:
        widths = _COLUMN_WIDTHS.get(source, [])
        if 0 <= logical_column < len(widths):
            return widths[logical_column]
        return 100

    def _refresh_model(self, source: str) -> None:
        if source not in self._filters:
            return
        cfg = self._filters[source]
        source_enum = (
            CalendarSource.FOREXFACTORY
            if source == "ig"
            else CalendarSource.FXSTREET
        )
        events = self._controller.filter_events(
            source_enum,
            region=str(cfg["region"]),
            impact=str(cfg["impact"]),
            date=str(cfg["date"]) if cfg["date_enabled"] else "",
            tz_offset_hours=self._tz_offset,
        )
        (self._ig_model if source == "ig" else self._fx_model).set_events(events)

    @Slot(str, "QVariantMap")
    def _handle_controller_notification(
        self,
        name: str,
        payload: dict[str, Any],
    ) -> None:
        source = str(payload.get("source", ""))
        if source not in {"ig", "fxstreet"}:
            return

        if name == "calendar_refresh_started":
            if source == "ig":
                self._ig_status = "running"
                self._ig_error = ""
                self.igStatusChanged.emit()
                self.igErrorChanged.emit()
            else:
                self._fx_status = "running"
                self._fx_error = ""
                self.fxStatusChanged.emit()
                self.fxErrorChanged.emit()
            return

        if name == "calendar_refreshed":
            timestamp = str(payload.get("timestamp", "--"))
            if source == "ig":
                self._ig_status = "stopped"
                self._ig_last_refresh = timestamp
                self._ig_error = ""
                self.igStatusChanged.emit()
                self.igLastRefreshChanged.emit()
                self.igErrorChanged.emit()
            else:
                self._fx_status = "stopped"
                self._fx_last_refresh = timestamp
                self._fx_error = ""
                self.fxStatusChanged.emit()
                self.fxLastRefreshChanged.emit()
                self.fxErrorChanged.emit()
            self._refresh_model(source)
            return

        if name == "calendar_refresh_error":
            message = str(payload.get("error", "Errore sconosciuto"))
            if source == "ig":
                self._ig_status = "error"
                self._ig_error = message
                self.igStatusChanged.emit()
                self.igErrorChanged.emit()
            else:
                self._fx_status = "error"
                self._fx_error = message
                self.fxStatusChanged.emit()
                self.fxErrorChanged.emit()
