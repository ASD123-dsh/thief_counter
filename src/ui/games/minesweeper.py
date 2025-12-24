"""
模块: minesweeper
作用: 纯字符扫雷游戏对话框（无边框）。保持原逻辑，接入统一悬隐与拖动。
"""

from typing import Optional, List
from PySide6.QtWidgets import QDialog, QLabel, QWidget, QGridLayout, QVBoxLayout, QMessageBox, QGraphicsOpacityEffect
from PySide6.QtGui import QRegion
from PySide6.QtCore import Qt, QPoint, QSettings

from ui.games.mixins import HoverHideMixin, DraggableMixin
from ui.games.services import apply_message_box_theme


class GameMinesweeperDialog(HoverHideMixin, DraggableMixin, QDialog):
    """
    类: GameMinesweeperDialog
    作用: 文字版扫雷窗口（无边框）。20x20 默认棋盘，默认 10 个地雷；左键揭开，右键标记/取消标记；胜利条件为揭开所有安全区域或正确标记所有地雷。
    参数:
        parent: 父级 QWidget。
    返回:
        无。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化扫雷对话框，构建界面与游戏状态，设置无边框与透明背景，启用悬隐与拖动。
        参数:
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        try:
            self.setWindowTitle("扫")
            self.setModal(False)
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setWindowModality(Qt.NonModal)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_StyledBackground, True)
            self._apply_bg_from_settings()
        except Exception:
            pass

        self.cols = 20
        self.rows = 20
        self.mine_count = 10
        self.mines = set()
        self.flags = set()
        self.revealed = set()
        self.counts: List[List[int]] = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        self.status_label = QLabel("状态: 标记 0/10 已揭 0")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.cells: List[List[QLabel]] = []
        grid = QGridLayout()
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(2)
        self._grid_wrap = QWidget(self)
        self._grid_wrap.setLayout(grid)
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
                try:
                    lbl.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                except Exception:
                    pass
                try:
                    def _bind_press(ev, rr=r, cc=c, owner=self):
                        try:
                            if ev.button() == Qt.LeftButton:
                                owner._reveal_cell(rr, cc)
                                return
                            if ev.button() == Qt.RightButton:
                                owner._toggle_flag(rr, cc)
                                return
                        except Exception:
                            pass
                        try:
                            QLabel.mousePressEvent(lbl, ev)
                        except Exception:
                            pass
                    lbl.mousePressEvent = _bind_press
                except Exception:
                    pass
                try:
                    lbl.setProperty("rc", f"{r},{c}")
                    lbl.installEventFilter(self)
                except Exception:
                    pass
                row.append(lbl)
                grid.addWidget(lbl, r, c)
            self.cells.append(row)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        root.addWidget(self.status_label)
        root.addWidget(self._grid_wrap)
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
            self.init_hover()
        except Exception:
            pass
        try:
            self._grid_wrap.installEventFilter(self)
        except Exception:
            pass
        try:
            self._apply_cells_bg_from_settings()
        except Exception:
            pass

        self.new_game()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        try:
            self._ensure_hit_test_surface()
        except Exception:
            pass

    def new_game(self) -> None:
        try:
            self._game_over = False
        except Exception:
            pass
        self.mines.clear()
        self.flags.clear()
        self.revealed.clear()
        try:
            placed = 0
            total = self.rows * self.cols
            if self.mine_count > total:
                self.mine_count = total
            import random
            while placed < int(self.mine_count):
                r = random.randint(0, self.rows - 1)
                c = random.randint(0, self.cols - 1)
                if (r, c) not in self.mines:
                    self.mines.add((r, c))
                    placed += 1
            for r in range(self.rows):
                for c in range(self.cols):
                    self.counts[r][c] = self._count_adjacent_mines(r, c)
        except Exception:
            pass
        self.update_view()
        self._update_status()

    def _count_adjacent_mines(self, r: int, c: int) -> int:
        try:
            cnt = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if (nr, nc) in self.mines:
                            cnt += 1
            return cnt
        except Exception:
            return 0

    def _update_status(self) -> None:
        try:
            self.status_label.setText(f"状态: 标记 {len(self.flags)}/{self.mine_count} 已揭 {len(self.revealed)}")
        except Exception:
            pass

    def update_view(self) -> None:
        try:
            for r in range(self.rows):
                for c in range(self.cols):
                    ch = ""
                    if (r, c) in self.flags and (r, c) not in self.revealed:
                        ch = "?"
                    elif (r, c) in self.revealed:
                        if (r, c) in self.mines:
                            ch = "X"
                        else:
                            n = self.counts[r][c]
                            ch = str(n) if n > 0 else ""
                    else:
                        ch = "·"
                    self.cells[r][c].setText(ch)
        except Exception:
            pass

    def _reveal_cell(self, r: int, c: int) -> None:
        try:
            if getattr(self, "_game_over", False):
                return
            if (r, c) in self.flags or (r, c) in self.revealed:
                return
            self.revealed.add((r, c))
            if (r, c) in self.mines:
                try:
                    self._game_over = True
                except Exception:
                    pass
                try:
                    self._reveal_all_mines()
                    self.update_view()
                    self._update_status()
                except Exception:
                    pass
                try:
                    self._show_game_over_dialog(False)
                except Exception:
                    pass
                return
            if self.counts[r][c] == 0:
                self._flood_reveal(r, c)
            self.update_view()
            self._update_status()
            self._check_win()
        except Exception:
            pass

    def _flood_reveal(self, r: int, c: int) -> None:
        try:
            from collections import deque
            q = deque()
            q.append((r, c))
            visited = set()
            while q:
                cr, cc = q.popleft()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                if (cr, cc) in self.flags:
                    continue
                if (cr, cc) not in self.revealed:
                    self.revealed.add((cr, cc))
                if self.counts[cr][cc] == 0:
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr = cr + dr
                            nc = cc + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if (nr, nc) not in self.revealed and (nr, nc) not in self.mines:
                                    q.append((nr, nc))
        except Exception:
            pass

    def _toggle_flag(self, r: int, c: int) -> None:
        try:
            if getattr(self, "_game_over", False):
                return
            if (r, c) in self.revealed:
                return
            if (r, c) in self.flags:
                self.flags.remove((r, c))
            else:
                self.flags.add((r, c))
            self.update_view()
            self._update_status()
            self._check_win()
        except Exception:
            pass

    def _reveal_all_mines(self) -> None:
        try:
            for (r, c) in self.mines:
                self.revealed.add((r, c))
        except Exception:
            pass

    def _check_win(self) -> None:
        try:
            safe_total = self.rows * self.cols - self.mine_count
            if len(self.revealed) >= safe_total or self.flags == self.mines:
                try:
                    self._game_over = True
                except Exception:
                    pass
                try:
                    self._show_game_over_dialog(True)
                except Exception:
                    pass
        except Exception:
            pass

    def keyPressEvent(self, event) -> None:
        key = event.key()
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

    def eventFilter(self, obj, event) -> bool:
        try:
            from PySide6.QtCore import QEvent
            if event.type() != QEvent.MouseButtonPress:
                return False
        except Exception:
            return False
        try:
            btn = event.button()
        except Exception:
            return False
        r = None
        c = None
        try:
            rc = obj.property("rc")
            if isinstance(rc, str) and "," in rc:
                parts = rc.split(",")
                r = int(parts[0])
                c = int(parts[1])
        except Exception:
            r = None
            c = None
        if r is None or c is None:
            try:
                if obj is getattr(self, "_grid_wrap", None):
                    gpos = event.globalPosition().toPoint()
                    found = False
                    for rr in range(self.rows):
                        for cc in range(self.cols):
                            lbl = self.cells[rr][cc]
                            try:
                                geo = lbl.frameGeometry()
                            except Exception:
                                geo = lbl.geometry()
                            x = gpos.x()
                            y = gpos.y()
                            if geo.left() <= x <= geo.right() and geo.top() <= y <= geo.bottom():
                                r = rr
                                c = cc
                                found = True
                                break
                        if found:
                            break
            except Exception:
                r = None
                c = None
        if r is None or c is None:
            return False
        if btn == Qt.LeftButton:
            self._reveal_cell(int(r), int(c))
            return True
        if btn == Qt.RightButton:
            self._toggle_flag(int(r), int(c))
            return True
        return False

    def _apply_text_opacity(self, alpha: float) -> None:
        try:
            a = 0.9 if alpha is None else float(alpha)
            a = 0.0 if a < 0.0 else (1.0 if a > 1.0 else a)
        except Exception:
            a = 0.9
        try:
            eff = QGraphicsOpacityEffect(self.status_label)
            eff.setOpacity(a)
            self.status_label.setGraphicsEffect(eff)
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
            self.status_label.setStyleSheet(f"QLabel{{color:{fg}; background: transparent;}}")
        except Exception:
            pass
        try:
            settings = QSettings()
            bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
            rr, gg, bb = self._hex_to_rgb(bg)
            a = 0.04
            for r in range(self.rows):
                for c in range(self.cols):
                    lbl = self.cells[r][c]
                    lbl.setStyleSheet(
                        f"QLabel{{color:{fg}; border: 1px solid #888; border-radius: 3px; background: rgba({rr},{gg},{bb},{a});}}"
                    )
        except Exception:
            pass

    def preview_theme(self, scheme: dict) -> None:
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
            self._apply_cells_bg_low_alpha(bg, 0.04)
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
        """
        函数: mousePressEvent
        作用: 鼠标左键按下时仅在非棋盘区域启动拖动；棋盘区域内保留左/右键交互（揭开/标记）。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            if event.button() == Qt.LeftButton:
                pos = None
                try:
                    pos = event.position().toPoint()
                except Exception:
                    pos = event.pos()
                try:
                    wrap = getattr(self, "_grid_wrap", None)
                    if wrap is not None:
                        rect = wrap.geometry()
                        if rect.contains(pos):
                            super().mousePressEvent(event)
                            return
                except Exception:
                    pass
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
        作用: 拖动过程中根据记录偏移移动窗口位置；棋盘区域内不影响点击操作。
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
        作用: 鼠标释放后结束拖动状态。
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

    def showEvent(self, event) -> None:
        """
        函数: showEvent
        作用: 对话框显示时更新命中测试遮罩，避免点击穿透。
        参数:
            event: 显示事件。
        返回:
            无。
        """
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
        作用: 在窗口大小变化时更新遮罩，确保任意非透明区域可命中。
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

    def _ensure_hit_test_surface(self) -> None:
        """
        函数: _ensure_hit_test_surface
        作用: 启用样式背景并设置整窗遮罩，使对话框整体参与命中测试。
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

    def _hex_to_rgb(self, s: str) -> tuple:
        """
        函数: _hex_to_rgb
        作用: 将 #RGB/#RRGGBB 颜色字符串转换为整数 RGB。
        参数:
            s: 颜色字符串。
        返回:
            (r, g, b)。
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
        作用: 以极低透明度应用背景色到对话框根，避免点击穿透。
        参数:
            bg_hex: 背景色（HEX）。
            alpha: 透明度。
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
            self.setStyleSheet(f"background: rgba({r},{g},{b},{a}); border: none;")
        except Exception:
            pass

    def _apply_bg_from_settings(self) -> None:
        """
        函数: _apply_bg_from_settings
        作用: 从设置读取摸鱼背景色并以极低透明度应用到对话框根背景。
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

    def _apply_cells_bg_low_alpha(self, bg_hex: str, alpha: float = 0.04) -> None:
        """
        函数: _apply_cells_bg_low_alpha
        作用: 为棋盘格 QLabel 应用极低透明度背景色，提升命中性。
        参数:
            bg_hex: 背景色（HEX）。
            alpha: 透明度。
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
            for rr in range(self.rows):
                for cc in range(self.cols):
                    lbl = self.cells[rr][cc]
                    lbl.setStyleSheet(
                        f"QLabel{{ border: 1px solid #888; border-radius: 3px; background: rgba({r},{g},{b},{a}); }}"
                    )
        except Exception:
            pass

    def _apply_cells_bg_from_settings(self) -> None:
        """
        函数: _apply_cells_bg_from_settings
        作用: 从设置读取摸鱼背景色并以极低透明度应用到所有棋盘格背景。
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

    def _show_game_over_dialog(self, win: bool) -> None:
        """
        函数: _show_game_over_dialog
        作用: 弹出胜利/失败提示框，并与主程序白天/黑夜模式配色保持一致。
        参数:
            win: True 胜利；False 失败。
        返回:
            无。
        """
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("提示")
            msg.setText("胜利！" if bool(win) else "游戏失败：踩到地雷")
            apply_message_box_theme(msg)
            try:
                msg.setStandardButtons(QMessageBox.Ok)
            except Exception:
                pass
            msg.exec()
        except Exception:
            try:
                QMessageBox.information(self, "提示", "胜利！" if bool(win) else "游戏失败：踩到地雷")
            except Exception:
                pass