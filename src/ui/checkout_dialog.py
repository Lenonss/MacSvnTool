import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QLabel, QGroupBox, QSpinBox,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal

from src.services.svn_service import SvnService, SvnError
from src.services.worker_thread import WorkerThread


class CheckoutDialog(QDialog):
    checkout_completed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("检出仓库")
        self.resize(520, 260)

        main_layout = QVBoxLayout(self)

        form = QFormLayout()
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("例如: http://svn.example.com/repo/trunk")
        form.addRow("仓库URL:", self._url_edit)

        path_layout = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("选择或输入本地目标路径")
        path_layout.addWidget(self._path_edit)
        self._browse_btn = QPushButton("选择...")
        self._browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self._browse_btn)
        form.addRow("目标路径:", path_layout)

        main_layout.addLayout(form)

        version_group = QGroupBox("版本")
        version_layout = QVBoxLayout(version_group)
        self._radio_head = QRadioButton("HEAD（最新版本）")
        self._radio_head.setChecked(True)
        self._radio_specific = QRadioButton("指定版本号:")
        version_layout.addWidget(self._radio_head)
        spec_layout = QHBoxLayout()
        spec_layout.addWidget(self._radio_specific)
        self._revision_spin = QSpinBox()
        self._revision_spin.setRange(1, 999999)
        self._revision_spin.setEnabled(False)
        self._radio_specific.toggled.connect(self._revision_spin.setEnabled)
        spec_layout.addWidget(self._revision_spin)
        spec_layout.addStretch()
        version_layout.addLayout(spec_layout)

        self._radio_group = QButtonGroup()
        self._radio_group.addButton(self._radio_head)
        self._radio_group.addButton(self._radio_specific)

        main_layout.addWidget(version_group)
        main_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("检出")
        buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._on_checkout)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if path:
            self._path_edit.setText(path)

    def _on_checkout(self):
        url = self._url_edit.text().strip()
        target_path = self._path_edit.text().strip()

        if not url:
            QMessageBox.warning(self, "提示", "请输入仓库URL。")
            return
        if not target_path:
            QMessageBox.warning(self, "提示", "请选择目标路径。")
            return
        if os.path.exists(target_path) and os.listdir(target_path):
            QMessageBox.warning(self, "提示", "目标目录已存在且不为空，请选择其他路径。")
            return

        revision = "HEAD"
        if self._radio_specific.isChecked():
            revision = str(self._revision_spin.value())

        self._set_controls_enabled(False)
        self._thread = WorkerThread(self._do_checkout, url, target_path, revision)
        self._thread.finished.connect(self._on_checkout_finished)
        self._thread.error.connect(self._on_checkout_error)
        self._thread.start()

    def _do_checkout(self, url, path, revision):
        SvnService.checkout(url, path)
        return path

    def _on_checkout_finished(self, result):
        self._set_controls_enabled(True)
        QMessageBox.information(self, "成功", "仓库检出成功！")
        self.checkout_completed.emit(result)
        self.accept()

    def _on_checkout_error(self, error_msg):
        self._set_controls_enabled(True)
        QMessageBox.critical(self, "检出失败", error_msg)

    def _set_controls_enabled(self, enabled):
        self._url_edit.setEnabled(enabled)
        self._path_edit.setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)
        self._radio_head.setEnabled(enabled)
        self._radio_specific.setEnabled(enabled)
        self._revision_spin.setEnabled(enabled and self._radio_specific.isChecked())
