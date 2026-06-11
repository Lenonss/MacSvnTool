import sys
import shutil

from PySide6.QtWidgets import QApplication, QMessageBox


def main():
    app = QApplication(["MacSvnTool"])

    if shutil.which("svn") is None:
        QMessageBox.critical(
            None,
            "错误",
            "未检测到 SVN 命令行工具。请确保已安装 Subversion。"
        )
        sys.exit(1)

    from src.ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
