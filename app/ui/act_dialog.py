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
    QCheckBox,
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
        self.read_only = self._is_read_only_act(act)
        self.setWindowTitle(self._dialog_title(act))
        self.setMinimumSize(860, 560)

        title = QLabel(self._dialog_title(act))
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        subtitle = QLabel(f"Договор #{contract_id}. Добавьте услуги, проверьте итог и сохраните акт.")
        subtitle.setStyleSheet("color: #666;")
        if self.read_only:
            subtitle.setText(f"Договор #{contract_id}. Акт оплачен и открыт только для просмотра.")
        self.read_only_label = QLabel("По этому акту уже создан платеж. Чтобы изменить акт, сначала распроведите платеж.")
        self.read_only_label.setStyleSheet(
            "QLabel { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px; "
            "padding: 8px 10px; color: #9a3412; font-weight: 600; }"
        )
        self.read_only_label.setWordWrap(True)
        self.read_only_label.setVisible(self.read_only)

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Номер акта")
        self.number_input.textChanged.connect(self._update_dialog_state)
        self.date_input = QDateTimeEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDateTime(QDateTime.currentDateTime())
        self.comments_input = QLineEdit()
        self.comments_input.setPlaceholderText("Комментарий к акту")
        self.add_payment_checkbox = QCheckBox("Добавить платеж на сумму акта")
        self.add_payment_checkbox.setToolTip("После сохранения будет создан платеж с суммой всех строк акта.")
        self.discharge_checkbox = QCheckBox("Отметить договор как выписанный")
        self.discharge_checkbox.setToolTip("После сохранения договор будет отмечен как выписанный.")

        form = QFormLayout()
        form.addRow("Номер", self.number_input)
        form.addRow("Дата", self.date_input)
        form.addRow("Комментарий", self.comments_input)
        form.addRow("", self.add_payment_checkbox)
        form.addRow("", self.discharge_checkbox)

        self.rows_model = ActServicesTableModel()
        self.pending_label = QLabel("")
        self.pending_label.setStyleSheet("font-weight: 600; color: #334155;")
        self.empty_label = QLabel("Услуги не добавлены. Нажмите «Добавить услугу», чтобы заполнить акт.")
        self.empty_label.setStyleSheet("color: #777; padding: 8px 0;")
        self.empty_label.setWordWrap(True)
        self.rows_table = QTableView()
        self.rows_table.setModel(self.rows_model)
        self.rows_table.setSelectionBehavior(QTableView.SelectRows)
        self.rows_table.setSelectionMode(QTableView.SingleSelection)
        header = self.rows_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setStretchLastSection(False)
        self.rows_table.setColumnWidth(0, 80)
        self.rows_table.setColumnWidth(2, 58)
        self.rows_table.setColumnWidth(3, 96)
        self.rows_table.setColumnWidth(4, 76)
        self.rows_table.setColumnWidth(5, 78)
        self.rows_table.setColumnWidth(6, 104)
        self.rows_table.setColumnWidth(7, 150)
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
        self.buttons.button(QDialogButtonBox.Cancel).setText("Закрыть" if self.read_only else "Отмена")
        self.save_print_button = QPushButton("Сохранить и распечатать")
        set_dialog_button_icons(self.buttons)
        set_dialog_button_icon(self.save_print_button, ICON_SAVE_PRINT)
        self.buttons.addButton(self.save_print_button, QDialogButtonBox.ActionRole)
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        self.save_print_button.clicked.connect(self._save_and_print)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.read_only_label)
        layout.addLayout(form)
        layout.addLayout(service_toolbar)
        layout.addWidget(self.pending_label)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.rows_table)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        self._setup_shortcuts()
        if act is not None:
            self._load_act(act)
        else:
            self._load_next_act_number()
        self._apply_read_only_state()
        self._update_dialog_state()

    def _dialog_title(self, act: Act | None) -> str:
        if self.read_only:
            return "Просмотр акта"
        return "Редактирование акта" if act is not None else "Новый акт"

    def _is_read_only_act(self, act: Act | None) -> bool:
        if act is None:
            return False
        try:
            return self.act_service.is_act_paid(act.id)
        except DomainError:
            return False

    def _load_act(self, act: Act) -> None:
        self.number_input.setText(act.number)
        if act.date is not None:
            self.date_input.setDateTime(QDateTime(act.date))
        self.comments_input.setText(act.comments or "")
        self.rows_model.set_rows(self.act_service.list_service_rows(act.id))
        self._update_dialog_state()

    def _load_next_act_number(self) -> None:
        try:
            self.number_input.setText(self.act_service.next_act_number(self.contract_id))
        except DomainError:
            self.number_input.clear()
            self.number_input.setPlaceholderText("Сформируется автоматически")

    def _save(self) -> None:
        self._save_data(print_after_save=False)

    def _save_and_print(self) -> None:
        self._save_data(print_after_save=True)

    def _save_data(self, print_after_save: bool = False) -> None:
        if not self._can_save():
            QMessageBox.warning(self, "Роддом №4", self._save_block_reason())
            return
        data = {
            "number": self.number_input.text().strip(),
            "date": self._to_datetime(self.date_input),
            "comments": self.comments_input.text().strip() or None,
        }
        try:
            if self.act is None:
                data["services"] = self.pending_services
                saved_act = self.act_service.create_act(
                    self.contract_id,
                    data,
                    self.current_user,
                    add_payment=self.add_payment_checkbox.isChecked(),
                    mark_discharged=self.discharge_checkbox.isChecked(),
                )
                self.saved_act_id = saved_act.id
            else:
                saved_act = self.act_service.update_act(
                    self.act.id,
                    data,
                    self.current_user,
                    add_payment=self.add_payment_checkbox.isChecked(),
                    mark_discharged=self.discharge_checkbox.isChecked(),
                )
                self.saved_act_id = saved_act.id
        except DomainError as exc:
            QMessageBox.warning(self, "Роддом №4", str(exc))
            return
        self.print_after_save = print_after_save
        self.accept()

    def _add_service(self) -> None:
        if self.read_only:
            QMessageBox.information(self, "Роддом №4", self._read_only_reason())
            return
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
        self._update_dialog_state()

    def _edit_service(self) -> None:
        if self.read_only:
            QMessageBox.information(self, "Роддом №4", self._read_only_reason())
            return
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
        self._update_dialog_state()

    def _remove_service(self) -> None:
        if self.read_only:
            QMessageBox.information(self, "Роддом №4", self._read_only_reason())
            return
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
        self._update_dialog_state()

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

    def _refresh_pending_rows(self) -> None:
        self.rows_model.set_rows(self.pending_services)
        self._update_dialog_state()

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

    def _apply_read_only_state(self) -> None:
        if not self.read_only:
            return

        self.number_input.setReadOnly(True)
        self.date_input.setEnabled(False)
        self.comments_input.setReadOnly(True)
        self.add_payment_checkbox.setEnabled(False)
        self.discharge_checkbox.setEnabled(False)
        self.add_service_button.setEnabled(False)
        self.edit_service_button.setEnabled(False)
        self.remove_service_button.setEnabled(False)
        self.buttons.button(QDialogButtonBox.Save).setVisible(False)
        self.save_print_button.setVisible(False)

    def _update_row_actions(self, *args) -> None:
        if self.read_only:
            self.edit_service_button.setEnabled(False)
            self.remove_service_button.setEnabled(False)
            return
        has_selection = self._selected_row() is not None
        self.edit_service_button.setEnabled(has_selection)
        self.remove_service_button.setEnabled(has_selection)

    def _update_dialog_state(self, *args) -> None:
        self._update_row_actions()
        rows_count, quantity, total = self._services_summary()
        self.pending_label.setText(
            f"Услуг: {rows_count} | Количество: {self._format_decimal(quantity)} | Итого: {self._format_money(total)}"
        )
        has_rows = rows_count > 0
        self.empty_label.setVisible(not has_rows)
        self.rows_table.setVisible(has_rows)

        can_save = self._can_save()
        save_button = self.buttons.button(QDialogButtonBox.Save)
        save_button.setEnabled(can_save)
        self.save_print_button.setEnabled(can_save)
        reason = "" if can_save else self._save_block_reason()
        save_button.setToolTip(reason)
        self.save_print_button.setToolTip(reason)

    def _can_save(self) -> bool:
        if self.read_only:
            return False
        if self.act is not None and not self.number_input.text().strip():
            return False
        if self.act is None and not self.pending_services:
            return False
        return True

    def _save_block_reason(self) -> str:
        if self.read_only:
            return self._read_only_reason()
        if self.act is not None and not self.number_input.text().strip():
            return "Укажите номер акта."
        if self.act is None and not self.pending_services:
            return "Добавьте хотя бы одну услугу."
        return ""

    def _read_only_reason(self) -> str:
        return "По этому акту уже создан платеж. Акт доступен только для просмотра."

    def _services_summary(self) -> tuple[int, Decimal, Decimal]:
        quantity = Decimal("0")
        total = Decimal("0")
        for row in self.rows_model.rows:
            price = self._row_decimal(row, "price")
            count = self._row_decimal(row, "count")
            discount = self._row_decimal(row, "discount")
            quantity += count
            total += price * count * (Decimal("1") - discount / Decimal("100"))
        return len(self.rows_model.rows), quantity, total

    def _row_decimal(self, row, name: str) -> Decimal:
        if isinstance(row, dict):
            value = row.get(name)
        else:
            value = getattr(row, name, None)
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    def _format_decimal(self, value: Decimal) -> str:
        if value == int(value):
            return str(int(value))
        return str(value.normalize())

    def _format_money(self, value: Decimal) -> str:
        return str(value.quantize(Decimal("0.01")))
