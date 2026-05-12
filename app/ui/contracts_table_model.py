from __future__ import annotations

from app.models import Contract
from app.ui.qt import QAbstractTableModel, QBrush, QColor, QFont, QModelIndex, Qt


class ContractsTableModel(QAbstractTableModel):
    """Qt table model for the contracts registry.

    The model displays cheap contract fields plus precomputed summaries passed
    in by the page.
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
        "Баланс",
        "Статус",
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
        if role == Qt.ForegroundRole and contract.deleted:
            return QBrush(QColor("#777777"))
        if role == Qt.ForegroundRole and index.column() in {8, 9}:
            return self._status_brush(contract)
        if role == Qt.FontRole and (contract.deleted or index.column() in {8, 9}):
            font = QFont()
            font.setBold(index.column() in {8, 9})
            font.setStrikeOut(contract.deleted)
            return font
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
            self._balance_text(contract),
            self._status_text(contract),
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
            self._balance_sort_value(contract),
            self._status_text(contract),
        ]
        value = values[column]
        if hasattr(value, "timestamp"):
            return value.timestamp()
        if isinstance(value, (int, float)):
            return value
        return str(value or "").lower()

    def _balance_text(self, contract: Contract) -> str:
        summary = self.summaries.get(contract.id, {})
        balance = summary.get("balance")
        if balance is None:
            return ""
        return str(balance)

    def _balance_sort_value(self, contract: Contract):
        summary = self.summaries.get(contract.id, {})
        balance = summary.get("balance")
        if balance is None:
            return 0
        return float(balance)

    def _status_text(self, contract: Contract) -> str:
        if contract.deleted:
            return "Удален"
        summary = self.summaries.get(contract.id, {})
        services_total = summary.get("services_total")
        payments_total = summary.get("payments_total")
        if services_total == 0 and payments_total == 0:
            return "Без актов"
        status = summary.get("status")
        if status == "debt":
            return "Долг"
        if status == "overpaid":
            return "Переплата"
        if status == "paid":
            return "Оплачен"
        return ""

    def _status_brush(self, contract: Contract):
        status = self._status_text(contract)
        if status == "Долг":
            return QBrush(QColor("#b00020"))
        if status == "Переплата":
            return QBrush(QColor("#2f5fb3"))
        if status == "Оплачен":
            return QBrush(QColor("#237a3b"))
        return QBrush(QColor("#666666"))
