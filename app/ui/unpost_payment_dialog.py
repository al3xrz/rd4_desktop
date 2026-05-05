from __future__ import annotations

from app.ui.qt import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout


class UnpostPaymentDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Распровести платёж")
        self.setMinimumWidth(420)

        self.reason_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Причина", self.reason_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def reason(self) -> str:
        return self.reason_input.text().strip()
