from __future__ import annotations

import sys

from app.services.bootstrap import ensure_initial_admin
from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow
from app.ui.qt import QApplication


def run_ui() -> int:
    ensure_initial_admin()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(
        """
        QPushButton {
            min-height: 30px;
            padding: 6px 12px;
        }
        QDialogButtonBox QPushButton {
            min-width: 96px;
        }
        """
    )
    windows = {}

    login_window = LoginWindow()
    windows["login"] = login_window

    def open_main_window(user) -> None:
        main_window = MainWindow(user)
        windows["main"] = main_window
        main_window.show()

    login_window.login_success.connect(open_main_window)
    login_window.show()
    return app.exec_()
