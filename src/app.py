# -*- coding: utf-8 -*-
"""
文件: src/app.py
描述: 应用入口，加载样式并启动主窗口。
"""

import os
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QCoreApplication, QSettings, QTranslator, QLibraryInfo, QLocale

from ui.main_window import MainWindow


def resource_path(relative_path: str) -> str:
    """
    函数: resource_path
    作用: 在开发环境与打包后的环境中，正确定位资源文件路径。
    参数:
        relative_path: 相对资源路径，如 "resources/style.qss"。
    返回:
        资源文件的绝对路径字符串。
    """
    base_path: Optional[str]
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # PyInstaller 暂存目录
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def load_style(app: QApplication) -> None:
    """
    函数: load_style
    作用: 加载并应用 QSS 样式文件；根据持久化设置选择浅色或深色。
    参数:
        app: QApplication 实例。
    返回:
        无。
    """
    # 读取持久化主题设置
    settings = QSettings()
    dark_mode = bool(settings.value("dark_mode", False, type=bool))
    qss_file = "resources/style_dark.qss" if dark_mode else "resources/style.qss"
    qss_path = resource_path(qss_file)
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> None:
    """
    函数: main
    作用: 程序主入口，创建应用、加载样式并显示主窗口。
    参数:
        无。
    返回:
        无。
    """
    # 设置组织/应用名，便于 QSettings 持久化到系统注册表
    QCoreApplication.setOrganizationName("计算器")
    QCoreApplication.setApplicationName("计算器")
    app = QApplication(sys.argv)
    try:
        QLocale.setDefault(QLocale("zh_CN"))
    except Exception:
        pass
    try:
        trans_dir = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
        try:
            pack_dir = resource_path("translations")
            if os.path.isdir(pack_dir):
                trans_dir = pack_dir
        except Exception:
            pass
        tr_base = QTranslator(app)
        if tr_base.load(QLocale("zh_CN"), "qtbase", "_", trans_dir):
            app.installTranslator(tr_base)
        tr_qt = QTranslator(app)
        if tr_qt.load(QLocale("zh_CN"), "qt", "_", trans_dir):
            app.installTranslator(tr_qt)
    except Exception:
        pass
    load_style(app)
    win = MainWindow()
    # 增加默认宽度以适应带空格的二进制显示 (630 -> 720)
    win.resize(640, 600)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()