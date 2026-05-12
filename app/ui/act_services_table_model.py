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
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return self._alignment(index.column())
        if role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        price = self._as_decimal(self._value(row, "price", Decimal("0")))
        count = self._value(row, "count", 0)
        discount = self._as_decimal(self._value(row, "discount", Decimal("0")))
        total = price * Decimal(str(count or 0)) * (Decimal("1") - discount / Decimal("100"))
        values = [
            self._value(row, "current_code", "") or "",
            self._value(row, "current_name", ""),
            self._value(row, "unit", ""),
            self._format_money(price),
            str(count),
            self._format_percent(discount),
            self._format_money(total),
            self._value(row, "comments", "") or "",
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.TextAlignmentRole and orientation == Qt.Horizontal:
            return self._alignment(section)
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

    def _alignment(self, column: int):
        if column in {0, 2, 4}:
            return int(Qt.AlignCenter)
        if column in {3, 5, 6}:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return int(Qt.AlignLeft | Qt.AlignVCenter)

    def _as_decimal(self, value) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    def _format_money(self, value: Decimal) -> str:
        return str(value.quantize(Decimal("0.01")))

    def _format_percent(self, value: Decimal) -> str:
        return str(value.quantize(Decimal("0.01")))
