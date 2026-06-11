from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPlainTextEdit,
    QDialogButtonBox, QCheckBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from src.services.svn_service import SvnService
from src.services.worker_thread import WorkerThread
from src.models.svn_status import SvnItemStatus


STATUS_ICONS = {
    SvnItemStatus.MODIFIED: ("●", QColor("#F44336"), "已修改"),
    SvnItemStatus.ADDED: ("✚", QColor("#2196F3"), "已添加"),
    SvnItemStatus.DELETED: ("✖", QColor("#F44336"), "已删除"),
    SvnItemStatus.CONFLICTED: ("⚠", QColor("#FF9800"), "冲突"),
    SvnItemStatus.UNVERSIONED: ("?", QColor("#9E9E9E"), "未版本控制"),
    SvnItemStatus.MISSING: ("!", QColor("#F44336"), "丢失"),
    SvnItemStatus.REPLACED: ("☑", QColor("#9C27B0"), "已替换"),
}


class CommitDialog(QDialog):
    commit_completed = Signal(int)

    def __init__(self, statuses: list, working_copy: str, parent=None):
        super().__init__(parent)
        self._statuses = statuses
        self._working_copy = working_copy
        self._thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("提交变更")
        self.resize(550, 480)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("待提交文件:"))

        self._file_list = QListWidget()
        for s in self._statuses:
            item = QListWidgetItem()
            icon_char, color, label = STATUS_ICONS.get(
                s.status, ("●", QColor("#000000"), "未知")
            )
            item.setText(f"{icon_char}  {s.path}  [{label}]")
            item.setForeground(color)
            item.setData(Qt.ItemDataRole.UserRole, s.path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if s.status != SvnItemStatus.UNVERSIONED:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self._file_list.addItem(item)
        layout.addWidget(self._file_list)

        layout.addWidget(QLabel("提交信息:"))
        self._message_edit = QPlainTextEdit()
        self._message_edit.setPlaceholderText("请输入提交信息（必填）")
        self._message_edit.setMaximumHeight(100)
        layout.addWidget(self._message_edit)

        self._update_after_check = QCheckBox("提交后更新到最新")
        layout.addWidget(self._update_after_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("提交")
        buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._on_commit)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_commit(self):
        checked_paths = []
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_paths.append(item.data(Qt.ItemDataRole.UserRole))

        if not checked_paths:
            QMessageBox.warning(self, "提示", "请至少选择一个文件进行提交。")
            return

        message = self._message_edit.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "提示", "请输入提交信息。")
            return

        self._set_controls_enabled(False)

        self._thread = WorkerThread(
            self._do_commit, checked_paths, message, self._working_copy,
            self._update_after_check.isChecked()
        )
        self._thread.finished.connect(self._on_commit_finished)
        self._thread.error.connect(self._on_commit_error)
        self._thread.start()

    def _do_commit(self, paths, message, working_copy, update_after):
        revision = SvnService.commit(paths, message)
        if update_after:
            SvnService.update(working_copy)
        return revision

    def _on_commit_finished(self, revision):
        self._set_controls_enabled(True)
        QMessageBox.information(self, "提交成功", f"提交成功！新版本号: {revision}")
        self.commit_completed.emit(revision)
        self.accept()

    def _on_commit_error(self, error_msg):
        self._set_controls_enabled(True)
        QMessageBox.critical(self, "提交失败", error_msg)

    def _set_controls_enabled(self, enabled):
        self._file_list.setEnabled(enabled)
        self._message_edit.setEnabled(enabled)
        self._update_after_check.setEnabled(enabled)
