from __future__ import annotations

from app.models import Act, User
from app.services import ActService, DocxService
from app.services.exceptions import DomainError
from app.ui.act_dialog import ActDialog
from app.ui.acts_table_model import ActsTableModel
from app.ui.icons import ICON_DELETE, ICON_NEW, ICON_OPEN, ICON_PRINT, set_button_icon
from app.ui.qt import QHBoxLayout, QHeaderView, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget


class ActsPanel(QWidget):
    def __init__(
        self,
        contract_id: int,
        current_user: User,
        act_service: ActService | None = None,
        docx_service: DocxService | None = None,
        on_changed=None,
    ) -> None:
        super().__init__()
        self.contract_id = contract_id
        self.current_user = current_user
        self.act_service = act_service or ActService()
        self.docx_service = docx_service or DocxService()
        self.on_changed = on_changed
        self.model = ActsTableModel()

        self.create_button = QPushButton("Создать акт")
        self.open_button = QPushButton("Открыть акт")
        self.delete_button = QPushButton("Удалить акт")
        self.print_button = QPushButton("Печать талона")
        set_button_icon(self.create_button, ICON_NEW)
        set_button_icon(self.open_button, ICON_OPEN)
        set_button_icon(self.delete_button, ICON_DELETE)
        set_button_icon(self.print_button, ICON_PRINT)
        self.create_button.clicked.connect(self._create_act)
        self.open_button.clicked.connect(self._open_act)
        self.delete_button.clicked.connect(self._delete_act)
        self.print_button.clicked.connect(self._print_not_ready)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.create_button)
        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addWidget(self.print_button)
        toolbar.addStretch()

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.doubleClicked.connect(self._open_act)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.reload()

    def reload(self) -> None:
        self.model.set_acts(self.act_service.list_acts(self.contract_id))

    def _selected_act(self) -> Act | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.act_at(indexes[0].row())

    def _create_act(self) -> None:
        dialog = ActDialog(self.contract_id, self.current_user)
        if dialog.exec_() == ActDialog.Accepted:
            self._reload_and_notify()

    def _open_act(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        try:
            act = self.act_service.get_act(act.id)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        dialog = ActDialog(self.contract_id, self.current_user, act)
        if dialog.exec_() == ActDialog.Accepted:
            self._reload_and_notify()

    def _delete_act(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        confirmed = QMessageBox.question(self, "Удалить акт", f"Удалить акт {act.number}?")
        if confirmed != QMessageBox.Yes:
            return
        try:
            self.act_service.delete_act(act.id, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self._reload_and_notify()

    def _print_not_ready(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        try:
            path = self.docx_service.render_act_ticket(act.id)
            self.docx_service.open_document(path)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))

    def _reload_and_notify(self) -> None:
        self.reload()
        if self.on_changed is not None:
            self.on_changed()
