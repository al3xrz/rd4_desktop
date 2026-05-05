from __future__ import annotations

import logging
import sys

from app.core.config import settings
from app.core.database import init_database
from app.core.logging import configure_logging
from app.core.migrations import run_migrations
from app.core.paths import get_log_file
from app.services.bootstrap import ensure_initial_admin


logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    try:
        run_app()
    except Exception:
        logger.exception("Critical startup error")
        show_critical_startup_error()
        raise


def run_app() -> None:
    init_database()
    run_migrations()
    configure_logging()
    initial_admin_created = ensure_initial_admin()
    logger.info("RD4 desktop started")
    logger.info("Data directory: %s", settings.data_dir)
    if initial_admin_created:
        logger.info("Initial admin user created")

    try:
        from app.ui.application import run_ui
    except RuntimeError as exc:
        logger.warning("%s", exc)
        return

    run_ui()


def show_critical_startup_error() -> None:
    message = f"Не удалось запустить Роддом №4.\nПодробности записаны в:\n{get_log_file()}"

    try:
        from app.ui.qt import QApplication, QMessageBox
    except RuntimeError:
        print(message, file=sys.stderr)
        return

    app = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.critical(None, "Роддом №4", message)


if __name__ == "__main__":
    main()
