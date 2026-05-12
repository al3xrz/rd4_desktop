from __future__ import annotations

from app.core.config import settings
from app.services import AuthService
from app.services.exceptions import DomainError
from app.ui.icons import ICON_OPEN, set_button_icon
from app.ui.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    Signal,
)


class LoginWindow(QDialog):
    login_success = Signal(object)

    def __init__(self, auth_service: AuthService | None = None) -> None:
        super().__init__()
        self.auth_service = auth_service or AuthService()
        self.setWindowTitle("Роддом №4")
        self.setMinimumSize(620, 320)

        self.username_input = QComboBox()
        self.username_input.setEditable(True)
        self.username_input.lineEdit().setPlaceholderText("Пользователь")
        self._load_users()

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.show_password_checkbox = QCheckBox("Показать пароль")
        self.show_password_checkbox.toggled.connect(self._toggle_password_visibility)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #b00020;")

        self.login_button = QPushButton("Войти")
        set_button_icon(self.login_button, ICON_OPEN)
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self._login)
        self.password_input.returnPressed.connect(self._login)

        title = QLabel("Роддом №4")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        subtitle = QLabel("Вход в систему")
        subtitle.setStyleSheet("color: #666;")

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)
        form_layout.addWidget(QLabel("Пользователь"), 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)
        form_layout.addWidget(QLabel("Пароль"), 1, 0)
        form_layout.addWidget(self.password_input, 1, 1)
        form_layout.addWidget(self.show_password_checkbox, 2, 1)
        form_layout.setColumnStretch(1, 1)

        form_panel = QVBoxLayout()
        form_panel.addWidget(title)
        form_panel.addWidget(subtitle)
        form_panel.addSpacing(12)
        form_panel.addLayout(form_layout)
        form_panel.addWidget(self.error_label)
        form_panel.addStretch()
        form_panel.addWidget(self.login_button)

        info_panel = QFrame()
        info_panel.setFrameShape(QFrame.StyledPanel)
        info_panel.setMinimumWidth(250)
        info_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        info_panel.setStyleSheet(
            "QFrame { background: #f8fafc; border: 1px solid #d8e2ef; border-radius: 6px; }"
            "QLabel { background: transparent; border: none; }"
        )
        info_title = QLabel("Подключение")
        info_title.setStyleSheet("font-weight: 600; color: #1f4f82;")
        data_dir_label = QLabel(f"Папка данных:\n{settings.data_dir}")
        database_label = QLabel(f"База данных:\n{settings.database_path}")
        for label in [data_dir_label, database_label]:
            label.setWordWrap(True)
            label.setStyleSheet("color: #475569;")

        info_layout = QVBoxLayout()
        info_layout.addWidget(info_title)
        info_layout.addSpacing(8)
        info_layout.addWidget(data_dir_label)
        info_layout.addSpacing(10)
        info_layout.addWidget(database_label)
        info_layout.addStretch()
        info_panel.setLayout(info_layout)

        layout = QHBoxLayout()
        layout.setSpacing(16)
        layout.addLayout(form_panel, 2)
        layout.addWidget(info_panel, 1)
        self.setLayout(layout)

    def _load_users(self) -> None:
        try:
            users = self.auth_service.list_login_users()
        except DomainError:
            users = []
        for user in users:
            label = user.name or user.username
            if label != user.username:
                label = f"{label} ({user.username})"
            self.username_input.addItem(label, user.username)

    def _toggle_password_visibility(self, checked: bool) -> None:
        echo_mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.password_input.setEchoMode(echo_mode)

    def _login(self) -> None:
        self.error_label.clear()
        username = self.username_input.currentText().strip()
        current_index = self.username_input.currentIndex()
        if current_index >= 0 and username == self.username_input.itemText(current_index):
            username = self.username_input.itemData(current_index) or username
        username = username.strip()
        password = self.password_input.text()

        try:
            user = self.auth_service.login(username, password)
        except DomainError:
            self.error_label.setText("Неверный логин или пароль")
            return

        self.login_success.emit(user)
        self.accept()
