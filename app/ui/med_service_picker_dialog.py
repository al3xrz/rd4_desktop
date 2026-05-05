from __future__ import annotations

from app.models import MedService
from app.services import MedServiceService
from app.ui.qt import QDialog, QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QVBoxLayout


class MedServicePickerDialog(QDialog):
    def __init__(self, med_service_service: MedServiceService | None = None) -> None:
        super().__init__()
        self.med_service_service = med_service_service or MedServiceService()
        self.selected_service_id: int | None = None
        self.setWindowTitle("Выбор услуги")
        self.setMinimumSize(520, 420)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Код", "Наименование", "Цена"])
        self.tree.itemDoubleClicked.connect(self._accept_item)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._accept_selected)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        self._load_tree()

    def _load_tree(self) -> None:
        self.tree.clear()
        for service in self.med_service_service.get_tree():
            self.tree.addTopLevelItem(self._build_item(service))
        self.tree.expandAll()

    def _build_item(self, service: MedService) -> QTreeWidgetItem:
        item = QTreeWidgetItem([service.code or "", service.name, "" if service.is_folder else str(service.price)])
        item.setData(0, 32, service.id)
        item.setData(1, 32, service.is_folder)
        for child in service.children:
            if not child.deleted:
                item.addChild(self._build_item(child))
        return item

    def _accept_selected(self) -> None:
        item = self.tree.currentItem()
        if item is not None:
            self._accept_item(item)

    def _accept_item(self, item: QTreeWidgetItem, column: int = 0) -> None:
        is_folder = item.data(1, 32)
        if is_folder:
            return
        self.selected_service_id = item.data(0, 32)
        self.accept()
