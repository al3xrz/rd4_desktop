from __future__ import annotations

from app.ui.qt import QSize, QSizePolicy, QToolBar, QToolButton, Qt


TOOLBAR_ICON_SIZE = QSize(18, 18)
TOOLBAR_BUTTON_MIN_WIDTH = 58
TOOLBAR_STYLE = (
    "QToolBar { border: none; spacing: 2px; background: transparent; }"
    "QToolButton { padding: 2px 5px; }"
)


def make_toolbar() -> QToolBar:
    toolbar = QToolBar()
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setIconSize(TOOLBAR_ICON_SIZE)
    toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    toolbar.setStyleSheet(TOOLBAR_STYLE)
    return toolbar


def make_toolbar_button(text: str, tooltip: str) -> QToolButton:
    button = QToolButton()
    button.setText(text)
    button.setToolTip(tooltip)
    button.setIconSize(TOOLBAR_ICON_SIZE)
    button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    button.setMinimumWidth(TOOLBAR_BUTTON_MIN_WIDTH)
    return button
