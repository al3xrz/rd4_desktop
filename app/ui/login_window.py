from __future__ import annotations

from app.services import AuthService
from app.services.exceptions import DomainError
from app.ui.icons import ICON_OPEN, set_button_icon
from app.ui.qt import QCheckBox, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, Signal


class LoginWindow(QDialog):
    login_success = Signal(object)

    def __init__(self, auth_service: AuthService | None = None) -> None:
        super().__init__()
        self.auth_service = auth_service or AuthService()
        self.setWindowTitle("Роддом №4")
        self.setMinimumWidth(360)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.show_password_checkbox = QCheckBox("Показать пароль")
        self.show_password_checkbox.toggled.connect(self._toggle_password_visibility)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #b00020;")

        self.login_button = QPushButton("Войти")
        set_button_icon(self.login_button, ICON_OPEN)
        self.login_button.clicked.connect(self._login)
        self.password_input.returnPressed.connect(self._login)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Роддом №4"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_password_checkbox)
        layout.addWidget(self.error_label)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def _toggle_password_visibility(self, checked: bool) -> None:
        echo_mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.password_input.setEchoMode(echo_mode)

    def _login(self) -> None:
        self.error_label.clear()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        try:
            user = self.auth_service.login(username, password)
        except DomainError:
            self.error_label.setText("Неверный логин или пароль")
            return

        self.login_success.emit(user)
        self.accept()
