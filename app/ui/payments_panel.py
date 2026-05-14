from __future__ import annotations

from decimal import Decimal

from app.models import Payment, User
from app.services import PaymentService
from app.services.exceptions import DomainError
from app.ui.icons import ICON_DELETE, ICON_EDIT, ICON_NEW, ICON_REFUND, ICON_REFRESH, icon_for, set_button_icon
from app.ui.payment_dialog import PaymentDialog
from app.ui.payments_table_model import PaymentsTableModel
from app.ui.qt import QLabel, QMessageBox, QHeaderView, QMenu, QTableView, Qt, QVBoxLayout, QWidget
from app.ui.toolbars import make_toolbar, make_toolbar_button
from app.ui.unpost_payment_dialog import UnpostPaymentDialog


class PaymentsPanel(QWidget):
    def __init__(
        self,
        contract_id: int,
        current_user: User,
        payment_service: PaymentService | None = None,
        on_changed=None,
    ) -> None:
        super().__init__()
        self.contract_id = contract_id
        self.current_user = current_user
        self.payment_service = payment_service or PaymentService()
        self.on_changed = on_changed
        self.model = PaymentsTableModel()
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 600; color: #334155;")

        self.add_payment_button = make_toolbar_button("Оплата", "Добавить оплату")
        self.add_refund_button = make_toolbar_button("Возврат", "Добавить возврат")
        self.edit_button = make_toolbar_button("Редактировать", "Редактировать выбранный платеж")
        self.unpost_button = make_toolbar_button("Распровести", "Распровести выбранный платеж")
        set_button_icon(self.add_payment_button, ICON_NEW)
        set_button_icon(self.add_refund_button, ICON_REFUND)
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.unpost_button, ICON_DELETE)

        self.add_payment_button.clicked.connect(self._add_payment)
        self.add_refund_button.clicked.connect(self._add_refund)
        self.edit_button.clicked.connect(self._edit_payment)
        self.unpost_button.clicked.connect(self._unpost_payment)

        toolbar = make_toolbar()
        toolbar.addWidget(self.add_payment_button)
        toolbar.addWidget(self.add_refund_button)
        toolbar.addSeparator()
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.unpost_button)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.selectionModel().selectionChanged.connect(self._update_selection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(0, 36)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 240)

        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.reload()

    def reload(self) -> None:
        self.model.set_payments(self.payment_service.list_payments(self.contract_id))
        self._update_summary()
        self._update_selection()

    def payment_count(self) -> int:
        return self.model.rowCount()

    def _update_summary(self) -> None:
        payments = [payment for payment in self.model.payments if not payment.deleted]
        posted_payments = [payment for payment in payments if payment.posted]
        incoming = sum((payment.amount for payment in posted_payments if payment.amount > 0), Decimal("0"))
        refunds = sum((payment.amount for payment in posted_payments if payment.amount < 0), Decimal("0"))
        total = incoming + refunds
        unposted_count = sum(1 for payment in payments if not payment.posted)
        self.summary_label.setText(
            f"Оплаты: {incoming} | Возвраты: {refunds} | Итого: {total} | Распроведено: {unposted_count}"
        )

    def _selected_payment(self) -> Payment | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.payment_at(indexes[0].row())

    def _update_selection(self, *args) -> None:
        payment = self._selected_payment()
        can_change = bool(payment and payment.posted and not payment.deleted)
        self.edit_button.setEnabled(can_change)
        self.unpost_button.setEnabled(can_change)

    def _add_payment(self) -> None:
        dialog = PaymentDialog("Добавить оплату")
        if dialog.exec_() != PaymentDialog.Accepted:
            return
        try:
            self.payment_service.create_payment(self.contract_id, dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self._reload_and_notify()

    def _add_refund(self) -> None:
        dialog = PaymentDialog("Добавить возврат")
        if dialog.exec_() != PaymentDialog.Accepted:
            return
        try:
            self.payment_service.create_refund(self.contract_id, dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self._reload_and_notify()

    def _edit_payment(self) -> None:
        payment = self._selected_payment()
        if payment is None:
            self._show_error("Выберите платёж")
            return
        if payment.deleted:
            self._show_error("Платёж удален")
            return
        dialog = PaymentDialog("Редактировать платёж", payment)
        if dialog.exec_() != PaymentDialog.Accepted:
            return
        data = dialog.data()
        if payment.amount < 0:
            data["amount"] = -abs(data["amount"])
        try:
            self.payment_service.update_payment(payment.id, data, self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self._reload_and_notify()

    def _unpost_payment(self) -> None:
        payment = self._selected_payment()
        if payment is None:
            self._show_error("Выберите платёж")
            return
        if payment.deleted:
            self._show_error("Платёж удален")
            return
        dialog = UnpostPaymentDialog()
        if dialog.exec_() != UnpostPaymentDialog.Accepted:
            return
        try:
            self.payment_service.unpost_payment(payment.id, dialog.reason(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self._reload_and_notify()

    def _open_context_menu(self, position) -> None:
        index = self.table.indexAt(position)
        if index.isValid():
            self.table.selectRow(index.row())
        payment = self._selected_payment()

        menu = QMenu(self)
        add_payment_action = menu.addAction(icon_for(ICON_NEW), "Добавить оплату")
        add_refund_action = menu.addAction(icon_for(ICON_REFUND), "Добавить возврат")
        refresh_action = menu.addAction(icon_for(ICON_REFRESH), "Обновить")
        menu.addSeparator()
        edit_action = menu.addAction(icon_for(ICON_EDIT), "Редактировать")
        unpost_action = menu.addAction(icon_for(ICON_DELETE), "Распровести")

        has_payment = payment is not None
        is_active = bool(payment and not payment.deleted)
        is_posted = bool(payment and payment.posted)
        edit_action.setEnabled(has_payment and is_active and is_posted)
        unpost_action.setEnabled(has_payment and is_active and is_posted)

        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == add_payment_action:
            self._add_payment()
        elif action == add_refund_action:
            self._add_refund()
        elif action == refresh_action:
            self.reload()
        elif action == edit_action:
            self._edit_payment()
        elif action == unpost_action:
            self._unpost_payment()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Роддом №4", message)

    def _reload_and_notify(self) -> None:
        self.reload()
        if self.on_changed is not None:
            self.on_changed()
