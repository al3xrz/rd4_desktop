from __future__ import annotations

from app.models import User
from app.services import AuthService
from app.services.exceptions import DomainError
from app.ui.icons import ICON_DELETE, ICON_EDIT, ICON_NEW, ICON_PASSWORD, ICON_REFRESH, icon_for, set_button_icon
from app.ui.password_dialog import PasswordDialog
from app.ui.qt import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    Qt,
)
from app.ui.user_dialog import UserDialog
from app.ui.users_table_model import UsersTableModel


class UsersPage(QWidget):
    """Administration page for managing user accounts.

    The page keeps a local list of users, filters it in memory for fast search,
    and delegates all state changes to ``AuthService`` so role checks and password
    handling stay outside of UI code.
    """

    def __init__(self, current_user: User, auth_service: AuthService | None = None) -> None:
        super().__init__()
        self.current_user = current_user
        self.auth_service = auth_service or AuthService()
        self.users: list[User] = []
        self.model = UsersTableModel()

        self.title_label = QLabel("Пользователи")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.subtitle_label = QLabel("Управление учетными записями, ролями и доступом")
        self.subtitle_label.setStyleSheet("color: #666;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по логину, имени, роли или комментарию")
        self.search_input.textChanged.connect(self._apply_filter)

        self.create_button = QPushButton("Создать")
        self.edit_button = QPushButton("Редактировать")
        self.reset_password_button = QPushButton("Сбросить пароль")
        self.toggle_active_button = QPushButton("Блок./разблок.")
        set_button_icon(self.create_button, ICON_NEW)
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.reset_password_button, ICON_PASSWORD)
        set_button_icon(self.toggle_active_button, ICON_DELETE)

        self.create_button.clicked.connect(self._create_user)
        self.edit_button.clicked.connect(self._edit_user)
        self.reset_password_button.clicked.connect(self._reset_password)
        self.toggle_active_button.clicked.connect(self._toggle_active)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.create_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.reset_password_button)
        toolbar.addWidget(self.toggle_active_button)
        toolbar.addStretch()

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.doubleClicked.connect(self._edit_user)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.selectionModel().selectionChanged.connect(self._update_selection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 600;")
        self.details_label = QLabel("Выберите пользователя")
        self.details_label.setStyleSheet("color: #666;")
        self.details_label.setWordWrap(True)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header.addLayout(header_text)
        header.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addLayout(toolbar)
        layout.addWidget(self.search_input)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.details_label)
        self.setLayout(layout)

        self.reload()

    def reload(self) -> None:
        """Reload users from the service and reapply the current search text."""
        try:
            self.users = self.auth_service.list_users(self.current_user)
            self._apply_filter()
        except DomainError as exc:
            self._show_error(str(exc))

    def _selected_user(self) -> User | None:
        """Return the selected table row as a ``User`` object."""
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.user_at(indexes[0].row())

    def _create_user(self) -> None:
        """Open the user dialog and create an account from its data."""
        dialog = UserDialog()
        if dialog.exec_() != UserDialog.Accepted:
            return
        try:
            self.auth_service.create_user(dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _edit_user(self, *args) -> None:
        """Edit the selected account."""
        user = self._selected_user()
        if user is None:
            self._show_error("Выберите пользователя")
            return
        dialog = UserDialog(user)
        if dialog.exec_() != UserDialog.Accepted:
            return
        try:
            self.auth_service.update_user(user.id, dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _reset_password(self) -> None:
        """Open a password dialog and replace the selected user's password."""
        user = self._selected_user()
        if user is None:
            self._show_error("Выберите пользователя")
            return
        dialog = PasswordDialog()
        if dialog.exec_() != PasswordDialog.Accepted:
            return
        try:
            self.auth_service.reset_password(user.id, dialog.password(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _toggle_active(self) -> None:
        """Block active users or unblock blocked users."""
        user = self._selected_user()
        if user is None:
            self._show_error("Выберите пользователя")
            return
        try:
            self.auth_service.set_user_active(user.id, not user.is_active, self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _apply_filter(self) -> None:
        """Filter users by text typed in the search field."""
        query = self.search_input.text().strip().lower()
        if query:
            users = [user for user in self.users if query in self._user_text(user)]
        else:
            users = list(self.users)
        self.model.set_users(users)
        self.summary_label.setText(f"Показано: {len(users)} из {len(self.users)}" if query else f"Всего пользователей: {len(users)}")
        self._update_selection()

    def _user_text(self, user: User) -> str:
        role = getattr(user.role, "value", user.role)
        return " ".join([user.username or "", user.name or "", role or "", user.comments or ""]).lower()

    def _open_context_menu(self, position) -> None:
        """Show row-level account actions under the mouse cursor."""
        index = self.table.indexAt(position)
        if index.isValid():
            self.table.selectRow(index.row())
        user = self._selected_user()

        menu = QMenu(self)
        create_action = menu.addAction(icon_for(ICON_NEW), "Создать пользователя")
        menu.addSeparator()
        edit_action = menu.addAction(icon_for(ICON_EDIT), "Редактировать")
        reset_action = menu.addAction(icon_for(ICON_PASSWORD), "Сбросить пароль")
        toggle_text = "Заблокировать" if user is not None and user.is_active else "Разблокировать"
        toggle_action = menu.addAction(icon_for(ICON_DELETE if user is not None and user.is_active else ICON_REFRESH), toggle_text)
        edit_action.setEnabled(user is not None)
        reset_action.setEnabled(user is not None)
        toggle_action.setEnabled(user is not None)

        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == create_action:
            self._create_user()
        elif action == edit_action:
            self._edit_user()
        elif action == reset_action:
            self._reset_password()
        elif action == toggle_action:
            self._toggle_active()

    def _update_selection(self, *args) -> None:
        """Refresh action availability and the selected-user summary."""
        user = self._selected_user()
        has_selection = user is not None
        self.edit_button.setEnabled(has_selection)
        self.reset_password_button.setEnabled(has_selection)
        self.toggle_active_button.setEnabled(has_selection)
        if user is None:
            self.details_label.setText("Выберите пользователя")
            return

        role = getattr(user.role, "value", user.role)
        status = "активен" if user.is_active else "заблокирован"
        self.details_label.setText(
            f"{user.username} | {user.name or 'без имени'} | роль: {role} | статус: {status}"
        )

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Роддом №4", message)
