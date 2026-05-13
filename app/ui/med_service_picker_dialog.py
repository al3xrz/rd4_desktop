from __future__ import annotations

from app.models import MedService
from app.services import MedServiceService
from app.ui.icons import ICON_FOLDER, ICON_SERVICE, icon_for, set_dialog_button_icons
from app.ui.qt import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    Qt,
)


class MedServicePickerDialog(QDialog):
    SERVICE_ID_ROLE = Qt.UserRole
    IS_FOLDER_ROLE = Qt.UserRole + 1
    SERVICE_DATA_ROLE = Qt.UserRole + 2

    def __init__(self, med_service_service: MedServiceService | None = None) -> None:
        super().__init__()
        self.med_service_service = med_service_service or MedServiceService()
        self.selected_service_id: int | None = None
        self.selected_service: dict | None = None
        self.setWindowTitle("Выбор услуги")
        self.setMinimumSize(760, 520)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по коду, названию, единице или цене")
        self.search_input.textChanged.connect(self._apply_filter)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Наименование", "Код", "Ед.", "Цена"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setStyleSheet(
            "QTreeWidget { alternate-background-color: #f7f9fb; }"
            "QTreeWidget::item { min-height: 26px; padding: 3px; }"
            "QTreeWidget::item:selected { background: #dcecff; color: #111; }"
        )
        self.tree.itemDoubleClicked.connect(self._accept_item)
        self.tree.currentItemChanged.connect(self._update_selection)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 600;")
        self.details_label = QLabel("Выберите услугу из справочника")
        self.details_label.setStyleSheet("color: #666;")
        self.details_label.setWordWrap(True)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        set_dialog_button_icons(self.buttons)
        self.buttons.accepted.connect(self._accept_selected)
        self.buttons.rejected.connect(self.reject)
        self.ok_button = self.buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setText("Выбрать")
        self.ok_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.search_input)
        layout.addWidget(self.tree)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.details_label)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        self._load_tree()

    def _load_tree(self) -> None:
        self.tree.clear()
        for service in self.med_service_service.get_tree():
            self.tree.addTopLevelItem(self._build_item(service))
        self.tree.expandAll()
        self._resize_columns()
        self._apply_filter()
        self._update_selection()

    def _build_item(self, service: MedService) -> QTreeWidgetItem:
        service_data = {
            "id": service.id,
            "code": service.code or "",
            "name": service.name,
            "unit": "" if service.is_folder else service.unit or "",
            "price": service.price,
        }
        item = QTreeWidgetItem(
            [
                service.name,
                service.code or "",
                "" if service.is_folder else service.unit or "",
                "" if service.is_folder else str(service.price),
            ]
        )
        item.setIcon(0, icon_for(ICON_FOLDER if service.is_folder else ICON_SERVICE))
        item.setData(0, self.SERVICE_ID_ROLE, service.id)
        item.setData(0, self.IS_FOLDER_ROLE, service.is_folder)
        item.setData(0, self.SERVICE_DATA_ROLE, service_data)
        if service.is_folder:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        for child in service.children:
            if not child.deleted:
                item.addChild(self._build_item(child))
        return item

    def _accept_selected(self) -> None:
        item = self.tree.currentItem()
        if item is not None:
            self._accept_item(item)

    def _accept_item(self, item: QTreeWidgetItem, column: int = 0) -> None:
        is_folder = item.data(0, self.IS_FOLDER_ROLE)
        if is_folder:
            item.setExpanded(not item.isExpanded())
            return
        self.selected_service_id = item.data(0, self.SERVICE_ID_ROLE)
        self.selected_service = item.data(0, self.SERVICE_DATA_ROLE)
        self.accept()

    def _apply_filter(self) -> None:
        query = self.search_input.text().strip().lower()
        visible_count = 0
        for index in range(self.tree.topLevelItemCount()):
            visible_count += self._filter_item(self.tree.topLevelItem(index), query)
        if query:
            self.tree.expandAll()
            self.summary_label.setText(f"Найдено услуг: {visible_count}")
        else:
            self.summary_label.setText("")
        self._update_selection()

    def _filter_item(self, item: QTreeWidgetItem, query: str) -> int:
        own_match = not query or self._item_text(item).find(query) >= 0
        visible_children = 0
        for index in range(item.childCount()):
            visible_children += self._filter_item(item.child(index), query)
        visible = own_match or visible_children > 0
        item.setHidden(not visible)
        return (1 if visible and own_match and not item.data(0, self.IS_FOLDER_ROLE) else 0) + visible_children

    def _item_text(self, item: QTreeWidgetItem) -> str:
        return " ".join(item.text(column).lower() for column in range(item.columnCount()))

    def _update_selection(self, *args) -> None:
        item = self.tree.currentItem()
        can_select = item is not None and not item.isHidden() and not item.data(0, self.IS_FOLDER_ROLE)
        self.ok_button.setEnabled(can_select)
        if item is None:
            self.details_label.setText("Выберите услугу из справочника")
            return
        if item.data(0, self.IS_FOLDER_ROLE):
            self.details_label.setText(f"Папка: {item.text(0)}. Раскройте её и выберите конкретную услугу.")
            return
        self.details_label.setText(
            f"Услуга: {item.text(0)} | Код: {item.text(1) or '-'} | Ед.: {item.text(2) or '-'} | "
            f"Цена: {item.text(3) or '0'}"
        )

    def _resize_columns(self) -> None:
        width = self.tree.viewport().width()
        if width <= 0:
            return

        name_width = int(width * 0.70)
        remaining_width = max(width - name_width, 180)
        self.tree.setColumnWidth(0, name_width)
        self.tree.setColumnWidth(1, int(remaining_width * 0.45))
        self.tree.setColumnWidth(2, int(remaining_width * 0.20))
        self.tree.setColumnWidth(3, int(remaining_width * 0.35))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._resize_columns()
