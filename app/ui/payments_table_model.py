from __future__ import annotations

from app.models import Payment
from app.ui.qt import QAbstractTableModel, QBrush, QColor, QFont, QModelIndex, Qt


class PaymentsTableModel(QAbstractTableModel):
    HEADERS = ["", "Дата", "Сумма", "Статус", "Комментарий", "Распроведение"]

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
        if not index.isValid():
            return None

        payment = self.payments[index.row()]
        column = index.column()
        if role == Qt.TextAlignmentRole and column == 0:
            return Qt.AlignCenter
        if role == Qt.ForegroundRole and payment.deleted:
            return QBrush(QColor("#777777"))
        if role == Qt.FontRole and payment.deleted:
            font = QFont()
            font.setStrikeOut(True)
            return font
        if role == Qt.ForegroundRole and column == 0:
            if not payment.posted:
                return QBrush(QColor("#f2b705"))
            if payment.amount < 0:
                return QBrush(QColor("#c0392b"))
            return QBrush(QColor("#1e8e3e"))
        if role != Qt.DisplayRole:
            return None

        values = [
            self._indicator(payment),
            payment.date.strftime("%d.%m.%Y %H:%M") if payment.date else "",
            str(payment.amount),
            self._status_text(payment),
            self._comments_text(payment),
            payment.unpost_reason or "",
        ]
        return values[column]

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

    def _indicator(self, payment: Payment) -> str:
        if payment.deleted:
            return "×"
        if not payment.posted:
            return "●"
        if payment.amount < 0:
            return "←"
        return "→"

    def _status_text(self, payment: Payment) -> str:
        if payment.deleted:
            return "Удален"
        return "Проведён" if payment.posted else "Распроведён"

    def _comments_text(self, payment: Payment) -> str:
        if payment.deleted:
            comment = payment.comments or ""
            return f"Удален | {comment}" if comment else "Удален"
        return payment.comments or ""
