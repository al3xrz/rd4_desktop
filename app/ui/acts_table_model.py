from __future__ import annotations

from app.models import Act
from app.ui.qt import QAbstractTableModel, QModelIndex, Qt


class ActsTableModel(QAbstractTableModel):
    HEADERS = ["Номер", "Дата", "Комментарий"]

    def __init__(self, acts: list[Act] | None = None) -> None:
        super().__init__()
        self.acts = acts or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.acts)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        act = self.acts[index.row()]
        values = [
            act.number,
            act.date.strftime("%d.%m.%Y") if act.date else "",
            act.comments or "",
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def act_at(self, row: int) -> Act | None:
        if row < 0 or row >= len(self.acts):
            return None
        return self.acts[row]

    def set_acts(self, acts: list[Act]) -> None:
        self.beginResetModel()
        self.acts = acts
        self.endResetModel()
