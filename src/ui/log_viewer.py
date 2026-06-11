from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableView, QTextEdit, QPushButton, QLabel,
    QHeaderView, QSplitter, QAbstractItemView, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont

from src.services.svn_service import SvnService
from src.services.worker_thread import WorkerThread
from src.models.svn_log import SvnLogEntry


class _LogTableModel(QAbstractTableModel):
    COLUMNS = ["版本号", "作者", "日期", "信息"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []

    def set_entries(self, entries: list):
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def append_entries(self, entries: list):
        self.beginInsertRows(QModelIndex(), len(self._entries), len(self._entries) + len(entries) - 1)
        self._entries.extend(entries)
        self.endInsertRows()

    def get_entry(self, row: int):
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._entries)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        entry = self._entries[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return str(entry.revision)
            elif col == 1:
                return entry.author
            elif col == 2:
                return entry.date
            elif col == 3:
                msg = entry.message.split("\n")[0]
                return msg[:60] + "..." if len(msg) > 60 else msg
        if role == Qt.ItemDataRole.UserRole:
            return entry
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None


class LogViewer(QDialog):
    diff_requested = Signal(str, str)

    def __init__(self, working_copy: str, parent=None):
        super().__init__(parent)
        self._working_copy = working_copy
        self._page_size = 50
        self._current_to_rev = 0
        self._thread = None
        self._setup_ui()
        self._load_logs()

    def _setup_ui(self):
        self.setWindowTitle(f"提交日志 - {self._working_copy}")
        self.resize(750, 600)

        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table_model = _LogTableModel(self)
        self._table = QTableView()
        self._table.setModel(self._table_model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.clicked.connect(self._on_selection_changed)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        splitter.addWidget(self._table)

        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        font = QFont("Monospace", 10)
        self._detail.setFont(font)
        splitter.addWidget(self._detail)
        splitter.setSizes([300, 200])

        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        self._load_more_btn = QPushButton("加载更多")
        self._load_more_btn.clicked.connect(self._on_load_more)
        btn_layout.addWidget(self._load_more_btn)

        self._diff_btn = QPushButton("差异对比")
        self._diff_btn.setEnabled(False)
        self._diff_btn.clicked.connect(self._on_diff)
        btn_layout.addWidget(self._diff_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_logs(self):
        self._set_controls_enabled(False)
        to_rev = self._current_to_rev
        if to_rev == 0:
            rev_range = "HEAD:1"
        else:
            from_rev = to_rev - 1
            rev_range = f"{from_rev}:1"

        self._thread = WorkerThread(self._do_load_logs, rev_range)
        self._thread.finished.connect(self._on_logs_loaded)
        self._thread.error.connect(self._on_load_error)
        self._thread.start()

    def _do_load_logs(self, rev_range):
        entries = SvnService.log(self._working_copy, limit=self._page_size, revision=rev_range)
        return entries

    def _on_logs_loaded(self, entries):
        self._set_controls_enabled(True)
        if self._current_to_rev == 0:
            self._table_model.set_entries(entries)
        else:
            self._table_model.append_entries(entries)

        if entries:
            self._current_to_rev = entries[-1].revision
        if len(entries) < self._page_size:
            self._load_more_btn.setEnabled(False)

    def _on_load_error(self, error_msg):
        self._set_controls_enabled(True)

    def _on_load_more(self):
        self._load_logs()

    def _on_selection_changed(self, index):
        entry = self._table_model.get_entry(index.row())
        if not entry:
            return
        self._diff_btn.setEnabled(True)
        lines = [
            f"版本 {entry.revision} - {entry.author} - {entry.date}",
            "",
            entry.message,
            "",
            "变更文件:",
        ]
        for cp in entry.changed_paths:
            lines.append(f"  {cp.action}  {cp.path}")
        self._detail.setPlainText("\n".join(lines))

    def _on_diff(self):
        index = self._table.selectionModel().currentIndex()
        if not index.isValid():
            return
        entry = self._table_model.get_entry(index.row())
        if entry and entry.changed_paths:
            path = entry.changed_paths[0].path
            self.diff_requested.emit(path, str(entry.revision))

    def _set_controls_enabled(self, enabled):
        self._load_more_btn.setEnabled(enabled)
