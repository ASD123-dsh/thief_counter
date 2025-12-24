# -*- coding: utf-8 -*-
"""
文件: scripts/ui_smoke.py
描述: 基于 PySide6 的 UI 冒烟测试，覆盖置顶切换与 2048 基本交互。
"""

import sys


def main():
    """
    函数: main
    作用: 启动 QApplication，构建 MainWindow 与 2048 窗口并进行基本交互验证。
    参数:
        无。
    返回:
        无（打印测试结果）。
    """
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings, Qt
    from PySide6.QtTest import QTest

    sys.path.append("src")
    from ui.main_window import MainWindow
    from ui.games.game2048 import Game2048Dialog

    app = QApplication.instance() or QApplication(sys.argv)

    win = MainWindow()
    win.show()

    win._apply_pin(True)
    settings = QSettings()
    pin1 = bool(settings.value("always_on_top", False, type=bool))
    win._apply_pin(False)
    pin2 = bool(settings.value("always_on_top", True, type=bool))

    dlg = Game2048Dialog(None)
    dlg.show()
    dlg.activateWindow()
    dlg.raise_()
    dlg.setFocus()

    dlg.board = [[0, 0, 0, 0] for _ in range(4)]
    dlg.board[0] = [2, 2, 0, 0]
    dlg.update_view()
    QTest.qWait(50)

    QTest.keyPress(dlg, Qt.Key_Left)
    QTest.qWait(50)

    merged_ok = (dlg.board[0][0] == 4)
    score_ok = (dlg.score >= 4)

    print("PIN:", pin1, pin2)
    print("2048:", merged_ok, score_ok)

    QTest.qWait(100)
    dlg.close()
    win.close()


if __name__ == "__main__":
    main()