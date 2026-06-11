import PyInstaller.__main__
import os
import sys


def build():
    base_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(base_path, "src")

    args = [
        os.path.join(base_path, "main.py"),
        "--name=MacSvnTool",
        "--onefile",
        "--windowed",
        "--clean",
        f"--add-data={src_path}{os.pathsep}src",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
    ]

    if sys.platform == "darwin":
        icon_path = os.path.join(base_path, "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            args.append(f"--icon={icon_path}")

    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    build()
