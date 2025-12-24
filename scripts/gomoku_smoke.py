# -*- coding: utf-8 -*-
"""
文件: scripts/gomoku_smoke.py
描述: 快速验证五子棋窗口的悬隐逻辑（移出隐藏/移入延迟显示）。
"""

import sys


def main():
    """
    函数: main
    作用: 构建并显示 GameGomokuDialog，调用隐藏与显示方法验证不透明度与状态。
    参数:
        无。
    返回:
        无（打印测试结果）。
    """
    from PySide6.QtWidgets import QApplication
    sys.path.append("src")
    from ui.games.gomoku import GameGomokuDialog

    app = QApplication.instance() or QApplication(sys.argv)
    dlg = GameGomokuDialog(None)
    dlg.show()
    dlg.setFocus()

    before = round(dlg.windowOpacity(), 2)
    dlg._hover_hide()
    hidden = getattr(dlg, "_hover_hidden", False)
    mid = round(dlg.windowOpacity(), 2)
    dlg._hover_show_now()
    after = round(dlg.windowOpacity(), 2)

    print("GOMOKU:", before, hidden, mid, after)

    dlg.close()


if __name__ == "__main__":
    main()