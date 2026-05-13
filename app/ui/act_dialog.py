from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models import Act, User
from app.services import ActService
from app.services.exceptions import DomainError
from app.ui.act_service_row_dialog import ActServiceRowDialog
from app.ui.act_services_table_model import ActServicesTableModel
from app.ui.icons import (
    ICON_DELETE,
    ICON_EDIT,
    ICON_NEW,
    ICON_SAVE_PRINT,
    set_button_icon,
    set_dialog_button_icon,
    set_dialog_button_icons,
)
from app.ui.med_service_picker_dialog import MedServicePickerDialog
from app.ui.qt import (
    QAction,
    QDateTime,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QKeySequence,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QShortcut,
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
        self.saved_act_id: int | None = act.id if act is not None else None
        self.print_after_save = False
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
        self.rows_table.doubleClicked.connect(lambda *args: self._edit_service())
        self.rows_table.selectionModel().selectionChanged.connect(self._update_row_actions)

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
        self.buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        self.save_print_button = QPushButton("Сохранить и распечатать")
        set_dialog_button_icons(self.buttons)
        set_dialog_button_icon(self.save_print_button, ICON_SAVE_PRINT)
        self.buttons.addButton(self.save_print_button, QDialogButtonBox.ActionRole)
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        self.save_print_button.clicked.connect(self._save_and_print)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(service_toolbar)
        layout.addWidget(self.pending_label)
        layout.addWidget(self.rows_table)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        self._setup_shortcuts()
        if act is not None:
            self._load_act(act)
        self._update_pending_label()
        self._update_row_actions()

    def _load_act(self, act: Act) -> None:
        self.number_input.setText(act.number)
        if act.date is not None:
            self.date_input.setDateTime(QDateTime(act.date))
        self.comments_input.setText(act.comments or "")
        self.rows_model.set_rows(self.act_service.list_service_rows(act.id))
        self._update_row_actions()

    def _save(self) -> None:
        self._save_data(print_after_save=False)

    def _save_and_print(self) -> None:
        self._save_data(print_after_save=True)

    def _save_data(self, print_after_save: bool = False) -> None:
        data = {
            "number": self.number_input.text().strip(),
            "date": self._to_datetime(self.date_input),
            "comments": self.comments_input.text().strip() or None,
        }
        try:
            if self.act is None:
                data["services"] = self.pending_services
                saved_act = self.act_service.create_act(self.contract_id, data, self.current_user)
                self.saved_act_id = saved_act.id
            else:
                saved_act = self.act_service.update_act(self.act.id, data, self.current_user)
                self.saved_act_id = saved_act.id
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.print_after_save = print_after_save
        self.accept()

    def _add_service(self) -> None:
        picker = MedServicePickerDialog()
        if picker.exec_() != MedServicePickerDialog.Accepted or picker.selected_service_id is None:
            return

        row_dialog = ActServiceRowDialog(service=picker.selected_service)
        if row_dialog.exec_() != ActServiceRowDialog.Accepted:
            return
        data = row_dialog.data()

        if self.act is None:
            data["med_service_id"] = picker.selected_service_id
            data["current_code"] = picker.selected_service.get("code", "") if picker.selected_service else ""
            data["current_name"] = picker.selected_service.get("name", "") if picker.selected_service else ""
            data["unit"] = picker.selected_service.get("unit", "") if picker.selected_service else ""
            self._add_or_increment_pending_service(data)
            self._refresh_pending_rows()
            return

        try:
            self.act_service.add_service(self.act.id, picker.selected_service_id, data, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.rows_model.set_rows(self.act_service.list_service_rows(self.act.id))
        self._update_row_actions()

    def _edit_service(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите строку услуги")
            return
        dialog = ActServiceRowDialog(row)
        if dialog.exec_() != ActServiceRowDialog.Accepted:
            return
        if self.act is None:
            row.update(dialog.data())
            self._refresh_pending_rows()
            return
        try:
            self.act_service.update_service_row(row.id, dialog.data(), self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.rows_model.set_rows(self.act_service.list_service_rows(self.act.id))
        self._update_row_actions()

    def _remove_service(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.warning(self, "Роддом №4", "Выберите строку услуги")
            return
        if self.act is None:
            index = self._selected_row_index()
            if index is not None:
                self.pending_services.pop(index)
                self._refresh_pending_rows()
            return
        try:
            self.act_service.remove_service_row(row.id, self.current_user)
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.rows_model.set_rows(self.act_service.list_service_rows(self.act.id))
        self._update_row_actions()

    def _selected_row(self):
        indexes = self.rows_table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.rows_model.row_at(indexes[0].row())

    def _selected_row_index(self) -> int | None:
        indexes = self.rows_table.selectionModel().selectedRows()
        if not indexes:
            return None
        return indexes[0].row()

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

    def _refresh_pending_rows(self) -> None:
        self.rows_model.set_rows(self.pending_services)
        self._update_pending_label()
        self._update_row_actions()

    def _add_or_increment_pending_service(self, data: dict) -> None:
        matching_row = self._find_pending_service(data["med_service_id"], data.get("discount"))
        if matching_row is None:
            self.pending_services.append(data)
            return
        matching_row["count"] = int(matching_row.get("count") or 0) + int(data.get("count") or 0)

    def _find_pending_service(self, med_service_id: int, discount) -> dict | None:
        expected_discount = Decimal(str(discount or 0))
        for row in self.pending_services:
            if row.get("med_service_id") == med_service_id and Decimal(str(row.get("discount") or 0)) == expected_discount:
                return row
        return None

    def _setup_shortcuts(self) -> None:
        add_action = QAction(self)
        add_action.setShortcut(QKeySequence("Ctrl+N"))
        add_action.triggered.connect(self._add_service)
        self.addAction(add_action)

        save_action = QAction(self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._save)
        self.addAction(save_action)

        delete_action = QAction(self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.triggered.connect(self._remove_service)
        self.addAction(delete_action)

        edit_shortcut = QShortcut(QKeySequence("Return"), self.rows_table)
        edit_shortcut.activated.connect(self._edit_service)

    def _update_row_actions(self, *args) -> None:
        has_selection = self._selected_row() is not None
        self.edit_service_button.setEnabled(has_selection)
        self.remove_service_button.setEnabled(has_selection)
