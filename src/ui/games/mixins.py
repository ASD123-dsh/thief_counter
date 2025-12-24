"""
模块: mixins
作用: 提供统一的悬隐与拖动行为混入类，供四款文字小游戏复用。
"""

from PySide6.QtCore import QTimer, QPoint, Qt
from PySide6.QtGui import QCursor

from ui.games.services import HoverConfig


class HoverHideMixin:
    """
    类: HoverHideMixin
    作用: 统一实现鼠标悬隐策略：移出立即隐藏、靠近边缘/移入延时显示、显示态轮询离开即隐藏。
    参数:
        无。
    返回:
        无。
    """

    def init_hover(self) -> None:
        """
        函数: init_hover
        作用: 初始化悬隐定时器与参数，注册回调。
        参数:
            无。
        返回:
            无。
        """
        try:
            self._hover_enabled = True
            self._hover_hidden = False
            self._hover_hidden_opacity = float(HoverConfig.hidden_opacity())
            self._hover_window_edge_px = int(HoverConfig.edge_margin_px())
            self._hover_delay_ms = int(HoverConfig.delay_ms())
            self._hover_timer = QTimer(self)
            self._hover_timer.setInterval(160)
            self._hover_timer.timeout.connect(self._on_hover_timer)
            self._hover_show_delay_timer = QTimer(self)
            self._hover_show_delay_timer.setSingleShot(True)
            self._hover_show_delay_timer.setInterval(int(self._hover_delay_ms))
            self._hover_show_delay_timer.timeout.connect(self._hover_show_now)
            self._edge_near_ticks = 0
            self._hover_timer.start()
        except Exception:
            pass

    def hover_enter(self, event) -> None:
        """
        函数: hover_enter
        作用: 鼠标进入时按设置延时触发显示。
        参数:
            event: 进入事件。
        返回:
            无。
        """
        try:
            if getattr(self, "_hover_hidden", False):
                self._hover_delay_ms = int(HoverConfig.delay_ms())
                self._hover_show()
        except Exception:
            pass

    def hover_leave(self, event) -> None:
        """
        函数: hover_leave
        作用: 鼠标离开时立即隐藏；拖动过程中不触发隐藏。
        参数:
            event: 离开事件。
        返回:
            无。
        """
        try:
            if not getattr(self, "_dragging", False):
                self._hover_hide()
        except Exception:
            pass

    def _hover_show(self) -> None:
        """
        函数: _hover_show
        作用: 启动延时显示计时器。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not getattr(self, "_hover_enabled", True):
                return
            if hasattr(self, "_hover_show_delay_timer") and self._hover_show_delay_timer is not None:
                self._hover_show_delay_timer.setInterval(int(getattr(self, "_hover_delay_ms", 1500)))
                if not self._hover_show_delay_timer.isActive():
                    self._hover_show_delay_timer.start()
        except Exception:
            pass

    def _hover_show_now(self) -> None:
        """
        函数: _hover_show_now
        作用: 立即恢复窗口显示（不透明度 1.0），显示态保持轮询。
        参数:
            无。
        返回:
            无。
        """
        try:
            try:
                self._animate_opacity(1.0, 150)
            except Exception:
                try:
                    self.setWindowOpacity(1.0)
                except Exception:
                    pass
            self._hover_hidden = False
            try:
                if hasattr(self, "_hover_timer") and self._hover_timer is not None:
                    if not self._hover_timer.isActive():
                        self._hover_timer.start()
            except Exception:
                pass
            try:
                self._on_hover_shown_hook()
            except Exception:
                pass
        except Exception:
            pass

    def _hover_hide(self) -> None:
        """
        函数: _hover_hide
        作用: 鼠标移出时立即隐藏（不透明度设置为隐藏值），停止等待计时器并保持轮询。
        参数:
            无。
        返回:
            无。
        """
        try:
            if hasattr(self, "_hover_show_delay_timer") and self._hover_show_delay_timer is not None:
                if self._hover_show_delay_timer.isActive():
                    self._hover_show_delay_timer.stop()
        except Exception:
            pass
        try:
            target = float(getattr(self, "_hover_hidden_opacity", 0.06))
        except Exception:
            target = 0.06
        try:
            self._animate_opacity(target, 150)
        except Exception:
            try:
                self.setWindowOpacity(target)
            except Exception:
                pass
        try:
            self._hover_hidden = True
        except Exception:
            pass
        try:
            if hasattr(self, "_hover_timer") and self._hover_timer is not None:
                if not self._hover_timer.isActive():
                    self._hover_timer.start()
        except Exception:
            pass
        try:
            self._on_hover_hidden_hook()
        except Exception:
            pass

    def _on_hover_timer(self) -> None:
        """
        函数: _on_hover_timer
        作用: 悬隐轮询：隐藏态靠近边缘累计达到阈值后显示；显示态未拖动且离开窗口立即隐藏。
        参数:
            无。
        返回:
            无。
        """
        try:
            pos = None
            try:
                pos = QCursor.pos()
            except Exception:
                pos = None
            if pos is None:
                return
            if getattr(self, "_hover_hidden", False):
                try:
                    if self._is_near_window_edge(pos):
                        try:
                            self._edge_near_ticks += 1
                        except Exception:
                            self._edge_near_ticks = 1
                        try:
                            ms = int(getattr(self, "_hover_delay_ms", 1500))
                            need = int(ms / max(1, int(self._hover_timer.interval())))
                        except Exception:
                            need = 10
                        if self._edge_near_ticks >= need:
                            self._hover_show()
                            self._edge_near_ticks = 0
                            return
                    else:
                        self._edge_near_ticks = 0
                except Exception:
                    pass
            else:
                try:
                    if not getattr(self, "_dragging", False):
                        local = self.mapFromGlobal(pos)
                        inside = self.rect().contains(local)
                        if not inside:
                            self._hover_hide()
                except Exception:
                    pass
        except Exception:
            pass

    def _is_near_window_edge(self, pos) -> bool:
        """
        函数: _is_near_window_edge
        作用: 判断鼠标是否接近窗口矩形边缘或处于窗口内部。
        参数:
            pos: 全局坐标位置。
        返回:
            True/False。
        """
        try:
            geo = self.frameGeometry()
        except Exception:
            geo = self.geometry()
        try:
            margin = int(getattr(self, "_hover_window_edge_px", 10))
        except Exception:
            margin = 10
        try:
            left = geo.left()
            right = geo.right()
            top = geo.top()
            bottom = geo.bottom()
            x = pos.x()
            y = pos.y()
            near_h = (left - margin <= x <= left + margin) or (right - margin <= x <= right + margin)
            near_v = (top - margin <= y <= top + margin) or (bottom - margin <= y <= bottom + margin)
            inside = (left <= x <= right) and (top <= y <= bottom)
            return (near_h and (top - margin <= y <= bottom + margin)) or (near_v and (left - margin <= x <= right + margin)) or inside
        except Exception:
            return False


class DraggableMixin:
    """
    类: DraggableMixin
    作用: 统一实现拖动行为，优先使用系统拖动，失败时回退到手工拖动。
    参数:
        无。
    返回:
        无。
    """

    def init_drag(self) -> None:
        """
        函数: init_drag
        作用: 初始化拖动相关状态与系统拖动能力探测。
        参数:
            无。
        返回:
            无。
        """
        try:
            self._dragging = False
            self._drag_offset = QPoint(0, 0)
        except Exception:
            pass
        try:
            win = getattr(self, "windowHandle", None)
            if callable(win):
                w = win()
            else:
                w = None
            self._sys_drag_available = (w is not None and hasattr(w, "startSystemMove"))
        except Exception:
            self._sys_drag_available = False

    def _drag_try_system(self, event) -> bool:
        """
        函数: _drag_try_system
        作用: 尝试使用系统拖动（若可用）。
        参数:
            event: 鼠标事件。
        返回:
            是否已启动系统拖动。
        """
        try:
            if event.button() != Qt.LeftButton:
                return False
            if not getattr(self, "_sys_drag_available", False):
                return False
            win = self.windowHandle()
            if win is None:
                return False
            try:
                win.startSystemMove()
                return True
            except Exception:
                return False
        except Exception:
            return False

    def _drag_handle_press(self, event) -> None:
        """
        函数: _drag_handle_press
        作用: 左键按下时启动系统拖动或记录偏移进入手工拖动模式。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            if event.button() != Qt.LeftButton:
                return
            if self._drag_try_system(event):
                return
            gpos = event.globalPosition().toPoint()
            try:
                geo = self.frameGeometry()
            except Exception:
                geo = self.geometry()
            self._drag_offset = gpos - geo.topLeft()
            self._dragging = True
        except Exception:
            pass

    def _drag_handle_move(self, event) -> None:
        """
        函数: _drag_handle_move
        作用: 手工拖动模式下根据记录偏移移动窗口位置。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            if getattr(self, "_dragging", False):
                gpos = event.globalPosition().toPoint()
                new_pos = gpos - getattr(self, "_drag_offset", QPoint(0, 0))
                self.move(new_pos)
        except Exception:
            pass

    def _drag_handle_release(self, event) -> None:
        """
        函数: _drag_handle_release
        作用: 鼠标释放后结束手工拖动模式。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            if event.button() == Qt.LeftButton:
                self._dragging = False
        except Exception:
            pass

    def eventFilter(self, obj, event) -> bool:
        try:
            from PySide6.QtCore import QEvent
        except Exception:
            return False
        try:
            et = event.type()
        except Exception:
            return False
        try:
            if et == QEvent.MouseButtonPress:
                try:
                    if event.button() == Qt.LeftButton:
                        try:
                            gpos = event.globalPosition().toPoint()
                        except Exception:
                            gpos = event.globalPos()
                        try:
                            geo = self.frameGeometry()
                        except Exception:
                            geo = self.geometry()
                        self._drag_offset = gpos - geo.topLeft()
                        self._dragging = True
                        try:
                            wh = self.windowHandle()
                            if wh is not None:
                                wh.startSystemMove()
                                return True
                        except Exception:
                            pass
                        try:
                            self.setFocus()
                        except Exception:
                            pass
                except Exception:
                    pass
                return False
            if et == QEvent.MouseMove:
                if getattr(self, "_dragging", False):
                    try:
                        try:
                            gpos = QCursor.pos()
                        except Exception:
                            try:
                                gpos = event.globalPosition().toPoint()
                            except Exception:
                                gpos = event.globalPos()
                        new_pos = gpos - getattr(self, "_drag_offset", QPoint(0, 0))
                        self.move(new_pos)
                        return True
                    except Exception:
                        return False
                return False
            if et == QEvent.MouseButtonRelease:
                try:
                    if event.button() == Qt.LeftButton:
                        self._dragging = False
                except Exception:
                    pass
                return False
        except Exception:
            return False
        return False