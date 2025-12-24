"""
模块: gomoku
作用: 纯字符五子棋游戏对话框（无边框）。保持原逻辑，接入统一悬隐与拖动。
"""

from typing import Optional, List, Tuple
from PySide6.QtWidgets import QDialog, QLabel, QWidget, QGridLayout, QVBoxLayout, QMessageBox, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPoint, QTimer, QSettings
from PySide6.QtGui import QPainter, QColor, QBrush, QCursor, QFont
from ui.games.services import apply_message_box_theme

from ui.games.mixins import HoverHideMixin, DraggableMixin


class GameGomokuDialog(HoverHideMixin, DraggableMixin, QDialog):
    """
    类: GameGomokuDialog
    作用: 纯字符五子棋游戏窗口（无边框）。15x15 棋盘，黑先，黑白交替；支持鼠标左键落子、方向键移动光标与空格键落子；内置困难 AI（评分系统）。
    参数:
        parent: 父级 QWidget。
    返回:
        无。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化五子棋窗口，构建 15x15 棋盘与状态栏，设置透明背景、悬隐与拖动限制。
        参数:
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        try:
            self.setWindowTitle("五")
            self.setModal(False)
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setWindowModality(Qt.NonModal)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setStyleSheet("background: transparent; border: none;")
        except Exception:
            pass

        self.cols = 15
        self.rows = 15
        self.board: List[List[int]] = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_player: int = 1
        self.ai_enabled: bool = True
        self.ai_player: int = 2
        try:
            self.ai_depth: int = 2
            self.ai_branch_limit: int = 8
            self._ai_topk_eval: int = 6
        except Exception:
            pass
        try:
            self._win_line: List[Tuple[int, int]] = []
        except Exception:
            self._win_line = []
        self._game_over: bool = False
        self._cursor_r: int = self.rows // 2
        self._cursor_c: int = self.cols // 2

        self.status_label = QLabel("状态: 当前 黑方 (AI: 白方)")
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
                    lbl.setMinimumSize(20, 20)
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
                                owner._on_cell_click(rr, cc)
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
            self.setFixedSize(self.cols * 22 + 16, self.rows * 22 + 60)
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

        self.new_game()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def new_game(self) -> None:
        """
        函数: new_game
        作用: 开始新局，重置棋盘、当前方与光标位置。
        参数:
            无。
        返回:
            无。
        """
        try:
            self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
            self.current_player = 1
            self._game_over = False
            self._cursor_r = self.rows // 2
            self._cursor_c = self.cols // 2
            self.status_label.setText("状态: 当前 黑方 (AI: 白方)")
            try:
                self._win_line = []
            except Exception:
                pass
            self.update_view()
        except Exception:
            pass

    def update_view(self) -> None:
        """
        函数: update_view
        作用: 刷新棋盘显示，根据棋子与光标状态设置字符。
        参数:
            无。
        返回:
            无。
        """
        try:
            for r in range(self.rows):
                for c in range(self.cols):
                    v = self.board[r][c]
                    ch = ""
                    if v == 1:
                        ch = "■"
                    elif v == 2:
                        ch = "□"
                    else:
                        if r == self._cursor_r and c == self._cursor_c:
                            ch = "*"
                        else:
                            ch = ""
                    self.cells[r][c].setText(ch)
                    try:
                        winset = set(getattr(self, "_win_line", []))
                        lbl = self.cells[r][c]
                        f = lbl.font()
                        if (r, c) in winset:
                            try:
                                f.setBold(True)
                                f.setWeight(QFont.Weight.Bold)
                            except Exception:
                                f.setBold(True)
                        else:
                            try:
                                f.setBold(False)
                                f.setWeight(QFont.Weight.Normal)
                            except Exception:
                                f.setBold(False)
                        lbl.setFont(f)
                    except Exception:
                        pass
        except Exception:
            pass

    def _on_cell_click(self, r: int, c: int) -> None:
        """
        函数: _on_cell_click
        作用: 鼠标左键在指定格子落子（若为空且未结束）。
        参数:
            r, c: 行列索引。
        返回:
            无。
        """
        try:
            if self._game_over:
                return
            if self.board[r][c] != 0:
                return
            if self.ai_enabled and self.current_player == self.ai_player:
                return
            self._cursor_r, self._cursor_c = r, c
            self._place_current(r, c)
        except Exception:
            pass

    def _place_current(self, r: int, c: int) -> None:
        """
        函数: _place_current
        作用: 在 (r,c) 放置当前方棋子，判定胜负、切换行方，并驱动 AI 回合。
        参数:
            r, c: 行列索引。
        返回:
            无。
        """
        try:
            if self._game_over or self.board[r][c] != 0:
                return
            self.board[r][c] = self.current_player
            if self._check_win_at(r, c):
                self._game_over = True
                side = "黑方" if self.current_player == 1 else "白方"
                try:
                    self.status_label.setText(f"状态: {side} 获胜")
                except Exception:
                    pass
                try:
                    self._show_game_over_dialog(f"{side} 获胜！")
                except Exception:
                    pass
                self.update_view()
                return
            if self._is_draw():
                self._game_over = True
                try:
                    self.status_label.setText("状态: 平局")
                except Exception:
                    pass
                try:
                    self._show_game_over_dialog("平局！")
                except Exception:
                    pass
                self.update_view()
                return
            self.current_player = 2 if self.current_player == 1 else 1
            try:
                self.status_label.setText(f"状态: 当前 {'黑方' if self.current_player == 1 else '白方'} (AI: {'白方' if self.ai_player == 2 else '黑方'})")
            except Exception:
                pass
            self.update_view()
            try:
                if self.ai_enabled and self.current_player == self.ai_player and not self._game_over:
                    QTimer.singleShot(1, self._ai_move)
            except Exception:
                pass
        except Exception:
            pass

    def _check_win_at(self, r: int, c: int) -> bool:
        """
        函数: _check_win_at
        作用: 判断在 (r,c) 处最新落子是否形成五连。
        参数:
            r, c: 行列索引。
        返回:
            True/False。
        """
        try:
            color = self.board[r][c]
            if color == 0:
                return False
            dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]
            for dr, dc in dirs:
                try:
                    line = self._collect_line_positions(r, c, dr, dc)
                except Exception:
                    line = []
                if len(line) >= 5:
                    try:
                        self._win_line = list(line)
                    except Exception:
                        self._win_line = line
                    return True
            return False
        except Exception:
            return False

    def _collect_line_positions(self, r: int, c: int, dr: int, dc: int) -> List[Tuple[int, int]]:
        """
        函数: _collect_line_positions
        作用: 收集以 (r,c) 为中心，沿方向 (dr,dc) 的同色连续坐标序列（包含双向）。
        参数:
            r, c: 行列索引。
            dr, dc: 方向增量。
        返回:
            连续坐标列表（按顺序）。
        """
        try:
            color = self.board[r][c]
            if color == 0:
                return []
            line: List[Tuple[int, int]] = [(r, c)]
            rr = r + dr
            cc = c + dc
            while 0 <= rr < self.rows and 0 <= cc < self.cols and self.board[rr][cc] == color:
                line.append((rr, cc))
                rr += dr
                cc += dc
            rr = r - dr
            cc = c - dc
            left: List[Tuple[int, int]] = []
            while 0 <= rr < self.rows and 0 <= cc < self.cols and self.board[rr][cc] == color:
                left.append((rr, cc))
                rr -= dr
                cc -= dc
            if left:
                try:
                    left.reverse()
                except Exception:
                    pass
                line = left + line
            return line
        except Exception:
            return []

    def _show_game_over_dialog(self, text: str) -> None:
        """
        函数: _show_game_over_dialog
        作用: 弹出结束提示框，并与主程序黑夜/白天模式配色保持一致。
        参数:
            text: 提示文本。
        返回:
            无。
        """
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("提示")
            msg.setText(str(text))
            apply_message_box_theme(msg)
            try:
                msg.setStandardButtons(QMessageBox.Ok)
            except Exception:
                pass
            msg.exec()
        except Exception:
            try:
                QMessageBox.information(self, "提示", str(text))
            except Exception:
                pass

    def _is_draw(self) -> bool:
        """
        函数: _is_draw
        作用: 判断是否棋盘已满且无胜负。
        参数:
            无。
        返回:
            True/False。
        """
        try:
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.board[r][c] == 0:
                        return False
            return True
        except Exception:
            return False

    def _ai_move(self) -> None:
        """
        函数: _ai_move
        作用: 执行 AI 回合，使用浅层 Alpha-Beta 搜索（默认 2 层）与增强评分选择最优落点。
        参数:
            无。
        返回:
            无。
        """
        try:
            if self._game_over or not self.ai_enabled or self.current_player != self.ai_player:
                return
            cand = self._ai_generate_candidates()
            if not cand:
                self._place_current(self.rows // 2, self.cols // 2)
                return
            try:
                depth = int(getattr(self, "ai_depth", 2))
                if len(cand) <= 8:
                    depth = min(3, max(2, depth))
            except Exception:
                depth = 2
            score, move = self._alpha_beta(depth, self.ai_player, -1e18, 1e18)
            if move is None:
                move = cand[0]
            self._place_current(int(move[0]), int(move[1]))
        except Exception:
            pass

    def _score_if_place(self, player: int, r: int, c: int) -> float:
        """
        函数: _score_if_place
        作用: 模拟在 (r,c) 放置 player 的棋子并评估该点得分。
        参数:
            player: 行方（1 黑 / 2 白）。
            r, c: 行列索引。
        返回:
            分数（越大越好）。
        """
        try:
            if self.board[r][c] != 0:
                return -1e18
            dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]
            total = 0.0
            win = False
            for dr, dc in dirs:
                left = self._contiguous(r, c, -dr, -dc, player)
                right = self._contiguous(r, c, dr, dc, player)
                count = 1 + left[0] + right[0]
                if count >= 5:
                    win = True
                open_ends = int(left[1]) + int(right[1])
                if count == 4:
                    total += 2e6 if open_ends == 2 else 2e5
                elif count == 3:
                    total += 4e4 if open_ends == 2 else 6e3
                elif count == 2:
                    total += 600 if open_ends == 2 else 160
                else:
                    total += 30 if open_ends >= 1 else 6
            if win:
                return 1e9
            try:
                center_r = self.rows // 2
                center_c = self.cols // 2
                center_bias = -0.5 * float(abs(r - center_r) + abs(c - center_c))
                return total + center_bias
            except Exception:
                return total
        except Exception:
            return 0.0

    def _ai_generate_candidates(self) -> List[Tuple[int, int]]:
        """
        函数: _ai_generate_candidates
        作用: 生成 AI 搜索候选集（围绕已有棋子 2 格内的空位），并按启发式排序。
        参数:
            无。
        返回:
            候选坐标列表。
        """
        try:
            stones = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.board[r][c] != 0]
            if not stones:
                return [(self.rows // 2, self.cols // 2)]
            cand = set()
            for r, c in stones:
                for dr in (-2, -1, 0, 1, 2):
                    for dc in (-2, -1, 0, 1, 2):
                        rr = r + dr
                        cc = c + dc
                        if 0 <= rr < self.rows and 0 <= cc < self.cols and self.board[rr][cc] == 0:
                            cand.add((rr, cc))
            scored = []
            op = 1 if self.ai_player == 2 else 2
            for (r, c) in cand:
                try:
                    s_ai = self._score_if_place(self.ai_player, r, c)
                    s_op = self._score_if_place(op, r, c)
                    scored.append(((r, c), s_ai * 1.2 + s_op * 1.0))
                except Exception:
                    scored.append(((r, c), 0.0))
            try:
                scored.sort(key=lambda x: x[1], reverse=True)
            except Exception:
                pass
            try:
                limit = int(getattr(self, "ai_branch_limit", 8))
                scored = scored[:max(1, limit)]
            except Exception:
                pass
            return [xy for (xy, _) in scored]
        except Exception:
            return []

    def _evaluate_board(self, player: int) -> float:
        """
        函数: _evaluate_board
        作用: 评估当前棋盘形势，返回对 player 的综合评分（越大越好）。
        参数:
            player: 行方（1/2）。
        返回:
            分数。
        """
        try:
            cand = self._ai_generate_candidates()
            if not cand:
                return 0.0
            op = 1 if player == 2 else 2
            ai_scores = []
            op_scores = []
            for (r, c) in cand:
                ai_scores.append(self._score_if_place(player, r, c))
                op_scores.append(self._score_if_place(op, r, c))
            try:
                ai_scores.sort(reverse=True)
                op_scores.sort(reverse=True)
            except Exception:
                pass
            try:
                k = int(getattr(self, "_ai_topk_eval", 6))
            except Exception:
                k = 6
            ai_sum = sum(ai_scores[:k])
            op_sum = sum(op_scores[:k])
            return ai_sum * 1.0 - op_sum * 1.05
        except Exception:
            return 0.0

    def _alpha_beta(self, depth: int, to_move: int, alpha: float, beta: float) -> Tuple[float, Optional[Tuple[int, int]]]:
        """
        函数: _alpha_beta
        作用: Alpha-Beta 搜索，返回评分与最优着法。
        参数:
            depth: 搜索深度（层数）。
            to_move: 当前行方（1/2）。
            alpha, beta: 剪枝边界。
        返回:
            (评分, 最优坐标 或 None)。
        """
        try:
            if depth <= 0:
                return self._evaluate_board(self.ai_player), None
            cand = self._ai_generate_candidates()
            if not cand:
                return 0.0, None
            maximizing = (to_move == self.ai_player)
            best_move = None
            if maximizing:
                best_score = -1e18
                for (r, c) in cand:
                    try:
                        self.board[r][c] = to_move
                        if self._check_win_at(r, c):
                            score = 1e12 - (3 - depth) * 1e6
                        else:
                            score, _ = self._alpha_beta(depth - 1, 1 if to_move == 2 else 2, alpha, beta)
                        if score > best_score:
                            best_score = score
                            best_move = (r, c)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            self.board[r][c] = 0
                            break
                    except Exception:
                        pass
                    try:
                        self.board[r][c] = 0
                    except Exception:
                        pass
                return best_score, best_move
            else:
                best_score = 1e18
                for (r, c) in cand:
                    try:
                        self.board[r][c] = to_move
                        if self._check_win_at(r, c):
                            score = -1e12 + (3 - depth) * 1e6
                        else:
                            score, _ = self._alpha_beta(depth - 1, 1 if to_move == 2 else 2, alpha, beta)
                        if score < best_score:
                            best_score = score
                            best_move = (r, c)
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            self.board[r][c] = 0
                            break
                    except Exception:
                        pass
                    try:
                        self.board[r][c] = 0
                    except Exception:
                        pass
                return best_score, best_move
        except Exception:
            return 0.0, None

    def _contiguous(self, r: int, c: int, dr: int, dc: int, player: int) -> Tuple[int, bool]:
        """
        函数: _contiguous
        作用: 计算从 (r,c) 出发沿方向 (dr,dc) 的同色连续数量以及该侧端点是否空（开放）。
        参数:
            r, c: 行列索引。
            dr, dc: 方向增量。
            player: 行方。
        返回:
            (连续数量, 该侧开放端 True/False)。
        """
        try:
            cnt = 0
            rr = r + dr
            cc = c + dc
            while 0 <= rr < self.rows and 0 <= cc < self.cols and self.board[rr][cc] == player:
                cnt += 1
                rr += dr
                cc += dc
            open_side = (0 <= rr < self.rows and 0 <= cc < self.cols and self.board[rr][cc] == 0)
            return cnt, open_side
        except Exception:
            return 0, False

    def keyPressEvent(self, event) -> None:
        """
        函数: keyPressEvent
        作用: 方向键/WASD 移动光标；空格落子；Esc 关闭；R 重开。
        参数:
            event: 键盘事件。
        返回:
            无。
        """
        try:
            key = event.key()
            if key in (Qt.Key_Left, Qt.Key_A):
                self._cursor_c = max(0, self._cursor_c - 1)
                self.update_view()
                return
            if key in (Qt.Key_Right, Qt.Key_D):
                self._cursor_c = min(self.cols - 1, self._cursor_c + 1)
                self.update_view()
                return
            if key in (Qt.Key_Up, Qt.Key_W):
                self._cursor_r = max(0, self._cursor_r - 1)
                self.update_view()
                return
            if key in (Qt.Key_Down, Qt.Key_S):
                self._cursor_r = min(self.rows - 1, self._cursor_r + 1)
                self.update_view()
                return
            if key == Qt.Key_Space:
                if not self._game_over and self.board[self._cursor_r][self._cursor_c] == 0 and (not (self.ai_enabled and self.current_player == self.ai_player)):
                    self._place_current(self._cursor_r, self._cursor_c)
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
        except Exception:
            pass
        try:
            super().keyPressEvent(event)
        except Exception:
            pass

    def eventFilter(self, obj, event) -> bool:
        """
        函数: eventFilter
        作用: 兜底处理棋盘容器点击命中，确保用户点击映射到格子。
        参数:
            obj: 事件源对象。
            event: 事件实例。
        返回:
            True/False。
        """
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
        if btn != Qt.LeftButton:
            return False
        try:
            rc = obj.property("rc")
            if isinstance(rc, str) and "," in rc:
                parts = rc.split(",")
                r = int(parts[0])
                c = int(parts[1])
                self._on_cell_click(r, c)
                return True
        except Exception:
            pass
        try:
            if obj is getattr(self, "_grid_wrap", None):
                gpos = event.globalPosition().toPoint()
                for rr in range(self.rows):
                    for cc in range(self.cols):
                        lbl = self.cells[rr][cc]
                        try:
                            geo = lbl.frameGeometry()
                        except Exception:
                            geo = lbl.geometry()
                        if geo.left() <= gpos.x() <= geo.right() and geo.top() <= gpos.y() <= geo.bottom():
                            self._on_cell_click(rr, cc)
                            return True
        except Exception:
            pass
        return False

    def mousePressEvent(self, event) -> None:
        """
        函数: mousePressEvent
        作用: 左键点击非棋盘区域时记录偏移以允许拖动；棋盘范围内不触发拖动。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            if event.button() == Qt.LeftButton:
                gpos = event.globalPosition().toPoint()
                try:
                    top_left = self._grid_wrap.mapToGlobal(QPoint(0, 0))
                except Exception:
                    top_left = QPoint(0, 0)
                try:
                    size = self._grid_wrap.size()
                except Exception:
                    from PySide6.QtCore import QSize
                    size = QSize(0, 0)
                gx = top_left.x()
                gy = top_left.y()
                inside = (gx <= gpos.x() <= gx + size.width()) and (gy <= gpos.y() <= gy + size.height())
                if not inside:
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
        作用: 鼠标移动时若处于拖动状态，则按记录偏移移动窗口位置。
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

    def paintEvent(self, event) -> None:
        """
        函数: paintEvent
        作用: 在透明背景上绘制低不透明度棋盘格，提供伪装底纹。
        参数:
            event: 绘制事件。
        返回:
            无。
        """
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
        """
        函数: enterEvent
        作用: 鼠标移入窗口区域时，启动延时计时器，延时后恢复显示。
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
            self.setFocus()
        except Exception:
            pass
        try:
            super().enterEvent(event)
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
            super().leaveEvent(event)
        except Exception:
            pass

    def _apply_text_opacity(self, alpha: float) -> None:
        """
        函数: _apply_text_opacity
        作用: 为状态栏与棋盘格标签设置统一的不透明度效果。
        参数:
            alpha: 不透明度 (0.0~1.0)。
        返回:
            无。
        """
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
        """
        函数: _apply_theme_fg_from_settings
        作用: 从 QSettings 读取极简模式前景色并应用。
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
        作用: 应用前景色到状态与棋盘格标签的文本颜色。
        参数:
            fg: 文本颜色字符串。
        返回:
            无。
        """
        try:
            self.status_label.setStyleSheet(f"QLabel{{color:{fg}; background: transparent;}}")
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
        """
        函数: preview_theme
        作用: 预览主题（仅应用 fg 颜色）。
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