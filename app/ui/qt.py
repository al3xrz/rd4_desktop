from __future__ import annotations


try:
    from PySide2.QtCore import QAbstractTableModel, QDateTime, QModelIndex, QSortFilterProxyModel, Qt, Signal
    from PySide2.QtGui import QBrush, QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap
    from PySide2.QtWidgets import (
        QAction,
        QApplication,
        QButtonGroup,
        QDialogButtonBox,
        QDoubleSpinBox,
        QFormLayout,
        QGridLayout,
        QDialog,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QGroupBox,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QComboBox,
        QDateTimeEdit,
        QSizePolicy,
        QStackedWidget,
        QStatusBar,
        QStyle,
        QScrollArea,
        QShortcut,
        QTableView,
        QTabWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
        QCheckBox,
    )
except ImportError as exc:  # pragma: no cover - depends on local desktop runtime
    raise RuntimeError("PySide2 is required to launch RD4 desktop UI.") from exc
