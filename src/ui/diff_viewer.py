from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QComboBox, QPlainTextEdit, QSplitter, QLabel,
    QDialogButtonBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

from src.services.svn_service import SvnService
from src.services.worker_thread import WorkerThread


class DiffViewer(QDialog):
    def __init__(self, file_path: str, working_copy: str, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._working_copy = working_copy
        self._thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"差异对比 - {self._file_path}")
        self.resize(1000, 600)

        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("旧版本:"))
        self._old_combo = QComboBox()
        self._old_combo.addItems(["BASE", "WORKING", "HEAD"])
        self._old_combo.setCurrentText("BASE")
        top_layout.addWidget(self._old_combo)

        self._old_spec_spin = QSpinBox()
        self._old_spec_spin.setRange(1, 999999)
        self._old_spec_spin.setVisible(False)
        self._old_combo.currentTextChanged.connect(self._on_old_combo_changed)
        top_layout.addWidget(self._old_spec_spin)

        top_layout.addWidget(QLabel("  →  "))
        top_layout.addWidget(QLabel("新版本:"))
        self._new_combo = QComboBox()
        self._new_combo.addItems(["WORKING", "HEAD", "BASE"])
        self._new_combo.setCurrentText("WORKING")
        top_layout.addWidget(self._new_combo)

        self._new_spec_spin = QSpinBox()
        self._new_spec_spin.setRange(1, 999999)
        self._new_spec_spin.setVisible(False)
        self._new_combo.currentTextChanged.connect(self._on_new_combo_changed)
        top_layout.addWidget(self._new_spec_spin)

        self._diff_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._diff_btn.button(QDialogButtonBox.StandardButton.Ok).setText("显示差异")
        self._diff_btn.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._on_show_diff)
        top_layout.addStretch()
        top_layout.addWidget(self._diff_btn)

        layout.addLayout(top_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._old_edit = QPlainTextEdit()
        self._old_edit.setReadOnly(True)
        font = QFont("Monospace", 10)
        self._old_edit.setFont(font)
        splitter.addWidget(self._old_edit)

        self._new_edit = QPlainTextEdit()
        self._new_edit.setReadOnly(True)
        self._new_edit.setFont(font)
        splitter.addWidget(self._new_edit)

        splitter.setSizes([480, 480])
        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _on_old_combo_changed(self, text):
        self._old_spec_spin.setVisible(text not in ["BASE", "WORKING", "HEAD"])

    def _on_new_combo_changed(self, text):
        self._new_spec_spin.setVisible(text not in ["BASE", "WORKING", "HEAD"])

    def _on_show_diff(self):
        old_rev = self._old_combo.currentText()
        if old_rev not in ["BASE", "WORKING", "HEAD"]:
            old_rev = str(self._old_spec_spin.value())

        new_rev = self._new_combo.currentText()
        if new_rev not in ["BASE", "WORKING", "HEAD"]:
            new_rev = str(self._new_spec_spin.value())

        revision = f"{old_rev}:{new_rev}"
        self._thread = WorkerThread(self._do_load_diff, revision)
        self._thread.finished.connect(self._on_diff_loaded)
        self._thread.error.connect(lambda e: None)
        self._thread.start()

    def _do_load_diff(self, revision):
        diff_text = SvnService.diff(self._file_path, revision)
        return diff_text

    def _on_diff_loaded(self, diff_text):
        self._old_edit.clear()
        self._new_edit.clear()

        if not diff_text:
            self._old_edit.setPlainText("（无差异）")
            self._new_edit.setPlainText("（无差异）")
            return

        old_lines = []
        new_lines = []
        old_line_nums = []
        new_line_nums = []

        old_ln = 0
        new_ln = 0

        for line in diff_text.splitlines():
            if line.startswith("@@"):
                old_lines.append(line)
                new_lines.append(line)
                old_line_nums.append("")
                new_line_nums.append("")
                try:
                    parts = line.split("@@")
                    if len(parts) >= 2:
                        range_old = parts[1].strip()
                        range_new = parts[2].strip() if len(parts) >= 3 else ""
                        old_start = int(range_old.split(",")[0].lstrip("-"))
                        new_start = int(range_new.split(",")[0].lstrip("+"))
                        old_ln = old_start
                        new_ln = new_start
                except (ValueError, IndexError):
                    pass
            elif line.startswith("---") or line.startswith("+++") or line.startswith("Index:") or line.startswith("==="):
                old_lines.append(line)
                new_lines.append(line)
                old_line_nums.append("")
                new_line_nums.append("")
            elif line.startswith("-"):
                old_ln += 1
                old_lines.append(line)
                old_line_nums.append(str(old_ln))
                new_lines.append("")
                new_line_nums.append("")
            elif line.startswith("+"):
                new_ln += 1
                old_lines.append("")
                old_line_nums.append("")
                new_lines.append(line)
                new_line_nums.append(str(new_ln))
            else:
                old_ln += 1
                new_ln += 1
                old_lines.append(line)
                new_lines.append(line)
                old_line_nums.append(str(old_ln))
                new_line_nums.append(str(new_ln))

        self._render_diff(self._old_edit, old_lines, old_line_nums, is_old=True)
        self._render_diff(self._new_edit, new_lines, new_line_nums, is_old=False)

    def _render_diff(self, edit, lines, line_nums, is_old):
        fmt_normal = QTextCharFormat()
        fmt_normal.setForeground(QColor("#333333"))

        fmt_add = QTextCharFormat()
        fmt_add.setBackground(QColor("#D4EDDA"))
        fmt_add.setForeground(QColor("#155724"))

        fmt_del = QTextCharFormat()
        fmt_del.setBackground(QColor("#F8D7DA"))
        fmt_del.setForeground(QColor("#721C24"))

        fmt_header = QTextCharFormat()
        fmt_header.setForeground(QColor("#6C757D"))

        fmt_meta = QTextCharFormat()
        fmt_meta.setForeground(QColor("#007BFF"))

        cursor = edit.textCursor()

        for i, line in enumerate(lines):
            if not line and not line_nums[i]:
                continue

            if line.startswith("@@"):
                if cursor.position() > 0:
                    cursor.insertBlock()
                cursor.insertText(line + "\n", fmt_header)
            elif line.startswith("---") or line.startswith("+++") or line.startswith("Index:") or line.startswith("==="):
                if cursor.position() > 0:
                    cursor.insertBlock()
                cursor.insertText(line + "\n", fmt_meta)
            elif line.startswith("-") or (is_old and not line and line_nums[i]):
                if cursor.position() > 0:
                    cursor.insertBlock()
                cursor.insertText((line if line else "") + "\n", fmt_del)
            elif line.startswith("+") or (not is_old and not line and line_nums[i]):
                if cursor.position() > 0:
                    cursor.insertBlock()
                cursor.insertText((line if line else "") + "\n", fmt_add)
            else:
                if cursor.position() > 0:
                    cursor.insertBlock()
                cursor.insertText(line + "\n", fmt_normal)
