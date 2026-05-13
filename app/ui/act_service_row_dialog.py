from __future__ import annotations

from decimal import Decimal

from app.models import ActMedService
from app.ui.icons import set_dialog_button_icons
from app.ui.qt import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout


class ActServiceRowDialog(QDialog):
    def __init__(self, row: ActMedService | dict | None = None, service: dict | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Строка услуги")
        self.setMinimumWidth(420)

        self.service_label = QLabel("")
        self.service_label.setStyleSheet("font-weight: 600;")
        self.service_label.setWordWrap(True)
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
        form.addRow("Услуга", self.service_label)
        form.addRow("Цена", self.price_input)
        form.addRow("Количество", self.count_input)
        form.addRow("Скидка, %", self.discount_input)
        form.addRow("Комментарий", self.comments_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        set_dialog_button_icons(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        if row is not None:
            self._load_row(row)
        elif service is not None:
            self._load_service(service)

    def data(self) -> dict:
        return {
            "price": Decimal(str(self.price_input.value())),
            "count": int(self.count_input.value()),
            "discount": Decimal(str(self.discount_input.value())),
            "comments": self.comments_input.text().strip() or None,
        }

    def _load_row(self, row: ActMedService | dict) -> None:
        if isinstance(row, dict):
            name = row.get("current_name") or row.get("name") or ""
            code = row.get("current_code") or row.get("code") or ""
            unit = row.get("unit") or ""
            price = row.get("price", 0)
            count = row.get("count", 1)
            discount = row.get("discount", 0)
            comments = row.get("comments") or ""
        else:
            name = row.current_name
            code = row.current_code or ""
            unit = row.unit or ""
            price = row.price
            count = row.count
            discount = row.discount
            comments = row.comments or ""

        self._set_service_label(name, code, unit)
        self.price_input.setValue(float(price or 0))
        self.count_input.setValue(float(count or 1))
        self.discount_input.setValue(float(discount or 0))
        self.comments_input.setText(comments)

    def _load_service(self, service: dict) -> None:
        self._set_service_label(service.get("name", ""), service.get("code", ""), service.get("unit", ""))
        self.price_input.setValue(float(service.get("price") or 0))

    def _set_service_label(self, name: str, code: str, unit: str) -> None:
        parts = [name]
        if code:
            parts.append(f"код {code}")
        if unit:
            parts.append(f"ед. {unit}")
        self.service_label.setText(" | ".join(part for part in parts if part))
