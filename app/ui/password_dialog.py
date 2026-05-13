from __future__ import annotations

from app.ui.icons import set_dialog_button_icons
from app.ui.qt import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout


class PasswordDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Новый пароль")
        self.setMinimumWidth(360)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Пароль", self.password_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        set_dialog_button_icons(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def password(self) -> str:
        return self.password_input.text()
