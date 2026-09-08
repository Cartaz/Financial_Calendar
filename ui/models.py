"""Qt projections of immutable backend snapshots; no query or persistence policy."""

from PySide6.QtCore import (
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Slot,
)
from config.constants import PathConfig, CalendarDefaults
from core.calendar_view import LABELS, SOURCES


class RecordListModel(QAbstractListModel):
    def __init__(self, roles, parent=None):
        super().__init__(parent)
        self._roles = {
            Qt.UserRole + i + 1: name.encode() for i, name in enumerate(roles)
        }
        self.records = ()

    def roleNames(self):
        return self._roles

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.records)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.records):
            return None
        name = self._roles.get(role)
        return self.records[index.row()].get(name.decode()) if name else None

    def replace(self, records):
        if tuple(records) == self.records:
            return
        self.beginResetModel()
        self.records = tuple(dict(row) for row in records)
        self.endResetModel()


class CalendarTableModel(QAbstractTableModel):
    ROLES = {
        Qt.DisplayRole: b"display",
        Qt.UserRole + 1: b"columnKey",
        Qt.UserRole + 2: b"impactLevel",
        Qt.UserRole + 3: b"flagUrl",
        Qt.UserRole + 4: b"timing",
        Qt.UserRole + 5: b"duplicate",
        Qt.UserRole + 6: b"isPast",
        Qt.UserRole + 7: b"isNextHigh",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = ()
        self.columns = ()
        self._sort_key = ""
        self._sort_direction = "asc"

    def roleNames(self):
        return self.ROLES

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if (
            not index.isValid()
            or not 0 <= index.row() < len(self.rows)
            or not 0 <= index.column() < len(self.columns)
        ):
            return None
        row, key = self.rows[index.row()], self.columns[index.column()]
        name = self.ROLES.get(role)
        if role == Qt.DisplayRole:
            value = row[key]
            return SOURCES.get(value, value) if key == "source" else str(value or "—")
        values = {
            b"columnKey": key,
            b"impactLevel": row["impact"],
            b"timing": row["countdown"],
            b"duplicate": row["duplicate_group"],
            b"isPast": row["past"],
            b"isNextHigh": row["next_high"],
        }
        if name == b"flagUrl":
            code = CalendarDefaults.FLAG_CODES.get(row["country"])
            return (PathConfig.FLAGS_DIR / f"{code}.svg").as_uri() if code else ""
        return values.get(name)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if (
            role == Qt.DisplayRole
            and orientation == Qt.Horizontal
            and 0 <= section < len(self.columns)
        ):
            key = self.columns[section]
            suffix = (
                (" ↑" if self._sort_direction == "asc" else " ↓")
                if key == self._sort_key
                else ""
            )
            return LABELS[key] + suffix
        return None

    @Slot(int, result=float)
    def columnWidth(self, column):
        if not 0 <= column < len(self.columns):
            return 110.0
        return {
            "event_name": 340.0,
            "country": 95.0,
            "source": 140.0,
            "time": 80.0,
        }.get(self.columns[column], 112.0)

    def replace(self, view):
        self._sort_key = view.state["sort_key"]
        self._sort_direction = view.state["sort_direction"]
        if self.columns:
            self.headerDataChanged.emit(Qt.Horizontal, 0, len(self.columns) - 1)
        if self.rows == view.rows and self.columns == view.columns:
            return
        same = (
            self.columns == view.columns
            and len(self.rows) == len(view.rows)
            and all(
                (a["source"], a["utc_dt"], a["country"], a["event_name"])
                == (b["source"], b["utc_dt"], b["country"], b["event_name"])
                for a, b in zip(self.rows, view.rows)
            )
        )
        if same:
            old = self.rows
            self.rows = view.rows
            for i, (a, b) in enumerate(zip(old, self.rows)):
                if a != b:
                    self.dataChanged.emit(
                        self.index(i, 0),
                        self.index(i, len(self.columns) - 1),
                        list(self.ROLES),
                    )
        else:
            self.beginResetModel()
            self.rows, self.columns = view.rows, view.columns
            self.endResetModel()
