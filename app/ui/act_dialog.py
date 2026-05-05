from __future__ import annotations

from datetime import datetime, timezone

from app.models import Act, User
from app.services import ActService
from app.services.exceptions import DomainError
from app.ui.act_service_row_dialog import ActServiceRowDialog
from app.ui.act_services_table_model import ActServicesTableModel
from app.ui.icons import ICON_DELETE, ICON_EDIT, ICON_NEW, set_button_icon
from app.ui.med_service_picker_dialog import MedServicePickerDialog
from app.ui.qt import (
    QDateTime,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)


class ActDialog(QDialog):
    def __init__(self, contract_id: int, current_user: User, act: Act | None = None, act_service: ActService | None = None) -> None:
        super().__init__()
        self.contract_id = contract_id
        self.current_user = current_user
        self.act = act
        self.act_service = act_service or ActService()
        self.pending_services: list[dict] = []
        self.setWindowTitle("Акт")
        self.setMinimumSize(760, 520)

        self.number_input = QLineEdit()
        self.date_input = QDateTimeEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDateTime(QDateTime.currentDateTime())
        self.comments_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Номер", self.number_input)
        form.addRow("Дата", self.date_input)
        form.addRow("Комментарий", self.comments_input)

        self.rows_model = ActServicesTableModel()
        self.pending_label = QLabel("")
        self.rows_table = QTableView()
        self.rows_table.setModel(self.rows_model)
        self.rows_table.setSelectionBehavior(QTableView.SelectRows)
        self.rows_table.setSelectionMode(QTableView.SingleSelection)
        self.rows_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.add_service_button = QPushButton("Добавить услугу")
        self.edit_service_button = QPushButton("Изменить строку")
        self.remove_service_button = QPushButton("Удалить строку")
        set_button_icon(self.add_service_button, ICON_NEW)
        set_button_icon(self.edit_service_button, ICON_EDIT)
        set_button_icon(self.remove_service_button, ICON_DELETE)
        self.add_service_button.clicked.connect(self._add_service)
        self.edit_service_button.clicked.connect(self._edit_service)
        self.remove_service_button.clicked.connect(self._remove_service)

        service_toolbar = QHBoxLayout()
        service_toolbar.addWidget(self.add_service_button)
        service_toolbar.addWidget(self.edit_service_button)
        service_toolbar.addWidget(self.remove_service_button)
        service_toolbar.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(service_toolbar)
        layout.addWidget(self.pending_label)
        layout.addWidget(self.rows_table)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        if act is not None:
            self._load_act(act)
        self._update_pending_label()

    def _load_act(self, act: Act) -> None:
        self.number_input.setText(act.number)
        if act.date is not None:
            self.date_input.setDateTime(QDateTime(act.date))
        self.comments_input.setText(act.comments or "")
        self.rows_model.set_rows(self.act_service.list_service_rows(act.id))

    def _save(self) -> None:
        data = {
            "number": self.number_input.text().strip(),
            "date": self._to_datetime(self.date_input),
            "comments": self.comments_input.text().strip() or None,
        }
        try:
            if self.act is None:
                data["services"] = self.pending_services
                self.act_service.create_act(self.contract_id, data, self.current_user)
            else:
                self.act_service.update_act(self.act.id, data, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.accept()

    def _add_service(self) -> None:
        picker = MedServicePickerDialog()
        if picker.exec_() != MedServicePickerDialog.Accepted or picker.selected_service_id is None:
            return

        row_dialog = ActServiceRowDialog()
        if row_dialog.exec_() != ActServiceRowDialog.Accepted:
            return
        data = row_dialog.data()

        if self.act is None:
            data["med_service_id"] = picker.selected_service_id
            self.pending_services.append(data)
            self._update_pending_label()
            return

        try:
            self.act_service.add_service(self.act.id, picker.selected_service_id, data, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.rows_model.set_rows(self.act_service.list_service_rows(self.act.id))

    def _edit_service(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите строку услуги")
            return
        dialog = ActServiceRowDialog(row)
        if dialog.exec_() != ActServiceRowDialog.Accepted:
            return
        try:
            self.act_service.update_service_row(row.id, dialog.data(), self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.rows_model.set_rows(self.act_service.list_service_rows(self.act.id))

    def _remove_service(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите строку услуги")
            return
        try:
            self.act_service.remove_service_row(row.id, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.rows_model.set_rows(self.act_service.list_service_rows(self.act.id))

    def _selected_row(self):
        indexes = self.rows_table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.rows_model.row_at(indexes[0].row())

    def _to_datetime(self, widget: QDateTimeEdit) -> datetime:
        qt_value = widget.dateTime()
        converter = getattr(qt_value, "toPyDateTime", None) or getattr(qt_value, "toPython")
        value = converter()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    def _update_pending_label(self) -> None:
        if self.act is None and self.pending_services:
            self.pending_label.setText(f"Добавлено услуг: {len(self.pending_services)}")
        else:
            self.pending_label.clear()
