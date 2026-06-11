import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QModelIndex, QDir
from PySide6.QtGui import QFileSystemModel, QColor, QDesktopServices
from PySide6.QtCore import QUrl

from src.models.svn_status import SvnStatus, SvnItemStatus


STATUS_ICONS = {
    SvnItemStatus.NORMAL: ("●", QColor("#4CAF50")),
    SvnItemStatus.MODIFIED: ("●", QColor("#F44336")),
    SvnItemStatus.ADDED: ("✚", QColor("#2196F3")),
    SvnItemStatus.DELETED: ("✖", QColor("#F44336")),
    SvnItemStatus.CONFLICTED: ("⚠", QColor("#FF9800")),
    SvnItemStatus.UNVERSIONED: ("?", QColor("#9E9E9E")),
    SvnItemStatus.MISSING: ("!", QColor("#F44336")),
    SvnItemStatus.REPLACED: ("☑", QColor("#9C27B0")),
}


class _SvnFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_map = {}

    def set_status_map(self, status_map: dict):
        self._status_map = status_map
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and index.column() == 0:
            file_path = self.filePath(index)
            status = self._status_map.get(file_path)
            if status:
                icon, color = STATUS_ICONS.get(status.status, ("", QColor()))
                name = super().data(index, role)
                return f"{icon} {name}"
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 0:
            file_path = self.filePath(index)
            status = self._status_map.get(file_path)
            if status:
                _, color = STATUS_ICONS.get(status.status, ("", QColor()))
                return color
        return super().data(index, role)


class RepoBrowser(QWidget):
    file_double_clicked = Signal(str)
    context_menu_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._working_copy_path = ""
        self._statuses = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._model = _SvnFileSystemModel(self)
        self._model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.doubleClicked.connect(self._on_double_clicked)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        self._tree.hideColumn(1)
        self._tree.hideColumn(2)
        self._tree.hideColumn(3)

        layout.addWidget(self._tree)

    def load_working_copy(self, path: str, statuses: list):
        self._working_copy_path = path
        self._statuses = statuses
        root_index = self._model.setRootPath(path)
        self._tree.setRootIndex(root_index)

        status_map = {}
        for s in statuses:
            abs_path = os.path.normpath(s.path)
            status_map[abs_path] = s
        self._model.set_status_map(status_map)

    def get_selected_paths(self) -> list:
        paths = []
        for index in self._tree.selectionModel().selectedRows(0):
            paths.append(self._model.filePath(index))
        return paths

    def _on_context_menu(self, pos):
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return
        file_path = self._model.filePath(index)
        action = "file" if os.path.isfile(file_path) else "dir"
        self.context_menu_requested.emit(file_path, action)

    def _on_double_clicked(self, index):
        file_path = self._model.filePath(index)
        if os.path.isfile(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
