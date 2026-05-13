from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models import Payment
from app.ui.icons import set_dialog_button_icons
from app.ui.qt import QDateTime, QDateTimeEdit, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit, QVBoxLayout


class PaymentDialog(QDialog):
    def __init__(self, title: str, payment: Payment | None = None) -> None:
        super().__init__()
        self.payment = payment
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        self.date_input = QDateTimeEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDateTime(QDateTime.currentDateTime())

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(10_000_000)
        self.amount_input.setDecimals(2)

        self.comments_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Дата", self.date_input)
        form.addRow("Сумма", self.amount_input)
        form.addRow("Комментарий", self.comments_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        set_dialog_button_icons(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        if payment is not None:
            self._load_payment(payment)

    def data(self) -> dict:
        return {
            "date": self._to_datetime(self.date_input),
            "amount": Decimal(str(self.amount_input.value())),
            "comments": self.comments_input.text().strip() or None,
        }

    def _load_payment(self, payment: Payment) -> None:
        if payment.date is not None:
            self.date_input.setDateTime(QDateTime(payment.date))
        self.amount_input.setValue(float(abs(payment.amount)))
        self.comments_input.setText(payment.comments or "")

    def _to_datetime(self, widget: QDateTimeEdit) -> datetime:
        qt_value = widget.dateTime()
        converter = getattr(qt_value, "toPyDateTime", None) or getattr(qt_value, "toPython")
        value = converter()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value
