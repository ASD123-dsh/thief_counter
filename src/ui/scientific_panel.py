# -*- coding: utf-8 -*-
"""
文件: src/ui/scientific_panel.py
描述: 科学计算器面板，支持三角/指数/对数等函数，角度模式可切换，含历史与记忆功能。
"""

from typing import Optional, List, Tuple

from PySide6.QtCore import Qt, QPoint, QSettings
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QLabel,
    QComboBox,
    QToolButton,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QGraphicsOpacityEffect,
    QSplitter,
)
 

from core.expr_parser import safe_eval
from core.scientific_engine import get_functions, get_variables
from core.memory_store import MemoryStore

# 引入拆分后的小游戏模块类
# 注: 新的 games 子模块已建立，但为保持原逻辑与功能，本文件仍使用原内置类。
import ui.games.game2048 as game2048
import ui.games.snake as snake
import ui.games.minesweeper as minesweeper
import ui.games.gomoku as gomoku
from ui.games.mixins import HoverHideMixin, DraggableMixin

# 兼容别名，逐步移除内置类
Game2048Dialog = game2048.Game2048Dialog
GameSnakeDialog = snake.GameSnakeDialog
GameMinesweeperDialog = minesweeper.GameMinesweeperDialog
GameGomokuDialog = gomoku.GameGomokuDialog


class ScientificPanel(QWidget):
    """
    类: ScientificPanel
    作用: 提供科学计算界面，包含函数按键、角度模式选择、表达式输入与历史记录。
    """

    def __init__(self, memory_store: MemoryStore, default_angle_mode: str = "deg", parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化科学面板，设置默认角度模式与界面布局。
        参数:
            memory_store: 共享记忆存储实例。
            default_angle_mode: 默认角度模式（"deg" 或 "rad"）。
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        self.memory_store = memory_store
        self.angle_mode = default_angle_mode
        self._game_secret = "666888"

        # 顶部：模式切换与提示
        top = QWidget()
        top_h = QHBoxLayout(top)
        top_h.setContentsMargins(0, 0, 0, 0)
        top_h.setSpacing(8)

        top_h.addWidget(QLabel("角度单位:"))
        self.angle_combo = QComboBox()
        self.angle_combo.addItems(["角度 (deg)", "弧度 (rad)"])
        self.angle_combo.setCurrentIndex(0 if self.angle_mode == "deg" else 1)
        self.angle_combo.currentIndexChanged.connect(self.on_angle_changed)
        top_h.addWidget(self.angle_combo)
        top_h.addStretch(1)

        # 显示与网格
        self.display = QLineEdit()
        self.display.setObjectName("display")
        self.display.setPlaceholderText("例如: sin(30)+log(100)+sqrt(2)")
        self.display.setAlignment(Qt.AlignRight)
        self.display.setMinimumHeight(40)

        grid = QGridLayout()
        grid.setSpacing(8)

        # 统一每行6列，避免空缺区域
        buttons = [
            ["%", "√", "x²", "1/x", "n!", "Exp"],
            ["sin", "cos", "tan", "sinh", "cosh", "tanh"],
            ["log", "ln", "10^x", "x^y", "π", "e"],
            ["CE", "C", "Back", "/", "*", "-"],
            ["7", "8", "9", "+", "(", ")"],
            ["4", "5", "6", "1", "2", "3"],
            ["±", "0", ".", "(", ")", "="]
        ]

        for r, row in enumerate(buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setMinimumHeight(40)
                btn.clicked.connect(lambda checked=False, t=text: self.on_button_clicked(t))
                grid.addWidget(btn, r, c)

        # 历史
        self.history = QListWidget()
        self.history.setMinimumWidth(240)

        # 根布局
        left = QWidget()
        left_v = QVBoxLayout(left)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)
        left_v.addWidget(top)
        left_v.addWidget(self.display)
        left_v.addLayout(grid)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.history)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        self.history.setMinimumWidth(100)
        
        root.addWidget(splitter)

    def get_help_text(self) -> str:
        """
        函数: get_help_text
        作用: 返回科学计算器的使用说明文本（简体中文）。
        参数:
            无。
        返回:
            使用说明字符串。
        """
        return (
            "【概述】\n"
            "- 支持三角/双曲/指数/对数/幂/平方/倒数/阶乘等函数。\n"
            "- 顶部选择角度单位：角度(deg)/弧度(rad)。角度模式下自动换算为弧度。\n"
            "\n"
            "【常用函数】\n"
            "- sin/cos/tan, sinh/cosh/tanh, log(10底)/ln(自然底), exp, 10^x, x^y, x², 1/x, n!。\n"
            "- π/e 常量可直接插入。\n"
            "\n"
            "【输入与计算】\n"
            "- 按键会插入函数名与括号，例如‘sin(’、‘exp(’；补全参数后点击‘=’。\n"
            "- % 等价于除以 100；± 切换符号；CE/C/Back 分别清空/清空输入/退格。\n"
            "\n"
            "【记忆功能】\n"
            "- MC/MR/M+/M-：清除/读取/累加/累减记忆值（以计算结果为基）。\n"
            "\n"
            "【示例】\n"
            "- 角度模式：sin(30)+log(100)+√(2) -> 点击‘=’得到结果并记录到历史。\n"
            "- 幂运算：x^y 会插入‘**’，例如输入 2**10 -> 点击‘=’得到 1024。\n"
        )

    def on_angle_changed(self, idx: int) -> None:
        """
        函数: on_angle_changed
        作用: 响应角度模式选择，更新内部角度标志。
        参数:
            idx: 角度下拉索引（0 角度/1 弧度）。
        返回:
            无。
        """
        self.angle_mode = "deg" if idx == 0 else "rad"

    def on_button_clicked(self, text: str) -> None:
        """
        函数: on_button_clicked
        作用: 处理按钮点击，插入函数或执行计算与记忆操作。
        参数:
            text: 按钮文本。
        返回:
            无。
        """
        if text == "CE":
            self.display.clear()
            return
        if text == "C":
            self.display.clear()
            return
        if text == "Back":
            self.display.backspace()
            return
        if text == "=":
            self.evaluate_and_record()
            return
        if text in {"MC", "MR", "M+", "M-"}:
            self.handle_memory(text)
            return

        # 特殊插入处理
        if text in {"sin", "cos", "tan", "sinh", "cosh", "tanh", "sqrt", "log", "ln", "exp", "pow"}:
            # 函数插入形如 fn(
            self.display.insert(f"{text}(")
            return
        if text == "π":
            self.display.insert("pi")
            return
        if text == "e":
            self.display.insert("e")
            return
        if text == "x^y":
            self.display.insert("**")
            return
        if text == "10^x":
            self.display.insert("pow10(")
            return
        if text == "x²":
            self.display.insert("square(")
            return
        if text == "1/x":
            self.display.insert("inv(")
            return
        if text == "n!":
            self.display.insert("fact(")
            return
        if text == "Exp":
            self.display.insert("exp(")
            return
        if text == "%":
            self.display.insert("/100")
            return
        if text == "±":
            txt = self.display.text().strip()
            if txt.startswith("-"):
                self.display.setText(txt[1:])
            else:
                self.display.setText("-" + txt)
            return

        # 其它直接插入
        self.display.insert(text)

    def preview_game_2048_theme(self, scheme: dict) -> None:
        """
        函数: preview_game_2048_theme
        作用: 预览应用 2048 游戏窗口的主题前景色（fg），不持久化。
        参数:
            scheme: 包含 fg 的主题字典。
        返回:
            无。
        """
        try:
            g = getattr(self, "_game_2048_dialog", None)
            if g is not None and hasattr(g, "preview_theme"):
                g.preview_theme(dict(scheme) if isinstance(scheme, dict) else {})
        except Exception:
            pass

    def preview_game_2048_opacity(self, percent: int) -> None:
        """
        函数: preview_game_2048_opacity
        作用: 预览应用 2048 游戏窗口整体不透明度，隐藏状态下忽略。
        参数:
            percent: 透明度百分比 1~100。
        返回:
            无。
        """
        try:
            g = getattr(self, "_game_2048_dialog", None)
            if g is not None and hasattr(g, "preview_opacity"):
                g.preview_opacity(int(percent))
        except Exception:
            pass

    def evaluate_and_record(self) -> None:
        """
        函数: evaluate_and_record
        作用: 按当前角度模式计算表达式并记录历史。
        参数:
            无。
        返回:
            无。
        """
        expr = self.display.text().strip()
        if not expr:
            return
        if expr == self._game_secret:
            try:
                win = self.window()
                if hasattr(win, "reveal_game_button"):
                    win.reveal_game_button()
            except Exception:
                pass
            try:
                self.history.addItem("[提示] 已解锁：点击顶部‘选择’按钮")
            except Exception:
                pass
            try:
                self.display.clear()
            except Exception:
                pass
            return
        try:
            fns = get_functions(self.angle_mode)
            vars_ = get_variables()
            result = safe_eval(expr, functions=fns, variables=vars_)
            self.display.setText(str(result))
            self.history.addItem(f"{expr} = {result}")
        except Exception as e:
            self.history.addItem(f"[错误] {expr} -> {e}")

    def _open_game_selector(self) -> None:
        """
        函数: _open_game_selector
        作用: 弹出隐藏游戏选择窗口，提供文字版 2048/贪吃蛇/扫雷/五子棋的选择。
        参数:
            无。
        返回:
            无。
        """
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("选择")
            cont = QWidget(dlg)
            v = QVBoxLayout(cont)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(8)
            lbl = QLabel("选择游戏")
            v.addWidget(lbl)
            lst = QListWidget()
            try:
                lst.addItem("文字2048")
                lst.addItem("文字贪吃蛇")
                lst.addItem("文字扫雷")
                lst.addItem("字符五子棋")
            except Exception:
                pass
            v.addWidget(lst)
            btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
            v.addWidget(btns)
            root = QVBoxLayout(dlg)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(10)
            root.addWidget(cont)
            sel = {"text": ""}
            def on_ok():
                try:
                    item = lst.currentItem()
                    if item is not None:
                        sel["text"] = item.text()
                except Exception:
                    sel["text"] = ""
                try:
                    dlg.accept()
                except Exception:
                    pass
            try:
                btns.accepted.connect(on_ok)
                btns.rejected.connect(dlg.reject)
            except Exception:
                pass
            res = dlg.exec()
            if res == QDialog.Accepted and sel["text"]:
                if sel["text"] == "文字2048":
                    try:
                        try:
                            self._close_existing_games()
                        except Exception:
                            pass
                        g = game2048.Game2048Dialog(None)
                        try:
                            setattr(self, "_game_2048_dialog", g)
                        except Exception:
                            pass
                        try:
                            g.setAttribute(Qt.WA_DeleteOnClose, True)
                        except Exception:
                            pass
                        try:
                            g.destroyed.connect(lambda *_: setattr(self, "_game_2048_dialog", None))
                        except Exception:
                            pass
                        try:
                            g.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                        except Exception:
                            pass
                        try:
                            g.show()
                        except Exception:
                            pass
                        # 弹出默认置顶时，取消主程序置顶（互斥）
                        try:
                            win = self.window()
                            if hasattr(win, "_apply_pin"):
                                win._apply_pin(False)
                        except Exception:
                            pass
                        self.history.addItem("[提示]2048已打开（Esc 关闭，R 重开）")
                    except Exception:
                        QMessageBox.information(self, "提示", "无法打开 2048 ")
                elif sel["text"] == "文字贪吃蛇":
                    try:
                        try:
                            self._close_existing_games()
                        except Exception:
                            pass
                        s = snake.GameSnakeDialog(None)
                        try:
                            setattr(self, "_game_snake_dialog", s)
                        except Exception:
                            pass
                        try:
                            s.setAttribute(Qt.WA_DeleteOnClose, True)
                        except Exception:
                            pass
                        try:
                            s.destroyed.connect(lambda *_: setattr(self, "_game_snake_dialog", None))
                        except Exception:
                            pass
                        try:
                            s.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                        except Exception:
                            pass
                        try:
                            s.show()
                        except Exception:
                            pass
                        try:
                            win = self.window()
                            if hasattr(win, "_apply_pin"):
                                win._apply_pin(False)
                        except Exception:
                            pass
                        self.history.addItem("[提示] 文字贪吃蛇 已打开（Esc 关闭，R 重开）")
                    except Exception:
                        QMessageBox.information(self, "提示", "无法打开 文字贪吃蛇 窗口")
                elif sel["text"] == "文字扫雷":
                    try:
                        try:
                            self._close_existing_games()
                        except Exception:
                            pass
                        m = minesweeper.GameMinesweeperDialog(None)
                        try:
                            setattr(self, "_game_minesweeper_dialog", m)
                        except Exception:
                            pass
                        try:
                            m.setAttribute(Qt.WA_DeleteOnClose, True)
                        except Exception:
                            pass
                        try:
                            m.destroyed.connect(lambda *_: setattr(self, "_game_minesweeper_dialog", None))
                        except Exception:
                            pass
                        try:
                            m.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                        except Exception:
                            pass
                        try:
                            m.show()
                        except Exception:
                            pass
                        try:
                            win = self.window()
                            if hasattr(win, "_apply_pin"):
                                win._apply_pin(False)
                        except Exception:
                            pass
                        self.history.addItem("[提示] 文字扫雷 已打开（Esc 关闭，R 重开）")
                    except Exception:
                        QMessageBox.information(self, "提示", "无法打开 文字扫雷 窗口")
                elif sel["text"] == "字符五子棋":
                    try:
                        try:
                            self._close_existing_games()
                        except Exception:
                            pass
                        gmk = gomoku.GameGomokuDialog(None)
                        try:
                            setattr(self, "_game_gomoku_dialog", gmk)
                        except Exception:
                            pass
                        try:
                            gmk.setAttribute(Qt.WA_DeleteOnClose, True)
                        except Exception:
                            pass
                        try:
                            gmk.destroyed.connect(lambda *_: setattr(self, "_game_gomoku_dialog", None))
                        except Exception:
                            pass
                        try:
                            gmk.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                        except Exception:
                            pass
                        try:
                            gmk.show()
                        except Exception:
                            pass
                        try:
                            win = self.window()
                            if hasattr(win, "_apply_pin"):
                                win._apply_pin(False)
                        except Exception:
                            pass
                        self.history.addItem("[提示] 字符五子棋 已打开（Esc 关闭，R 重开）")
                    except Exception:
                        QMessageBox.information(self, "提示", "无法打开 字符五子棋 窗口")
                else:
                    try:
                        self.history.addItem(f"[提示] 已选择: {sel['text']}（功能待开发）")
                    except Exception:
                        pass
                    try:
                        QMessageBox.information(self, "提示", f"已选择 {sel['text']}，后续功能待开发")
                    except Exception:
                        pass
        except Exception:
            pass

    def _close_existing_games(self) -> None:
        """
        函数: _close_existing_games
        作用: 关闭当前已打开的所有小游戏窗口，确保互斥仅保留一个窗口。
        参数:
            无。
        返回:
            无。
        """
        try:
            for name in ("_game_2048_dialog", "_game_snake_dialog", "_game_minesweeper_dialog", "_game_gomoku_dialog"):
                try:
                    dlg = getattr(self, name, None)
                except Exception:
                    dlg = None
                if dlg is not None:
                    try:
                        dlg.close()
                    except Exception:
                        pass
        except Exception:
            pass

    def handle_memory(self, op: str) -> None:
        """
        函数: handle_memory
        作用: 科学模式下的记忆操作，基于当前表达式计算值进行读写。
        参数:
            op: 记忆操作标识（MC/MR/M+/M-）。
        返回:
            无。
        """
        try:
            current = 0.0
            txt = self.display.text().strip()
            if txt:
                current = safe_eval(txt, functions=get_functions(self.angle_mode), variables=get_variables())
            if op == "MC":
                self.memory_store.clear()
            elif op == "MR":
                self.display.setText(str(self.memory_store.recall()))
            elif op == "M+":
                self.memory_store.add(current)
            elif op == "M-":
                self.memory_store.subtract(current)
        except Exception as e:
            self.history.addItem(f"[错误] 记忆操作: {e}")

    def keyPressEvent(self, event) -> None:
        """
        函数: keyPressEvent
        作用: 处理键盘输入，支持数字、基本运算符与回车计算。
        参数:
            event: 键盘事件。
        返回:
            无。
        """
        key = event.key()
        if key in (Qt.Key_0, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4,
                   Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9):
            self.display.insert(chr(key))
            return
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.evaluate_and_record()
            return
        if key == Qt.Key_Backspace:
            self.display.backspace()
            return
        if key in (Qt.Key_Plus, Qt.Key_Minus, Qt.Key_Asterisk, Qt.Key_Slash,
                   Qt.Key_Period, Qt.Key_ParenLeft, Qt.Key_ParenRight):
            self.display.insert(event.text())
            return
        super().keyPressEvent(event)