from __future__ import annotations

from app.models import Contract
from app.ui.qt import QAbstractTableModel, QModelIndex, Qt


class ContractsTableModel(QAbstractTableModel):
    """Qt table model for the contracts registry.

    The model exposes only cheap contract fields. Financial totals are not
    calculated per row here because that would make large registries sluggish.
    """

    HEADERS = [
        "Номер договора",
        "Дата",
        "Пациент",
        "Дата рождения",
        "История родов",
        "Категория",
        "Телефон",
        "Тип оплаты",
    ]

    def __init__(self, contracts: list[Contract] | None = None, summaries: dict[int, dict] | None = None) -> None:
        super().__init__()
        self.contracts = contracts or []
        self.summaries = summaries or {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return visible contract row count for Qt."""
        if parent.isValid():
            return 0
        return len(self.contracts)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the fixed number of registry columns."""
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Return display and sort values for a contract table cell."""
        if not index.isValid():
            return None

        contract = self.contracts[index.row()]
        if role == Qt.UserRole:
            return self._sort_value(contract, index.column())
        if role != Qt.DisplayRole:
            return None
        values = [
            contract.contract_number,
            self._date_text(contract.contract_date),
            contract.patient_name,
            self._date_text(contract.patient_birth_date),
            contract.birth_history_number or "",
            contract.category or "",
            contract.patient_phone or "",
            self._payment_type(contract),
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Return column captions and row numbers."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def contract_at(self, row: int) -> Contract | None:
        """Return the backing contract for a source-model row."""
        if row < 0 or row >= len(self.contracts):
            return None
        return self.contracts[row]

    def set_contracts(self, contracts: list[Contract], summaries: dict[int, dict]) -> None:
        """Replace table contents and notify connected Qt views."""
        self.beginResetModel()
        self.contracts = contracts
        self.summaries = summaries
        self.endResetModel()

    def contract_row(self, contract_id: int) -> int:
        """Find the source-model row for a contract ID."""
        for index, contract in enumerate(self.contracts):
            if contract.id == contract_id:
                return index
        return -1

    def _date_text(self, value) -> str:
        if value is None:
            return ""
        return value.strftime("%d.%m.%Y")

    def _payment_type(self, contract: Contract) -> str:
        if contract.service_insurance:
            return "Страховая"
        if contract.service_payed:
            return "Платно"
        return ""

    def _sort_value(self, contract: Contract, column: int):
        values = [
            contract.contract_number or "",
            contract.contract_date,
            contract.patient_name or "",
            contract.patient_birth_date,
            contract.birth_history_number or "",
            contract.category or "",
            contract.patient_phone or "",
            self._payment_type(contract),
        ]
        value = values[column]
        if hasattr(value, "timestamp"):
            return value.timestamp()
        return str(value or "").lower()
