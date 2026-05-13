from __future__ import annotations

from app.models import Role, User
from app.ui.icons import set_dialog_button_icons
from app.ui.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class UserDialog(QDialog):
    ROLE_LABELS = {
        "admin": "Администратор",
        "operator": "Оператор",
        "cashier": "Кассир",
    }

    def __init__(self, user: User | None = None) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle("Новый пользователь" if user is None else "Редактирование пользователя")
        self.setMinimumWidth(560)

        self.username_input = QLineEdit()
        self.name_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.show_password_input = QCheckBox("Показать пароль")
        self.show_password_input.toggled.connect(self._toggle_password_visibility)
        self.role_input = QComboBox()
        for role in Role:
            self.role_input.addItem(self.ROLE_LABELS.get(role.value, role.value), role.value)
        self.is_active_input = QCheckBox("Пользователь активен")
        self.is_active_input.setChecked(True)
        self.comments_input = QTextEdit()
        self.comments_input.setFixedHeight(88)

        self._configure_inputs()
        self._build_layout()

        if user is not None:
            self._load_user(user)

    def data(self) -> dict:
        payload = {
            "username": self.username_input.text().strip(),
            "name": self.name_input.text().strip() or None,
            "role": self.role_input.currentData(),
            "is_active": self.is_active_input.isChecked(),
            "comments": self.comments_input.toPlainText().strip() or None,
        }
        if self.user is None:
            payload["password"] = self.password_input.text()
        return payload

    def _configure_inputs(self) -> None:
        self.username_input.setPlaceholderText("Логин для входа")
        self.name_input.setPlaceholderText("Имя сотрудника")
        self.password_input.setPlaceholderText("Первичный пароль")
        self.comments_input.setPlaceholderText("Комментарий для администраторов")

    def _build_layout(self) -> None:
        title = QLabel("Пользователь")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        subtitle = QLabel("Настройте роль и доступ к приложению")
        subtitle.setStyleSheet("color: #666;")

        identity = QGroupBox("Учетная запись")
        identity_form = QFormLayout()
        identity_form.addRow("Логин", self.username_input)
        identity_form.addRow("Имя", self.name_input)
        if self.user is None:
            identity_form.addRow("Пароль", self.password_input)
            identity_form.addRow("", self.show_password_input)
        identity.setLayout(identity_form)

        access = QGroupBox("Доступ")
        access_form = QFormLayout()
        access_form.addRow("Роль", self.role_input)
        access_form.addRow("Статус", self.is_active_input)
        access_form.addRow("Комментарий", self.comments_input)
        access.setLayout(access_form)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        set_dialog_button_icons(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(identity)
        layout.addWidget(access)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def _load_user(self, user: User) -> None:
        self.username_input.setText(user.username)
        self.name_input.setText(user.name or "")
        self.is_active_input.setChecked(bool(user.is_active))
        self.comments_input.setPlainText(user.comments or "")
        role = getattr(user.role, "value", user.role)
        for index in range(self.role_input.count()):
            if self.role_input.itemData(index) == role:
                self.role_input.setCurrentIndex(index)
                break

    def _toggle_password_visibility(self, checked: bool) -> None:
        echo_mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.password_input.setEchoMode(echo_mode)
