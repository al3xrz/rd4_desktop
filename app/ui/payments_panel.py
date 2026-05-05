from __future__ import annotations

from app.models import Payment, User
from app.services import PaymentService
from app.services.exceptions import DomainError
from app.ui.icons import ICON_DELETE, ICON_EDIT, ICON_NEW, ICON_REFRESH, set_button_icon
from app.ui.payment_dialog import PaymentDialog
from app.ui.payments_table_model import PaymentsTableModel
from app.ui.qt import QHBoxLayout, QHeaderView, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget
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

        self.add_payment_button = QPushButton("Добавить оплату")
        self.add_refund_button = QPushButton("Добавить возврат")
        self.edit_button = QPushButton("Редактировать")
        self.unpost_button = QPushButton("Распровести")
        set_button_icon(self.add_payment_button, ICON_NEW)
        set_button_icon(self.add_refund_button, ICON_REFRESH)
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.unpost_button, ICON_DELETE)

        self.add_payment_button.clicked.connect(self._add_payment)
        self.add_refund_button.clicked.connect(self._add_refund)
        self.edit_button.clicked.connect(self._edit_payment)
        self.unpost_button.clicked.connect(self._unpost_payment)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.add_payment_button)
        toolbar.addWidget(self.add_refund_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.unpost_button)
        toolbar.addStretch()

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.reload()

    def reload(self) -> None:
        self.model.set_payments(self.payment_service.list_payments(self.contract_id))

    def _selected_payment(self) -> Payment | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.payment_at(indexes[0].row())

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
        dialog = UnpostPaymentDialog()
        if dialog.exec_() != UnpostPaymentDialog.Accepted:
            return
        try:
            self.payment_service.unpost_payment(payment.id, dialog.reason(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self._reload_and_notify()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Роддом №4", message)

    def _reload_and_notify(self) -> None:
        self.reload()
        if self.on_changed is not None:
            self.on_changed()
