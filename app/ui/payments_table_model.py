from __future__ import annotations

from app.models import Payment
from app.ui.qt import QAbstractTableModel, QModelIndex, Qt


class PaymentsTableModel(QAbstractTableModel):
    HEADERS = ["Дата", "Сумма", "Статус", "Комментарий", "Распроведение"]

    def __init__(self, payments: list[Payment] | None = None) -> None:
        super().__init__()
        self.payments = payments or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.payments)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        payment = self.payments[index.row()]
        values = [
            payment.date.strftime("%d.%m.%Y") if payment.date else "",
            str(payment.amount),
            "Проведён" if payment.posted else "Распроведён",
            payment.comments or "",
            payment.unpost_reason or "",
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def payment_at(self, row: int) -> Payment | None:
        if row < 0 or row >= len(self.payments):
            return None
        return self.payments[row]

    def set_payments(self, payments: list[Payment]) -> None:
        self.beginResetModel()
        self.payments = payments
        self.endResetModel()
