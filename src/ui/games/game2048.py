"""
模块: game2048
作用: 文字版 2048 游戏对话框（无边框）。保持原逻辑，接入统一悬隐与拖动。
"""

from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QMessageBox,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QPoint, QTimer, QSettings, QEvent
from PySide6.QtGui import QCursor, QShortcut, QKeySequence, QRegion

import random

from ui.games.mixins import HoverHideMixin, DraggableMixin
from ui.games.services import apply_message_box_theme


class Game2048Dialog(HoverHideMixin, DraggableMixin, QDialog):
    """
    类: Game2048Dialog
    作用: 文字版 2048 游戏窗口（无边框）。支持方向键/WASD 控制、合并与分数统计，含结束检测。
    参数:
        parent: 父级 QWidget。
    返回:
        无。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化 2048 对话框，构建界面与游戏状态，设置无边框属性。
        参数:
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        try:
            self.setWindowTitle("2048")
            self.setModal(False)
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setWindowModality(Qt.NonModal)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_StyledBackground, True)
            self._apply_bg_from_settings()
        except Exception:
            pass

        self.board: List[List[int]] = [[0 for _ in range(4)] for _ in range(4)]
        self.score: int = 0

        self.score_label = QLabel("分数: 0")
        self.score_label.setAlignment(Qt.AlignCenter)

        self.cells: List[List[QLabel]] = []
        grid = QGridLayout()
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(8)
        for r in range(4):
            row: List[QLabel] = []
            for c in range(4):
                lbl = QLabel("")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setMinimumSize(50, 50)
                lbl.setStyleSheet("QLabel { border: 1px solid #888; border-radius: 6px; background: transparent; }")
                try:
                    lbl.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                    lbl.setMouseTracking(True)
                    lbl.installEventFilter(self)
                except Exception:
                    pass
                row.append(lbl)
                grid.addWidget(lbl, r, c)
            self.cells.append(row)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        root.addWidget(self.score_label)
        root.addLayout(grid)
        try:
            self.setFixedSize(4 * 58 + 16, 4 * 58 + 60)
        except Exception:
            pass

        self.new_game()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        try:
            self.bind_shortcuts()
        except Exception:
            pass
        try:
            self.setMouseTracking(True)
            self.score_label.setMouseTracking(True)
        except Exception:
            pass

        try:
            self.init_drag()
        except Exception:
            pass
        try:
            self.installEventFilter(self)
            self.score_label.installEventFilter(self)
        except Exception:
            pass
        try:
            self._apply_text_opacity(0.9)
        except Exception:
            pass
        try:
            self.setMouseTracking(True)
            if hasattr(self, "_grid_wrap") and self._grid_wrap is not None:
                self._grid_wrap.setMouseTracking(True)
        except Exception:
            pass
        try:
            self.init_hover()
        except Exception:
            pass
        try:
            self._apply_cells_bg_from_settings()
        except Exception:
            pass

        try:
            QTimer.singleShot(0, self._ensure_focus_and_keyboard)
        except Exception:
            pass
        try:
            self._ensure_hit_test_surface()
        except Exception:
            pass

    def bind_shortcuts(self) -> None:
        """
        函数: bind_shortcuts
        作用: 绑定方向键与 WASD 的快捷键，作为键盘事件兜底，提升操控可靠性。
        参数:
            无。
        返回:
            无。
        """
        try:
            QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self._after_move(self.move_left()))
            QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self._after_move(self.move_right()))
            QShortcut(QKeySequence(Qt.Key_Up), self, lambda: self._after_move(self.move_up()))
            QShortcut(QKeySequence(Qt.Key_Down), self, lambda: self._after_move(self.move_down()))
            QShortcut(QKeySequence(Qt.Key_A), self, lambda: self._after_move(self.move_left()))
            QShortcut(QKeySequence(Qt.Key_D), self, lambda: self._after_move(self.move_right()))
            QShortcut(QKeySequence(Qt.Key_W), self, lambda: self._after_move(self.move_up()))
            QShortcut(QKeySequence(Qt.Key_S), self, lambda: self._after_move(self.move_down()))
            QShortcut(QKeySequence(Qt.Key_R), self, self.new_game)
            QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)
        except Exception:
            pass

    def new_game(self) -> None:
        """
        函数: new_game
        作用: 开始新一局，清空棋盘并生成两个随机初始方块。
        参数:
            无。
        返回:
            无。
        """
        self.board = [[0 for _ in range(4)] for _ in range(4)]
        self.score = 0
        self.spawn_tile()
        self.spawn_tile()
        self.update_view()

    def spawn_tile(self) -> None:
        """
        函数: spawn_tile
        作用: 在空位随机生成一个方块，数值为 2（90%）或 4（10%）。
        参数:
            无。
        返回:
            无。
        """
        empties = [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
        if not empties:
            return
        r, c = random.choice(empties)
        val = 4 if random.random() < 0.10 else 2
        self.board[r][c] = val

    def update_view(self) -> None:
        """
        函数: update_view
        作用: 刷新界面显示，更新每个格子的文本与分数栏。
        参数:
            无。
        返回:
            无。
        """
        self.score_label.setText(f"分数: {self.score}")
        for r in range(4):
            for c in range(4):
                v = self.board[r][c]
                self.cells[r][c].setText(str(v) if v > 0 else "")

    def compress_line(self, line: List[int]) -> List[int]:
        non_zero = [x for x in line if x != 0]
        return non_zero + [0] * (4 - len(non_zero))

    def merge_line(self, line: List[int]) -> Tuple[List[int], int]:
        score_add = 0
        line = self.compress_line(line)
        for i in range(3):
            if line[i] != 0 and line[i] == line[i + 1]:
                line[i] *= 2
                score_add += line[i]
                line[i + 1] = 0
        line = self.compress_line(line)
        return line, score_add

    def _after_move(self, moved: bool) -> None:
        """
        函数: _after_move
        作用: 移动后通用处理：生成新方块、刷新视图、结束判定与提示。
        参数:
            moved: 是否发生变化。
        返回:
            无。
        """
        if moved:
            self.spawn_tile()
            self.update_view()
            if self.is_game_over():
                try:
                    self._show_game_over_dialog()
                except Exception:
                    try:
                        QMessageBox.information(self, "提示", f"游戏结束，分数：{self.score}")
                    except Exception:
                        pass

    def move_left(self) -> bool:
        changed = False
        total_add = 0
        new_board: List[List[int]] = []
        for r in range(4):
            merged, add = self.merge_line(self.board[r][:])
            if merged != self.board[r]:
                changed = True
            new_board.append(merged)
            total_add += add
        if changed:
            self.board = new_board
            self.score += total_add
        return changed

    def move_right(self) -> bool:
        changed = False
        total_add = 0
        new_board: List[List[int]] = []
        for r in range(4):
            reversed_line = list(reversed(self.board[r]))
            merged, add = self.merge_line(reversed_line)
            merged = list(reversed(merged))
            if merged != self.board[r]:
                changed = True
            new_board.append(merged)
            total_add += add
        if changed:
            self.board = new_board
            self.score += total_add
        return changed

    def move_up(self) -> bool:
        changed = False
        total_add = 0
        new_cols: List[List[int]] = []
        for c in range(4):
            col = [self.board[r][c] for r in range(4)]
            merged, add = self.merge_line(col)
            if merged != col:
                changed = True
            new_cols.append(merged)
            total_add += add
        if changed:
            for c in range(4):
                for r in range(4):
                    self.board[r][c] = new_cols[c][r]
            self.score += total_add
        return changed

    def move_down(self) -> bool:
        changed = False
        total_add = 0
        new_cols: List[List[int]] = []
        for c in range(4):
            col = [self.board[r][c] for r in range(4)]
            reversed_col = list(reversed(col))
            merged, add = self.merge_line(reversed_col)
            merged = list(reversed(merged))
            if merged != col:
                changed = True
            new_cols.append(merged)
            total_add += add
        if changed:
            for c in range(4):
                for r in range(4):
                    self.board[r][c] = new_cols[c][r]
            self.score += total_add
        return changed

    def has_empty(self) -> bool:
        return any(self.board[r][c] == 0 for r in range(4) for c in range(4))

    def can_merge(self) -> bool:
        for r in range(4):
            for c in range(4):
                v = self.board[r][c]
                if v == 0:
                    continue
                if c < 3 and self.board[r][c + 1] == v:
                    return True
                if r < 3 and self.board[r + 1][c] == v:
                    return True
        return False

    def is_game_over(self) -> bool:
        return (not self.has_empty()) and (not self.can_merge())

    def _apply_theme_fg_from_settings(self) -> None:
        """
        函数: _apply_theme_fg_from_settings
        作用: 从 QSettings 读取极简模式前景色并应用到游戏窗口文字。
        参数:
            无。
        返回:
            无。
        """
        try:
            settings = QSettings()
            fg = str(settings.value("minimal_theme_fg", "#1E1E1E", type=str))
        except Exception:
            fg = "#1E1E1E"
        try:
            self._apply_theme_fg(str(fg))
        except Exception:
            pass

    def _apply_theme_fg(self, fg: str) -> None:
        """
        函数: _apply_theme_fg
        作用: 应用前景色到分数与棋盘格标签的文本颜色，并保持格子背景为极低透明度以可命中。
        参数:
            fg: 文本颜色字符串（HEX/RGB）。
        返回:
            无。
        """
        try:
            self.score_label.setStyleSheet(f"QLabel{{color:{fg}; background: transparent;}}")
        except Exception:
            pass
        try:
            settings = QSettings()
            bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
            r_i, g_i, b_i = self._hex_to_rgb(bg)
            a = 0.04
            for r in range(4):
                for c in range(4):
                    lbl = self.cells[r][c]
                    lbl.setStyleSheet(
                        f"QLabel{{color:{fg}; border: 1px solid #888; border-radius: 6px; background: rgba({r_i},{g_i},{b_i},{a});}}"
                    )
        except Exception:
            pass

    def preview_theme(self, scheme: dict) -> None:
        """
        函数: preview_theme
        作用: 预览主题（应用 fg 颜色，并以极低透明度应用 bg 背景）。
        参数:
            scheme: 主题字典。
        返回:
            无。
        """
        try:
            fg = str(scheme.get("fg", "#1E1E1E")) if isinstance(scheme, dict) else "#1E1E1E"
            self._apply_theme_fg(fg)
        except Exception:
            pass
        try:
            if isinstance(scheme, dict):
                bg = str(scheme.get("bg", "#F5F5F7"))
            else:
                bg = "#F5F5F7"
            self._apply_bg_low_alpha(bg, 0.04)
            try:
                self._apply_cells_bg_low_alpha(bg, 0.04)
            except Exception:
                pass
        except Exception:
            pass

    def preview_opacity(self, percent: int) -> None:
        """
        函数: preview_opacity
        作用: 预览窗口不透明度（隐藏状态下忽略）。
        参数:
            percent: 透明度百分比 1~100。
        返回:
            无。
        """
        try:
            if getattr(self, "_hover_hidden", False):
                return
            p = 1 if int(percent) < 1 else (100 if int(percent) > 100 else int(percent))
            self.setWindowOpacity(p / 100.0 if p > 1 else 1.0)
        except Exception:
            pass

    def _apply_text_opacity(self, alpha: float) -> None:
        """
        函数: _apply_text_opacity
        作用: 为分数栏与棋盘格标签设置统一的不透明度效果，用于透明背景特例。
        参数:
            alpha: 文本与部件的不透明度 (0.0~1.0)。
        返回:
            无。
        """
        try:
            a = 0.9 if alpha is None else float(alpha)
            a = 0.0 if a < 0.0 else (1.0 if a > 1.0 else a)
        except Exception:
            a = 0.9
        try:
            eff = QGraphicsOpacityEffect(self.score_label)
            eff.setOpacity(a)
            self.score_label.setGraphicsEffect(eff)
        except Exception:
            pass

    def _ensure_hit_test_surface(self) -> None:
        """
        函数: _ensure_hit_test_surface
        作用: 确保整个对话框区域参与命中测试：启用样式背景绘制，并设置整窗遮罩区域。
        参数:
            无。
        返回:
            无。
        """
        try:
            self.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass
        try:
            rect = self.rect()
            if rect is not None and not rect.isNull():
                self.setMask(QRegion(rect))
        except Exception:
            pass

    def _hex_to_rgb(self, s: str) -> Tuple[int, int, int]:
        """
        函数: _hex_to_rgb
        作用: 将 #RGB/#RRGGBB 颜色字符串转换为整数 RGB 元组。
        参数:
            s: 颜色字符串。
        返回:
            (r, g, b) 三元组。
        """
        try:
            s = str(s).strip()
            if s.startswith("#"):
                s = s[1:]
            if len(s) == 3:
                r = int(s[0] * 2, 16)
                g = int(s[1] * 2, 16)
                b = int(s[2] * 2, 16)
                return r, g, b
            if len(s) == 6:
                r = int(s[0:2], 16)
                g = int(s[2:4], 16)
                b = int(s[4:6], 16)
                return r, g, b
        except Exception:
            pass
        return 245, 245, 247

    def _apply_bg_low_alpha(self, bg_hex: str, alpha: float = 0.04) -> None:
        """
        函数: _apply_bg_low_alpha
        作用: 以极低透明度应用背景色到对话框，避免点击穿透且保持视觉极简。
        参数:
            bg_hex: 背景色（HEX）。
            alpha: 透明度 0.0~1.0（建议 0.01~0.05）。
        返回:
            无。
        """
        try:
            a = 0.04 if alpha is None else float(alpha)
            a = 0.0 if a < 0.0 else (0.10 if a > 0.10 else a)
        except Exception:
            a = 0.02
        try:
            r, g, b = self._hex_to_rgb(bg_hex)
            self.setStyleSheet(f"background: rgba({r},{g},{b},{a}); border: none;")
        except Exception:
            pass

    def _apply_cells_bg_low_alpha(self, bg_hex: str, alpha: float = 0.04) -> None:
        """
        函数: _apply_cells_bg_low_alpha
        作用: 为棋盘格 QLabel 应用极低透明度背景色，确保格子区域可进行命中与拖动。
        参数:
            bg_hex: 背景色（HEX）。
            alpha: 透明度 0.0~1.0（建议 0.01~0.05）。
        返回:
            无。
        """
        try:
            a = 0.04 if alpha is None else float(alpha)
            a = 0.0 if a < 0.0 else (0.10 if a > 0.10 else a)
        except Exception:
            a = 0.04
        try:
            r, g, b = self._hex_to_rgb(bg_hex)
            for rr in range(4):
                for cc in range(4):
                    lbl = self.cells[rr][cc]
                    lbl.setStyleSheet(
                        f"QLabel{{ border: 1px solid #888; border-radius: 6px; background: rgba({r},{g},{b},{a}); }}"
                    )
        except Exception:
            pass

    def _apply_cells_bg_from_settings(self) -> None:
        """
        函数: _apply_cells_bg_from_settings
        作用: 读取摸鱼背景色并以极低透明度应用到所有棋盘格标签背景。
        参数:
            无。
        返回:
            无。
        """
        try:
            settings = QSettings()
            bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
        except Exception:
            bg = "#F5F5F7"
        try:
            self._apply_cells_bg_low_alpha(bg, 0.04)
        except Exception:
            pass

    def _apply_bg_from_settings(self) -> None:
        """
        函数: _apply_bg_from_settings
        作用: 从 QSettings 读取摸鱼配色的背景色，并以极低透明度应用到 2048 对话框根背景。
        参数:
            无。
        返回:
            无。
        """
        try:
            settings = QSettings()
            bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
        except Exception:
            bg = "#F5F5F7"
        try:
            self._apply_bg_low_alpha(bg, 0.04)
        except Exception:
            pass
        try:
            self._apply_text_opacity(0.9)
        except Exception:
            pass

    def keyPressEvent(self, event) -> None:
        """
        函数: keyPressEvent
        作用: 处理键盘输入，支持方向键与 WASD 控制；Esc 关闭，R 重开。
        参数:
            event: 键盘事件。
        返回:
            无。
        """
        key = event.key()
        handled = False
        if key in (Qt.Key_Left, Qt.Key_A):
            handled = self.move_left()
        elif key in (Qt.Key_Right, Qt.Key_D):
            handled = self.move_right()
        elif key in (Qt.Key_Up, Qt.Key_W):
            handled = self.move_up()
        elif key in (Qt.Key_Down, Qt.Key_S):
            handled = self.move_down()
        elif key == Qt.Key_Escape:
            try:
                self.close()
            except Exception:
                pass
            return
        elif key == Qt.Key_R:
            self.new_game()
            return

        if handled:
            self._after_move(True)
        else:
            super().keyPressEvent(event)

    def _ensure_focus_and_keyboard(self) -> None:
        """
        函数: _ensure_focus_and_keyboard
        作用: 统一确保窗口激活、置顶、获取焦点与抓取键盘，以保证方向键与 WASD 可用。
        参数:
            无。
        返回:
            无。
        """
        try:
            self.activateWindow()
            self.raise_()
            self.setFocus()
            self.grabKeyboard()
        except Exception:
            pass

    def enterEvent(self, event) -> None:
        """
        函数: enterEvent
        作用: 鼠标移入窗口区域时，启动延时计时器，延时后恢复显示并设置焦点。
        参数:
            event: 进入事件。
        返回:
            无。
        """
        try:
            self.hover_enter(event)
        except Exception:
            pass
        try:
            self._ensure_focus_and_keyboard()
        except Exception:
            pass
        try:
            super().enterEvent(event)
        except Exception:
            pass

    def focusInEvent(self, event) -> None:
        """
        函数: focusInEvent
        作用: 当窗口获得焦点时确保抓取键盘，避免按键丢失。
        参数:
            event: 焦点事件。
        返回:
            无。
        """
        try:
            self.grabKeyboard()
        except Exception:
            pass
        try:
            super().focusInEvent(event)
        except Exception:
            pass

    def leaveEvent(self, event) -> None:
        """
        函数: leaveEvent
        作用: 鼠标移出窗口区域时立即隐藏；拖动过程中不触发隐藏。
        参数:
            event: 离开事件。
        返回:
            无。
        """
        try:
            self.hover_leave(event)
        except Exception:
            pass
        try:
            self.releaseKeyboard()
        except Exception:
            pass
        try:
            super().leaveEvent(event)
        except Exception:
            pass

    def mousePressEvent(self, event) -> None:
        """
        函数: mousePressEvent
        作用: 鼠标左键按下时启动拖动（系统拖动或手工拖动），保证在窗口任意区域可拖动。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            self._drag_handle_press(event)
        except Exception:
            pass
        try:
            super().mousePressEvent(event)
        except Exception:
            pass

    def mouseMoveEvent(self, event) -> None:
        """
        函数: mouseMoveEvent
        作用: 拖动过程中根据记录偏移移动窗口位置，持续响应鼠标移动。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            self._drag_handle_move(event)
        except Exception:
            pass
        try:
            super().mouseMoveEvent(event)
        except Exception:
            pass

    def mouseReleaseEvent(self, event) -> None:
        """
        函数: mouseReleaseEvent
        作用: 鼠标释放后结束拖动状态，恢复正常交互。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            self._drag_handle_release(event)
        except Exception:
            pass
        try:
            super().mouseReleaseEvent(event)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """
        函数: eventFilter
        作用: 捕获子部件的鼠标事件并委托拖动处理，确保点击棋盘格或分数栏也可拖动窗口。
        参数:
            obj: 事件来源对象。
            event: 事件对象。
        返回:
            True/False（返回 False 以继续默认处理）。
        """
        try:
            et = event.type()
        except Exception:
            et = None
        try:
            if et == QEvent.MouseButtonPress:
                self._drag_handle_press(event)
            elif et == QEvent.MouseMove:
                self._drag_handle_move(event)
            elif et == QEvent.MouseButtonRelease:
                self._drag_handle_release(event)
        except Exception:
            pass
        try:
            return False
        except Exception:
            return False

    def showEvent(self, event) -> None:
        """
        函数: showEvent
        作用: 2048窗口显示时确保获得键盘焦点并置顶，避免WASD无响应。
        参数:
            event: 显示事件。
        返回:
            无。
        """
        try:
            self._ensure_focus_and_keyboard()
        except Exception:
            pass
        try:
            self._ensure_hit_test_surface()
        except Exception:
            pass
        try:
            super().showEvent(event)
        except Exception:
            pass

    def resizeEvent(self, event) -> None:
        """
        函数: resizeEvent
        作用: 在窗口大小变化时更新整窗遮罩，确保任意区域可接收鼠标事件。
        参数:
            event: 调整大小事件。
        返回:
            无。
        """
        try:
            self._ensure_hit_test_surface()
        except Exception:
            pass
        try:
            super().resizeEvent(event)
        except Exception:
            pass

    def _hover_show(self) -> None:
        """
        函数: _hover_show
        作用: 启动延时显示计时器（委托统一悬隐实现）。
        参数:
            无。
        返回:
            无。
        """
        try:
            super()._hover_show()
        except Exception:
            pass

    def _hover_show_now(self) -> None:
        """
        函数: _hover_show_now
        作用: 立即恢复窗口显示（委托统一悬隐实现）。
        参数:
            无。
        返回:
            无。
        """
        try:
            super()._hover_show_now()
        except Exception:
            pass

    def _hover_hide(self) -> None:
        """
        函数: _hover_hide
        作用: 鼠标移出立即隐藏（委托统一悬隐实现）。
        参数:
            无。
        返回:
            无。
        """
        try:
            super()._hover_hide()
        except Exception:
            pass

    def _show_game_over_dialog(self) -> None:
        """
        函数: _show_game_over_dialog
        作用: 弹出“游戏结束”提示框，并根据主程序黑夜/白天模式应用一致的配色样式。
        参数:
            无。
        返回:
            无。
        """
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("提示")
            msg.setText(f"游戏结束，分数：{self.score}")
            apply_message_box_theme(msg)
            try:
                msg.setStandardButtons(QMessageBox.Ok)
            except Exception:
                pass
            msg.exec()
        except Exception:
            try:
                QMessageBox.information(self, "提示", f"游戏结束，分数：{self.score}")
            except Exception:
                pass

    def _on_hover_timer(self) -> None:
        """
        函数: _on_hover_timer
        作用: 悬隐轮询（委托统一悬隐实现）。
        参数:
            无。
        返回:
            无。
        """
        try:
            super()._on_hover_timer()
        except Exception:
            pass

    def _is_near_window_edge(self, pos: QPoint) -> bool:
        """
        函数: _is_near_window_edge
        作用: 判断鼠标是否接近窗口矩形边缘（委托统一悬隐实现）。
        参数:
            pos: 全局坐标位置。
        返回:
            True/False。
        """
        try:
            return super()._is_near_window_edge(pos)
        except Exception:
            return False