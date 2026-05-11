from __future__ import annotations

from app.models import Act, User
from app.services import ActService, DocxService
from app.services.exceptions import DomainError
from app.ui.act_dialog import ActDialog
from app.ui.acts_table_model import ActsTableModel
from app.ui.icons import ICON_DELETE, ICON_NEW, ICON_OPEN, ICON_PRINT, set_button_icon
from app.ui.qt import QGroupBox, QHBoxLayout, QHeaderView, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget


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
        self.print_tickets_button = QPushButton("Талоны")
        self.print_act_button = QPushButton("Акт")
        self.print_all_button = QPushButton("Акт + Талоны")
        set_button_icon(self.create_button, ICON_NEW)
        set_button_icon(self.open_button, ICON_OPEN)
        set_button_icon(self.delete_button, ICON_DELETE)
        set_button_icon(self.print_tickets_button, ICON_PRINT)
        set_button_icon(self.print_act_button, ICON_PRINT)
        set_button_icon(self.print_all_button, ICON_PRINT)
        self.create_button.clicked.connect(self._create_act)
        self.open_button.clicked.connect(self._open_act)
        self.delete_button.clicked.connect(self._delete_act)
        self.print_tickets_button.clicked.connect(self._print_tickets)
        self.print_act_button.clicked.connect(self._print_act)
        self.print_all_button.clicked.connect(self._print_act_and_tickets)

        act_group = QGroupBox("Акт")
        act_layout = QHBoxLayout()
        act_layout.addWidget(self.create_button)
        act_layout.addWidget(self.open_button)
        act_layout.addWidget(self.delete_button)
        act_group.setLayout(act_layout)

        print_group = QGroupBox("Печать")
        print_layout = QHBoxLayout()
        print_layout.addWidget(self.print_tickets_button)
        print_layout.addWidget(self.print_act_button)
        print_layout.addWidget(self.print_all_button)
        print_group.setLayout(print_layout)

        toolbar = QHBoxLayout()
        toolbar.addWidget(act_group)
        toolbar.addWidget(print_group)
        toolbar.addStretch()

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.doubleClicked.connect(self._open_act)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 140)

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

    def _print_tickets(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        try:
            path = self.docx_service.render_act_ticket(act.id)
            self.docx_service.open_document(path)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))

    def _print_act(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        try:
            path = self.docx_service.render_act(act.id)
            self.docx_service.open_document(path)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))

    def _print_act_and_tickets(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        try:
            act_path = self.docx_service.render_act(act.id)
            tickets_path = self.docx_service.render_act_ticket(act.id)
            self.docx_service.open_document(act_path)
            self.docx_service.open_document(tickets_path)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))

    def _reload_and_notify(self) -> None:
        self.reload()
        if self.on_changed is not None:
            self.on_changed()
