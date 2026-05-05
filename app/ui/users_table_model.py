from __future__ import annotations

from app.models import User
from app.ui.qt import QAbstractTableModel, QColor, QModelIndex, Qt


class UsersTableModel(QAbstractTableModel):
    """Qt table model that adapts ``User`` ORM objects for ``QTableView``."""

    HEADERS = ["Логин", "Имя", "Роль", "Активен", "Комментарий"]

    def __init__(self, users: list[User] | None = None) -> None:
        super().__init__()
        self.users = users or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return visible user row count for Qt."""
        if parent.isValid():
            return 0
        return len(self.users)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the fixed number of user columns."""
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Return display text and visual roles for a table cell."""
        if not index.isValid():
            return None
        user = self.users[index.row()]
        if role == Qt.ForegroundRole and not user.is_active:
            return QColor("#777777")
        if role != Qt.DisplayRole:
            return None
        values = [
            user.username,
            user.name or "",
            getattr(user.role, "value", user.role),
            "Да" if user.is_active else "Нет",
            user.comments or "",
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Return column captions and row numbers."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def user_at(self, row: int) -> User | None:
        """Return the backing user for a view row."""
        if row < 0 or row >= len(self.users):
            return None
        return self.users[row]

    def set_users(self, users: list[User]) -> None:
        """Replace table contents and notify Qt views."""
        self.beginResetModel()
        self.users = users
        self.endResetModel()
