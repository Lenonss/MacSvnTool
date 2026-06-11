import os

from PySide6.QtWidgets import (
    QMainWindow, QMenu, QToolBar, QStatusBar,
    QSplitter, QLabel, QWidget, QVBoxLayout, QFileDialog,
    QMessageBox, QApplication, QMenuBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence

from src.ui.repo_browser import RepoBrowser
from src.ui.status_widget import StatusWidget
from src.ui.checkout_dialog import CheckoutDialog
from src.ui.commit_dialog import CommitDialog
from src.ui.log_viewer import LogViewer
from src.ui.diff_viewer import DiffViewer
from src.services.svn_service import SvnService, SvnError
from src.services.worker_thread import WorkerThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._working_copy_path = None
        self._repository_info = None
        self._statuses = []
        self._setup_window()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_central()
        self._set_initial_state()

    def _setup_window(self):
        self.setWindowTitle("MacSvnTool")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        self._act_open = QAction("打开工作副本...", self)
        self._act_open.setShortcut(QKeySequence("Ctrl+O"))
        self._act_open.triggered.connect(self._on_open_working_copy)
        file_menu.addAction(self._act_open)

        self._act_checkout = QAction("检出...", self)
        self._act_checkout.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self._act_checkout.triggered.connect(self._on_checkout)
        file_menu.addAction(self._act_checkout)

        file_menu.addSeparator()
        self._act_exit = QAction("退出", self)
        self._act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self._act_exit.triggered.connect(self.close)
        file_menu.addAction(self._act_exit)

        svn_menu = menubar.addMenu("SVN操作")
        self._act_update = QAction("更新", self)
        self._act_update.setShortcut(QKeySequence("Ctrl+U"))
        self._act_update.triggered.connect(self._on_update)
        svn_menu.addAction(self._act_update)

        self._act_commit = QAction("提交...", self)
        self._act_commit.setShortcut(QKeySequence("Ctrl+M"))
        self._act_commit.triggered.connect(self._on_commit)
        svn_menu.addAction(self._act_commit)

        svn_menu.addSeparator()
        self._act_log = QAction("查看日志", self)
        self._act_log.setShortcut(QKeySequence("Ctrl+L"))
        self._act_log.triggered.connect(self._on_log)
        svn_menu.addAction(self._act_log)

        self._act_diff = QAction("比较差异", self)
        self._act_diff.triggered.connect(self._on_diff)
        svn_menu.addAction(self._act_diff)

        svn_menu.addSeparator()
        self._act_revert = QAction("还原", self)
        self._act_revert.triggered.connect(self._on_revert)
        svn_menu.addAction(self._act_revert)

        self._act_add = QAction("添加", self)
        self._act_add.triggered.connect(self._on_add)
        svn_menu.addAction(self._act_add)

        self._act_cleanup = QAction("清理", self)
        self._act_cleanup.triggered.connect(self._on_cleanup)
        svn_menu.addAction(self._act_cleanup)

        view_menu = menubar.addMenu("视图")
        self._act_refresh = QAction("刷新", self)
        self._act_refresh.setShortcut(QKeySequence("F5"))
        self._act_refresh.triggered.connect(self._on_refresh)
        view_menu.addAction(self._act_refresh)

        help_menu = menubar.addMenu("帮助")
        self._act_about = QAction("关于", self)
        self._act_about.triggered.connect(self._on_about)
        help_menu.addAction(self._act_about)

    def _setup_toolbar(self):
        self._toolbar = QToolBar("工具栏")
        self._toolbar.setIconSize(QSize(24, 24))
        self._toolbar.setMovable(False)
        self.addToolBar(self._toolbar)

        self._toolbar.addAction(self._act_checkout)
        self._toolbar.addAction(self._act_update)
        self._toolbar.addAction(self._act_commit)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._act_log)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._act_revert)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._act_refresh)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._status_path = QLabel("就绪")
        self._status_revision = QLabel("")
        self._statusbar.addWidget(self._status_path, 1)
        self._statusbar.addPermanentWidget(self._status_revision)

    def _setup_central(self):
        self._empty_label = QLabel("打开工作副本或检出仓库")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #888; font-size: 16px;")

        self._repo_browser = RepoBrowser(self)
        self._repo_browser.context_menu_requested.connect(self._on_repo_context_menu)

        self._status_widget = StatusWidget(self)
        self._status_widget.commit_requested.connect(self._on_commit)
        self._status_widget.revert_requested.connect(self._on_revert_paths)
        self._status_widget.add_requested.connect(self._on_add_paths)
        self._status_widget.diff_requested.connect(self._on_diff_file)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self._repo_browser)
        self._splitter.addWidget(self._status_widget)
        self._splitter.setSizes([550, 550])
        self._splitter.hide()

        self._central_stack = QWidget()
        layout = QVBoxLayout(self._central_stack)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._splitter)

        self.setCentralWidget(self._central_stack)

    def _set_initial_state(self):
        self._empty_label.show()
        self._splitter.hide()
        self._act_update.setEnabled(False)
        self._act_commit.setEnabled(False)
        self._act_log.setEnabled(False)
        self._act_diff.setEnabled(False)
        self._act_revert.setEnabled(False)
        self._act_add.setEnabled(False)
        self._act_cleanup.setEnabled(False)
        self._act_refresh.setEnabled(False)

    def _set_working_copy_state(self):
        self._empty_label.hide()
        self._splitter.show()
        self._act_update.setEnabled(True)
        self._act_commit.setEnabled(True)
        self._act_log.setEnabled(True)
        self._act_diff.setEnabled(True)
        self._act_revert.setEnabled(True)
        self._act_add.setEnabled(True)
        self._act_cleanup.setEnabled(True)
        self._act_refresh.setEnabled(True)

    def _on_open_working_copy(self):
        path = QFileDialog.getExistingDirectory(self, "选择 SVN 工作副本目录")
        if not path:
            return
        self.open_working_copy(path)

    def open_working_copy(self, path):
        self._working_copy_path = path
        self._statusbar.showMessage("正在加载工作副本...")
        self._set_controls_enabled(False)
        thread = WorkerThread(self._load_working_copy, path)
        thread.finished.connect(self._on_working_copy_loaded)
        thread.error.connect(self._on_working_copy_error)
        thread.start()

    def _load_working_copy(self, path):
        info = SvnService.info(path)
        statuses = SvnService.status(path)
        return info, statuses

    def _on_working_copy_loaded(self, result):
        self._set_controls_enabled(True)
        info, statuses = result
        self._repository_info = info
        self._statuses = statuses
        self.setWindowTitle(f"MacSvnTool - {self._working_copy_path}")
        self._status_path.setText(self._working_copy_path)
        self._status_revision.setText(f"版本: {info.revision}")
        self._repo_browser.load_working_copy(self._working_copy_path, statuses)
        self._status_widget.load_status(statuses)
        self._set_working_copy_state()
        self._statusbar.showMessage("就绪", 3000)

    def _on_working_copy_error(self, error_msg):
        self._set_controls_enabled(True)
        self._statusbar.showMessage("加载失败", 3000)
        QMessageBox.critical(self, "错误", f"无法打开工作副本:\n{error_msg}")

    def _on_checkout(self):
        dialog = CheckoutDialog(self)
        dialog.checkout_completed.connect(self.open_working_copy)
        dialog.exec()

    def _on_update(self):
        self._statusbar.showMessage("正在更新...")
        self._set_controls_enabled(False)
        thread = WorkerThread(SvnService.update, self._working_copy_path)
        thread.finished.connect(self._on_update_finished)
        thread.error.connect(self._on_operation_error)
        thread.start()

    def _on_update_finished(self, revision):
        self._set_controls_enabled(True)
        self._statusbar.showMessage(f"更新完成，版本: {revision}", 5000)
        self._status_revision.setText(f"版本: {revision}")
        self._on_refresh()

    def _on_commit(self):
        changed = [s for s in self._statuses if s.status != self._statuses[0].__class__.NORMAL] if self._statuses else []
        if not changed:
            QMessageBox.information(self, "提示", "没有需要提交的变更。")
            return
        dialog = CommitDialog(changed, self._working_copy_path, self)
        dialog.commit_completed.connect(self._on_commit_completed)
        dialog.exec()

    def _on_commit_completed(self, revision):
        self._status_revision.setText(f"版本: {revision}")
        self._on_refresh()

    def _on_log(self):
        dialog = LogViewer(self._working_copy_path, self)
        dialog.diff_requested.connect(self._on_diff_revision)
        dialog.exec()

    def _on_diff(self):
        paths = self._repo_browser.get_selected_paths()
        if paths:
            file_path = paths[0]
            if os.path.isfile(file_path):
                self._on_diff_file(file_path)
            else:
                QMessageBox.information(self, "提示", "请选择一个文件进行比较差异。")
        else:
            paths = self._status_widget.get_selected_paths()
            if paths:
                self._on_diff_file(paths[0])
            else:
                QMessageBox.information(self, "提示", "请选择一个文件进行比较差异。")

    def _on_diff_file(self, file_path):
        dialog = DiffViewer(file_path, self._working_copy_path, self)
        dialog.exec()

    def _on_diff_revision(self, file_path, revision):
        dialog = DiffViewer(file_path, self._working_copy_path, self)
        dialog._old_combo.setCurrentText(revision)
        dialog.exec()

    def _on_revert(self):
        paths = self._status_widget.get_selected_paths()
        if not paths:
            paths = self._repo_browser.get_selected_paths()
        if not paths:
            QMessageBox.information(self, "提示", "请选择要还原的文件。")
            return
        self._on_revert_paths(paths)

    def _on_revert_paths(self, paths):
        reply = QMessageBox.question(
            self, "确认还原",
            f"确定要还原选中的 {len(paths)} 个文件吗？\n所有未提交的修改将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._statusbar.showMessage("正在还原...")
        self._set_controls_enabled(False)
        thread = WorkerThread(SvnService.revert, paths)
        thread.finished.connect(lambda _: self._on_revert_finished())
        thread.error.connect(self._on_operation_error)
        thread.start()

    def _on_revert_finished(self):
        self._set_controls_enabled(True)
        self._statusbar.showMessage("还原完成", 3000)
        self._on_refresh()

    def _on_add(self):
        paths = self._status_widget.get_selected_paths()
        if not paths:
            paths = self._repo_browser.get_selected_paths()
        if not paths:
            QMessageBox.information(self, "提示", "请选择要添加的文件。")
            return
        self._on_add_paths(paths)

    def _on_add_paths(self, paths):
        self._statusbar.showMessage("正在添加文件...")
        self._set_controls_enabled(False)
        thread = WorkerThread(SvnService.add, paths)
        thread.finished.connect(lambda _: self._on_add_finished())
        thread.error.connect(self._on_operation_error)
        thread.start()

    def _on_add_finished(self):
        self._set_controls_enabled(True)
        self._statusbar.showMessage("添加完成", 3000)
        self._on_refresh()

    def _on_cleanup(self):
        self._statusbar.showMessage("正在清理...")
        self._set_controls_enabled(False)
        thread = WorkerThread(SvnService.cleanup, self._working_copy_path)
        thread.finished.connect(lambda _: self._on_cleanup_finished())
        thread.error.connect(self._on_operation_error)
        thread.start()

    def _on_cleanup_finished(self):
        self._set_controls_enabled(True)
        self._statusbar.showMessage("清理完成", 3000)

    def _on_refresh(self):
        self._statusbar.showMessage("正在刷新...")
        thread = WorkerThread(self._load_status, self._working_copy_path)
        thread.finished.connect(self._on_refresh_finished)
        thread.error.connect(self._on_operation_error)
        thread.start()

    def _load_status(self, path):
        return SvnService.status(path)

    def _on_refresh_finished(self, statuses):
        self._statuses = statuses
        self._repo_browser.load_working_copy(self._working_copy_path, statuses)
        self._status_widget.load_status(statuses)
        self._statusbar.showMessage("就绪", 2000)

    def _on_operation_error(self, error_msg):
        self._set_controls_enabled(True)
        self._statusbar.showMessage("操作失败", 3000)
        QMessageBox.critical(self, "操作失败", error_msg)

    def _on_repo_context_menu(self, file_path, action_type):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        act_update = menu.addAction("更新")
        act_commit = menu.addAction("提交...")
        menu.addSeparator()
        act_diff = menu.addAction("比较差异")
        act_log = menu.addAction("查看日志")
        menu.addSeparator()
        act_revert = menu.addAction("还原")
        act_add = menu.addAction("添加")
        menu.addSeparator()
        act_show = menu.addAction("在访达中显示")

        chosen = menu.exec(self._repo_browser.mapToGlobal(
            self._repo_browser.rect().center()
        ))

        if chosen == act_update:
            self._on_update()
        elif chosen == act_commit:
            self._on_commit()
        elif chosen == act_diff:
            if action_type == "file":
                self._on_diff_file(file_path)
            else:
                QMessageBox.information(self, "提示", "请选择一个文件进行比较差异。")
        elif chosen == act_log:
            self._on_log()
        elif chosen == act_revert:
            self._on_revert_paths([file_path])
        elif chosen == act_add:
            self._on_add_paths([file_path])
        elif chosen == act_show:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            parent_dir = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
            QDesktopServices.openUrl(QUrl.fromLocalFile(parent_dir))

    def _set_controls_enabled(self, enabled):
        self._act_open.setEnabled(enabled)
        self._act_checkout.setEnabled(enabled)
        self._act_update.setEnabled(enabled and self._working_copy_path is not None)
        self._act_commit.setEnabled(enabled and self._working_copy_path is not None)
        self._act_log.setEnabled(enabled and self._working_copy_path is not None)
        self._act_diff.setEnabled(enabled and self._working_copy_path is not None)
        self._act_revert.setEnabled(enabled and self._working_copy_path is not None)
        self._act_add.setEnabled(enabled and self._working_copy_path is not None)
        self._act_cleanup.setEnabled(enabled and self._working_copy_path is not None)
        self._act_refresh.setEnabled(enabled and self._working_copy_path is not None)

    def _on_about(self):
        QMessageBox.about(self, "关于 MacSvnTool",
                          "MacSvnTool v1.0\n\n"
                          "macOS SVN 图形化管理工具\n"
                          "类似于 TortoiseSVN 的操作体验")
