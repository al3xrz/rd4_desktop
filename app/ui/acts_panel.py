from __future__ import annotations

from decimal import Decimal

from app.models import Act, User
from app.services import ActService, DocxService
from app.services.exceptions import DomainError
from app.ui.act_dialog import ActDialog
from app.ui.acts_table_model import ActsTableModel
from app.ui.icons import (
    ICON_DELETE,
    ICON_FINANCIAL_REPORT,
    ICON_NEW,
    ICON_OPEN,
    ICON_PRINT,
    ICON_REFRESH,
    icon_for,
    set_button_icon,
)
from app.ui.toolbars import make_toolbar, make_toolbar_button
from app.ui.qt import (
    QAction,
    QHeaderView,
    QKeySequence,
    QLabel,
    QMessageBox,
    QMenu,
    QShortcut,
    QTableView,
    Qt,
    QVBoxLayout,
    QWidget,
)


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
        self.total_label = QLabel("")
        self.total_label.setStyleSheet("font-weight: 600; color: #334155;")
        self.summary_label = QLabel("Выберите акт")
        self.summary_label.setStyleSheet("color: #666;")
        self.summary_label.setWordWrap(True)

        self.create_button = make_toolbar_button("Создать", "Создать акт")
        self.open_button = make_toolbar_button("Открыть", "Открыть выбранный акт")
        self.pay_button = make_toolbar_button("Оплатить", "Создать платеж по выбранному акту")
        self.delete_button = make_toolbar_button("Удалить", "Удалить выбранный акт")
        self.print_tickets_button = make_toolbar_button("Талоны", "Распечатать талоны выбранного акта")
        self.print_act_button = make_toolbar_button("Акт", "Распечатать выбранный акт")
        self.print_all_button = make_toolbar_button("Акт + Талоны", "Распечатать акт и талоны")
        set_button_icon(self.create_button, ICON_NEW)
        set_button_icon(self.open_button, ICON_OPEN)
        set_button_icon(self.pay_button, ICON_FINANCIAL_REPORT)
        set_button_icon(self.delete_button, ICON_DELETE)
        set_button_icon(self.print_tickets_button, ICON_PRINT)
        set_button_icon(self.print_act_button, ICON_PRINT)
        set_button_icon(self.print_all_button, ICON_PRINT)
        self.create_button.clicked.connect(self._create_act)
        self.open_button.clicked.connect(self._open_act)
        self.pay_button.clicked.connect(self._pay_act)
        self.delete_button.clicked.connect(self._delete_act)
        self.print_tickets_button.clicked.connect(self._print_tickets)
        self.print_act_button.clicked.connect(self._print_act)
        self.print_all_button.clicked.connect(self._print_act_and_tickets)

        toolbar = make_toolbar()
        toolbar.addWidget(self.create_button)
        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.pay_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addSeparator()
        toolbar.addWidget(self.print_tickets_button)
        toolbar.addWidget(self.print_act_button)
        toolbar.addWidget(self.print_all_button)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.doubleClicked.connect(self._open_act)
        self.table.selectionModel().selectionChanged.connect(self._update_selection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 140)

        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.total_label)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)
        self.setLayout(layout)

        self._setup_shortcuts()
        self.reload()

    def reload(self) -> None:
        self.model.set_acts(self.act_service.list_acts(self.contract_id))
        self._update_totals()
        self._update_selection()

    def act_count(self) -> int:
        return self.model.rowCount()

    def _update_totals(self) -> None:
        acts = self.model.acts
        service_count = sum(sum(1 for row in act.services if not row.deleted) for act in acts)
        total = sum((self.model.services_total(act) for act in acts), start=Decimal("0"))
        self.total_label.setText(f"Актов: {len(acts)} | Услуг: {service_count} | Сумма по актам: {total}")

    def _selected_act(self) -> Act | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.act_at(indexes[0].row())

    def _create_act(self) -> None:
        dialog = ActDialog(self.contract_id, self.current_user)
        if dialog.exec_() == ActDialog.Accepted:
            self._reload_and_notify()
            self._print_saved_act_if_requested(dialog)

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
            self._print_saved_act_if_requested(dialog)

    def _delete_act(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        if act.deleted:
            QMessageBox.warning(self, "Роддом №4", "Акт уже удален")
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

    def _pay_act(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        if act.deleted:
            QMessageBox.warning(self, "Роддом №4", "Удаленный акт нельзя оплатить")
            return
        total = self.model.services_total(act)
        confirmed = QMessageBox.question(
            self,
            "Оплатить акт",
            f"Создать платеж на сумму {total} по акту {act.number}?",
        )
        if confirmed != QMessageBox.Yes:
            return
        try:
            self.act_service.pay_act(act.id, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self._reload_and_notify()

    def _print_tickets(self) -> None:
        act = self._selected_act()
        if act is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите акт")
            return
        if act.deleted:
            QMessageBox.warning(self, "Роддом №4", "Удаленный акт нельзя распечатать")
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
        if act.deleted:
            QMessageBox.warning(self, "Роддом №4", "Удаленный акт нельзя распечатать")
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
        if act.deleted:
            QMessageBox.warning(self, "Роддом №4", "Удаленный акт нельзя распечатать")
            return
        try:
            act_path = self.docx_service.render_act(act.id)
            tickets_path = self.docx_service.render_act_ticket(act.id)
            self.docx_service.open_document(act_path)
            self.docx_service.open_document(tickets_path)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))

    def _print_saved_act_if_requested(self, dialog: ActDialog) -> None:
        if not dialog.print_after_save or dialog.saved_act_id is None:
            return
        try:
            path = self.docx_service.render_act(dialog.saved_act_id)
            self.docx_service.open_document(path)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))

    def _reload_and_notify(self) -> None:
        self.reload()
        if self.on_changed is not None:
            self.on_changed()

    def _open_context_menu(self, position) -> None:
        index = self.table.indexAt(position)
        if index.isValid():
            self.table.selectRow(index.row())
        act = self._selected_act()

        menu = QMenu(self)
        create_action = menu.addAction(icon_for(ICON_NEW), "Создать акт")
        refresh_action = menu.addAction(icon_for(ICON_REFRESH), "Обновить")
        menu.addSeparator()
        open_action = menu.addAction(icon_for(ICON_OPEN), "Открыть")
        pay_action = menu.addAction(icon_for(ICON_FINANCIAL_REPORT), "Оплатить акт")
        print_tickets_action = menu.addAction(icon_for(ICON_PRINT), "Печать талонов")
        print_act_action = menu.addAction(icon_for(ICON_PRINT), "Печать акта")
        print_all_action = menu.addAction(icon_for(ICON_PRINT), "Печать акта и талонов")
        menu.addSeparator()
        delete_action = menu.addAction(icon_for(ICON_DELETE), "Удалить")

        has_act = act is not None
        is_deleted = bool(act and act.deleted)
        is_paid = self._is_act_paid(act) if has_act else False
        open_action.setEnabled(has_act)
        pay_action.setEnabled(has_act and not is_deleted and not is_paid)
        print_tickets_action.setEnabled(has_act and not is_deleted)
        print_act_action.setEnabled(has_act and not is_deleted)
        print_all_action.setEnabled(has_act and not is_deleted)
        delete_action.setEnabled(has_act and not is_deleted)

        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == create_action:
            self._create_act()
        elif action == refresh_action:
            self.reload()
        elif action == open_action:
            self._open_act()
        elif action == pay_action:
            self._pay_act()
        elif action == print_tickets_action:
            self._print_tickets()
        elif action == print_act_action:
            self._print_act()
        elif action == print_all_action:
            self._print_act_and_tickets()
        elif action == delete_action:
            self._delete_act()

    def _setup_shortcuts(self) -> None:
        create_action = QAction(self)
        create_action.setShortcut(QKeySequence("Ctrl+N"))
        create_action.triggered.connect(self._create_act)
        self.addAction(create_action)

        delete_action = QAction(self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.triggered.connect(self._delete_act)
        self.addAction(delete_action)

        print_action = QAction(self)
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self._print_act)
        self.addAction(print_action)

        open_shortcut = QShortcut(QKeySequence("Return"), self.table)
        open_shortcut.activated.connect(self._open_act)

    def _update_selection(self, *args) -> None:
        act = self._selected_act()
        has_selection = act is not None
        self.open_button.setEnabled(has_selection)
        can_change = has_selection and not act.deleted
        can_pay = can_change and not self._is_act_paid(act)
        self.pay_button.setEnabled(can_pay)
        self.delete_button.setEnabled(can_change)
        self.print_tickets_button.setEnabled(can_change)
        self.print_act_button.setEnabled(can_change)
        self.print_all_button.setEnabled(can_change)

        if act is None:
            if self.model.rowCount() == 0:
                self.summary_label.setText("По договору ещё нет актов. Создайте акт, чтобы добавить оказанные услуги.")
            else:
                self.summary_label.setText("Выберите акт")
            return

        service_count = sum(1 for row in act.services if not row.deleted)
        total = self.model.services_total(act)
        comment = f" | комментарий: {act.comments}" if act.comments else ""
        deleted = " | удален" if act.deleted else ""
        paid = " | оплачен" if self._is_act_paid(act) else ""
        self.summary_label.setText(f"Акт: {act.number}{deleted}{paid} | услуг: {service_count} | сумма: {total}{comment}")

    def _is_act_paid(self, act: Act | None) -> bool:
        if act is None:
            return False
        try:
            return self.act_service.is_act_paid(act.id)
        except DomainError:
            return False
