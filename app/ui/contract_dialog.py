from __future__ import annotations

import re
from datetime import datetime, time, timezone
from decimal import Decimal

from app.models import Contract
from app.ui.icons import set_dialog_button_icons
from app.ui.qt import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateTime,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
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
    PHONE_INPUT_MASK = "+7 (000) 000-00-00;_"
    FORM_HORIZONTAL_MARGIN = 12
    INVALID_FIELD_STYLE = "border: 1px solid #d92d20; background: #fff5f5;"
    INVALID_CHECK_STYLE = "color: #b42318; font-weight: 600;"

    def __init__(self, contract: Contract | None = None, source_contract: Contract | None = None) -> None:
        super().__init__()
        self.contract = contract
        self.source_contract = source_contract
        self._invalid_widgets: list[QWidget] = []
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
        self.patient_reg_address = QTextEdit()
        self.patient_live_address = QTextEdit()
        self.patient_phone = QLineEdit()
        self.patient_passport_issued_by = QTextEdit()
        self.patient_passport_issued_code = QLineEdit()
        self.patient_passport_series = QLineEdit()
        self.patient_passport_date = self._date_time_edit()

        self.delegate_enabled = QCheckBox("Представитель")
        self.delegate_name = QLineEdit()
        self.delegate_birth_date = self._date_time_edit()
        self.delegate_reg_address = QTextEdit()
        self.delegate_live_address = QTextEdit()
        self.delegate_phone = QLineEdit()
        self.delegate_passport_issued_by = QTextEdit()
        self.delegate_passport_issued_code = QLineEdit()
        self.delegate_passport_series = QLineEdit()
        self.delegate_passport_date = self._date_time_edit()

        self.inpatient_treatment = QCheckBox("Стационарное лечение")
        self.childbirth = QCheckBox("Роды")
        self.prepay_inpatient_treatment = self._money_input()
        self.prepay_childbirth = self._money_input()
        self.service_payed = QRadioButton("Платная")
        self.service_insurance = QRadioButton("ФОМС")
        self.payment_type_group = QButtonGroup(self)
        self.payment_type_group.addButton(self.service_payed)
        self.payment_type_group.addButton(self.service_insurance)
        self.service_payed.setChecked(True)
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
        self.patient_phone.setInputMask(self.PHONE_INPUT_MASK)
        self.patient_passport_issued_by.setPlaceholderText("Кем выдан паспорт")
        self.patient_passport_issued_code.setPlaceholderText("000-000")
        self.patient_passport_issued_code.setInputMask("000-000;_")
        self.patient_passport_series.setPlaceholderText("0000 000000")
        self.patient_passport_series.setInputMask("0000 000000;_")

        self.delegate_name.setPlaceholderText("Фамилия Имя Отчество")
        self.delegate_reg_address.setPlaceholderText("Адрес по регистрации")
        self.delegate_live_address.setPlaceholderText("Фактический адрес")
        self.delegate_phone.setInputMask(self.PHONE_INPUT_MASK)
        self.delegate_passport_issued_by.setPlaceholderText("Кем выдан паспорт")
        self.delegate_passport_issued_code.setPlaceholderText("000-000")
        self.delegate_passport_issued_code.setInputMask("000-000;_")
        self.delegate_passport_series.setPlaceholderText("0000 000000")
        self.delegate_passport_series.setInputMask("0000 000000;_")

        self.service_insurance_number.setPlaceholderText("Номер полиса/страхового случая ФОМС")
        self.comments.setPlaceholderText("Внутренний комментарий к договору")
        self.comments.setFixedHeight(90)

        for text_edit in [
            self.patient_reg_address,
            self.patient_live_address,
            self.patient_passport_issued_by,
            self.delegate_reg_address,
            self.delegate_live_address,
            self.delegate_passport_issued_by,
        ]:
            text_edit.setFixedHeight(58)
            text_edit.setAcceptRichText(False)
            text_edit.setTabChangesFocus(True)
        self.comments.setTabChangesFocus(True)

        for input_widget in self.findChildren(QLineEdit):
            input_widget.setMinimumWidth(max(input_widget.minimumWidth(), 110))

    def _build_layout(self) -> None:
        self.form = self._scrollable(self._build_contract_form())

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        set_dialog_button_icons(self.buttons)
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
        self._configure_tab_order()

    def _build_contract_form(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(self.FORM_HORIZONTAL_MARGIN, 0, self.FORM_HORIZONTAL_MARGIN, 0)
        layout.addWidget(self._build_contract_section())
        layout.addLayout(self._build_people_section())
        layout.addWidget(self._build_payment_section())
        layout.addWidget(self._build_discharge_section())
        layout.addStretch()
        page.setLayout(layout)
        return page

    def _build_contract_section(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(4, 0)
        layout.addWidget(self._field("№ договора", self.contract_number), 0, 0)
        layout.addWidget(self._field("Дата", self.contract_date), 0, 1)
        layout.addWidget(self._field("№ истории родов", self.birth_history_number), 0, 2)
        layout.addWidget(self._field("Категория", self.category), 0, 3)
        layout.addWidget(self._checkbox_field("", self.delegate_enabled), 0, 4)
        page.setLayout(layout)
        return page

    def _build_people_section(self) -> QHBoxLayout:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)

        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.addWidget(self._build_person_column("пациента", is_delegate=False))
        columns.addWidget(self._build_person_column("представителя", is_delegate=True))
        outer.addLayout(columns)

        foms_row = QHBoxLayout()
        foms_row.setContentsMargins(0, 0, 0, 0)
        foms_row.addWidget(self._field("№ ФОМС", self.service_insurance_number), 1)
        foms_row.addWidget(QWidget(), 1)
        outer.addLayout(foms_row)
        return outer

    def _build_person_column(self, suffix: str, is_delegate: bool) -> QWidget:
        name = self.delegate_name if is_delegate else self.patient_name
        birth_date = self.delegate_birth_date if is_delegate else self.patient_birth_date
        reg_address = self.delegate_reg_address if is_delegate else self.patient_reg_address
        live_address = self.delegate_live_address if is_delegate else self.patient_live_address
        phone = self.delegate_phone if is_delegate else self.patient_phone
        passport_series = self.delegate_passport_series if is_delegate else self.patient_passport_series
        passport_issued_by = self.delegate_passport_issued_by if is_delegate else self.patient_passport_issued_by
        passport_date = self.delegate_passport_date if is_delegate else self.patient_passport_date
        passport_code = self.delegate_passport_issued_code if is_delegate else self.patient_passport_issued_code

        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._field(f"ФИО {suffix}", name))
        layout.addWidget(self._field(f"Дата рождения {suffix}", birth_date))
        layout.addWidget(self._field(f"Адрес регистрации {suffix}", reg_address))
        layout.addWidget(self._field(f"Адрес проживания {suffix}", live_address))
        layout.addWidget(self._field(f"Телефон {suffix}", phone))

        layout.addWidget(self._field(f"Серия и номер паспорта {suffix}", passport_series))
        layout.addWidget(self._field("Кем выдан паспорт", passport_issued_by))
        passport_meta = QHBoxLayout()
        passport_meta.addWidget(self._field("Когда выдан паспорт", passport_date))
        passport_meta.addWidget(self._field("Код подразделения", passport_code))
        layout.addLayout(passport_meta)
        page.setLayout(layout)
        return page

    def _build_payment_section(self) -> QWidget:
        group = QGroupBox("Условия договора")
        layout = QVBoxLayout()

        payment_row = QHBoxLayout()
        payment_row.setContentsMargins(0, 0, 0, 0)
        payment_row.addLayout(self._inline_group("Тип оплаты:", [self.service_payed, self.service_insurance]), 1)
        payment_row.addLayout(self._inline_group("Услуги:", [self.inpatient_treatment, self.childbirth]), 1)
        layout.addLayout(payment_row)

        prepay_row = QHBoxLayout()
        prepay_row.addWidget(self._field("Предоплата стационар", self.prepay_inpatient_treatment))
        prepay_row.addWidget(self._field("Предоплата роды", self.prepay_childbirth))
        layout.addLayout(prepay_row)

        if self.contract is not None:
            note = QLabel("Предоплата редактируется через платежи после создания договора.")
            note.setStyleSheet("color: #666;")
            layout.addWidget(note)
        group.setLayout(layout)
        return group

    def _inline_group(self, label: str, widgets: list[QWidget]) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label))
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch()
        return layout

    def _build_discharge_section(self) -> QWidget:
        group = QGroupBox("Выписка")
        layout = QVBoxLayout()
        status_row = QHBoxLayout()
        status_row.addWidget(self.discharged)
        status_row.addSpacing(16)
        status_row.addWidget(QLabel("Дата выписки"))
        status_row.addWidget(self.discharge_date, 1)
        status_row.addStretch()
        layout.addLayout(status_row)
        layout.addWidget(self._field("Комментарий", self.comments))
        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        self.delegate_enabled.toggled.connect(self._set_delegate_enabled)
        self.inpatient_treatment.toggled.connect(self._sync_inpatient_prepay)
        self.childbirth.toggled.connect(self._sync_childbirth_prepay)
        self.discharged.toggled.connect(self.discharge_date.setEnabled)
        self.service_payed.toggled.connect(self._clear_validation_highlight)
        self.service_insurance.toggled.connect(self._clear_validation_highlight)

        for widget in self._validation_inputs():
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._clear_validation_highlight)
            elif isinstance(widget, QTextEdit):
                widget.textChanged.connect(self._clear_validation_highlight)
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(self._clear_validation_highlight)

    def data(self) -> dict:
        payload = {
            "contract_number": self.contract_number.text().strip(),
            "contract_date": self._to_datetime(self.contract_date),
            "category": self.category.currentData(),
            "patient_name": self.patient_name.text().strip(),
            "patient_birth_date": self._to_datetime(self.patient_birth_date),
            "birth_history_number": self.birth_history_number.text().strip() or None,
            "patient_reg_address": self._text_value(self.patient_reg_address),
            "patient_live_address": self._text_value(self.patient_live_address),
            "patient_phone": self._phone_value(self.patient_phone) or "",
            "patient_passport_issued_by": self._text_value(self.patient_passport_issued_by),
            "patient_passport_issued_code": self.patient_passport_issued_code.text().strip(),
            "patient_passport_series": self.patient_passport_series.text().strip(),
            "patient_passport_date": self._to_datetime(self.patient_passport_date),
            "delegate_name": self._optional_delegate_text(self.delegate_name),
            "delegate_birth_date": self._optional_delegate_datetime(self.delegate_birth_date),
            "delegate_reg_address": self._optional_delegate_text(self.delegate_reg_address),
            "delegate_live_address": self._optional_delegate_text(self.delegate_live_address),
            "delegate_phone": self._optional_delegate_phone(self.delegate_phone),
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
        self.patient_reg_address.setPlainText(contract.patient_reg_address)
        self.patient_live_address.setPlainText(contract.patient_live_address)
        self._set_phone(self.patient_phone, contract.patient_phone)
        self.patient_passport_issued_by.setPlainText(contract.patient_passport_issued_by)
        self.patient_passport_issued_code.setText(contract.patient_passport_issued_code)
        self.patient_passport_series.setText(contract.patient_passport_series)
        self._set_datetime(self.patient_passport_date, contract.patient_passport_date)
        self.delegate_enabled.setChecked(self._has_delegate(contract))
        self.delegate_name.setText(contract.delegate_name or "")
        self._set_datetime(self.delegate_birth_date, contract.delegate_birth_date)
        self.delegate_reg_address.setPlainText(contract.delegate_reg_address or "")
        self.delegate_live_address.setPlainText(contract.delegate_live_address or "")
        self._set_phone(self.delegate_phone, contract.delegate_phone)
        self.delegate_passport_issued_by.setPlainText(contract.delegate_passport_issued_by or "")
        self.delegate_passport_issued_code.setText(contract.delegate_passport_issued_code or "")
        self.delegate_passport_series.setText(contract.delegate_passport_series or "")
        self._set_datetime(self.delegate_passport_date, contract.delegate_passport_date)
        self.inpatient_treatment.setChecked(bool(contract.inpatient_treatment))
        self.childbirth.setChecked(bool(contract.childbirth))
        self.prepay_inpatient_treatment.setValue(float(contract.prepay_inpatient_treatment or 0))
        self.prepay_childbirth.setValue(float(contract.prepay_childbirth or 0))
        if contract.service_insurance:
            self.service_insurance.setChecked(True)
        else:
            self.service_payed.setChecked(True)
        self.service_insurance_number.setText(contract.service_insurance_number or "")
        self.discharged.setChecked(bool(contract.discharged))
        self._set_datetime(self.discharge_date, contract.discharge_date)
        self.comments.setPlainText(contract.comments or "")
        self.prepay_inpatient_treatment.setEnabled(False)
        self.prepay_childbirth.setEnabled(False)

    def _load_from_source(self, contract: Contract) -> None:
        self.patient_name.setText(contract.patient_name)
        self._set_datetime(self.patient_birth_date, contract.patient_birth_date)
        self.patient_reg_address.setPlainText(contract.patient_reg_address)
        self.patient_live_address.setPlainText(contract.patient_live_address)
        self._set_phone(self.patient_phone, contract.patient_phone)
        self.patient_passport_issued_by.setPlainText(contract.patient_passport_issued_by)
        self.patient_passport_issued_code.setText(contract.patient_passport_issued_code)
        self.patient_passport_series.setText(contract.patient_passport_series)
        self._set_datetime(self.patient_passport_date, contract.patient_passport_date)
        self.delegate_enabled.setChecked(self._has_delegate(contract))
        self.delegate_name.setText(contract.delegate_name or "")
        self._set_datetime(self.delegate_birth_date, contract.delegate_birth_date)
        self.delegate_reg_address.setPlainText(contract.delegate_reg_address or "")
        self.delegate_live_address.setPlainText(contract.delegate_live_address or "")
        self._set_phone(self.delegate_phone, contract.delegate_phone)
        self.delegate_passport_issued_by.setPlainText(contract.delegate_passport_issued_by or "")
        self.delegate_passport_issued_code.setText(contract.delegate_passport_issued_code or "")
        self.delegate_passport_series.setText(contract.delegate_passport_series or "")
        self._set_datetime(self.delegate_passport_date, contract.delegate_passport_date)
        if contract.service_insurance:
            self.service_insurance.setChecked(True)
            self.service_insurance_number.setText(contract.service_insurance_number or "")
        else:
            self.service_payed.setChecked(True)

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

    def _field(self, label: str, widget: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        caption = QLabel(label)
        caption.setStyleSheet("font-size: 12px;")
        layout.addWidget(caption)
        layout.addWidget(widget)
        page.setLayout(layout)
        return page

    def _checkbox_field(self, label: str, widget: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        caption = QLabel(label or " ")
        caption.setStyleSheet("font-size: 12px;")
        layout.addWidget(caption)
        layout.addWidget(widget)
        page.setLayout(layout)
        return page

    def _scrollable(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    def _configure_tab_order(self) -> None:
        widgets = [
            self.contract_number,
            self.contract_date,
            self.birth_history_number,
            self.category,
            self.delegate_enabled,
            self.patient_name,
            self.patient_birth_date,
            self.patient_reg_address,
            self.patient_live_address,
            self.patient_phone,
            self.patient_passport_series,
            self.patient_passport_issued_by,
            self.patient_passport_date,
            self.patient_passport_issued_code,
            self.delegate_name,
            self.delegate_birth_date,
            self.delegate_reg_address,
            self.delegate_live_address,
            self.delegate_phone,
            self.delegate_passport_series,
            self.delegate_passport_issued_by,
            self.delegate_passport_date,
            self.delegate_passport_issued_code,
            self.service_insurance_number,
            self.service_payed,
            self.service_insurance,
            self.inpatient_treatment,
            self.childbirth,
            self.discharged,
            self.discharge_date,
            self.comments,
            self.buttons.button(QDialogButtonBox.Save),
            self.buttons.button(QDialogButtonBox.Cancel),
        ]
        for current, next_widget in zip(widgets, widgets[1:]):
            QWidget.setTabOrder(current, next_widget)

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
        return self._text_value(widget) or None

    def _phone_value(self, widget: QLineEdit) -> str | None:
        digits = self._phone_digits(widget.text())
        if not digits:
            return None
        return self._format_phone(digits)

    def _set_phone(self, widget: QLineEdit, value: str | None) -> None:
        widget.clear()
        if value:
            widget.setText(self._format_phone(self._phone_digits(value)))

    def _phone_digits(self, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if not digits or digits == "7":
            return ""
        if len(digits) == 11 and digits[0] in {"7", "8"}:
            digits = digits[1:]
        if len(digits) != 10:
            return ""
        return digits

    def _format_phone(self, digits: str) -> str:
        if len(digits) != 10:
            return digits
        return f"+7 ({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"

    def _text_value(self, widget: QWidget) -> str:
        if isinstance(widget, QTextEdit):
            return widget.toPlainText().strip()
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return ""

    def _has_required_text(self, widget: QWidget) -> bool:
        if isinstance(widget, QTextEdit):
            return bool(widget.toPlainText().strip())
        if isinstance(widget, QLineEdit):
            if widget in [self.patient_phone, self.delegate_phone]:
                return bool(self._phone_value(widget))
            if widget in [self.patient_passport_issued_code, self.delegate_passport_issued_code]:
                return self._has_digits(widget, 6)
            if widget in [self.patient_passport_series, self.delegate_passport_series]:
                return self._has_digits(widget, 10)
            return bool(widget.text().strip())
        return True

    def _has_digits(self, widget: QLineEdit, count: int) -> bool:
        return len(re.sub(r"\D", "", widget.text())) == count

    def _set_category(self, value: str | None) -> None:
        if not value:
            value = "Категория 2"
        index = self.category.findData(value)
        if index < 0:
            self.category.addItem(value, value)
            index = self.category.findData(value)
        self.category.setCurrentIndex(index)

    def _optional_delegate_text(self, widget: QWidget) -> str | None:
        if not self.delegate_enabled.isChecked():
            return None
        return self._optional_text(widget)

    def _optional_delegate_phone(self, widget: QLineEdit) -> str | None:
        if not self.delegate_enabled.isChecked():
            return None
        return self._phone_value(widget)

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
        self._clear_validation_highlight()

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
        invalid_widgets, messages = self._validate_required_fields()
        if invalid_widgets:
            self._highlight_invalid_widgets(invalid_widgets)
            QMessageBox.warning(self, "Роддом №4", "\n".join(messages))
            self._focus_invalid_widget(invalid_widgets[0])
            return
        self.accept()

    def _validation_inputs(self) -> list[QWidget]:
        return [
            self.contract_number,
            self.birth_history_number,
            self.patient_name,
            self.patient_reg_address,
            self.patient_live_address,
            self.patient_phone,
            self.patient_passport_issued_by,
            self.patient_passport_issued_code,
            self.patient_passport_series,
            self.delegate_enabled,
            self.delegate_name,
            self.delegate_reg_address,
            self.delegate_live_address,
            self.delegate_phone,
            self.delegate_passport_issued_by,
            self.delegate_passport_issued_code,
            self.delegate_passport_series,
            self.inpatient_treatment,
            self.childbirth,
            self.service_insurance_number,
        ]

    def _validate_required_fields(self) -> tuple[list[QWidget], list[str]]:
        invalid: list[QWidget] = []
        messages: list[str] = []

        required_fields = [
            (self.contract_number, "№ договора"),
            (self.birth_history_number, "№ истории родов"),
            (self.patient_name, "ФИО пациента"),
            (self.patient_reg_address, "адрес регистрации пациента"),
            (self.patient_live_address, "адрес проживания пациента"),
            (self.patient_passport_issued_by, "кем выдан паспорт пациента"),
            (self.patient_passport_issued_code, "код подразделения пациента"),
            (self.patient_passport_series, "серия и номер паспорта пациента"),
        ]

        missing_labels = []
        for widget, label in required_fields:
            if not self._has_required_text(widget):
                invalid.append(widget)
                missing_labels.append(label)

        if not self._phone_value(self.patient_phone):
            invalid.append(self.patient_phone)
            missing_labels.append("телефон пациента")

        if missing_labels:
            messages.append("Заполните обязательные поля: " + ", ".join(missing_labels) + ".")

        if self.delegate_enabled.isChecked():
            delegate_fields = [
                (self.delegate_name, "ФИО представителя"),
                (self.delegate_reg_address, "адрес регистрации представителя"),
                (self.delegate_live_address, "адрес проживания представителя"),
                (self.delegate_passport_issued_by, "кем выдан паспорт представителя"),
                (self.delegate_passport_issued_code, "код подразделения представителя"),
                (self.delegate_passport_series, "серия и номер паспорта представителя"),
            ]
            missing_delegate_labels = []
            for widget, label in delegate_fields:
                if not self._has_required_text(widget):
                    invalid.append(widget)
                    missing_delegate_labels.append(label)
            if not self._phone_value(self.delegate_phone):
                invalid.append(self.delegate_phone)
                missing_delegate_labels.append("телефон представителя")
            if missing_delegate_labels:
                messages.append("Заполните данные представителя: " + ", ".join(missing_delegate_labels) + ".")

        if not self.inpatient_treatment.isChecked() and not self.childbirth.isChecked():
            invalid.extend([self.inpatient_treatment, self.childbirth])
            messages.append("Выберите хотя бы один вид услуги: стационарное лечение или роды.")

        if self.service_insurance.isChecked() and not self._optional_text(self.service_insurance_number):
            invalid.append(self.service_insurance_number)
            messages.append("Для ФОМС укажите номер полиса/страхового случая.")

        return self._deduplicate_widgets(invalid), messages

    def _deduplicate_widgets(self, widgets: list[QWidget]) -> list[QWidget]:
        result: list[QWidget] = []
        seen = set()
        for widget in widgets:
            if widget not in seen:
                result.append(widget)
                seen.add(widget)
        return result

    def _highlight_invalid_widgets(self, widgets: list[QWidget]) -> None:
        self._clear_validation_highlight()
        self._invalid_widgets = widgets
        for widget in widgets:
            if isinstance(widget, QCheckBox):
                widget.setStyleSheet(self.INVALID_CHECK_STYLE)
            else:
                widget.setStyleSheet(self.INVALID_FIELD_STYLE)

    def _clear_validation_highlight(self, *args) -> None:
        for widget in self._invalid_widgets:
            widget.setStyleSheet("")
        self._invalid_widgets = []

    def _focus_invalid_widget(self, widget: QWidget) -> None:
        if hasattr(self, "form"):
            self.form.ensureWidgetVisible(widget)
        if widget.isEnabled():
            widget.setFocus()

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
