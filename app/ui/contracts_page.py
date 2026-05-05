from __future__ import annotations

from datetime import datetime, timedelta

from app.models import Contract, User
from app.services import ContractService
from app.services.exceptions import DomainError
from app.ui.contract_dialog import ContractDialog
from app.ui.contracts_table_model import ContractsTableModel
from app.ui.icons import ICON_CONTRACT, ICON_DELETE, ICON_EDIT, ICON_NEW, ICON_OPEN, icon_for, set_button_icon
from app.ui.qt import (
    QHBoxLayout,
    QHeaderView,
    QComboBox,
    QDateTime,
    QDateTimeEdit,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSortFilterProxyModel,
    QTableView,
    QVBoxLayout,
    QWidget,
    Qt,
)


class ContractsPage(QWidget):
    """Main contract registry page.

    The page keeps all active contracts in memory and applies lightweight client-side
    filters for the current workload. Expensive balance calculations are deliberately
    limited to the selected contract, so a large registry can still be searched and
    sorted quickly.
    """

    PERIOD_LAST_3_MONTHS = "Последние 3 месяца"
    PERIOD_LAST_6_MONTHS = "Последние 6 месяцев"
    PERIOD_CURRENT_YEAR = "Текущий год"
    PERIOD_ALL = "Все договоры"
    PERIOD_CUSTOM = "Произвольный период"

    def __init__(self, current_user: User, contract_service: ContractService | None = None, on_open_contract=None) -> None:
        super().__init__()
        self.current_user = current_user
        self.contract_service = contract_service or ContractService()
        self.on_open_contract = on_open_contract
        self.contracts: list[Contract] = []
        self.model = ContractsTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(Qt.UserRole)
        self.last_focused_contract_id: int | None = None
        self._updating_period_controls = False

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
        self.period_input.currentIndexChanged.connect(self._period_changed)

        self.date_from_input = self._date_filter_input()
        self.date_to_input = self._date_filter_input()
        self.date_from_input.dateTimeChanged.connect(self._date_filter_changed)
        self.date_to_input.dateTimeChanged.connect(self._date_filter_changed)

        self.create_button = QPushButton("Создать")
        self.clone_button = QPushButton("На основе")
        self.edit_button = QPushButton("Редактировать")
        self.open_button = QPushButton("Открыть")
        self.delete_button = QPushButton("Удалить")
        set_button_icon(self.create_button, ICON_NEW)
        set_button_icon(self.clone_button, ICON_CONTRACT)
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.open_button, ICON_OPEN)
        set_button_icon(self.delete_button, ICON_DELETE)

        self.create_button.clicked.connect(self.create_contract)
        self.clone_button.clicked.connect(self._clone_contract)
        self.edit_button.clicked.connect(self._edit_contract)
        self.open_button.clicked.connect(self._open_contract)
        self.delete_button.clicked.connect(self._delete_contract)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.create_button)
        toolbar.addWidget(self.clone_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addStretch()

        period_toolbar = QHBoxLayout()
        period_toolbar.addWidget(QLabel("Период"))
        period_toolbar.addWidget(self.period_input)
        period_toolbar.addWidget(QLabel("с"))
        period_toolbar.addWidget(self.date_from_input)
        period_toolbar.addWidget(QLabel("по"))
        period_toolbar.addWidget(self.date_to_input)
        period_toolbar.addStretch()

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._open_contract)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.selectionModel().selectionChanged.connect(self._update_selection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)

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
        layout.addLayout(toolbar)
        layout.addLayout(period_toolbar)
        layout.addWidget(self.search_input)
        layout.addWidget(self.table)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.details_label)
        self.setLayout(layout)

        self._apply_period_preset(self.PERIOD_LAST_3_MONTHS)
        self.reload()

    def reload(self) -> None:
        """Reload active contracts from the service and re-apply UI filters."""
        self.contracts = self.contract_service.list_contracts()
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
        ]

        self.model.set_contracts(contracts, {})
        self._restore_focus()
        self.summary_label.setText(
            f"Показано: {len(contracts)} из {len(self.contracts)}" if query else f"Всего договоров: {len(contracts)}"
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
        self.last_focused_contract_id = contract.id
        if self.on_open_contract is not None:
            self.on_open_contract(contract.id)
            return
        QMessageBox.information(self, "Договор", f"{contract.contract_number}\n{contract.patient_name}")

    def _delete_contract(self) -> None:
        """Soft-delete the selected contract after user confirmation."""
        contract = self._selected_contract()
        if contract is None:
            self._show_error("Выберите договор")
            return
        self.last_focused_contract_id = contract.id

        confirmed = QMessageBox.question(self, "Удалить договор", f"Удалить договор {contract.contract_number}?")
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
        menu.addSeparator()
        open_action = menu.addAction(icon_for(ICON_OPEN), "Открыть")
        edit_action = menu.addAction(icon_for(ICON_EDIT), "Редактировать")
        delete_action = menu.addAction(icon_for(ICON_DELETE), "Удалить")
        has_contract = contract is not None
        clone_action.setEnabled(has_contract)
        open_action.setEnabled(has_contract)
        edit_action.setEnabled(has_contract)
        delete_action.setEnabled(has_contract)

        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == create_action:
            self.create_contract()
        elif action == clone_action:
            self._clone_contract()
        elif action == open_action:
            self._open_contract()
        elif action == edit_action:
            self._edit_contract()
        elif action == delete_action:
            self._delete_contract()

    def _update_selection(self, *args) -> None:
        """Refresh action availability and the selected-contract summary panel."""
        contract = self._selected_contract()
        has_selection = contract is not None
        self.edit_button.setEnabled(has_selection)
        self.clone_button.setEnabled(has_selection)
        self.open_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        if contract is None:
            self.details_label.setText("Выберите договор")
            return

        detail = (
            f"{contract.contract_number} | {contract.patient_name} | тел.: {contract.patient_phone or '-'} | "
            f"история родов: {contract.birth_history_number or '-'} | {self._payment_type(contract)}"
        )
        try:
            summary = self.contract_service.get_contract_summary(contract.id)
            detail += " | баланс: {balance} | статус: {status}".format(**summary)
        except DomainError:
            pass
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

    def _payment_type(self, contract: Contract) -> str:
        if contract.service_insurance:
            return "страховая"
        if contract.service_payed:
            return "платно"
        return "тип оплаты не указан"

    def _date_filter_input(self) -> QDateTimeEdit:
        """Create a compact date-time control used by registry period filters."""
        widget = QDateTimeEdit()
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("dd.MM.yyyy")
        widget.setMinimumWidth(132)
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
