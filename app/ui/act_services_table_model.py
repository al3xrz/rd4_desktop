from __future__ import annotations

from decimal import Decimal

from app.models import ActMedService
from app.ui.qt import QAbstractTableModel, QModelIndex, Qt


class ActServicesTableModel(QAbstractTableModel):
    HEADERS = ["Код", "Услуга", "Ед.", "Цена", "Кол-во", "Скидка", "Итого", "Комментарий"]

    def __init__(self, rows: list[ActMedService] | None = None) -> None:
        super().__init__()
        self.rows = rows or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        price = self._value(row, "price", Decimal("0"))
        count = self._value(row, "count", 0)
        discount = self._value(row, "discount", Decimal("0"))
        total = price * count * (1 - discount / 100)
        values = [
            self._value(row, "current_code", "") or "",
            self._value(row, "current_name", ""),
            self._value(row, "unit", ""),
            str(price),
            str(count),
            str(discount),
            str(total),
            self._value(row, "comments", "") or "",
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def row_at(self, index: int) -> ActMedService | None:
        if index < 0 or index >= len(self.rows):
            return None
        return self.rows[index]

    def set_rows(self, rows: list[ActMedService]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def _value(self, row: ActMedService | dict, name: str, default=None):
        if isinstance(row, dict):
            return row.get(name, default)
        return getattr(row, name, default)
