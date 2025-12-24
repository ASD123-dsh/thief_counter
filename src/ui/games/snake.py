"""
模块: snake
作用: 纯字符贪吃蛇游戏对话框（无边框）。保持原逻辑，接入统一悬隐与拖动。
"""

from typing import Optional, List, Tuple
from PySide6.QtWidgets import QDialog, QLabel, QWidget, QGridLayout, QVBoxLayout, QMessageBox, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QPainter, QColor, QBrush

from ui.games.mixins import HoverHideMixin, DraggableMixin
from ui.games.services import apply_message_box_theme


class GameSnakeDialog(HoverHideMixin, DraggableMixin, QDialog):
    """
    类: GameSnakeDialog
    作用: 文字版贪吃蛇游戏窗口（无边框）。使用“*”表示蛇身，“o”表示食物，仅支持方向键控制。
    参数:
        parent: 父级 QWidget。
    返回:
        无。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化贪吃蛇对话框，构建界面与游戏状态，设置无边框与透明背景，并启用悬隐与拖动。
        参数:
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        try:
            self.setWindowTitle("吃")
            self.setModal(False)
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setWindowModality(Qt.NonModal)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setStyleSheet("background: transparent; border: none;")
        except Exception:
            pass

        self.cols = 20
        self.rows = 14
        self.score: int = 0
        self.direction = Qt.Key_Right
        self.snake: List[Tuple[int, int]] = []
        self.food: Tuple[int, int] = (0, 0)

        self.score_label = QLabel("分数: 0")
        self.score_label.setAlignment(Qt.AlignCenter)

        self.cells: List[List[QLabel]] = []
        grid = QGridLayout()
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(2)
        for r in range(self.rows):
            row: List[QLabel] = []
            for c in range(self.cols):
                lbl = QLabel("")
                lbl.setAlignment(Qt.AlignCenter)
                try:
                    lbl.setMinimumSize(18, 18)
                except Exception:
                    pass
                try:
                    lbl.setStyleSheet("QLabel { border: 1px solid #888; border-radius: 3px; background: transparent; }")
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
            self.setFixedSize(self.cols * 20 + 16, self.rows * 20 + 60)
        except Exception:
            pass

        try:
            self.init_drag()
        except Exception:
            pass
        try:
            self._apply_text_opacity(0.9)
        except Exception:
            pass
        try:
            self._apply_theme_fg_from_settings()
        except Exception:
            pass
        try:
            self.init_hover()
        except Exception:
            pass

        try:
            self._tick_timer = QTimer(self)
            self._tick_timer.setInterval(260)
            self._tick_timer.timeout.connect(self._on_tick)
        except Exception:
            pass

        self.new_game()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def new_game(self) -> None:
        self.score = 0
        try:
            self._game_over = False
        except Exception:
            pass
        self.direction = Qt.Key_Right
        cx, cy = self.cols // 2, self.rows // 2
        self.snake = [(cy, cx - 1), (cy, cx), (cy, cx + 1)]
        self._spawn_food()
        self.update_view()
        try:
            self._tick_timer.start()
        except Exception:
            pass

    def _spawn_food(self) -> None:
        import random as _rnd
        empties = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in self.snake]
        if not empties:
            return
        self.food = _rnd.choice(empties)

    def update_view(self) -> None:
        try:
            self.score_label.setText(f"分数: {self.score}")
        except Exception:
            pass
        try:
            for r in range(self.rows):
                for c in range(self.cols):
                    ch = ""
                    if (r, c) == self.food:
                        ch = "o"
                    elif (r, c) in self.snake:
                        ch = "*"
                    self.cells[r][c].setText(ch)
        except Exception:
            pass

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_A, Qt.Key_D, Qt.Key_W, Qt.Key_S):
            if key == Qt.Key_A:
                self._set_direction(Qt.Key_Left)
            elif key == Qt.Key_D:
                self._set_direction(Qt.Key_Right)
            elif key == Qt.Key_W:
                self._set_direction(Qt.Key_Up)
            elif key == Qt.Key_S:
                self._set_direction(Qt.Key_Down)
            else:
                self._set_direction(key)
            return
        if key == Qt.Key_Escape:
            try:
                self.close()
            except Exception:
                pass
            return
        if key == Qt.Key_R:
            self.new_game()
            return
        super().keyPressEvent(event)

    def _set_direction(self, key: int) -> None:
        try:
            if not self.snake:
                self.direction = key
                return
            head = self.snake[-1]
            prev = self.snake[-2] if len(self.snake) > 1 else head
            dx = head[1] - prev[1]
            dy = head[0] - prev[0]
            if key == Qt.Key_Left and dx != 1:
                self.direction = key
            elif key == Qt.Key_Right and dx != -1:
                self.direction = key
            elif key == Qt.Key_Up and dy != 1:
                self.direction = key
            elif key == Qt.Key_Down and dy != -1:
                self.direction = key
        except Exception:
            pass

    def _on_tick(self) -> None:
        try:
            if not self.snake:
                return
            head = self.snake[-1]
            nr, nc = head[0], head[1]
            if self.direction == Qt.Key_Left:
                nc -= 1
            elif self.direction == Qt.Key_Right:
                nc += 1
            elif self.direction == Qt.Key_Up:
                nr -= 1
            elif self.direction == Qt.Key_Down:
                nr += 1
            if nr < 0 or nr >= self.rows or nc < 0 or nc >= self.cols or (nr, nc) in self.snake:
                try:
                    self._tick_timer.stop()
                except Exception:
                    pass
                try:
                    self._game_over = True
                except Exception:
                    pass
                try:
                    self._show_game_over_dialog()
                except Exception:
                    pass
                return
            self.snake.append((nr, nc))
            if (nr, nc) == self.food:
                try:
                    self.score += 1
                    self._spawn_food()
                except Exception:
                    pass
            else:
                try:
                    self.snake.pop(0)
                except Exception:
                    pass
            self.update_view()
        except Exception:
            pass

    def _apply_text_opacity(self, alpha: float) -> None:
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
        try:
            for r in range(self.rows):
                for c in range(self.cols):
                    lbl = self.cells[r][c]
                    eff = QGraphicsOpacityEffect(lbl)
                    eff.setOpacity(a)
                    lbl.setGraphicsEffect(eff)
        except Exception:
            pass

    def _apply_theme_fg_from_settings(self) -> None:
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
        try:
            self.score_label.setStyleSheet(f"QLabel{{color:{fg}; background: transparent;}}")
        except Exception:
            pass
        try:
            for r in range(self.rows):
                for c in range(self.cols):
                    lbl = self.cells[r][c]
                    lbl.setStyleSheet(f"QLabel{{color:{fg}; border: 1px solid #888; border-radius: 3px; background: transparent;}}")
        except Exception:
            pass

    def preview_theme(self, scheme: dict) -> None:
        try:
            fg = str(scheme.get("fg", "#1E1E1E")) if isinstance(scheme, dict) else "#1E1E1E"
            self._apply_theme_fg(fg)
        except Exception:
            pass

    def preview_opacity(self, percent: int) -> None:
        try:
            if getattr(self, "_hover_hidden", False):
                return
            p = 1 if int(percent) < 1 else (100 if int(percent) > 100 else int(percent))
            self.setWindowOpacity(p / 100.0 if p > 1 else 1.0)
        except Exception:
            pass

    def mousePressEvent(self, event) -> None:
        try:
            self._drag_handle_press(event)
        except Exception:
            pass
        try:
            super().mousePressEvent(event)
        except Exception:
            pass

    def mouseMoveEvent(self, event) -> None:
        try:
            self._drag_handle_move(event)
        except Exception:
            pass
        try:
            super().mouseMoveEvent(event)
        except Exception:
            pass

    def mouseReleaseEvent(self, event) -> None:
        try:
            self._drag_handle_release(event)
        except Exception:
            pass
        try:
            super().mouseReleaseEvent(event)
        except Exception:
            pass

    def paintEvent(self, event) -> None:
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            rect = self.rect()
            size = 12
            light = QColor(0, 0, 0, 3)
            dark = QColor(0, 0, 0, 6)
            for y in range(0, rect.height(), size):
                for x in range(0, rect.width(), size):
                    is_dark = ((x // size) + (y // size)) % 2 == 1
                    painter.fillRect(x, y, size, size, QBrush(dark if is_dark else light))
            painter.end()
        except Exception:
            pass
        try:
            super().paintEvent(event)
        except Exception:
            pass

    def enterEvent(self, event) -> None:
        try:
            self.hover_enter(event)
        except Exception:
            pass
        try:
            super().enterEvent(event)
        except Exception:
            pass

    def leaveEvent(self, event) -> None:
        try:
            self.hover_leave(event)
        except Exception:
            pass
        try:
            super().leaveEvent(event)
        except Exception:
            pass

    def _on_hover_hidden_hook(self) -> None:
        """
        函数: _on_hover_hidden_hook
        作用: 悬隐隐藏回调：鼠标移出窗口时暂停贪吃蛇的计时器。
        参数:
            无。
        返回:
            无。
        """
        try:
            if hasattr(self, "_tick_timer") and self._tick_timer is not None:
                self._tick_timer.stop()
        except Exception:
            pass

    def _on_hover_shown_hook(self) -> None:
        """
        函数: _on_hover_shown_hook
        作用: 悬隐显示回调：鼠标移入并恢复显示后，若未游戏结束则继续计时。
        参数:
            无。
        返回:
            无。
        """
        try:
            if getattr(self, "_game_over", False):
                return
            if hasattr(self, "_tick_timer") and self._tick_timer is not None:
                self._tick_timer.start()
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