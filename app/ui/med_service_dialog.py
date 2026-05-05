from __future__ import annotations

from decimal import Decimal

from app.models import MedService
from app.services import MedServiceService
from app.ui.icons import ICON_FOLDER, icon_for
from app.ui.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class MedServiceDialog(QDialog):
    def __init__(
        self,
        is_folder: bool,
        service: MedService | None = None,
        med_service_service: MedServiceService | None = None,
        parent_id: int | None = None,
    ) -> None:
        super().__init__()
        self.is_folder = service.is_folder if service is not None else is_folder
        self.service = service
        self.initial_parent_id = service.parent_id if service is not None else parent_id
        self.med_service_service = med_service_service or MedServiceService()
        self.setWindowTitle(self._window_title())
        self.setMinimumWidth(560)

        self.parent_input = QComboBox()
        self._load_parent_options()

        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.unit_input = QLineEdit()
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(10_000_000)
        self.price_input.setDecimals(2)
        self.price_input.setSuffix(" руб.")
        self.vat_input = QDoubleSpinBox()
        self.vat_input.setMaximum(100)
        self.vat_input.setDecimals(2)
        self.vat_input.setSuffix(" %")
        self.comments_input = QTextEdit()
        self.comments_input.setFixedHeight(88)

        self._configure_inputs()
        self._build_layout()

        if self.is_folder:
            self._set_service_fields_enabled(False)

        if service is not None:
            self._load_service(service)
        else:
            self._select_parent(self.initial_parent_id)

    def data(self) -> dict:
        parent_id = self.parent_input.currentData()
        payload = {
            "parent_id": parent_id,
            "name": self.name_input.text().strip(),
            "comments": self.comments_input.toPlainText().strip() or None,
        }
        if not self.is_folder:
            payload.update(
                {
                    "code": self.code_input.text().strip() or None,
                    "unit": self.unit_input.text().strip() or "шт",
                    "price": Decimal(str(self.price_input.value())),
                    "vat": self.vat_input.value(),
                }
            )
        return payload

    def _build_layout(self) -> None:
        title = QLabel("Папка справочника" if self.is_folder else "Медицинская услуга")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        subtitle = QLabel("Папки используются для группировки. В акты добавляются только услуги.")
        subtitle.setStyleSheet("color: #666;")

        placement = QGroupBox("Размещение")
        placement_form = QFormLayout()
        placement_form.addRow("Родитель", self.parent_input)
        placement.setLayout(placement_form)

        details = QGroupBox("Основное")
        details_form = QFormLayout()
        details_form.addRow("Наименование", self.name_input)
        details_form.addRow("Код", self.code_input)
        details_form.addRow("Ед. изм.", self.unit_input)
        details_form.addRow("Цена", self.price_input)
        details_form.addRow("НДС", self.vat_input)
        details_form.addRow("Комментарий", self.comments_input)
        details.setLayout(details_form)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText("Сохранить")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(placement)
        layout.addWidget(details)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def _configure_inputs(self) -> None:
        self.code_input.setPlaceholderText("Код услуги")
        self.name_input.setPlaceholderText("Название папки или услуги")
        self.unit_input.setPlaceholderText("шт")
        self.comments_input.setPlaceholderText("Комментарий для сотрудников")
        self.unit_input.setText("шт")

    def _set_service_fields_enabled(self, enabled: bool) -> None:
        self.code_input.setEnabled(enabled)
        self.unit_input.setEnabled(enabled)
        self.price_input.setEnabled(enabled)
        self.vat_input.setEnabled(enabled)

    def _load_parent_options(self) -> None:
        self.parent_input.addItem(icon_for(ICON_FOLDER), "Верхний уровень", None)
        for folder in self.med_service_service.list_folders():
            if self.service is not None and folder.id == self.service.id:
                continue
            self.parent_input.addItem(icon_for(ICON_FOLDER), folder.name, folder.id)

    def _load_service(self, service: MedService) -> None:
        self.code_input.setText(service.code or "")
        self.name_input.setText(service.name)
        self.unit_input.setText(service.unit or "шт")
        self.price_input.setValue(float(service.price))
        self.vat_input.setValue(float(service.vat))
        self.comments_input.setPlainText(service.comments or "")
        self._select_parent(service.parent_id)

    def _select_parent(self, parent_id: int | None) -> None:
        for index in range(self.parent_input.count()):
            if self.parent_input.itemData(index) == parent_id:
                self.parent_input.setCurrentIndex(index)
                break

    def _window_title(self) -> str:
        if self.service is not None:
            return "Редактирование папки" if self.is_folder else "Редактирование услуги"
        return "Новая папка" if self.is_folder else "Новая услуга"
