from __future__ import annotations

from decimal import Decimal

from app.models import ActMedService
from app.ui.qt import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit, QVBoxLayout


class ActServiceRowDialog(QDialog):
    def __init__(self, row: ActMedService | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Строка услуги")
        self.setMinimumWidth(420)

        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(10_000_000)
        self.price_input.setDecimals(2)
        self.count_input = QDoubleSpinBox()
        self.count_input.setMaximum(10_000)
        self.count_input.setDecimals(2)
        self.count_input.setValue(1)
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMaximum(100)
        self.discount_input.setDecimals(2)
        self.comments_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Цена", self.price_input)
        form.addRow("Количество", self.count_input)
        form.addRow("Скидка, %", self.discount_input)
        form.addRow("Комментарий", self.comments_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        if row is not None:
            self.price_input.setValue(float(row.price))
            self.count_input.setValue(float(row.count))
            self.discount_input.setValue(float(row.discount))
            self.comments_input.setText(row.comments or "")

    def data(self) -> dict:
        return {
            "price": Decimal(str(self.price_input.value())),
            "count": int(self.count_input.value()),
            "discount": Decimal(str(self.discount_input.value())),
            "comments": self.comments_input.text().strip() or None,
        }
