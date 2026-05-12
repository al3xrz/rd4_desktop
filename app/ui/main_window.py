from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.core.config import settings
from app.core.paths import get_resource_path
from app.models import User
from app.ui.contract_details_page import ContractDetailsPage
from app.ui.contracts_page import ContractsPage
from app.ui.med_services_page import MedServicesPage
from app.ui.icons import (
    ICON_BACK,
    ICON_CONTRACT,
    ICON_EXIT,
    ICON_NEW,
    ICON_REFRESH,
    ICON_SERVICE,
    ICON_USERS,
    icon_for,
    set_button_icon,
)
from app.ui.qt import (
    QAction,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from app.ui.users_page import UsersPage


class MainWindow(QMainWindow):
    def __init__(self, current_user: User) -> None:
        super().__init__()
        self.current_user = current_user
        self.contracts_page_index = 0
        self.last_contract_id: int | None = None
        self.details_page: QWidget | None = None
        self.page_indexes: dict[str, int] = {}
        self.setWindowTitle("Роддом №4")
        self.resize(1100, 720)

        self.pages = QStackedWidget()
        self.pages.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.contracts_page = ContractsPage(current_user, on_open_contract=self.open_contract_details)
        self.contracts_page_index = self._add_page("contracts", "Договоры", self.contracts_page)
        self.med_services_page_index = self._add_page("med_services", "Справочник услуг", MedServicesPage())
        if self._has_role("admin"):
            self.users_page_index = self._add_page("users", "Пользователи", UsersPage(current_user))

        self.setCentralWidget(self.pages)
        self._setup_menu()

        self.setStatusBar(QStatusBar())
        role = getattr(current_user.role, "value", current_user.role)
        self.statusBar().showMessage(f"{current_user.username} | {role} | база: {settings.database_path}")
        self._set_page(self.contracts_page_index)

    def _add_page(self, key: str, title: str, page: QWidget | None = None) -> int:
        if page is None:
            page = QFrame()
            layout = QVBoxLayout()
            heading = QLabel(title)
            heading.setStyleSheet("font-size: 20px; font-weight: 600;")
            layout.addWidget(heading)
            layout.addStretch()
            page.setLayout(layout)
        if key != "contracts":
            page = self._with_back_button(page)
        index = self.pages.addWidget(page)
        self.page_indexes[key] = index
        return index

    def _with_back_button(self, page: QWidget) -> QWidget:
        back_button = QPushButton("К списку договоров")
        set_button_icon(back_button, ICON_BACK)
        back_button.clicked.connect(self.show_contracts_page)

        header = QHBoxLayout()
        header.addWidget(back_button)
        header.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(page)

        wrapper = QWidget()
        wrapper.setLayout(layout)
        return wrapper

    def _setup_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        new_contract_action = QAction(icon_for(ICON_CONTRACT), "Новый договор", self)
        new_contract_action.setShortcut("Ctrl+N")
        new_contract_action.triggered.connect(self.create_contract)
        file_menu.addAction(new_contract_action)
        refresh_action = QAction(icon_for(ICON_REFRESH), "Обновить список", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_contracts)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction(icon_for(ICON_EXIT), "Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = self.menuBar().addMenu("Настройки")
        users_index = self.page_indexes.get("users")
        if users_index is not None:
            users_action = QAction(icon_for(ICON_USERS), "Пользователи", self)
            users_action.triggered.connect(lambda: self._set_page(users_index))
            settings_menu.addAction(users_action)

        med_services_action = QAction(icon_for(ICON_SERVICE), "Справочник услуг", self)
        med_services_action.triggered.connect(lambda: self._set_page(self.med_services_page_index))
        settings_menu.addAction(med_services_action)
        settings_menu.addSeparator()
        data_dir_action = QAction("Папка данных", self)
        data_dir_action.triggered.connect(lambda: self._open_path(settings.data_dir))
        settings_menu.addAction(data_dir_action)
        templates_action = QAction("Шаблоны документов", self)
        templates_action.triggered.connect(lambda: self._open_path(get_resource_path("app", "templates", "docx")))
        settings_menu.addAction(templates_action)

    def _set_page(self, index: int) -> None:
        if index >= 0:
            self.pages.setCurrentIndex(index)

    def create_contract(self) -> None:
        if self.pages.widget(self.contracts_page_index) is not self.contracts_page:
            self.show_contracts_page()
        self._set_page(self.contracts_page_index)
        self.contracts_page.create_contract()

    def refresh_contracts(self) -> None:
        self.show_contracts_page()
        self.contracts_page.reload()
        self.statusBar().showMessage(f"{self.current_user.username} | список обновлён | база: {settings.database_path}")

    def open_contract_details(self, contract_id: int) -> None:
        self.last_contract_id = contract_id
        self._remove_details_page()
        details_page = ContractDetailsPage(
            contract_id,
            self.current_user,
            on_back=lambda: self.close_contract_details(contract_id),
        )
        self.details_page = details_page
        self.pages.addWidget(details_page)
        self.pages.setCurrentWidget(details_page)

    def close_contract_details(self, focus_contract_id: int | None = None) -> None:
        if focus_contract_id is not None:
            self.contracts_page.last_focused_contract_id = focus_contract_id
        self.contracts_page.reload()
        self.show_contracts_page(focus_contract_id)
        self._remove_details_page()

    def show_contracts_page(self, focus_contract_id: int | None = None) -> None:
        if focus_contract_id is not None:
            self.last_contract_id = focus_contract_id
        self.pages.setCurrentWidget(self.contracts_page)
        self.contracts_page.focus_contract(self.last_contract_id)

    def _remove_details_page(self) -> None:
        if self.details_page is None:
            return
        self.pages.removeWidget(self.details_page)
        self.details_page.deleteLater()
        self.details_page = None

    def _open_path(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return
        subprocess.Popen(["xdg-open", str(path)])

    def _has_role(self, role: str) -> bool:
        current_role = getattr(self.current_user.role, "value", self.current_user.role)
        return current_role == role
