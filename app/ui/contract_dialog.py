from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal

from app.models import Contract
from app.ui.qt import (
    QCheckBox,
    QComboBox,
    QDateTime,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTextEdit,
    Qt,
    QVBoxLayout,
    QWidget,
)


class ContractDialog(QDialog):
    CATEGORIES = ["Категория 1", "Категория 2"]
    DEFAULT_CHILDBIRTH_PREPAY = Decimal("22000")
    DEFAULT_INPATIENT_PREPAY = Decimal("5000")

    def __init__(self, contract: Contract | None = None, source_contract: Contract | None = None) -> None:
        super().__init__()
        self.contract = contract
        self.source_contract = source_contract
        self.setWindowTitle("Новый договор" if contract is None else "Редактирование договора")
        self.setMinimumSize(820, 640)

        self._create_widgets()
        self._configure_widgets()
        self._build_layout()
        self._connect_signals()

        if contract is not None:
            self._load_contract(contract)
        elif source_contract is not None:
            self._load_from_source(source_contract)

        self._set_delegate_enabled(self.delegate_enabled.isChecked())
        self.discharge_date.setEnabled(self.discharged.isChecked())
        self._sync_prepay_inputs()

    def _create_widgets(self) -> None:
        self.contract_number = QLineEdit()
        self.contract_date = self._date_time_edit()
        self.category = QComboBox()
        for category in self.CATEGORIES:
            self.category.addItem(category, category)
        self.category.setCurrentText("Категория 2")

        self.patient_name = QLineEdit()
        self.patient_birth_date = self._date_time_edit()
        self.birth_history_number = QLineEdit()
        self.patient_reg_address = QLineEdit()
        self.patient_live_address = QLineEdit()
        self.patient_phone = QLineEdit()
        self.patient_passport_issued_by = QLineEdit()
        self.patient_passport_issued_code = QLineEdit()
        self.patient_passport_series = QLineEdit()
        self.patient_passport_date = self._date_time_edit()

        self.delegate_enabled = QCheckBox("Договор оформляет представитель")
        self.delegate_name = QLineEdit()
        self.delegate_birth_date = self._date_time_edit()
        self.delegate_reg_address = QLineEdit()
        self.delegate_live_address = QLineEdit()
        self.delegate_phone = QLineEdit()
        self.delegate_passport_issued_by = QLineEdit()
        self.delegate_passport_issued_code = QLineEdit()
        self.delegate_passport_series = QLineEdit()
        self.delegate_passport_date = self._date_time_edit()

        self.inpatient_treatment = QCheckBox("Стационарное лечение")
        self.childbirth = QCheckBox("Роды")
        self.prepay_inpatient_treatment = self._money_input()
        self.prepay_childbirth = self._money_input()
        self.service_payed = QCheckBox("Платная услуга")
        self.service_insurance = QCheckBox("Страховая услуга")
        self.service_insurance_number = QLineEdit()

        self.discharged = QCheckBox("Пациентка выписана")
        self.discharge_date = self._date_time_edit()
        self.comments = QTextEdit()

    def _configure_widgets(self) -> None:
        self.contract_number.setPlaceholderText("Например: 2026-001")
        self.patient_name.setPlaceholderText("Фамилия Имя Отчество")
        self.birth_history_number.setPlaceholderText("Номер истории родов")
        self.patient_reg_address.setPlaceholderText("Адрес по регистрации")
        self.patient_live_address.setPlaceholderText("Фактический адрес")
        self.patient_phone.setPlaceholderText("+7...")
        self.patient_passport_issued_by.setPlaceholderText("Кем выдан паспорт")
        self.patient_passport_issued_code.setPlaceholderText("000-000")
        self.patient_passport_issued_code.setInputMask("000-000;_")
        self.patient_passport_series.setPlaceholderText("0000 000000")
        self.patient_passport_series.setInputMask("0000 000000;_")

        self.delegate_name.setPlaceholderText("Фамилия Имя Отчество")
        self.delegate_reg_address.setPlaceholderText("Адрес по регистрации")
        self.delegate_live_address.setPlaceholderText("Фактический адрес")
        self.delegate_phone.setPlaceholderText("+7...")
        self.delegate_passport_issued_by.setPlaceholderText("Кем выдан паспорт")
        self.delegate_passport_issued_code.setPlaceholderText("000-000")
        self.delegate_passport_issued_code.setInputMask("000-000;_")
        self.delegate_passport_series.setPlaceholderText("0000 000000")
        self.delegate_passport_series.setInputMask("0000 000000;_")

        self.service_insurance_number.setPlaceholderText("Номер полиса/страхового случая")
        self.comments.setPlaceholderText("Внутренний комментарий к договору")
        self.comments.setFixedHeight(90)

        for input_widget in self.findChildren(QLineEdit):
            input_widget.setMinimumWidth(240)

    def _build_layout(self) -> None:
        self.form = self._scrollable(self._build_contract_form())

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        title = QLabel("Договор")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        subtitle = QLabel("Заполните параметры договора в сгруппированных блоках. Обязательные поля проверяются при сохранении.")
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def _build_contract_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self._build_contract_section())
        layout.addWidget(self._build_patient_section())
        layout.addWidget(self._build_delegate_section())
        layout.addWidget(self._build_payment_section())
        layout.addWidget(self._build_discharge_section())
        layout.addStretch()
        page.setLayout(layout)
        return page

    def _build_contract_section(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(
            self._group(
                "Реквизиты",
                [
                    ("Номер договора", self.contract_number),
                    ("Дата договора", self.contract_date),
                    ("Категория", self.category),
                    ("История родов", self.birth_history_number),
                ],
            )
        )
        page.setLayout(layout)
        return page

    def _build_patient_section(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(
            self._group(
                "Пациент",
                [
                    ("ФИО", self.patient_name),
                    ("Дата рождения", self.patient_birth_date),
                    ("Телефон", self.patient_phone),
                ],
            )
        )
        layout.addWidget(
            self._group(
                "Адреса",
                [
                    ("Регистрация", self.patient_reg_address),
                    ("Проживание", self.patient_live_address),
                ],
            )
        )
        layout.addWidget(
            self._group(
                "Паспорт",
                [
                    ("Серия/номер", self.patient_passport_series),
                    ("Кем выдан", self.patient_passport_issued_by),
                    ("Код подразделения", self.patient_passport_issued_code),
                    ("Дата выдачи", self.patient_passport_date),
                ],
            )
        )
        page.setLayout(layout)
        return page

    def _build_delegate_section(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.delegate_enabled)
        layout.addWidget(
            self._group(
                "Представитель",
                [
                    ("ФИО", self.delegate_name),
                    ("Дата рождения", self.delegate_birth_date),
                    ("Телефон", self.delegate_phone),
                ],
            )
        )
        layout.addWidget(
            self._group(
                "Адреса представителя",
                [
                    ("Регистрация", self.delegate_reg_address),
                    ("Проживание", self.delegate_live_address),
                ],
            )
        )
        layout.addWidget(
            self._group(
                "Паспорт представителя",
                [
                    ("Серия/номер", self.delegate_passport_series),
                    ("Кем выдан", self.delegate_passport_issued_by),
                    ("Код подразделения", self.delegate_passport_issued_code),
                    ("Дата выдачи", self.delegate_passport_date),
                ],
            )
        )
        page.setLayout(layout)
        return page

    def _build_payment_section(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        service_type = QHBoxLayout()
        service_type.addWidget(self.inpatient_treatment)
        service_type.addWidget(self.childbirth)
        service_type.addStretch()
        service_widget = QWidget()
        service_widget.setLayout(service_type)
        payment_type = QHBoxLayout()
        payment_type.addWidget(self.service_payed)
        payment_type.addWidget(self.service_insurance)
        payment_type.addStretch()
        payment_widget = QWidget()
        payment_widget.setLayout(payment_type)

        layout.addWidget(
            self._group(
                "Тип договора",
                [
                    ("Услуги", service_widget),
                    ("Оплата", payment_widget),
                    ("Номер страхования", self.service_insurance_number),
                ],
            )
        )
        layout.addWidget(
            self._group(
                "Предоплата",
                [
                    ("Стационар", self.prepay_inpatient_treatment),
                    ("Роды", self.prepay_childbirth),
                ],
            )
        )
        if self.contract is not None:
            note = QLabel("Предоплата редактируется через платежи после создания договора.")
            note.setStyleSheet("color: #666;")
            layout.addWidget(note)
        page.setLayout(layout)
        return page

    def _build_discharge_section(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(
            self._group(
                "Выписка",
                [
                    ("Статус", self.discharged),
                    ("Дата выписки", self.discharge_date),
                    ("Комментарий", self.comments),
                ],
            )
        )
        page.setLayout(layout)
        return page

    def _connect_signals(self) -> None:
        self.delegate_enabled.toggled.connect(self._set_delegate_enabled)
        self.inpatient_treatment.toggled.connect(self._sync_inpatient_prepay)
        self.childbirth.toggled.connect(self._sync_childbirth_prepay)
        self.discharged.toggled.connect(self.discharge_date.setEnabled)

    def data(self) -> dict:
        payload = {
            "contract_number": self.contract_number.text().strip(),
            "contract_date": self._to_datetime(self.contract_date),
            "category": self.category.currentData(),
            "patient_name": self.patient_name.text().strip(),
            "patient_birth_date": self._to_datetime(self.patient_birth_date),
            "birth_history_number": self.birth_history_number.text().strip() or None,
            "patient_reg_address": self.patient_reg_address.text().strip(),
            "patient_live_address": self.patient_live_address.text().strip(),
            "patient_phone": self.patient_phone.text().strip(),
            "patient_passport_issued_by": self.patient_passport_issued_by.text().strip(),
            "patient_passport_issued_code": self.patient_passport_issued_code.text().strip(),
            "patient_passport_series": self.patient_passport_series.text().strip(),
            "patient_passport_date": self._to_datetime(self.patient_passport_date),
            "delegate_name": self._optional_delegate_text(self.delegate_name),
            "delegate_birth_date": self._optional_delegate_datetime(self.delegate_birth_date),
            "delegate_reg_address": self._optional_delegate_text(self.delegate_reg_address),
            "delegate_live_address": self._optional_delegate_text(self.delegate_live_address),
            "delegate_phone": self._optional_delegate_text(self.delegate_phone),
            "delegate_passport_issued_by": self._optional_delegate_text(self.delegate_passport_issued_by),
            "delegate_passport_issued_code": self._optional_delegate_text(self.delegate_passport_issued_code),
            "delegate_passport_series": self._optional_delegate_text(self.delegate_passport_series),
            "delegate_passport_date": self._optional_delegate_datetime(self.delegate_passport_date),
            "inpatient_treatment": self.inpatient_treatment.isChecked(),
            "childbirth": self.childbirth.isChecked(),
            "service_payed": self.service_payed.isChecked(),
            "service_insurance": self.service_insurance.isChecked(),
            "service_insurance_number": self._optional_text(self.service_insurance_number),
            "discharged": self.discharged.isChecked(),
            "discharge_date": self._to_datetime(self.discharge_date) if self.discharged.isChecked() else None,
            "comments": self.comments.toPlainText().strip() or None,
        }

        if self.contract is None:
            payload["prepay_inpatient_treatment"] = Decimal(str(self.prepay_inpatient_treatment.value()))
            payload["prepay_childbirth"] = Decimal(str(self.prepay_childbirth.value()))

        return payload

    def _load_contract(self, contract: Contract) -> None:
        self.contract_number.setText(contract.contract_number)
        self._set_datetime(self.contract_date, contract.contract_date)
        self._set_category(contract.category)
        self.patient_name.setText(contract.patient_name)
        self._set_datetime(self.patient_birth_date, contract.patient_birth_date)
        self.birth_history_number.setText(contract.birth_history_number or "")
        self.patient_reg_address.setText(contract.patient_reg_address)
        self.patient_live_address.setText(contract.patient_live_address)
        self.patient_phone.setText(contract.patient_phone)
        self.patient_passport_issued_by.setText(contract.patient_passport_issued_by)
        self.patient_passport_issued_code.setText(contract.patient_passport_issued_code)
        self.patient_passport_series.setText(contract.patient_passport_series)
        self._set_datetime(self.patient_passport_date, contract.patient_passport_date)
        self.delegate_enabled.setChecked(self._has_delegate(contract))
        self.delegate_name.setText(contract.delegate_name or "")
        self._set_datetime(self.delegate_birth_date, contract.delegate_birth_date)
        self.delegate_reg_address.setText(contract.delegate_reg_address or "")
        self.delegate_live_address.setText(contract.delegate_live_address or "")
        self.delegate_phone.setText(contract.delegate_phone or "")
        self.delegate_passport_issued_by.setText(contract.delegate_passport_issued_by or "")
        self.delegate_passport_issued_code.setText(contract.delegate_passport_issued_code or "")
        self.delegate_passport_series.setText(contract.delegate_passport_series or "")
        self._set_datetime(self.delegate_passport_date, contract.delegate_passport_date)
        self.inpatient_treatment.setChecked(bool(contract.inpatient_treatment))
        self.childbirth.setChecked(bool(contract.childbirth))
        self.prepay_inpatient_treatment.setValue(float(contract.prepay_inpatient_treatment or 0))
        self.prepay_childbirth.setValue(float(contract.prepay_childbirth or 0))
        self.service_payed.setChecked(bool(contract.service_payed))
        self.service_insurance.setChecked(bool(contract.service_insurance))
        self.service_insurance_number.setText(contract.service_insurance_number or "")
        self.discharged.setChecked(bool(contract.discharged))
        self._set_datetime(self.discharge_date, contract.discharge_date)
        self.comments.setPlainText(contract.comments or "")
        self.prepay_inpatient_treatment.setEnabled(False)
        self.prepay_childbirth.setEnabled(False)

    def _load_from_source(self, contract: Contract) -> None:
        self.patient_name.setText(contract.patient_name)
        self._set_datetime(self.patient_birth_date, contract.patient_birth_date)
        self.patient_reg_address.setText(contract.patient_reg_address)
        self.patient_live_address.setText(contract.patient_live_address)
        self.patient_phone.setText(contract.patient_phone)
        self.patient_passport_issued_by.setText(contract.patient_passport_issued_by)
        self.patient_passport_issued_code.setText(contract.patient_passport_issued_code)
        self.patient_passport_series.setText(contract.patient_passport_series)
        self._set_datetime(self.patient_passport_date, contract.patient_passport_date)
        self.delegate_enabled.setChecked(self._has_delegate(contract))
        self.delegate_name.setText(contract.delegate_name or "")
        self._set_datetime(self.delegate_birth_date, contract.delegate_birth_date)
        self.delegate_reg_address.setText(contract.delegate_reg_address or "")
        self.delegate_live_address.setText(contract.delegate_live_address or "")
        self.delegate_phone.setText(contract.delegate_phone or "")
        self.delegate_passport_issued_by.setText(contract.delegate_passport_issued_by or "")
        self.delegate_passport_issued_code.setText(contract.delegate_passport_issued_code or "")
        self.delegate_passport_series.setText(contract.delegate_passport_series or "")
        self._set_datetime(self.delegate_passport_date, contract.delegate_passport_date)

    def _date_time_edit(self) -> QDateTimeEdit:
        widget = QDateTimeEdit()
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("dd.MM.yyyy")
        today = datetime.combine(datetime.now().date(), time.min, tzinfo=timezone.utc)
        widget.setDateTime(QDateTime(today))
        return widget

    def _money_input(self) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setMaximum(10_000_000)
        widget.setDecimals(2)
        widget.setSuffix(" руб.")
        widget.setEnabled(False)
        return widget

    def _group(self, title: str, rows: list[tuple[str, QWidget]]) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        for label, widget in rows:
            if isinstance(widget, (QLineEdit, QComboBox, QDateTimeEdit, QDoubleSpinBox, QTextEdit)):
                widget.setMinimumWidth(320)
            form.addRow(label, widget)
        group.setLayout(form)
        return group

    def _scrollable(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    def _to_datetime(self, widget: QDateTimeEdit) -> datetime:
        qt_value = widget.date()
        converter = getattr(qt_value, "toPyDate", None) or getattr(qt_value, "toPython")
        return datetime.combine(converter(), time.min, tzinfo=timezone.utc)

    def _set_datetime(self, widget: QDateTimeEdit, value: datetime | None) -> None:
        if value is None:
            return
        normalized = datetime.combine(value.date(), time.min, tzinfo=value.tzinfo or timezone.utc)
        widget.setDateTime(QDateTime(normalized))

    def _optional_text(self, widget: QLineEdit) -> str | None:
        return widget.text().strip() or None

    def _set_category(self, value: str | None) -> None:
        if not value:
            value = "Категория 2"
        index = self.category.findData(value)
        if index < 0:
            self.category.addItem(value, value)
            index = self.category.findData(value)
        self.category.setCurrentIndex(index)

    def _optional_delegate_text(self, widget: QLineEdit) -> str | None:
        if not self.delegate_enabled.isChecked():
            return None
        return self._optional_text(widget)

    def _optional_delegate_datetime(self, widget: QDateTimeEdit) -> datetime | None:
        if not self.delegate_enabled.isChecked():
            return None
        return self._to_datetime(widget)

    def _set_delegate_enabled(self, enabled: bool) -> None:
        fields = [
            self.delegate_name,
            self.delegate_birth_date,
            self.delegate_reg_address,
            self.delegate_live_address,
            self.delegate_phone,
            self.delegate_passport_issued_by,
            self.delegate_passport_issued_code,
            self.delegate_passport_series,
            self.delegate_passport_date,
        ]
        for field in fields:
            field.setEnabled(enabled)

    def _sync_prepay_inputs(self) -> None:
        self._sync_inpatient_prepay(self.inpatient_treatment.isChecked())
        self._sync_childbirth_prepay(self.childbirth.isChecked())

    def _sync_inpatient_prepay(self, enabled: bool) -> None:
        if self.contract is not None:
            self.prepay_inpatient_treatment.setEnabled(False)
            return
        self.prepay_inpatient_treatment.setEnabled(enabled)
        if enabled:
            self.prepay_inpatient_treatment.setValue(float(self.DEFAULT_INPATIENT_PREPAY))
        else:
            self.prepay_inpatient_treatment.setValue(0)

    def _sync_childbirth_prepay(self, enabled: bool) -> None:
        if self.contract is not None:
            self.prepay_childbirth.setEnabled(False)
            return
        self.prepay_childbirth.setEnabled(enabled)
        if enabled:
            self.prepay_childbirth.setValue(float(self.DEFAULT_CHILDBIRTH_PREPAY))
        else:
            self.prepay_childbirth.setValue(0)

    def _save(self) -> None:
        if self.service_insurance.isChecked() and not self._optional_text(self.service_insurance_number):
            QMessageBox.warning(self, "Роддом №4", "Укажите номер полиса/страхового случая")
            self.service_insurance_number.setFocus()
            return
        self.accept()

    def _has_delegate(self, contract: Contract) -> bool:
        return any(
            [
                contract.delegate_name,
                contract.delegate_birth_date,
                contract.delegate_reg_address,
                contract.delegate_live_address,
                contract.delegate_phone,
                contract.delegate_passport_issued_by,
                contract.delegate_passport_issued_code,
                contract.delegate_passport_series,
                contract.delegate_passport_date,
            ]
        )
