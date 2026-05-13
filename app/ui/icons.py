from __future__ import annotations

from app.ui.qt import QApplication, QBrush, QColor, QDialogButtonBox, QIcon, QPainter, QPen, QPixmap, QSize, Qt, QStyle

try:
    import qtawesome as qta
except ImportError:  # pragma: no cover - optional UI dependency fallback
    qta = None


ICON_COLOR = "#334155"
ICON_DANGER = "#b42318"
ICON_SUCCESS = "#2e7d32"
ICON_WARNING = "#a16207"
DIALOG_ICON_SIZE = QSize(18, 18)


def set_button_icon(button, pixmap: int) -> None:
    button.setIcon(icon_for(pixmap))


def set_dialog_button_icon(button, pixmap: int) -> None:
    set_button_icon(button, pixmap)
    button.setIconSize(DIALOG_ICON_SIZE)


def set_dialog_button_icons(buttons: QDialogButtonBox) -> None:
    icons = {
        QDialogButtonBox.Save: ICON_SAVE,
        QDialogButtonBox.Ok: ICON_OK,
        QDialogButtonBox.Cancel: ICON_CANCEL,
    }
    for role, pixmap in icons.items():
        button = buttons.button(role)
        if button is not None:
            set_dialog_button_icon(button, pixmap)


def icon_for(pixmap: int):
    awesome = _qtawesome_icon(pixmap)
    if awesome is not None:
        return awesome
    if pixmap == ICON_NEW:
        return _plus_icon()
    if pixmap == ICON_EDIT:
        return _pencil_icon()
    if pixmap == ICON_FOLDER:
        return _folder_icon()
    if pixmap == ICON_SERVICE:
        return _service_icon()
    if pixmap == ICON_USERS:
        return _users_icon()
    if pixmap == ICON_REPORTS:
        return _reports_icon()
    if pixmap == ICON_FINANCIAL_REPORT:
        return _financial_report_icon()
    if pixmap == ICON_MATRIX_REPORT:
        return _matrix_report_icon()
    if pixmap == ICON_ABOUT:
        return QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation)
    if pixmap == ICON_EXIT:
        return _exit_icon()
    if pixmap == ICON_PASSWORD:
        return _key_icon()
    if pixmap == ICON_CONTRACT:
        return _contract_icon()
    if pixmap == ICON_SAVE:
        return QApplication.style().standardIcon(QStyle.SP_DialogSaveButton)
    if pixmap == ICON_OK:
        return QApplication.style().standardIcon(QStyle.SP_DialogOkButton)
    if pixmap == ICON_CANCEL:
        return QApplication.style().standardIcon(QStyle.SP_DialogCancelButton)
    if pixmap == ICON_SAVE_PRINT:
        return QApplication.style().standardIcon(QStyle.SP_DialogSaveButton)
    return QApplication.style().standardIcon(pixmap)


def _qtawesome_icon(pixmap: int) -> QIcon | None:
    if qta is None:
        return None

    icons = {
        ICON_BACK: ("fa5s.arrow-left", ICON_COLOR),
        ICON_CONTRACT: ("fa5s.file-contract", ICON_COLOR),
        ICON_DELETE: ("fa5s.trash-alt", ICON_DANGER),
        ICON_EDIT: ("fa5s.pen", ICON_COLOR),
        ICON_EXIT: ("fa5s.sign-out-alt", ICON_DANGER),
        ICON_FOLDER: ("fa5s.folder", ICON_WARNING),
        ICON_NEW: ("fa5s.plus", ICON_SUCCESS),
        ICON_OPEN: ("fa5s.folder-open", ICON_COLOR),
        ICON_PASSWORD: ("fa5s.key", ICON_WARNING),
        ICON_PRINT: ("fa5s.print", ICON_COLOR),
        ICON_REFRESH: ("fa5s.sync-alt", ICON_COLOR),
        ICON_RESET: ("fa5s.eraser", ICON_COLOR),
        ICON_REFUND: ("fa5s.undo-alt", ICON_WARNING),
        ICON_REPORTS: ("fa5s.file-alt", ICON_COLOR),
        ICON_FINANCIAL_REPORT: ("fa5s.file-invoice-dollar", ICON_SUCCESS),
        ICON_MATRIX_REPORT: ("fa5s.table", ICON_COLOR),
        ICON_ABOUT: ("fa5s.info-circle", ICON_COLOR),
        ICON_SERVICE: ("fa5s.briefcase-medical", ICON_COLOR),
        ICON_SETTINGS: ("fa5s.cog", ICON_COLOR),
        ICON_USERS: ("fa5s.users", ICON_COLOR),
        ICON_SAVE: ("fa5s.save", ICON_SUCCESS),
        ICON_OK: ("fa5s.check", ICON_SUCCESS),
        ICON_CANCEL: ("fa5s.times", ICON_DANGER),
        ICON_SAVE_PRINT: ("fa5s.print", ICON_COLOR),
    }
    icon_name, color = icons.get(pixmap, ("", ""))
    if not icon_name:
        return None
    try:
        return qta.icon(icon_name, color=color)
    except Exception:
        return None


def _plus_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor("#2e9d45")))
    painter.setPen(QPen(QColor("#1f7a33"), 1))
    painter.drawEllipse(3, 3, 18, 18)
    painter.setPen(QPen(QColor("#ffffff"), 3))
    painter.drawLine(12, 7, 12, 17)
    painter.drawLine(7, 12, 17, 12)
    painter.end()
    return QIcon(pixmap)


def _pencil_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#5c4630"), 3))
    painter.drawLine(7, 17, 17, 7)
    painter.setPen(QPen(QColor("#f2c94c"), 5))
    painter.drawLine(6, 18, 16, 8)
    painter.setPen(QPen(QColor("#2f80ed"), 3))
    painter.drawLine(15, 7, 18, 10)
    painter.setPen(QPen(QColor("#5c4630"), 2))
    painter.drawLine(5, 19, 8, 18)
    painter.end()
    return QIcon(pixmap)


def _folder_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#b88718"), 1))
    painter.setBrush(QBrush(QColor("#f2c14e")))
    painter.drawRoundedRect(3, 7, 18, 13, 2, 2)
    painter.setBrush(QBrush(QColor("#ffd66b")))
    painter.drawRoundedRect(3, 5, 8, 5, 2, 2)
    painter.end()
    return QIcon(pixmap)


def _service_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#2f80ed"), 1))
    painter.setBrush(QBrush(QColor("#d8e9ff")))
    painter.drawRoundedRect(5, 3, 14, 18, 2, 2)
    painter.setPen(QPen(QColor("#2f80ed"), 2))
    painter.drawLine(8, 9, 16, 9)
    painter.drawLine(8, 13, 16, 13)
    painter.drawLine(8, 17, 13, 17)
    painter.end()
    return QIcon(pixmap)


def _users_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#2f80ed"), 1))
    painter.setBrush(QBrush(QColor("#d8e9ff")))
    painter.drawEllipse(9, 4, 6, 6)
    painter.drawRoundedRect(6, 12, 12, 8, 4, 4)
    painter.setBrush(QBrush(QColor("#e8f1ff")))
    painter.drawEllipse(4, 8, 5, 5)
    painter.drawEllipse(15, 8, 5, 5)
    painter.end()
    return QIcon(pixmap)


def _reports_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#6f42c1"), 1))
    painter.setBrush(QBrush(QColor("#eee3ff")))
    painter.drawRoundedRect(5, 3, 14, 18, 2, 2)
    painter.setBrush(QBrush(QColor("#6f42c1")))
    painter.drawRect(8, 15, 2, 3)
    painter.drawRect(11, 11, 2, 7)
    painter.drawRect(14, 8, 2, 10)
    painter.end()
    return QIcon(pixmap)


def _financial_report_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#2e7d32"), 1))
    painter.setBrush(QBrush(QColor("#e7f6e7")))
    painter.drawRoundedRect(5, 3, 14, 18, 2, 2)
    painter.setPen(QPen(QColor("#2e7d32"), 2))
    painter.drawLine(8, 9, 16, 9)
    painter.drawLine(8, 13, 16, 13)
    painter.setPen(QPen(QColor("#2e7d32"), 1))
    painter.drawEllipse(9, 15, 6, 3)
    painter.end()
    return QIcon(pixmap)


def _matrix_report_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#334155"), 1))
    painter.setBrush(QBrush(QColor("#f1f5f9")))
    painter.drawRoundedRect(4, 5, 16, 14, 2, 2)
    painter.drawLine(4, 10, 20, 10)
    painter.drawLine(4, 14, 20, 14)
    painter.drawLine(9, 5, 9, 19)
    painter.drawLine(15, 5, 15, 19)
    painter.end()
    return QIcon(pixmap)


def _exit_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#b00020"), 2))
    painter.drawLine(6, 5, 6, 19)
    painter.drawLine(6, 5, 14, 5)
    painter.drawLine(6, 19, 14, 19)
    painter.drawLine(12, 12, 20, 12)
    painter.drawLine(17, 9, 20, 12)
    painter.drawLine(17, 15, 20, 12)
    painter.end()
    return QIcon(pixmap)


def _key_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#b88718"), 2))
    painter.drawEllipse(4, 8, 7, 7)
    painter.drawLine(11, 12, 20, 12)
    painter.drawLine(17, 12, 17, 15)
    painter.drawLine(20, 12, 20, 15)
    painter.end()
    return QIcon(pixmap)


def _contract_icon() -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#2f80ed"), 1))
    painter.setBrush(QBrush(QColor("#ffffff")))
    painter.drawRoundedRect(5, 3, 14, 18, 2, 2)
    painter.setPen(QPen(QColor("#2f80ed"), 2))
    painter.drawLine(8, 8, 16, 8)
    painter.drawLine(8, 12, 16, 12)
    painter.drawLine(8, 16, 13, 16)
    painter.end()
    return QIcon(pixmap)


ICON_BACK = QStyle.SP_ArrowBack
ICON_ABOUT = -15
ICON_CONTRACT = -8
ICON_DELETE = QStyle.SP_TrashIcon
ICON_EDIT = -2
ICON_EXIT = -7
ICON_FINANCIAL_REPORT = -16
ICON_FOLDER = -3
ICON_NEW = QStyle.SP_FileIcon
ICON_OPEN = QStyle.SP_DialogOpenButton
ICON_PASSWORD = -9
ICON_PRINT = QStyle.SP_DialogSaveButton
ICON_REFRESH = QStyle.SP_BrowserReload
ICON_RESET = QStyle.SP_DialogResetButton
ICON_REFUND = -10
ICON_REPORTS = -6
ICON_MATRIX_REPORT = -17
ICON_SERVICE = -4
ICON_SETTINGS = QStyle.SP_FileDialogListView
ICON_USERS = -5
ICON_SAVE = -11
ICON_OK = -12
ICON_CANCEL = -13
ICON_SAVE_PRINT = -14
