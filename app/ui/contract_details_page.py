from __future__ import annotations

from app.models import Contract, User
from app.services import ContractService, DocxService
from app.services.exceptions import DomainError
from app.ui.acts_panel import ActsPanel
from app.ui.contract_dialog import ContractDialog
from app.ui.icons import ICON_BACK, ICON_EDIT, ICON_PRINT, set_button_icon
from app.ui.payments_panel import PaymentsPanel
from app.ui.qt import QHBoxLayout, QLabel, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget


class ContractDetailsPage(QWidget):
    def __init__(
        self,
        contract_id: int,
        current_user: User,
        on_back=None,
        contract_service: ContractService | None = None,
        docx_service: DocxService | None = None,
    ) -> None:
        super().__init__()
        self.contract_id = contract_id
        self.current_user = current_user
        self.on_back = on_back
        self.contract_service = contract_service or ContractService()
        self.docx_service = docx_service or DocxService()

        self.back_button = QPushButton("К списку договоров")
        set_button_icon(self.back_button, ICON_BACK)
        self.back_button.clicked.connect(self._back)

        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.patient_label = QLabel("")
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(
            "QLabel { background: #f8fafc; border: 1px solid #d8e2ef; border-radius: 6px; padding: 8px 10px; }"
        )

        self.print_contract_button = QPushButton("Печать договора")
        self.edit_button = QPushButton("Редактировать")
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.print_contract_button, ICON_PRINT)
        self.edit_button.clicked.connect(self._edit_contract)
        self.print_contract_button.clicked.connect(self._print_contract)

        header = QHBoxLayout()
        header.addWidget(self.back_button)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.edit_button)
        header.addWidget(self.print_contract_button)

        self.tabs = QTabWidget()
        self.payments_panel = PaymentsPanel(contract_id, current_user, on_changed=self.reload)
        self.acts_panel = ActsPanel(contract_id, current_user, on_changed=self.reload)
        self.tabs.addTab(self.payments_panel, "Платежи")
        self.tabs.addTab(self.acts_panel, "Акты")

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.patient_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.reload()

    def reload(self) -> None:
        try:
            contract = self.contract_service.get_contract(self.contract_id)
            summary = self.contract_service.get_contract_summary(self.contract_id)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        self._render_header(contract, summary)
        self.payments_panel.reload()
        self.acts_panel.reload()
        self._update_tab_titles()

    def _render_header(self, contract: Contract, summary: dict) -> None:
        self.title_label.setText(f"Договор {contract.contract_number}")
        discharged = " | выписана" if contract.discharged else ""
        self.patient_label.setText(f"{contract.patient_name} | {contract.patient_phone}{discharged}")
        summary_text = dict(summary)
        summary_text["status"] = self._status_text(summary.get("status"))
        self.summary_label.setText(
            "Начислено: {services_total} | Оплачено: {payments_total} | Возвраты: {refunds_total} | "
            "Баланс: {balance} | Статус: {status}".format(**summary_text)
        )
        self.summary_label.setStyleSheet(
            "QLabel {{ background: {background}; border: 1px solid {border}; border-radius: 6px; "
            "padding: 8px 10px; color: {color}; font-weight: 600; }}".format(
                **self._summary_colors(summary.get("status"))
            )
        )

    def _summary_colors(self, status: str | None) -> dict[str, str]:
        if status == "debt":
            return {"background": "#fff5f5", "border": "#f5b5b5", "color": "#b00020"}
        if status == "overpaid":
            return {"background": "#f3f7ff", "border": "#b9cdfa", "color": "#2f5fb3"}
        if status == "paid":
            return {"background": "#f2fbf5", "border": "#b8e1c4", "color": "#237a3b"}
        return {"background": "#f8fafc", "border": "#d8e2ef", "color": "#334155"}

    def _status_text(self, status: str | None) -> str:
        if status == "debt":
            return "Долг"
        if status == "overpaid":
            return "Переплата"
        if status == "paid":
            return "Оплачен"
        return ""

    def _update_tab_titles(self) -> None:
        self.tabs.setTabText(0, f"Платежи ({self.payments_panel.payment_count()})")
        self.tabs.setTabText(1, f"Акты ({self.acts_panel.act_count()})")

    def _back(self) -> None:
        if self.on_back is not None:
            self.on_back()

    def _print_contract(self) -> None:
        try:
            contract = self.contract_service.get_contract(self.contract_id)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        if contract.service_insurance:
            self._render_and_open(lambda: self.docx_service.render_foms_contract(self.contract_id))
            return
        self._render_and_open(lambda: self.docx_service.render_paid_contract(self.contract_id))

    def _edit_contract(self) -> None:
        try:
            contract = self.contract_service.get_contract(self.contract_id)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        dialog = ContractDialog(contract)
        if dialog.exec_() != ContractDialog.Accepted:
            return
        try:
            self.contract_service.update_contract(contract.id, dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _render_and_open(self, render):
        try:
            path = render()
            self.docx_service.open_document(path)
        except DomainError as exc:
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Роддом №4", message)
