from __future__ import annotations

from app.models import MedService
from app.services import MedServiceService
from app.services.exceptions import DomainError
from app.ui.icons import ICON_DELETE, ICON_EDIT, ICON_FOLDER, ICON_NEW, ICON_SERVICE, icon_for, set_button_icon
from app.ui.med_service_dialog import MedServiceDialog
from app.ui.qt import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    Qt,
)


class MedServicesPage(QWidget):
    SERVICE_ID_ROLE = Qt.UserRole
    IS_FOLDER_ROLE = Qt.UserRole + 1
    PARENT_ID_ROLE = Qt.UserRole + 2

    def __init__(self, med_service_service: MedServiceService | None = None) -> None:
        super().__init__()
        self.med_service_service = med_service_service or MedServiceService()
        self.total_count = 0

        self.title_label = QLabel("Справочник услуг")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self.subtitle_label = QLabel("Дерево папок и медицинских услуг для договоров и актов")
        self.subtitle_label.setStyleSheet("color: #666;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по коду, названию, единице или цене")
        self.search_input.textChanged.connect(self._apply_filter)

        self.add_folder_button = QPushButton("Папка")
        self.add_service_button = QPushButton("Услуга")
        self.edit_button = QPushButton("Редактировать")
        self.delete_button = QPushButton("Удалить")
        set_button_icon(self.add_folder_button, ICON_FOLDER)
        set_button_icon(self.add_service_button, ICON_NEW)
        set_button_icon(self.edit_button, ICON_EDIT)
        set_button_icon(self.delete_button, ICON_DELETE)

        self.add_folder_button.clicked.connect(self._add_folder)
        self.add_service_button.clicked.connect(self._add_service)
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button.clicked.connect(self._delete_selected)

        actions = QHBoxLayout()
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.add_service_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Наименование", "Код", "Ед.", "Цена", "НДС", "Комментарий"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.setStyleSheet(
            "QTreeWidget { alternate-background-color: #f7f9fb; }"
            "QTreeWidget::item { min-height: 26px; padding: 3px; }"
            "QTreeWidget::item:selected { background: #dcecff; color: #111; }"
        )
        self.tree.itemDoubleClicked.connect(self._edit_selected)
        self.tree.currentItemChanged.connect(self._update_selection)
        self.tree.customContextMenuRequested.connect(self._open_context_menu)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: 600;")
        self.details_label = QLabel("Выберите папку или услугу")
        self.details_label.setStyleSheet("color: #666;")
        self.details_label.setWordWrap(True)

        layout = QVBoxLayout()
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header.addLayout(header_text)
        header.addStretch()

        layout.addLayout(header)
        layout.addLayout(actions)
        layout.addWidget(self.search_input)
        layout.addWidget(self.tree)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.details_label)
        self.setLayout(layout)

        self.reload()

    def reload(self) -> None:
        self.tree.clear()
        self.total_count = 0
        for service in self.med_service_service.get_tree():
            self.tree.addTopLevelItem(self._build_item(service))
        self.tree.expandAll()
        self._resize_columns()
        self._apply_filter()
        self._update_selection()

    def _build_item(self, service: MedService) -> QTreeWidgetItem:
        self.total_count += 1
        item = QTreeWidgetItem(
            [
                service.name,
                service.code or "",
                "" if service.is_folder else service.unit or "",
                "" if service.is_folder else str(service.price),
                "" if service.is_folder else str(service.vat),
                service.comments or "",
            ]
        )
        item.setIcon(0, icon_for(ICON_FOLDER if service.is_folder else ICON_SERVICE))
        item.setData(0, self.SERVICE_ID_ROLE, service.id)
        item.setData(0, self.IS_FOLDER_ROLE, service.is_folder)
        item.setData(0, self.PARENT_ID_ROLE, service.parent_id)
        if service.is_folder:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        for child in service.children:
            if not child.deleted:
                item.addChild(self._build_item(child))
        return item

    def _selected_item(self) -> QTreeWidgetItem | None:
        return self.tree.currentItem()

    def _selected_service_id(self) -> int | None:
        item = self._selected_item()
        if item is None:
            return None
        return item.data(0, self.SERVICE_ID_ROLE)

    def _selected_parent_id_for_create(self) -> int | None:
        item = self._selected_item()
        if item is None:
            return None
        if item.data(0, self.IS_FOLDER_ROLE):
            return item.data(0, self.SERVICE_ID_ROLE)
        return item.data(0, self.PARENT_ID_ROLE)

    def _add_folder(self) -> None:
        self._create(is_folder=True)

    def _add_service(self) -> None:
        self._create(is_folder=False)

    def _create(self, is_folder: bool, parent_id: int | None = None, use_selection: bool = True) -> None:
        if use_selection:
            parent_id = self._selected_parent_id_for_create()
        dialog = MedServiceDialog(is_folder=is_folder, parent_id=parent_id)
        if dialog.exec_() != MedServiceDialog.Accepted:
            return

        try:
            if is_folder:
                self.med_service_service.create_folder(dialog.data())
            else:
                self.med_service_service.create_service(dialog.data())
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _edit_selected(self, *args) -> None:
        service_id = self._selected_service_id()
        if service_id is None:
            self._show_error("Выберите элемент")
            return

        try:
            service = self.med_service_service.get_med_service(service_id)
        except DomainError as exc:
            self._show_error(str(exc))
            return

        dialog = MedServiceDialog(is_folder=service.is_folder, service=service)
        if dialog.exec_() != MedServiceDialog.Accepted:
            return
        try:
            self.med_service_service.update_med_service(service.id, dialog.data())
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _delete_selected(self) -> None:
        service_id = self._selected_service_id()
        item = self._selected_item()
        if service_id is None or item is None:
            self._show_error("Выберите элемент")
            return

        name = item.text(0)
        confirmed = QMessageBox.question(self, "Удалить", f"Удалить «{name}»?")
        if confirmed != QMessageBox.Yes:
            return
        try:
            self.med_service_service.delete_med_service(service_id)
        except DomainError as exc:
            self._show_error(str(exc))
            return
        self.reload()

    def _open_context_menu(self, position) -> None:
        item = self.tree.itemAt(position)
        if item is not None:
            self.tree.setCurrentItem(item)

        parent_id = self._parent_id_for_context_item(item)
        has_item = item is not None

        menu = QMenu(self)
        add_folder_action = menu.addAction(icon_for(ICON_FOLDER), "Создать папку")
        add_service_action = menu.addAction(icon_for(ICON_NEW), "Создать услугу")
        menu.addSeparator()
        edit_action = menu.addAction(icon_for(ICON_EDIT), "Редактировать")
        delete_action = menu.addAction(icon_for(ICON_DELETE), "Удалить")
        edit_action.setEnabled(has_item)
        delete_action.setEnabled(has_item)
        menu.addSeparator()
        expand_action = menu.addAction("Раскрыть ветку")
        collapse_action = menu.addAction("Свернуть ветку")
        expand_action.setEnabled(has_item and item.childCount() > 0)
        collapse_action.setEnabled(has_item and item.childCount() > 0)
        menu.addSeparator()
        expand_all_action = menu.addAction("Раскрыть все")
        collapse_all_action = menu.addAction("Свернуть все")

        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        if action == add_folder_action:
            self._create(is_folder=True, parent_id=parent_id, use_selection=False)
        elif action == add_service_action:
            self._create(is_folder=False, parent_id=parent_id, use_selection=False)
        elif action == edit_action:
            self._edit_selected()
        elif action == delete_action:
            self._delete_selected()
        elif action == expand_action:
            self.tree.expandItem(item)
        elif action == collapse_action:
            self.tree.collapseItem(item)
        elif action == expand_all_action:
            self.tree.expandAll()
        elif action == collapse_all_action:
            self.tree.collapseAll()

    def _parent_id_for_context_item(self, item: QTreeWidgetItem | None) -> int | None:
        if item is None:
            return None
        if item.data(0, self.IS_FOLDER_ROLE):
            return item.data(0, self.SERVICE_ID_ROLE)
        return item.data(0, self.PARENT_ID_ROLE)

    def _apply_filter(self) -> None:
        query = self.search_input.text().strip().lower()
        visible_count = 0
        for index in range(self.tree.topLevelItemCount()):
            visible_count += self._filter_item(self.tree.topLevelItem(index), query)
        if query:
            self.tree.expandAll()
            self.summary_label.setText(f"Показано: {visible_count} из {self.total_count}")
        else:
            self.summary_label.setText(f"Всего элементов: {self.total_count}")

    def _filter_item(self, item: QTreeWidgetItem, query: str) -> int:
        own_match = not query or self._item_text(item).find(query) >= 0
        visible_children = 0
        for index in range(item.childCount()):
            visible_children += self._filter_item(item.child(index), query)
        visible = own_match or visible_children > 0
        item.setHidden(not visible)
        return (1 if visible and own_match else 0) + visible_children

    def _item_text(self, item: QTreeWidgetItem) -> str:
        return " ".join(item.text(column).lower() for column in range(item.columnCount()))

    def _update_selection(self, *args) -> None:
        item = self._selected_item()
        has_selection = item is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        if item is None:
            self.details_label.setText("Выберите папку или услугу")
            return

        is_folder = item.data(0, self.IS_FOLDER_ROLE)
        kind = "Папка" if is_folder else "Услуга"
        if is_folder:
            self.details_label.setText(f"{kind}: {item.text(0)}")
            return
        self.details_label.setText(
            f"{kind}: {item.text(0)} | Код: {item.text(1) or '-'} | Ед.: {item.text(2) or '-'} | "
            f"Цена: {item.text(3) or '0'} | НДС: {item.text(4) or '0'}"
        )

    def _resize_columns(self) -> None:
        for column in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(column)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Роддом №4", message)
