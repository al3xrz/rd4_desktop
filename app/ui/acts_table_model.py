from __future__ import annotations

from decimal import Decimal

from app.models import Act
from app.ui.qt import QAbstractTableModel, QModelIndex, Qt


class ActsTableModel(QAbstractTableModel):
    HEADERS = ["Номер", "Дата", "Стоимость услуг", "Комментарий"]

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
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return self._alignment(index.column())
        if role != Qt.DisplayRole:
            return None
        act = self.acts[index.row()]
        values = [
            act.number,
            act.date.strftime("%d.%m.%Y") if act.date else "",
            self._format_money(self.services_total(act)),
            act.comments or "",
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

    def act_at(self, row: int) -> Act | None:
        if row < 0 or row >= len(self.acts):
            return None
        return self.acts[row]

    def set_acts(self, acts: list[Act]) -> None:
        self.beginResetModel()
        self.acts = acts
        self.endResetModel()

    def services_total(self, act: Act) -> Decimal:
        total = Decimal("0")
        for row in act.services:
            if not row.deleted:
                total += row.price * row.count * (Decimal("1") - row.discount / Decimal("100"))
        return total

    def _format_money(self, value: Decimal) -> str:
        return str(value.quantize(Decimal("0.01")))

    def _alignment(self, column: int):
        if column in {0, 1}:
            return int(Qt.AlignCenter)
        if column == 2:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return int(Qt.AlignLeft | Qt.AlignVCenter)
