from __future__ import annotations

from datetime import datetime, timedelta

from app.models import Contract, User
from app.services import ContractService, DocxService
from app.services.exceptions import DomainError
from app.ui.contract_dialog import ContractDialog
from app.ui.contracts_table_model import ContractsTableModel
from app.ui.icons import (
    ICON_CONTRACT,
    ICON_DELETE,
    ICON_EDIT,
    ICON_NEW,
    ICON_OPEN,
    ICON_PRINT,
    ICON_REFRESH,
    ICON_RESET,
    icon_for,
    set_button_icon,
)
from app.ui.toolbars import make_toolbar, make_toolbar_button
from app.ui.qt import (
    QAction,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QComboBox,
    QDateTime,
    QDateTimeEdit,
    QGroupBox,
    QLabel,
    QKeySequence,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QShortcut,
    QSortFilterProxyModel,
    QTableView,
    QVBoxLayout,
    QWidget,
    Qt,
)


class ContractsPage(QWidget):
    """Main contract registry page.

    The page keeps all active contracts in memory and applies lightweight client-side
    filters for the current workload. Balance calculations are limited to the
    visible rows so the registry can still be searched and sorted predictably.
    """

    PERIOD_LAST_3_MONTHS = "Последние 3 месяца"
    PERIOD_LAST_6_MONTHS = "Последние 6 месяцев"
    PERIOD_CURRENT_YEAR = "Текущий год"
    PERIOD_ALL = "Все договоры"
    PERIOD_CUSTOM = "Произвольный период"
    PAYMENT_ALL = "Все"
    PAYMENT_PAID = "Платно"
    PAYMENT_INSURANCE = "Страховая"
    PAYMENT_UNSET = "Не указан"
    BALANCE_ALL = "Все"
    BALANCE_PAID = "Оплачен"
    BALANCE_DEBT = "Долг"
    BALANCE_OVERPAID = "Переплата"
    BALANCE_NO_ACTS = "Без актов"
    VISIBILITY_ACTIVE = "Активные"
    VISIBILITY_ALL = "Все"
    VISIBILITY_DELETED = "Удаленные"

    def __init__(
        self,
        current_user: User,
        contract_service: ContractService | None = None,
        docx_service: DocxService | None = None,
        on_open_contract=None,
    ) -> None:
        super().__init__()
        self.current_user = current_user
        self.contract_service = contract_service or ContractService()
        self.docx_service = docx_service or DocxService()
        self.on_open_contract = on_open_contract
        self.contracts: list[Contract] = []
        self.summaries: dict[int, dict] = {}
        self.model = ContractsTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(Qt.UserRole)
        self.last_focused_contract_id: int | None = None
        self._updating_period_controls = False
        self._filters_stacked = False
        self._select_last_on_next_filter = True

        self.title_label = QLabel("Договоры")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.subtitle_label = QLabel("Реестр договоров с пациентами")
        self.subtitle_label.setStyleSheet("color: #666;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по номеру, пациенту, телефону, истории родов или категории")
        self.search_input.textChanged.connect(self._apply_filter)

        self.period_input = QComboBox()
        for period in [
            self.PERIOD_LAST_3_MONTHS,
            self.PERIOD_LAST_6_MONTHS,
            self.PERIOD_CURRENT_YEAR,
            self.PERIOD_ALL,
            self.PERIOD_CUSTOM,
        ]:
            self.period_input.addItem(period, period)
        self._make_compact_combo(self.period_input, 96)
        self.period_input.currentIndexChanged.connect(self._period_changed)

        self.date_from_input = self._date_filter_input()
        self.date_to_input = self._date_filter_input()
        self.date_from_input.dateTimeChanged.connect(self._date_filter_changed)
        self.date_to_input.dateTimeChanged.connect(self._date_filter_changed)

        self.payment_type_input = QComboBox()
        for payment_type in [self.PAYMENT_ALL, self.PAYMENT_PAID, self.PAYMENT_INSURANCE, self.PAYMENT_UNSET]:
            self.payment_type_input.addItem(payment_type, payment_type)
        self._make_compact_combo(self.payment_type_input, 76)
        self.payment_type_input.currentIndexChanged.connect(self._apply_filter)

        self.balance_status_input = QComboBox()
        for balance_status in [
            self.BALANCE_ALL,
            self.BALANCE_PAID,
            self.BALANCE_DEBT,
            self.BALANCE_OVERPAID,
            self.BALANCE_NO_ACTS,
        ]:
            self.balance_status_input.addItem(balance_status, balance_status)
        self._make_compact_combo(self.balance_status_input, 82)
        self.balance_status_input.currentIndexChanged.connect(self._apply_filter)

        self.visibility_input = QComboBox()
        for visibility in [self.VISIBILITY_ACTIVE, self.VISIBILITY_ALL, self.VISIBILITY_DELETED]:
            self.visibility_input.addItem(visibility, visibility)
        self._make_compact_combo(self.visibility_input, 90)
        self.visibility_input.currentIndexChanged.connect(lambda *_: self.reload())

        self.create_button = self._toolbar_button("Создать", "Создать новый договор")
        self.clone_button = self._toolbar_button("На основе", "Создать договор на основе выбранного")
        self.edit_button = self._toolbar_button("Редактировать", "Редактировать выбранный договор")
        self.open_button = self._toolbar_button("Открыть", "Открыть карточку выбранного договора")
        self.delete_button = self._toolbar_button("Удалить", "Удалить выбранный договор")
        self.refresh_button = self._toolbar_button("Обновить", "Обновить список договоров")
        self.reset_filters_button = self._toolbar_button("Сбросить фильтры", "Сбросить все фильтры списка")
        set_button_icon(self.create_button, ICON_NEW)
        set_button_icon(self.clone_button, ICON_CONTRACT)
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.open_button, ICON_OPEN)
        set_button_icon(self.delete_button, ICON_DELETE)
        set_button_icon(self.refresh_button, ICON_REFRESH)
        set_button_icon(self.reset_filters_button, ICON_RESET)

        self.create_button.clicked.connect(self.create_contract)
        self.clone_button.clicked.connect(self._clone_contract)
        self.edit_button.clicked.connect(self._edit_contract)
        self.open_button.clicked.connect(self._open_contract)
        self.delete_button.clicked.connect(self._delete_contract)
        self.refresh_button.clicked.connect(self.reload)
        self.reset_filters_button.clicked.connect(self._reset_filters)

        toolbar = make_toolbar()
        for button in [self.create_button, self.clone_button, self.edit_button, self.open_button, self.delete_button]:
            toolbar.addWidget(button)
        toolbar.addSeparator()
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.reset_filters_button)

        self.period_group = self._filter_group("Период")
        self.period_layout = QGridLayout(self.period_group)
        self.period_layout.setContentsMargins(8, 12, 8, 6)
        self.period_layout.setHorizontalSpacing(5)
        self.period_layout.setVerticalSpacing(4)
        self.period_type_label = QLabel("Тип")
        self.period_from_label = QLabel("с")
        self.period_to_label = QLabel("по")
        self.period_from_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.period_to_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.period_layout.addWidget(self.period_type_label, 0, 0)
        self.period_layout.addWidget(self.period_input, 0, 1)
        self.period_layout.addWidget(self.period_from_label, 0, 2)
        self.period_layout.addWidget(self.date_from_input, 0, 3)
        self.period_layout.addWidget(self.period_to_label, 0, 4)
        self.period_layout.addWidget(self.date_to_input, 0, 5)
        self.period_layout.setColumnStretch(1, 1)
        self.period_layout.setColumnStretch(3, 1)
        self.period_layout.setColumnStretch(5, 1)

        self.params_group = self._filter_group("Фильтры")
        self.params_layout = QGridLayout(self.params_group)
        self.params_layout.setContentsMargins(8, 12, 8, 6)
        self.params_layout.setHorizontalSpacing(5)
        self.params_layout.setVerticalSpacing(4)
        self.payment_label = QLabel("Оплата")
        self.balance_label = QLabel("Баланс")
        self.visibility_label = QLabel("Видимость")
        self.params_layout.addWidget(self.payment_label, 0, 0)
        self.params_layout.addWidget(self.payment_type_input, 0, 1)
        self.params_layout.addWidget(self.balance_label, 0, 2)
        self.params_layout.addWidget(self.balance_status_input, 0, 3)
        self.params_layout.addWidget(self.visibility_label, 0, 4)
        self.params_layout.addWidget(self.visibility_input, 0, 5)
        self.params_layout.setColumnStretch(1, 1)
        self.params_layout.setColumnStretch(3, 1)
        self.params_layout.setColumnStretch(5, 1)

        self.compact_filters_group = self._filter_group("Период и фильтры")
        self.compact_filters_layout = QGridLayout(self.compact_filters_group)
        self.compact_filters_layout.setContentsMargins(8, 12, 8, 6)
        self.compact_filters_layout.setHorizontalSpacing(5)
        self.compact_filters_layout.setVerticalSpacing(4)

        filters_panel = QWidget()
        filters_panel.setMinimumWidth(0)
        filters_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.filters_layout = QGridLayout(filters_panel)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setHorizontalSpacing(6)
        self.filters_layout.setVerticalSpacing(4)
        self._set_filters_layout(stacked=False)

        self.table = QTableView()
        self.table.setMinimumWidth(0)
        self.table.setModel(self.proxy_model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._open_contract)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.selectionModel().selectionChanged.connect(self._update_selection)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(36)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setSortIndicatorShown(True)
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 230)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 72)
        self.table.setColumnWidth(6, 140)
        self.table.setColumnWidth(7, 145)
        self.table.setColumnWidth(8, 110)
        self.table.setColumnWidth(9, 100)
        self.table.setColumnWidth(10, 105)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 600;")
        self.details_label = QLabel("Выберите договор")
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
        layout.addWidget(toolbar)
        layout.addWidget(filters_panel)
        layout.addWidget(self.search_input)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.details_label)
        self.setLayout(layout)

        self._setup_shortcuts()
        self._apply_period_preset(self.PERIOD_LAST_3_MONTHS)
        self.reload()

    def reload(self) -> None:
        """Reload active contracts from the service and re-apply UI filters."""
        selected = self._selected_contract()
        if selected is not None:
            self.last_focused_contract_id = selected.id
        include_deleted = self.visibility_input.currentData() != self.VISIBILITY_ACTIVE
        self.contracts = self.contract_service.list_contracts({"include_deleted": include_deleted})
        self.summaries = self.contract_service.list_contract_summaries(include_deleted=include_deleted)
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply period and search filters, then push rows into the table model."""
        query = self.search_input.text().strip().lower()
        date_from, date_to = self._date_range()
        contracts = [
            contract
            for contract in self.contracts
            if self._is_in_date_range(contract, date_from, date_to)
            and (not query or query in self._contract_text(contract))
            and self._matches_visibility(contract)
            and self._matches_payment_type(contract)
            and self._matches_balance_status(contract)
        ]

        self.model.set_contracts(contracts, self.summaries)
        if self._select_last_on_next_filter:
            self._select_last_visible_contract()
            self._select_last_on_next_filter = False
        else:
            self._restore_focus()
        self.summary_label.setText(
            f"Показано: {len(contracts)} из {len(self.contracts)}" if self._has_active_filters() else f"Всего договоров: {len(contracts)}"
        )
        self._update_selection()

    def _contract_text(self, contract: Contract) -> str:
        """Return text used for the quick in-memory registry search."""
        return " ".join(
            [
                contract.contract_number or "",
                contract.patient_name or "",
                contract.patient_phone or "",
                contract.birth_history_number or "",
                contract.category or "",
                contract.comments or "",
            ]
        ).lower()

    def _selected_contract(self) -> Contract | None:
        """Return the selected contract, mapping the sorted proxy row to source data."""
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        source_index = self.proxy_model.mapToSource(indexes[0])
        return self.model.contract_at(source_index.row())

    def create_contract(self) -> None:
        """Open an empty contract dialog and create a new contract."""
        dialog = ContractDialog()
        if dialog.exec_() != ContractDialog.Accepted:
            return

        try:
            contract = self.contract_service.create_contract(dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        self.last_focused_contract_id = contract.id
        self.reload()

    def _edit_contract(self, *args) -> None:
        """Edit the currently selected contract and keep focus on it afterwards."""
        contract = self._selected_contract()
        if contract is None:
            self._show_error("Выберите договор")
            return
        if contract.deleted:
            self._show_error("Удаленный договор нельзя редактировать")
            return
        self.last_focused_contract_id = contract.id

        dialog = ContractDialog(contract)
        if dialog.exec_() != ContractDialog.Accepted:
            self.focus_contract(contract.id)
            return

        try:
            self.contract_service.update_contract(contract.id, dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        self.reload()

    def _clone_contract(self, *args) -> None:
        """Create a new contract using patient data from the selected contract."""
        source = self._selected_contract()
        if source is None:
            self._show_error("Выберите договор")
            return

        dialog = ContractDialog(source_contract=source)
        if dialog.exec_() != ContractDialog.Accepted:
            return

        try:
            contract = self.contract_service.create_contract(dialog.data(), self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        self.last_focused_contract_id = contract.id
        self.reload()

    def _open_contract(self, *args) -> None:
        """Open details for the selected contract."""
        contract = self._selected_contract()
        if contract is None:
            self._show_error("Выберите договор")
            return
        if contract.deleted:
            self._show_error("Удаленный договор нельзя открыть")
            return
        self.last_focused_contract_id = contract.id
        if self.on_open_contract is not None:
            self.on_open_contract(contract.id)
            return
        QMessageBox.information(self, "Договор", f"{contract.contract_number}\n{contract.patient_name}")

    def _print_contract(self) -> None:
        """Render and open the selected contract document from the registry."""
        contract = self._selected_contract()
        if contract is None:
            self._show_error("Выберите договор")
            return
        if contract.deleted:
            self._show_error("Удаленный договор нельзя распечатать")
            return

        try:
            actual_contract = self.contract_service.get_contract(contract.id)
            if actual_contract.service_insurance:
                path = self.docx_service.render_foms_contract(contract.id)
            else:
                path = self.docx_service.render_paid_contract(contract.id)
            self.docx_service.open_document(path)
        except DomainError as exc:
            self._show_error(str(exc))

    def _delete_contract(self) -> None:
        """Soft-delete the selected contract after user confirmation."""
        contract = self._selected_contract()
        if contract is None:
            self._show_error("Выберите договор")
            return
        if contract.deleted:
            self._show_error("Договор уже удален")
            return
        self.last_focused_contract_id = contract.id

        confirmed = QMessageBox.question(
            self,
            "Удалить договор",
            f"Удалить договор {contract.contract_number}?\nСвязанные акты и платежи тоже будут скрыты.",
        )
        if confirmed != QMessageBox.Yes:
            return

        try:
            self.contract_service.delete_contract(contract.id, self.current_user)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        self.reload()

    def _open_context_menu(self, position) -> None:
        """Show row actions near the mouse cursor."""
        index = self.table.indexAt(position)
        if index.isValid():
            self.table.selectRow(index.row())
        contract = self._selected_contract()

        menu = QMenu(self)
        create_action = menu.addAction(icon_for(ICON_NEW), "Создать договор")
        clone_action = menu.addAction(icon_for(ICON_CONTRACT), "Создать на основе")
        refresh_action = menu.addAction(icon_for(ICON_REFRESH), "Обновить")
        menu.addSeparator()
        open_action = menu.addAction(icon_for(ICON_OPEN), "Открыть")
        edit_action = menu.addAction(icon_for(ICON_EDIT), "Редактировать")
        print_action = menu.addAction(icon_for(ICON_PRINT), "Печать договора")
        menu.addSeparator()
        delete_action = menu.addAction(icon_for(ICON_DELETE), "Удалить")
        has_contract = contract is not None
        is_deleted = bool(contract and contract.deleted)
        clone_action.setEnabled(has_contract)
        open_action.setEnabled(has_contract and not is_deleted)
        edit_action.setEnabled(has_contract and not is_deleted)
        print_action.setEnabled(has_contract and not is_deleted)
        delete_action.setEnabled(has_contract and not is_deleted)

        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == create_action:
            self.create_contract()
        elif action == refresh_action:
            self.reload()
        elif action == clone_action:
            self._clone_contract()
        elif action == open_action:
            self._open_contract()
        elif action == edit_action:
            self._edit_contract()
        elif action == print_action:
            self._print_contract()
        elif action == delete_action:
            self._delete_contract()

    def _update_selection(self, *args) -> None:
        """Refresh action availability and the selected-contract summary panel."""
        contract = self._selected_contract()
        has_selection = contract is not None
        is_deleted = bool(contract and contract.deleted)
        self.edit_button.setEnabled(has_selection and not is_deleted)
        self.clone_button.setEnabled(has_selection)
        self.open_button.setEnabled(has_selection and not is_deleted)
        self.delete_button.setEnabled(has_selection and not is_deleted)
        if contract is None:
            self.details_label.setText("Выберите договор")
            return

        deleted_text = " | удален" if contract.deleted else ""
        discharged_text = " | выписана" if contract.discharged else ""
        detail = (
            f"{contract.contract_number} | {contract.patient_name} | тел.: {contract.patient_phone or '-'} | "
            f"история родов: {contract.birth_history_number or '-'}{discharged_text} | {self._payment_type(contract)}{deleted_text}"
        )
        summary = self.summaries.get(contract.id)
        if summary:
            detail += f" | баланс: {summary['balance']} | статус: {self._status_text(contract)}"
        self.details_label.setText(detail)

    def focus_contract(self, contract_id: int | None) -> None:
        """Select and scroll to a contract after returning from another page."""
        self.last_focused_contract_id = contract_id
        self._restore_focus()

    def _restore_focus(self) -> None:
        """Restore focus through the sort proxy after filtering or reloading."""
        if self.last_focused_contract_id is None:
            self._update_selection()
            return
        source_row = self.model.contract_row(self.last_focused_contract_id)
        if source_row < 0:
            self._update_selection()
            return
        source_index = self.model.index(source_row, 0)
        proxy_index = self.proxy_model.mapFromSource(source_index)
        if not proxy_index.isValid():
            self._update_selection()
            return
        self.table.selectRow(proxy_index.row())
        self.table.scrollTo(proxy_index, QTableView.PositionAtCenter)
        self.table.setCurrentIndex(proxy_index)
        self.table.setFocus(Qt.OtherFocusReason)

    def _select_last_visible_contract(self) -> None:
        """Select and scroll to the last visible contract on initial page load."""
        last_row = self.proxy_model.rowCount() - 1
        if last_row < 0:
            self._update_selection()
            return
        proxy_index = self.proxy_model.index(last_row, 0)
        if not proxy_index.isValid():
            self._update_selection()
            return
        source_index = self.proxy_model.mapToSource(proxy_index)
        contract = self.model.contract_at(source_index.row())
        self.last_focused_contract_id = contract.id if contract is not None else None
        self.table.selectRow(last_row)
        self.table.scrollTo(proxy_index, QTableView.PositionAtBottom)
        self.table.setCurrentIndex(proxy_index)
        self.table.setFocus(Qt.OtherFocusReason)

    def _payment_type(self, contract: Contract) -> str:
        if contract.service_insurance:
            return "страховая"
        if contract.service_payed:
            return "платно"
        return "тип оплаты не указан"

    def _setup_shortcuts(self) -> None:
        new_action = QAction(self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.create_contract)
        self.addAction(new_action)

        refresh_action = QAction(self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.reload)
        self.addAction(refresh_action)

        delete_action = QAction(self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.triggered.connect(self._delete_contract)
        self.addAction(delete_action)

        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.search_input.setFocus)

        open_shortcut = QShortcut(QKeySequence("Return"), self.table)
        open_shortcut.activated.connect(self._open_contract)

        reset_search_shortcut = QShortcut(QKeySequence("Esc"), self.search_input)
        reset_search_shortcut.activated.connect(self.search_input.clear)

    def _reset_filters(self) -> None:
        self.search_input.clear()
        self.payment_type_input.setCurrentIndex(self.payment_type_input.findData(self.PAYMENT_ALL))
        self.balance_status_input.setCurrentIndex(self.balance_status_input.findData(self.BALANCE_ALL))
        self.visibility_input.setCurrentIndex(self.visibility_input.findData(self.VISIBILITY_ACTIVE))
        self.period_input.setCurrentIndex(self.period_input.findData(self.PERIOD_LAST_3_MONTHS))
        self._apply_period_preset(self.PERIOD_LAST_3_MONTHS)
        self._apply_filter()

    def _has_active_filters(self) -> bool:
        return (
            bool(self.search_input.text().strip())
            or self.period_input.currentData() != self.PERIOD_LAST_3_MONTHS
            or self.payment_type_input.currentData() != self.PAYMENT_ALL
            or self.balance_status_input.currentData() != self.BALANCE_ALL
            or self.visibility_input.currentData() != self.VISIBILITY_ACTIVE
        )

    def _matches_visibility(self, contract: Contract) -> bool:
        selected = self.visibility_input.currentData()
        if selected == self.VISIBILITY_ALL:
            return True
        if selected == self.VISIBILITY_DELETED:
            return bool(contract.deleted)
        return not bool(contract.deleted)

    def _matches_payment_type(self, contract: Contract) -> bool:
        selected = self.payment_type_input.currentData()
        if selected == self.PAYMENT_ALL:
            return True
        if selected == self.PAYMENT_PAID:
            return bool(contract.service_payed) and not bool(contract.service_insurance)
        if selected == self.PAYMENT_INSURANCE:
            return bool(contract.service_insurance)
        if selected == self.PAYMENT_UNSET:
            return not bool(contract.service_payed) and not bool(contract.service_insurance)
        return True

    def _matches_balance_status(self, contract: Contract) -> bool:
        selected = self.balance_status_input.currentData()
        if selected == self.BALANCE_ALL:
            return True
        return self._status_text(contract) == selected

    def _status_text(self, contract: Contract) -> str:
        if contract.deleted:
            return "Удален"
        summary = self.summaries.get(contract.id, {})
        if summary.get("services_total") == 0 and summary.get("payments_total") == 0:
            return self.BALANCE_NO_ACTS
        status = summary.get("status")
        if status == "debt":
            return self.BALANCE_DEBT
        if status == "overpaid":
            return self.BALANCE_OVERPAID
        if status == "paid":
            return self.BALANCE_PAID
        return ""

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._set_filters_layout(stacked=self.width() < 1040)

    def _set_filters_layout(self, stacked: bool) -> None:
        target = self.compact_filters_group if stacked else self.period_group
        if self._filters_stacked == stacked and self.filters_layout.indexOf(target) >= 0:
            return

        for group in [self.period_group, self.params_group, self.compact_filters_group]:
            self.filters_layout.removeWidget(group)
            group.hide()

        if stacked:
            self._set_compact_filter_controls()
            self.compact_filters_group.show()
            self.filters_layout.addWidget(self.compact_filters_group, 0, 0)
            self.filters_layout.setColumnStretch(0, 1)
            self.filters_layout.setColumnStretch(1, 0)
            self.filters_layout.setRowStretch(0, 1)
            self.filters_layout.setRowStretch(1, 0)
        else:
            self._set_separate_filter_controls()
            self.period_group.show()
            self.params_group.show()
            self.filters_layout.addWidget(self.period_group, 0, 0)
            self.filters_layout.addWidget(self.params_group, 0, 1)
            self.filters_layout.setColumnStretch(0, 1)
            self.filters_layout.setColumnStretch(1, 1)
            self.filters_layout.setColumnStretch(2, 0)
            self.filters_layout.setRowStretch(0, 1)
            self.filters_layout.setRowStretch(1, 0)

        self._filters_stacked = stacked

    def _remove_filter_controls_from_layouts(self) -> None:
        widgets = [
            self.period_type_label,
            self.period_input,
            self.period_from_label,
            self.date_from_input,
            self.period_to_label,
            self.date_to_input,
            self.payment_label,
            self.payment_type_input,
            self.balance_label,
            self.balance_status_input,
            self.visibility_label,
            self.visibility_input,
        ]
        for layout in [self.period_layout, self.params_layout, self.compact_filters_layout]:
            for widget in widgets:
                layout.removeWidget(widget)

    def _set_compact_filter_controls(self) -> None:
        self._remove_filter_controls_from_layouts()
        self.period_from_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.period_to_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.compact_filters_layout.addWidget(self.period_type_label, 0, 0)
        self.compact_filters_layout.addWidget(self.period_input, 0, 1)
        self.compact_filters_layout.addWidget(self.period_from_label, 0, 2)
        self.compact_filters_layout.addWidget(self.date_from_input, 0, 3)
        self.compact_filters_layout.addWidget(self.period_to_label, 0, 4)
        self.compact_filters_layout.addWidget(self.date_to_input, 0, 5)
        self.compact_filters_layout.addWidget(self.payment_label, 1, 0)
        self.compact_filters_layout.addWidget(self.payment_type_input, 1, 1)
        self.compact_filters_layout.addWidget(self.balance_label, 1, 2)
        self.compact_filters_layout.addWidget(self.balance_status_input, 1, 3)
        self.compact_filters_layout.addWidget(self.visibility_label, 1, 4)
        self.compact_filters_layout.addWidget(self.visibility_input, 1, 5)
        self._sync_stacked_filter_columns()

    def _set_separate_filter_controls(self) -> None:
        self._remove_filter_controls_from_layouts()
        self.period_from_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.period_to_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.period_layout.addWidget(self.period_type_label, 0, 0)
        self.period_layout.addWidget(self.period_input, 0, 1)
        self.period_layout.addWidget(self.period_from_label, 0, 2)
        self.period_layout.addWidget(self.date_from_input, 0, 3)
        self.period_layout.addWidget(self.period_to_label, 0, 4)
        self.period_layout.addWidget(self.date_to_input, 0, 5)
        self.params_layout.addWidget(self.payment_label, 0, 0)
        self.params_layout.addWidget(self.payment_type_input, 0, 1)
        self.params_layout.addWidget(self.balance_label, 0, 2)
        self.params_layout.addWidget(self.balance_status_input, 0, 3)
        self.params_layout.addWidget(self.visibility_label, 0, 4)
        self.params_layout.addWidget(self.visibility_input, 0, 5)

    def _toolbar_button(self, text: str, tooltip: str):
        return make_toolbar_button(text, tooltip)

    def _sync_stacked_filter_columns(self) -> None:
        label_pairs = [
            (self.period_type_label, self.payment_label),
            (self.period_from_label, self.balance_label),
            (self.period_to_label, self.visibility_label),
        ]
        for column, pair in zip([0, 2, 4], label_pairs):
            width = max(label.sizeHint().width() for label in pair)
            for label in pair:
                label.setMinimumWidth(width)
            self.period_layout.setColumnMinimumWidth(column, width)
            self.params_layout.setColumnMinimumWidth(column, width)
            self.compact_filters_layout.setColumnMinimumWidth(column, width)

        field_widths = {
            1: max(self.period_input.minimumWidth(), self.payment_type_input.minimumWidth()),
            3: max(self.date_from_input.minimumWidth(), self.balance_status_input.minimumWidth()),
            5: max(self.date_to_input.minimumWidth(), self.visibility_input.minimumWidth()),
        }
        for column, width in field_widths.items():
            self.period_layout.setColumnMinimumWidth(column, width)
            self.params_layout.setColumnMinimumWidth(column, width)
            self.compact_filters_layout.setColumnMinimumWidth(column, width)

    def _filter_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setMinimumWidth(0)
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        group.setStyleSheet(
            "QGroupBox {"
            "background: #f8fafc;"
            "border: 1px solid #d8e2ef;"
            "border-radius: 6px;"
            "color: #1f4f82;"
            "font-weight: 600;"
            "margin-top: 8px;"
            "}"
            "QGroupBox::title { subcontrol-origin: margin; left: 7px; padding: 0 3px; }"
            "QLabel { border: none; background: transparent; color: #475569; }"
            "QComboBox, QDateTimeEdit { background: #ffffff; selection-background-color: #2563eb; selection-color: #ffffff; }"
            "QComboBox QAbstractItemView {"
            "background: #ffffff;"
            "color: #111827;"
            "selection-background-color: #2563eb;"
            "selection-color: #ffffff;"
            "outline: 0;"
            "}"
        )
        return group

    def _make_compact_combo(self, combo: QComboBox, minimum_width: int) -> None:
        combo.setMinimumWidth(minimum_width)
        combo.setMinimumContentsLength(0)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _date_filter_input(self) -> QDateTimeEdit:
        """Create a compact date-time control used by registry period filters."""
        widget = QDateTimeEdit()
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("dd.MM.yyyy")
        widget.setMinimumWidth(88)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return widget

    def _period_changed(self) -> None:
        period = self.period_input.currentData()
        if period != self.PERIOD_CUSTOM:
            self._apply_period_preset(period)
        self._apply_filter()

    def _date_filter_changed(self) -> None:
        if self._updating_period_controls:
            return
        self.period_input.setCurrentIndex(self.period_input.findData(self.PERIOD_CUSTOM))
        self._apply_filter()

    def _apply_period_preset(self, period: str) -> None:
        now = datetime.now()
        if period == self.PERIOD_LAST_3_MONTHS:
            date_from = now - timedelta(days=90)
            date_to = now
            enabled = True
        elif period == self.PERIOD_LAST_6_MONTHS:
            date_from = now - timedelta(days=180)
            date_to = now
            enabled = True
        elif period == self.PERIOD_CURRENT_YEAR:
            date_from = datetime(now.year, 1, 1)
            date_to = now
            enabled = True
        elif period == self.PERIOD_ALL:
            date_from = datetime(2000, 1, 1)
            date_to = now + timedelta(days=1)
            enabled = False
        else:
            return

        self._updating_period_controls = True
        self.date_from_input.setDateTime(QDateTime(date_from))
        self.date_to_input.setDateTime(QDateTime(date_to))
        self.date_from_input.setEnabled(enabled)
        self.date_to_input.setEnabled(enabled)
        self._updating_period_controls = False

    def _date_range(self) -> tuple[datetime | None, datetime | None]:
        if self.period_input.currentData() == self.PERIOD_ALL:
            return None, None
        return self._to_datetime(self.date_from_input), self._to_datetime(self.date_to_input) + timedelta(days=1)

    def _is_in_date_range(self, contract: Contract, date_from: datetime | None, date_to: datetime | None) -> bool:
        contract_date = self._normalize_datetime(contract.contract_date)
        if date_from is not None and contract_date < date_from:
            return False
        if date_to is not None and contract_date >= date_to:
            return False
        return True

    def _to_datetime(self, widget: QDateTimeEdit) -> datetime:
        qt_value = widget.dateTime()
        converter = getattr(qt_value, "toPyDateTime", None) or getattr(qt_value, "toPython")
        value = converter()
        return self._normalize_datetime(value)

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return value

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Роддом №4", message)
