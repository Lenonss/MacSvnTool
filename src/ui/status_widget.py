from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from src.models.svn_status import SvnStatus, SvnItemStatus


STATUS_ICONS = {
    SvnItemStatus.NORMAL: "●",
    SvnItemStatus.MODIFIED: "●",
    SvnItemStatus.ADDED: "✚",
    SvnItemStatus.DELETED: "✖",
    SvnItemStatus.CONFLICTED: "⚠",
    SvnItemStatus.UNVERSIONED: "?",
    SvnItemStatus.MISSING: "!",
    SvnItemStatus.REPLACED: "☑",
}

STATUS_COLORS = {
    SvnItemStatus.NORMAL: QColor("#4CAF50"),
    SvnItemStatus.MODIFIED: QColor("#F44336"),
    SvnItemStatus.ADDED: QColor("#2196F3"),
    SvnItemStatus.DELETED: QColor("#F44336"),
    SvnItemStatus.CONFLICTED: QColor("#FF9800"),
    SvnItemStatus.UNVERSIONED: QColor("#9E9E9E"),
    SvnItemStatus.MISSING: QColor("#F44336"),
    SvnItemStatus.REPLACED: QColor("#9C27B0"),
}

STATUS_LABELS = {
    SvnItemStatus.NORMAL: "正常",
    SvnItemStatus.MODIFIED: "已修改",
    SvnItemStatus.ADDED: "已添加",
    SvnItemStatus.DELETED: "已删除",
    SvnItemStatus.CONFLICTED: "冲突",
    SvnItemStatus.UNVERSIONED: "未版本控制",
    SvnItemStatus.MISSING: "丢失",
    SvnItemStatus.REPLACED: "已替换",
}


class _StatusModel(QAbstractTableModel):
    COLUMNS = ["文件名", "状态", "版本号", "最后修改者", "最后修改时间"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def set_items(self, items: list):
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                icon = STATUS_ICONS.get(item.status, "●")
                return f"{icon} {item.path}"
            elif col == 1:
                return STATUS_LABELS.get(item.status, "未知")
            elif col == 2:
                return str(item.revision) if item.revision else ""
            elif col == 3:
                return item.last_author
            elif col == 4:
                return item.last_date
        if role == Qt.ItemDataRole.ForegroundRole and col == 0:
            return STATUS_COLORS.get(item.status, QColor())
        if role == Qt.ItemDataRole.UserRole:
            return item
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        reverse = order == Qt.SortOrder.DescendingOrder
        if column == 2:
            self._items.sort(key=lambda x: x.revision, reverse=reverse)
        elif column == 4:
            self._items.sort(key=lambda x: x.last_date, reverse=reverse)
        else:
            self._items.sort(key=lambda x: self.data(self.index(0, column), Qt.ItemDataRole.DisplayRole) or "", reverse=reverse)
        self.layoutChanged.emit()


class StatusWidget(QWidget):
    commit_requested = Signal()
    revert_requested = Signal(list)
    add_requested = Signal(list)
    diff_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._model = _StatusModel(self)

        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)

        self._tree = QTreeView()
        self._tree.setModel(self._proxy)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._tree.setAlternatingRowColors(True)
        self._tree.doubleClicked.connect(self._on_double_clicked)

        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._tree)

    def load_status(self, statuses: list):
        items = [s for s in statuses if s.status != SvnItemStatus.NORMAL]
        self._model.set_items(items)

    def get_selected_paths(self) -> list:
        paths = []
        for index in self._tree.selectionModel().selectedRows(0):
            source_index = self._proxy.mapToSource(index)
            item = self._model.data(source_index, Qt.ItemDataRole.UserRole)
            if item:
                paths.append(item.path)
        return paths

    def refresh(self):
        pass

    def _on_double_clicked(self, index):
        source_index = self._proxy.mapToSource(index)
        item = self._model.data(source_index, Qt.ItemDataRole.UserRole)
        if item:
            self.diff_requested.emit(item.path)
