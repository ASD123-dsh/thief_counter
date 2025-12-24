# -*- coding: utf-8 -*-
"""
文件: src/ui/normal_panel.py
描述: 普通计算器面板，支持基本算术、历史记录与记忆功能。
"""

from typing import Optional

from PySide6.QtCore import Qt, QSettings, QCoreApplication, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer, QThread, QObject, Signal
from PySide6.QtGui import QTextLayout, QTextOption, QPainter, QPen, QColor, QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QSizePolicy,
    QLabel,
    QPlainTextEdit,
    QFrame,
    QGraphicsOpacityEffect,
    QDialog,
    QFileDialog,
    QSizeGrip,
    QInputDialog,
)
import os
import random
import hashlib
import time

from core.expr_parser import safe_eval
from core.memory_store import MemoryStore


class NormalPanel(QWidget):
    """
    类: NormalPanel
    作用: 提供普通计算器功能界面，包括自适应按钮网格、
         记忆功能（MC/MR/M+/M-）与历史记录列表。
    """

    def __init__(self, memory_store: MemoryStore, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化界面元素与布局，绑定按钮事件。
        参数:
            memory_store: 共享记忆存储实例。
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        self.memory_store = memory_store
        self.setFocusPolicy(Qt.StrongFocus)
        # 摸鱼密钥（输入后点击“=”触发设置按钮显示）
        self._moyu_secret = "666888"
        # 模式状态：是否处于摸鱼模式（用于帮助文案切换）
        self._in_moyu_mode = False

        # 显示与历史区域
        self.display = QLineEdit()
        self.display.setObjectName("display")
        self.display.setPlaceholderText("请输入表达式，例如: (1+2)*3")
        self.display.setAlignment(Qt.AlignRight)
        self.display.setMinimumHeight(40)

        self.history = QListWidget()
        self.history.setMinimumWidth(200)
        # 历史列表优化：开启自动换行，禁用水平滚动，避免提示被截断
        try:
            self.history.setWordWrap(True)
            self.history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.history.setUniformItemSizes(False)
        except Exception:
            pass

        # 左侧栈：显示 + 网格
        left_box = QWidget()
        left_v = QVBoxLayout(left_box)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)
        left_v.addWidget(self.display)

        grid = QGridLayout()
        grid.setSpacing(8)

        buttons = [
            ["%", "√", "x²", "1/x"],
            ["CE", "C", "Back", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["±", "0", ".", "="]
        ]

        for r, row in enumerate(buttons):
            for c, text in enumerate(row):
                btn = QPushButton(text)
                btn.setMinimumHeight(40)
                btn.clicked.connect(lambda checked=False, t=text: self.on_button_clicked(t))
                grid.addWidget(btn, r, c)

        left_v.addLayout(grid)

        # 页码标签：放置在红框区域内（容器中），默认隐藏
        self.moyu_page_label = QLabel("")
        self.moyu_page_label.setVisible(False)
        try:
            self.moyu_page_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.moyu_page_label.setObjectName("moyuPageLabel")
            self.moyu_page_label.setStyleSheet("color: #9aa0a6;")
            self.moyu_page_label.installEventFilter(self)
        except Exception:
            pass

        # 摸鱼区域：隐藏设置按钮 + 路径输入框 + 文本展示
        self.moyu_settings_btn = QPushButton("设置")
        self.moyu_settings_btn.setToolTip("摸鱼设置：指定TXT目录")
        self.moyu_settings_btn.setVisible(False)
        self.moyu_settings_btn.clicked.connect(self._on_moyu_settings_clicked)

        self.moyu_path_edit = QLineEdit()
        self.moyu_path_edit.setPlaceholderText("请输入TXT文件夹路径，例如: D:/docs 或 C:/notes")
        self.moyu_path_edit.setVisible(False)
        self.moyu_path_edit.returnPressed.connect(self._load_moyu_texts_from_path)

        ctrl_row = QHBoxLayout()
        ctrl_row.setContentsMargins(0, 0, 0, 0)
        ctrl_row.setSpacing(8)
        ctrl_row.addWidget(self.moyu_settings_btn, 0)
        ctrl_row.addWidget(self.moyu_path_edit, 1)
        left_v.addLayout(ctrl_row)

        

        self.moyu_view = QPlainTextEdit()
        self.moyu_view.setReadOnly(True)
        try:
            f = self.moyu_view.font()
            f.setPointSize(13)
            self.moyu_view.setFont(f)
        except Exception:
            pass
        # 由外部容器固定高度，文本视图自适应填充
        self.moyu_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 无痕显示：去边框、去滚动条、按控件宽度换行
        try:
            self.moyu_view.setFrameStyle(QFrame.NoFrame)
            self.moyu_view.setStyleSheet("border: none; font-size: 13pt;")
            self.moyu_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.moyu_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.moyu_view.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            # 文档边距适当收紧，避免底部出现被裁剪的半行
            try:
                self.moyu_view.document().setDocumentMargin(2)
            except Exception:
                pass
            # 通过事件过滤器实现滚轮/方向键翻页
            self.moyu_view.installEventFilter(self)
        except Exception:
            pass
        self.moyu_view.setVisible(False)
        # 固定三行显示：根据当前字体行距设置文本视图高度为 3 行
        try:
            line_h = max(1, int(self.moyu_view.fontMetrics().lineSpacing()))
            doc_m = int(self.moyu_view.document().documentMargin()) if hasattr(self.moyu_view, 'document') else 0
            # 预设高度，稍后由 adjust_moyu_box_height 进行统一微调
            self.moyu_view.setFixedHeight(line_h * 3 + doc_m * 2)
        except Exception:
            pass
        # 红框区域容器：固定高度，占位不随显示隐藏变化
        self.moyu_box = QWidget()
        try:
            self.moyu_box.setObjectName("moyuBox")
        except Exception:
            pass
        self.moyu_box.setFixedHeight(96)
        try:
            self.moyu_box.installEventFilter(self)
        except Exception:
            pass
        box_v = QVBoxLayout(self.moyu_box)
        box_v.setContentsMargins(0, 0, 0, 0)
        box_v.setSpacing(2)
        box_v.addWidget(self.moyu_page_label)
        box_v.addWidget(self.moyu_view)
        left_v.addWidget(self.moyu_box)
        # 初始化后统一调整容器高度，确保完整三行不被裁剪
        try:
            self.adjust_moyu_box_height()
        except Exception:
            pass
        # 预填持久化路径但不自动显示
        try:
            settings = QSettings()
            saved = settings.value("moyu_path", "", type=str)
            if saved:
                self.moyu_path_edit.setText(saved)
        except Exception:
            pass

        # 主布局：左侧为计算器，右侧为历史
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addWidget(left_box, 1)
        root.addWidget(self.history, 0)

        # 分页状态
        self._moyu_pages = []  # type: list[str]
        self._moyu_page_index = 0
        # 行缓存与分批加载暂存
        self._moyu_line_cache = {}  # key: (width, font_key, content_hash) -> list[str]
        self._moyu_line_staging = []  # 暂存未满一页的行
        self._moyu_chunk_buffer = ""  # 分批加载时跨块的尾行缓冲
        # 淡入淡出动画资源
        self._moyu_effect = None
        self._moyu_anim = None
        self._moyu_effect_label = None
        self._moyu_anim_label = None
        self._moyu_anim_group = None
        self._wheel_accum = 0
        self._equal_press_count = 0
        self._last_equal_ts = 0.0
        self._minimal_reader = None
        self._moyu_prefetch_cache = {}
        self._moyu_full_text = ""
        self._loader_thread = None
        self._loader_worker = None
        self._dynamic_moyu_height = True
        self._last_moyu_view_h = 0

    def adjust_moyu_box_height(self) -> None:
        """
        函数: adjust_moyu_box_height
        作用: 依据当前字体行距与页码标签高度，统一计算文本视图与容器高度，
              确保红框区域恰好显示三行且不出现“半行”。
        参数:
            无。
        返回:
            无。
        """
        try:
            if getattr(self, "_dynamic_moyu_height", False):
                return
            line_h = max(1, int(self.moyu_view.fontMetrics().lineSpacing()))
            doc_m = int(self.moyu_view.document().documentMargin()) if hasattr(self.moyu_view, 'document') else 0
            # 视口边距（QAbstractScrollArea），不同平台可能非 0
            try:
                vm = self.moyu_view.viewportMargins()
                vp_pad = int(vm.top()) + int(vm.bottom())
            except Exception:
                vp_pad = 0
            # 冗余高度：按行高的 30% 取整，至少 6 像素，解决 2.5 行问题
            fudge = max(6, int(round(line_h * 0.30)))
            view_h = line_h * 3 + doc_m * 2 + vp_pad + fudge
            self.moyu_view.setFixedHeight(view_h)
            label_h = int(self.moyu_page_label.sizeHint().height())
            spacing = 2  # 与 box_v.setSpacing 保持一致
            box_h = view_h + label_h + spacing
            self.moyu_box.setFixedHeight(box_h)
        except Exception:
            pass

    def get_help_text(self) -> str:
        """
        函数: get_help_text
        作用: 返回普通（标准）计算器的使用说明文本（简体中文）。
        参数:
            无。
        返回:
            使用说明字符串。
        """
        return (
            "【概述】\n"
            "- 支持加/减/乘/除与一元操作（百分比、平方根、平方、倒数、±）。\n"
            "- 显示框右对齐输入；支持回车计算与退格。\n"
            "\n"
            "【按键说明】\n"
            "- CE：清空当前输入。C：清空输入（保留历史）。Back：退格。\n"
            "- ÷/×/-/+：插入对应运算符；‘=’计算并写入历史。\n"
            "- %：等价于除以 100；√/x²/1/x/±：直接对当前输入生效。\n"
            "\n"
            "【记忆功能】\n"
            "- MC/MR/M+/M-：清除/读取/累加/累减记忆值（在本面板中以表达式结果为基）。\n"
            "\n"
            "【示例】\n"
            "- 输入：7+8×9 -> 点击‘=’得到结果并记录到历史。\n"
            "- 输入：16 点击‘1/x’ -> 显示 0.0625；点击‘x²’ -> 显示 0.00390625。\n"
        )

    def get_moyu_help_text(self) -> str:
        """
        函数: get_moyu_help_text
        作用: 返回摸鱼模式的操作与快捷键说明（简体中文）。
        参数:
            无。
        返回:
            使用说明字符串。
        """
        return (
            "【概述】\n"
            "- 仅在摸鱼模式下，点击右上角‘?’显示本说明；退出后恢复普通说明。\n"
            "【进入方式】\n"
            "- 在数字键盘区域先输入密钥 666888 并点击‘=’解锁，顶部会显示‘设置’按键。\n"
            "- 快捷键：Ctrl+M（若已保存路径则直接进入并恢复上次观看记录）。快速进入\n"
            "【路径与透明度】\n"
            "- 路径配置：点击‘设置’按钮后，弹出设置对话框后粘贴 TXT 目录并确认；\n"
            "- 透明度设置：在设置对话框中输入 1~100；输入 1 启用透明背景特例，文本固定半透明（0.5），并可在对话框中即时预览。\n"
            "【快速唤出】\n"
            "- 在摸鱼模式下连续点击四次‘=’，快速唤出极简阅读窗口。\n"
            "【分页与浏览】\n"
            "- 鼠标滚轮：向上/向下翻页。\n"
            "- 方向键：↑/← 上一页；↓/→ 下一页。\n"
            "- PageUp/PageDown：上一页/下一页。\n"
            "- W/S：上一页/下一页（摸鱼模式下全局响应）。\n"
            "【极简阅读窗口】\n"
            "- 显示/隐藏：鼠标移入延迟 1.5 秒显示；移出立即隐藏。\n"
            "- 唤醒：仅当鼠标靠近窗口边缘或停留在窗口区域时唤醒；屏幕边缘不触发。\n"
            "- 移动与尺寸：左键拖动任意区域移动；右下角拖动调整尺寸，支持网格吸附与距屏幕边缘自动贴靠。\n"
            "- 外观：字体颜色与背景颜色支持屏幕取色自定义设置\n"
            "- 文本透明度：当透明度设置为 1 时启用透明背景并固定文本半透明 0.9；其他取值按设置显示。\n"
            "【记忆与恢复】\n"
            "- 自动记忆当前页：每次翻页立即保存。\n"
            "- 再次进入时恢复到上次观看页。\n"
            "【退出与伪装】\n"
            "- Esc：退出摸鱼模式，并显示随机数学公式以伪装。\n"
            "- 退出后再次点击‘?’将显示普通计算器说明。\n"
        )

    def is_in_moyu_mode(self) -> bool:
        """
        函数: is_in_moyu_mode
        作用: 返回当前是否处于摸鱼模式（用于主窗口帮助文案切换）。
        参数:
            无。
        返回:
            bool: True 表示处于摸鱼模式；False 表示普通模式。
        """
        return bool(self._in_moyu_mode)

    def set_moyu_mode(self, on: bool) -> None:
        """
        函数: set_moyu_mode
        作用: 设置摸鱼模式标志；主窗口进入/退出时调用，用于帮助文案切换。
        参数:
            on: 是否启用摸鱼模式。
        返回:
            无。
        """
        self._in_moyu_mode = bool(on)
        try:
            self._last_moyu_view_h = int(self.moyu_view.viewport().height())
        except Exception:
            pass

    def resizeEvent(self, event) -> None:
        """
        函数: resizeEvent
        作用: 监测视口高度变化，必要时基于全文重新分页以适配窗口尺寸。
        参数:
            event: 尺寸事件。
        返回:
            无。
        """
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        try:
            if getattr(self, "_in_moyu_mode", False):
                h = int(self.moyu_view.viewport().height())
                if h != self._last_moyu_view_h and self._moyu_full_text:
                    self._last_moyu_view_h = h
                    self._compute_moyu_pages_from_text(self._moyu_full_text)
                    self._show_moyu_page(min(self._moyu_page_index, len(self._moyu_pages) - 1))
        except Exception:
            pass

    def on_button_clicked(self, text: str) -> None:
        """
        函数: on_button_clicked
        作用: 处理按钮点击事件，根据按钮类型执行不同逻辑。
        参数:
            text: 按钮文本。
        返回:
            无。
        """
        if text == "CE":
            # 仅清空当前输入
            self.display.clear()
            return
        if text == "C":
            # 清空输入与不清除历史，保留对比
            self.display.clear()
            return
        if text == "Back":
            self.display.backspace()
            return
        if text == "=":
            self.evaluate_and_record()
            return
        if text in {"%", "√", "x²", "1/x", "±"}:
            self.apply_unary(text)
            return

        # 运算符与数字插入
        to_insert = text
        if text == "×":
            to_insert = "*"
        elif text == "÷":
            to_insert = "/"
        self.display.insert(to_insert)

    def handle_memory(self, op: str) -> None:
        """
        函数: handle_memory
        作用: 执行记忆操作：清除、读取、累加、累减。
        参数:
            op: 记忆操作标识（MC/MR/M+/M-）。
        返回:
            无。
        """
        try:
            current = 0.0
            txt = self.display.text().strip()
            if txt:
                current = safe_eval(txt)
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

    def evaluate_and_record(self) -> None:
        """
        函数: evaluate_and_record
        作用: 安全计算表达式并记录历史（表达式=结果）。
        参数:
            无。
        返回:
            无。
        """
        if self._handle_equal_press_trigger():
            return
        expr = self.display.text().strip()
        if not expr:
            return
        # 摸鱼密钥检测：当输入为指定密钥并点击“=”时，显示设置按钮
        if expr == self._moyu_secret:
            # 通过主窗口在顶部显示“设置”按钮
            try:
                win = self.window()
                if hasattr(win, "reveal_moyu_button"):
                    win.reveal_moyu_button()
            except Exception:
                pass
            self.history.addItem("[提示] 设置已解锁：点击顶部‘设置’按钮配置")
            # 不进行求值，清空输入便于继续操作
            self.display.clear()
            return
        try:
            result = safe_eval(expr)
            self.display.setText(str(result))
            self.history.addItem(f"{expr} = {result}")
        except Exception as e:
            self.history.addItem(f"[错误] {expr} -> {e}")
    def _handle_equal_press_trigger(self) -> bool:
        """
        函数: _handle_equal_press_trigger
        作用: 在摸鱼模式下统计 '=' 连续点击次数；达到四次时开启极简阅读窗口。
        参数:
            无。
        返回:
            bool: True 表示已触发极简阅读并拦截默认求值；False 表示未触发。
        """
        if not self._in_moyu_mode:
            self._equal_press_count = 0
            self._last_equal_ts = 0.0
            return False
        now = time.time()
        if self._last_equal_ts == 0.0 or (now - self._last_equal_ts) <= 2.0:
            self._equal_press_count += 1
        else:
            self._equal_press_count = 1
        self._last_equal_ts = now
        if self._equal_press_count >= 4:
            self._equal_press_count = 0
            self._last_equal_ts = 0.0
            self._open_minimal_reader()
            return True
        return False
    def _open_minimal_reader(self) -> None:
        """
        函数: _open_minimal_reader
        作用: 打开极简阅读窗口，用于以更简洁的界面浏览当前 TXT 分页内容。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not self._moyu_pages:
                return
            # 若已存在极简窗口，置顶并激活即可
            try:
                if self._minimal_reader is not None and hasattr(self._minimal_reader, 'isVisible') and self._minimal_reader.isVisible():
                    try:
                        self._minimal_reader.raise_()
                        self._minimal_reader.activateWindow()
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            # 创建独立顶层窗口（无父级），避免随主窗口最小化
            dlg = _MinimalReaderDialog(None, self._moyu_pages, int(self._moyu_page_index))
            dlg.on_page_changed = lambda idx: self._on_minimal_page_changed(idx)
            dlg.setWindowTitle("mini")
            dlg.resize(700, 100)
            try:
                dlg.setWindowFlag(Qt.Tool, True)
            except Exception:
                pass
            try:
                dlg.setModal(False)
            except Exception:
                pass
            try:
                # 极简窗口默认置顶
                dlg.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            except Exception:
                pass
            try:
                # 若主窗口当前置顶，则取消主窗口置顶，避免与极简窗口冲突
                win = self.window()
                if hasattr(win, "pin_on_top") and bool(getattr(win, "pin_on_top")):
                    if hasattr(win, "_apply_pin"):
                        win._apply_pin(False)
            except Exception:
                pass
            try:
                dlg.setWindowFlag(Qt.WindowTransparentForInput, False)
            except Exception:
                pass
            try:
                dlg.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            except Exception:
                pass
            try:
                if hasattr(dlg, "_view") and dlg._view is not None and hasattr(dlg._view, "viewport"):
                    dlg._view.viewport().setAttribute(Qt.WA_TransparentForMouseEvents, False)
            except Exception:
                pass
            try:
                dlg.setFocusPolicy(Qt.StrongFocus)
            except Exception:
                pass
            try:
                settings = QSettings()
                percent = int(settings.value("minimal_opacity_percent", 100, type=int))
                percent = max(1, min(100, percent))
                self._apply_minimal_opacity(dlg, percent)
            except Exception:
                pass
            try:
                theme = self._get_saved_minimal_theme()
                self._apply_minimal_theme(dlg, theme)
            except Exception:
                pass
            try:
                dlg.destroyed.connect(lambda *_: setattr(self, "_minimal_reader", None))
            except Exception:
                pass
            self._minimal_reader = dlg
            dlg.show()
            try:
                dlg.raise_()
                dlg.activateWindow()
            except Exception:
                pass
        except Exception:
            pass

    def set_minimal_reader_opacity(self, percent: int) -> None:
        """
        函数: set_minimal_reader_opacity
        作用: 设置极简阅读窗口透明度（1~100），立即应用并持久化。
        参数:
            percent: 透明度百分比，范围 1~100。
        返回:
            无。
        """
        try:
            p = int(percent)
        except Exception:
            p = 100
        p = max(1, min(100, p))
        try:
            settings = QSettings()
            settings.setValue("minimal_opacity_percent", int(p))
        except Exception:
            pass
    def set_minimal_reader_hover_delay(self, delay_ms: int) -> None:
        """
        函数: set_minimal_reader_hover_delay
        作用: 设置极简窗口鼠标移入显示的延迟时间（毫秒），立即应用并持久化。
        参数:
            delay_ms: 延迟毫秒数，范围 0~10000。
        返回:
            无。
        """
        try:
            d = int(delay_ms)
        except Exception:
            d = 1500
        d = max(0, min(10000, d))
        try:
            settings = QSettings()
            settings.setValue("minimal_hover_delay_ms", int(d))
        except Exception:
            pass
        try:
            dlg = getattr(self, "_minimal_reader", None)
            if dlg is not None and hasattr(dlg, "_hover_show_delay_timer") and dlg._hover_show_delay_timer is not None:
                try:
                    dlg._hover_delay_ms = int(d)
                except Exception:
                    pass
                dlg._hover_show_delay_timer.setInterval(int(d))
        except Exception:
            pass
    def preview_minimal_reader_hover_delay(self, delay_ms: int) -> None:
        """
        函数: preview_minimal_reader_hover_delay
        作用: 仅预览设置延迟（不持久化），若窗口未打开则忽略。
        参数:
            delay_ms: 延迟毫秒数。
        返回:
            无。
        """
        try:
            d = max(0, min(10000, int(delay_ms)))
        except Exception:
            d = 1500
        try:
            dlg = getattr(self, "_minimal_reader", None)
            if dlg is not None and hasattr(dlg, "_hover_show_delay_timer") and dlg._hover_show_delay_timer is not None:
                try:
                    dlg._hover_delay_ms = int(d)
                except Exception:
                    pass
                dlg._hover_show_delay_timer.setInterval(int(d))
        except Exception:
            pass
    def set_minimal_reader_theme(self, theme: dict, persist: bool = True) -> None:
        """
        函数: set_minimal_reader_theme
        作用: 应用极简窗口配色方案；可选择是否持久化。
        参数:
            theme: 包含 bg/fg/accent 的字典。
            persist: True 表示保存到 QSettings；False 仅预览。
        返回:
            无。
        """
        try:
            dlg = getattr(self, "_minimal_reader", None)
            if dlg is not None:
                self._apply_minimal_theme(dlg, theme)
            if persist:
                try:
                    settings = QSettings()
                    settings.setValue("minimal_theme_bg", str(theme.get("bg", "")))
                    settings.setValue("minimal_theme_fg", str(theme.get("fg", "")))
                    settings.setValue("minimal_theme_accent", str(theme.get("accent", "")))
                    settings.setValue("minimal_theme_name", str(theme.get("name", "")))
                except Exception:
                    pass
        except Exception:
            pass
    def preview_minimal_reader_theme(self, theme: dict) -> None:
        """
        函数: preview_minimal_reader_theme
        作用: 仅预览极简窗口配色（不持久化），若窗口未打开则忽略。
        参数:
            theme: 包含 bg/fg/accent 的字典。
        返回:
            无。
        """
        try:
            dlg = getattr(self, "_minimal_reader", None)
            if dlg is not None:
                self._apply_minimal_theme(dlg, theme)
        except Exception:
            pass
    def _apply_minimal_opacity(self, dlg: QDialog, percent: int) -> None:
        """
        函数: _apply_minimal_opacity
        作用: 应用极简窗口透明度；当为 0 时，背景透明且文本以 50% 透明度显示，保留交互。
        参数:
            dlg: 极简阅读窗口。
            percent: 透明度 0~100。
        返回:
            无。
        """
        try:
            p = max(1, min(100, int(percent)))
        except Exception:
            p = 100
        if p == 1:
            try:
                dlg.setAttribute(Qt.WA_TranslucentBackground, True)
            except Exception:
                pass
            try:
                dlg.setStyleSheet("background: transparent;")
            except Exception:
                pass
            try:
                if hasattr(dlg, "_view") and dlg._view is not None:
                    dlg._view.setStyleSheet("background: transparent; border: none; font-size: 13pt;")
                    eff = QGraphicsOpacityEffect(dlg._view.viewport())
                    eff.setOpacity(0.9)
                    dlg._view.viewport().setGraphicsEffect(eff)
                    dlg._text_effect = eff
                    try:
                        dlg._view.setTextInteractionFlags(Qt.NoTextInteraction)
                        dlg._view.viewport().setCursor(Qt.ArrowCursor)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                dlg.setWindowOpacity(1.0)
            except Exception:
                pass
            try:
                dlg._show_border = True
            except Exception:
                pass
            try:
                if hasattr(dlg, "_size_grip") and dlg._size_grip is not None:
                    dlg._size_grip.setStyleSheet("QSizeGrip{background: transparent; border: 0px;}")
                    try:
                        dlg._size_grip.setFixedSize(12, 12)
                    except Exception:
                        pass
            except Exception:
                pass
            return
        try:
            bg = None
            try:
                bg = getattr(dlg, "_theme_bg", None)
            except Exception:
                bg = None
            if not bg:
                try:
                    settings = QSettings()
                    bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
                except Exception:
                    bg = "#F5F5F7"
            dlg.setAttribute(Qt.WA_TranslucentBackground, False)
            dlg.setStyleSheet(f"background: {bg}; border: none;")
        except Exception:
            pass
        try:
            if hasattr(dlg, "_view") and dlg._view is not None:
                dlg._view.setStyleSheet("")
                eff = dlg._view.viewport().graphicsEffect()
                if not eff:
                    eff = QGraphicsOpacityEffect(dlg._view.viewport())
                    dlg._view.viewport().setGraphicsEffect(eff)
                try:
                    eff.setOpacity(0.5)
                    dlg._text_effect = eff
                except Exception:
                    pass
                try:
                    dlg._view.setTextInteractionFlags(Qt.NoTextInteraction)
                    dlg._view.viewport().setCursor(Qt.ArrowCursor)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            dlg.setWindowOpacity(p / 100.0)
        except Exception:
            pass
        try:
            dlg._show_border = False
        except Exception:
            pass
        try:
            if hasattr(dlg, "_size_grip") and dlg._size_grip is not None:
                try:
                    bg = getattr(dlg, "_theme_bg", None)
                except Exception:
                    bg = None
                if not bg:
                    try:
                        settings = QSettings()
                        bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
                    except Exception:
                        bg = "#F5F5F7"
                dlg._size_grip.setStyleSheet(f"QSizeGrip{{background: {bg}; border: 0px;}}")
        except Exception:
            pass
    def _get_saved_minimal_theme(self) -> dict:
        """
        函数: _get_saved_minimal_theme
        作用: 从 QSettings 读取已保存的极简窗口配色方案；若无则返回默认方案。
        参数:
            无。
        返回:
            dict: {bg, fg, accent, name}
        """
        try:
            settings = QSettings()
            bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
            fg = str(settings.value("minimal_theme_fg", "#1E1E1E", type=str))
            ac = str(settings.value("minimal_theme_accent", "#3B82F6", type=str))
            name = str(settings.value("minimal_theme_name", "白天默认", type=str))
            return {"bg": bg, "fg": fg, "accent": ac, "name": name}
        except Exception:
            return {"bg": "#F5F5F7", "fg": "#1E1E1E", "accent": "#3B82F6", "name": "白天默认"}
    def _apply_minimal_theme(self, dlg: QDialog, theme: dict) -> None:
        """
        函数: _apply_minimal_theme
        作用: 将配色方案应用到极简窗口文本视图与边框选中效果。
        参数:
            dlg: 极简窗口实例。
            theme: 包含 bg/fg/accent 的字典。
        返回:
            无。
        """
        try:
            if dlg is None or not hasattr(dlg, "_view") or dlg._view is None:
                return
            bg = str(theme.get("bg", "#F5F5F7"))
            fg = str(theme.get("fg", "#1E1E1E"))
            ac = str(theme.get("accent", "#3B82F6"))
            try:
                dlg._theme_bg = bg
            except Exception:
                pass
            settings = QSettings()
            percent = int(settings.value("minimal_opacity_percent", 100, type=int))
            percent = 1 if percent < 1 else (100 if percent > 100 else percent)
            if percent == 1:
                dlg._view.setStyleSheet(
                    f"QPlainTextEdit{{color:{fg}; background: transparent; border: none; font-size: 14pt; selection-background-color:{ac}; selection-color:{fg};}}"
                )
                try:
                    dlg.setAttribute(Qt.WA_TranslucentBackground, True)
                    dlg.setStyleSheet("background: transparent; border: none;")
                except Exception:
                    pass
                try:
                    if hasattr(dlg, "_size_grip") and dlg._size_grip is not None:
                        dlg._size_grip.setStyleSheet("QSizeGrip{background: transparent; border: 0px;}")
                        dlg._size_grip.setFixedSize(12, 12)
                except Exception:
                    pass
            else:
                dlg._view.setStyleSheet(
                    f"QPlainTextEdit{{color:{fg}; background:{bg}; border: none; font-size: 13pt; selection-background-color:{ac}; selection-color:{fg};}}"
                )
                try:
                    dlg.setAttribute(Qt.WA_TranslucentBackground, False)
                    dlg.setStyleSheet(f"background: {bg}; border: none;")
                except Exception:
                    pass
                try:
                    if hasattr(dlg, "_size_grip") and dlg._size_grip is not None:
                        dlg._size_grip.setStyleSheet(f"QSizeGrip{{background: {bg}; border: 0px;}}")
                        dlg._size_grip.setFixedSize(12, 12)
                except Exception:
                    pass
        except Exception:
            pass
    def _on_minimal_page_changed(self, idx: int) -> None:
        """
        函数: _on_minimal_page_changed
        作用: 当极简阅读窗口翻页时，同步主面板当前页并持久化。
        参数:
            idx: 新页索引。
        返回:
            无。
        """
        try:
            self._show_moyu_page(int(idx))
        except Exception:
            pass

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
        # 摸鱼模式全局翻页快捷键：W/S
        try:
            if self._in_moyu_mode and self.moyu_view.isVisible():
                if key in (Qt.Key_W, Qt.Key_PageUp, Qt.Key_Up, Qt.Key_Left):
                    self._show_moyu_page(self._moyu_page_index - 1)
                    return
                if key in (Qt.Key_S, Qt.Key_PageDown, Qt.Key_Down, Qt.Key_Right):
                    self._show_moyu_page(self._moyu_page_index + 1)
                    return
        except Exception:
            pass
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

    def mouseDoubleClickEvent(self, event) -> None:
        """
        函数: mouseDoubleClickEvent
        作用: 标准界面双击不触发页码跳转；仅在页码标签区域双击时由事件过滤器触发。
        参数:
            event: 鼠标双击事件。
        返回:
            无。
        """
        try:
            super().mouseDoubleClickEvent(event)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """
        函数: eventFilter
        作用: 拦截文本框的滚轮与方向键事件，实现分页翻页，无滚动条。
        参数:
            obj: 事件对象。
            event: 事件本体。
        返回:
            bool: 是否已处理事件。
        """
        try:
            # 摸鱼容器的移入/移出：在摸鱼模式下对文本区域进行淡入淡出
            if obj is self.moyu_box:
                et = event.type()
                if self._in_moyu_mode:
                    if et == event.Type.Enter:
                        self._fade_show_moyu_view()
                        return False
                    if et == event.Type.Leave:
                        self._fade_hide_moyu_view()
                        return False
            # 页码标签双击跳转
            if obj is getattr(self, "moyu_page_label", None):
                et = event.type()
                if et == event.Type.MouseButtonDblClick:
                    try:
                        if getattr(self, "_in_moyu_mode", False) and self._moyu_pages:
                            self._prompt_moyu_page_jump()
                            return True
                    except Exception:
                        pass
            # 仅处理摸鱼文本视图的事件
            # 仅处理摸鱼文本视图的事件
            if obj is self.moyu_view and self.moyu_view.isVisible():
                et = event.type()
                if et == event.Type.Wheel:
                    try:
                        delta = int(event.angleDelta().y())
                    except Exception:
                        delta = 0
                    if delta == 0:
                        try:
                            delta = int(getattr(event.pixelDelta(), 'y', lambda: 0)())
                        except Exception:
                            delta = 0
                    self._wheel_accum += delta
                    step = 120
                    moved = False
                    while self._wheel_accum >= step:
                        self._show_moyu_page(self._moyu_page_index - 1)
                        self._wheel_accum -= step
                        moved = True
                    while self._wheel_accum <= -step:
                        self._show_moyu_page(self._moyu_page_index + 1)
                        self._wheel_accum += step
                        moved = True
                    if moved:
                        return True
                    return True
                if et == event.Type.KeyPress:
                    key = event.key()
                    if key in (Qt.Key_PageUp, Qt.Key_Up, Qt.Key_Left, Qt.Key_W):
                        self._show_moyu_page(self._moyu_page_index - 1)
                        return True
                    if key in (Qt.Key_PageDown, Qt.Key_Down, Qt.Key_Right, Qt.Key_S):
                        self._show_moyu_page(self._moyu_page_index + 1)
                        return True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _prompt_moyu_page_jump(self) -> None:
        """
        函数: _prompt_moyu_page_jump
        作用: 弹出页码输入框，允许用户输入目标页码并跳转。
        参数:
            无。
        返回:
            无。
        """
        try:
            total = len(self._moyu_pages) if self._moyu_pages else 0
            if total <= 0:
                return
            current = int(self._moyu_page_index) + 1
            val, ok = QInputDialog.getInt(self, "跳转页码", f"请输入目标页码 (1~{total})", current, 1, total, 1)
            if ok:
                self._show_moyu_page(int(val) - 1)
        except Exception:
            pass

    def _setup_moyu_fade(self) -> None:
        """
        函数: _setup_moyu_fade
        作用: 初始化摸鱼文本视图的透明度特效与动画资源。
        参数:
            无。
        返回:
            无。
        """
        try:
            if self._moyu_effect is None:
                self._moyu_effect = QGraphicsOpacityEffect(self.moyu_view)
                self.moyu_view.setGraphicsEffect(self._moyu_effect)
                self._moyu_effect.setOpacity(0.0 if not self.moyu_view.isVisible() else 1.0)
            if self._moyu_anim is None:
                self._moyu_anim = QPropertyAnimation(self._moyu_effect, b"opacity", self)
                self._moyu_anim.setDuration(220)
                try:
                    self._moyu_anim.setEasingCurve(QEasingCurve.InOutQuad)
                except Exception:
                    pass
            if self._moyu_effect_label is None:
                self._moyu_effect_label = QGraphicsOpacityEffect(self.moyu_page_label)
                self.moyu_page_label.setGraphicsEffect(self._moyu_effect_label)
                self._moyu_effect_label.setOpacity(0.0 if not self.moyu_page_label.isVisible() else 1.0)
            if self._moyu_anim_label is None:
                self._moyu_anim_label = QPropertyAnimation(self._moyu_effect_label, b"opacity", self)
                self._moyu_anim_label.setDuration(220)
                try:
                    self._moyu_anim_label.setEasingCurve(QEasingCurve.InOutQuad)
                except Exception:
                    pass
        except Exception:
            pass

    def _fade_show_moyu_view(self) -> None:
        """
        函数: _fade_show_moyu_view
        作用: 在摸鱼模式下以淡入动画显示文本视图；若无分页则保持隐藏。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not self._in_moyu_mode:
                return
            if not self._moyu_pages:
                return
            self._setup_moyu_fade()
            # 可见并从当前透明度淡入到 1.0
            self.moyu_view.setVisible(True)
            try:
                self._update_moyu_page_label()
                self.moyu_page_label.setVisible(True)
            except Exception:
                pass
            start = 0.0
            try:
                start = float(self._moyu_effect.opacity())
            except Exception:
                start = 0.0
            try:
                self._moyu_anim.stop()
            except Exception:
                pass
            try:
                self._moyu_anim.setStartValue(start)
                self._moyu_anim.setEndValue(1.0)
                self._moyu_anim.start()
            except Exception:
                # 无动画回退：直接显示
                self.moyu_view.setVisible(True)
            # 页码标签淡入
            try:
                lbl_start = 0.0
                try:
                    lbl_start = float(self._moyu_effect_label.opacity())
                except Exception:
                    lbl_start = 0.0
                self._moyu_anim_label.stop()
                self._moyu_anim_label.setStartValue(lbl_start)
                self._moyu_anim_label.setEndValue(1.0)
                self._moyu_anim_label.start()
            except Exception:
                try:
                    self.moyu_page_label.setVisible(True)
                except Exception:
                    pass
        except Exception:
            pass

    def _fade_hide_moyu_view(self) -> None:
        """
        函数: _fade_hide_moyu_view
        作用: 在摸鱼模式下以淡出动画隐藏文本视图；动画结束后设置不可见。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not self._in_moyu_mode:
                return
            self._setup_moyu_fade()
            start = 1.0
            try:
                start = float(self._moyu_effect.opacity())
            except Exception:
                start = 1.0
            lbl_start = 1.0
            try:
                lbl_start = float(self._moyu_effect_label.opacity())
            except Exception:
                lbl_start = 1.0
            try:
                self._moyu_anim.stop()
            except Exception:
                pass
            try:
                self._moyu_anim_label.stop()
            except Exception:
                pass
            try:
                self._moyu_anim.setStartValue(start)
                self._moyu_anim.setEndValue(0.0)
                self._moyu_anim_label.setStartValue(lbl_start)
                self._moyu_anim_label.setEndValue(0.0)
                # 并行动画：两个透明度同时变化
                self._moyu_anim_group = QParallelAnimationGroup(self)
                self._moyu_anim_group.addAnimation(self._moyu_anim)
                self._moyu_anim_group.addAnimation(self._moyu_anim_label)
                try:
                    # 先断开旧连接，避免重复调用
                    self._moyu_anim_group.finished.disconnect()
                except Exception:
                    pass
                self._moyu_anim_group.finished.connect(self._on_moyu_fade_out_finished)
                self._moyu_anim_group.start()
            except Exception:
                # 无动画回退：直接隐藏
                try:
                    self.moyu_view.setVisible(False)
                    self.moyu_page_label.setVisible(False)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_moyu_fade_out_finished(self) -> None:
        """
        函数: _on_moyu_fade_out_finished
        作用: 淡出动画结束回调，将文本视图设置为不可见以阻止事件。
        参数:
            无。
        返回:
            无。
        """
        try:
            # 动画结束时若透明度为 0 则隐藏
            op = 1.0
            try:
                op = float(self._moyu_effect.opacity())
            except Exception:
                op = 0.0
            if op <= 0.001:
                self.moyu_view.setVisible(False)
            lbl_op = 1.0
            try:
                lbl_op = float(self._moyu_effect_label.opacity())
            except Exception:
                lbl_op = 0.0
            if lbl_op <= 0.001:
                self.moyu_page_label.setVisible(False)
        except Exception:
            pass
    def apply_unary(self, op: str) -> None:
        """
        函数: apply_unary
        作用: 标准模式的一元操作，包括百分比、平方根、平方、倒数与正负号。
        参数:
            op: 操作标识（%/√/x²/1/x/±）。
        返回:
            无。
        """
        try:
            txt = self.display.text().strip()
            val = 0.0
            if txt:
                val = safe_eval(txt)
            if op == "%":
                result = val / 100.0
            elif op == "√":
                result = safe_eval(f"sqrt({val})", functions={"sqrt": __import__("math").sqrt})
            elif op == "x²":
                result = val * val
            elif op == "1/x":
                if val == 0:
                    raise ValueError("除零错误")
                result = 1.0 / val
            elif op == "±":
                # 直接切换输入的符号
                if txt.startswith("-"):
                    self.display.setText(txt[1:])
                else:
                    self.display.setText("-" + txt)
                return
            else:
                return
            self.display.setText(str(result))
            self.history.addItem(f"{op} -> {result}")
        except Exception as e:
            self.history.addItem(f"[错误] 一元操作: {e}")

    def _on_moyu_settings_clicked(self) -> None:
        """
        函数: _on_moyu_settings_clicked
        作用: 显示或切换摸鱼路径输入框，用于粘贴TXT目录路径。
        参数:
            无。
        返回:
            无。
        """
        # 显示路径框并聚焦
        self.moyu_path_edit.setVisible(True)
        self.moyu_path_edit.setFocus()

    def load_moyu_texts_from_path(self, path: str) -> None:
        """
        函数: load_moyu_texts_from_path
        作用: 根据传入目录路径，提供 .txt 文件选择器；若仅一个文件则直接加载，
              若存在多个文件则弹出选择器并仅加载所选文件；成功后隐藏本面板路径框（若可见）。
        参数:
            path: 目录路径字符串。
        返回:
            无。
        """
        if not path:
            self.history.addItem("[提示] 请输入TXT目录路径")
            return
        if not os.path.isdir(path):
            self.history.addItem(f"[错误] 非有效目录: {path}")
            return
        files = []
        try:
            files = [f for f in os.listdir(path) if f.lower().endswith('.txt')]
        except Exception as e:
            self.history.addItem(f"[错误] 读取目录失败: {e}")
            return
        if not files:
            self.history.addItem("[提示] 目录下未找到 .txt 文件")
            self.moyu_view.clear()
            self.moyu_view.setVisible(False)
            return
        files.sort()
        selected_mode = False
        selected_name = None
        try:
            force = getattr(self, "_moyu_force_file", None)
            if force and force in files:
                files = [str(force)]
                selected_name = str(force)
                selected_mode = True
        except Exception:
            pass
        try:
            setattr(self, "_moyu_force_file", None)
        except Exception:
            pass
        try:
            if len(files) > 1:
                fp, _ = QFileDialog.getOpenFileName(self, "选择TXT文件", path, "Text Files (*.txt)")
                if not fp:
                    self.history.addItem("[提示] 已取消选择")
                    return
                try:
                    base = os.path.basename(fp)
                except Exception:
                    base = fp
                if base not in files:
                    self.history.addItem("[错误] 请选择当前目录内的 .txt 文件")
                    return
                files = [base]
                selected_name = base
                selected_mode = True
        except Exception:
            pass
        # 提示加载进行中，避免用户误以为无响应
        try:
            self.history.addItem("正在加载...")
        except Exception:
            pass
        # 初始化分页会话（行暂存与页面清空）
        self._moyu_pages = []
        self._moyu_line_staging = []
        self._moyu_line_cache.clear()
        self._moyu_chunk_buffer = ""
        # 计算内容宽度
        width = self._get_moyu_content_width()
        # 改为异步读取：将文件读取放入线程，主线程分页与渲染
        try:
            if self._loader_thread is not None:
                try:
                    self._loader_thread.quit()
                    self._loader_thread.wait()
                except Exception:
                    pass
            class _Worker(QObject):
                textChunk = Signal(str)
                headerChunk = Signal(str)
                fileEnded = Signal()
                finished = Signal()
                error = Signal(str)
                def __init__(self, base_path: str, names: list, emit_header: bool) -> None:
                    super().__init__()
                    self.base_path = base_path
                    self.names = names
                    self.emit_header = bool(emit_header)
                def run(self) -> None:
                    try:
                        for name in self.names:
                            fp = os.path.join(self.base_path, name)
                            if self.emit_header:
                                self.headerChunk.emit(f"===== {name} =====\n")
                            opened = False
                            last_err = None
                            for enc, opts in (("utf-8", {}), ("gbk", {"errors": "ignore"})):
                                try:
                                    with open(fp, 'r', encoding=enc, **opts) as f:
                                        opened = True
                                        while True:
                                            chunk = f.read(64 * 1024)
                                            if not chunk:
                                                break
                                            self.textChunk.emit(chunk)
                                except Exception as e:
                                    opened = False
                                    last_err = e
                                    continue
                                if opened:
                                    break
                            if not opened and last_err is not None:
                                self.error.emit(f"读取失败: {name} -> {last_err}")
                            self.fileEnded.emit()
                        self.finished.emit()
                    except Exception as e:
                        self.error.emit(str(e))
                        self.finished.emit()
            self._loader_thread = QThread(self)
            self._loader_worker = _Worker(path, files, emit_header=not selected_mode and len(files) > 1)
            self._loader_worker.moveToThread(self._loader_thread)
            self._loader_thread.started.connect(self._loader_worker.run)
            def on_header(s: str) -> None:
                try:
                    header_lines = self._wrap_text_to_lines_doc(s, width)
                except Exception:
                    header_lines = [s.strip()] if s.strip() else []
                self._append_lines_to_pages(header_lines)
                try:
                    self._moyu_full_text += s
                except Exception:
                    pass
                try:
                    QCoreApplication.processEvents()
                except Exception:
                    pass
            def on_chunk(s: str) -> None:
                combined = self._moyu_chunk_buffer + s
                parts = combined.splitlines(True)
                if parts:
                    if not (parts[-1].endswith("\n") or parts[-1].endswith("\r")):
                        self._moyu_chunk_buffer = parts[-1]
                        commit_text = "".join(parts[:-1])
                    else:
                        self._moyu_chunk_buffer = ""
                        commit_text = "".join(parts)
                else:
                    commit_text = combined
                    self._moyu_chunk_buffer = ""
                if commit_text:
                    try:
                        lines = self._wrap_text_to_lines_doc(commit_text, width)
                    except Exception:
                        lines = commit_text.splitlines()
                    self._append_lines_to_pages(lines)
                    try:
                        self._moyu_full_text += commit_text
                    except Exception:
                        pass
                try:
                    QCoreApplication.processEvents()
                except Exception:
                    pass
            def on_file_end() -> None:
                try:
                    if self._moyu_chunk_buffer:
                        tail_lines = self._wrap_text_to_lines_doc(self._moyu_chunk_buffer, width)
                        self._append_lines_to_pages(tail_lines)
                        try:
                            self._moyu_full_text += self._moyu_chunk_buffer
                        except Exception:
                            pass
                        self._moyu_chunk_buffer = ""
                except Exception:
                    pass
                self._append_lines_to_pages([""])
            def on_finished() -> None:
                self._finalize_pages_from_staging()
                try:
                    restore_idx = self._restore_moyu_page()
                    self._show_moyu_page(restore_idx)
                    self.set_moyu_mode(True)
                except Exception:
                    try:
                        self.moyu_view.setPlainText(self._moyu_pages[0] if self._moyu_pages else "")
                        self.moyu_view.setVisible(True)
                        self.moyu_page_label.setVisible(True)
                        self.set_moyu_mode(True)
                    except Exception:
                        pass
                self.history.addItem("已加载")
                try:
                    settings = QSettings()
                    settings.setValue("moyu_path", path)
                    if selected_name:
                        settings.setValue("moyu_last_file", selected_name)
                except Exception:
                    pass
                try:
                    if self.moyu_path_edit.isVisible():
                        self.moyu_path_edit.setVisible(False)
                except Exception:
                    pass
                try:
                    self._loader_thread.quit()
                except Exception:
                    pass
            def on_error(msg: str) -> None:
                try:
                    self.history.addItem(f"[警告] {msg}")
                except Exception:
                    pass
            self._loader_worker.headerChunk.connect(on_header)
            self._loader_worker.textChunk.connect(on_chunk)
            self._loader_worker.fileEnded.connect(on_file_end)
            self._loader_worker.finished.connect(on_finished)
            self._loader_worker.error.connect(on_error)
            self._loader_thread.start()
        except Exception as e:
            self.history.addItem(f"[错误] 启动异步加载失败: {e}")
            # 回退到同步模式（原有逻辑）
            for name in files:
                fp = os.path.join(path, name)
                if not selected_mode and len(files) > 1:
                    header = f"===== {name} =====\n"
                    try:
                        header_lines = self._wrap_text_to_lines_doc(header, width)
                    except Exception:
                        header_lines = [header.strip()] if header.strip() else []
                    self._append_lines_to_pages(header_lines)
                opened = False
                for enc in (('utf-8', {}), ('gbk', {'errors': 'ignore'})):
                    try:
                        with open(fp, 'r', encoding=enc[0], **enc[1]) as f:
                            opened = True
                            while True:
                                chunk = f.read(64 * 1024)
                                if not chunk:
                                    break
                                combined = self._moyu_chunk_buffer + chunk
                                parts = combined.splitlines(True)
                                if parts:
                                    if not (parts[-1].endswith("\n") or parts[-1].endswith("\r")):
                                        self._moyu_chunk_buffer = parts[-1]
                                        commit_text = "".join(parts[:-1])
                                    else:
                                        self._moyu_chunk_buffer = ""
                                        commit_text = "".join(parts)
                                else:
                                    commit_text = combined
                                    self._moyu_chunk_buffer = ""
                                if commit_text:
                                    lines = self._wrap_text_to_lines_doc(commit_text, width)
                                    self._append_lines_to_pages(lines)
                                    try:
                                        QCoreApplication.processEvents()
                                    except Exception:
                                        pass
                            if self._moyu_chunk_buffer:
                                tail_lines = self._wrap_text_to_lines_doc(self._moyu_chunk_buffer, width)
                                self._append_lines_to_pages(tail_lines)
                                self._moyu_chunk_buffer = ""
                    except Exception:
                        opened = False
                        continue
                if not opened:
                    self.history.addItem(f"[警告] 读取失败: {name}")
                self._append_lines_to_pages([""])
            self._finalize_pages_from_staging()
            try:
                restore_idx = self._restore_moyu_page()
                self._show_moyu_page(restore_idx)
                self.set_moyu_mode(True)
            except Exception:
                pass
            fp = os.path.join(path, name)
            # 文件标题（作为分隔），按宽度换行后加入（仅多文件时）
            if not selected_mode and len(files) > 1:
                header = f"===== {name} =====\n"
                try:
                    header_lines = self._wrap_text_to_lines(header, width)
                except Exception:
                    header_lines = [header.strip()] if header.strip() else []
                self._append_lines_to_pages(header_lines)
            # 尝试 UTF-8，失败再退回到 GBK/ANSI
            opened = False
            for enc in (('utf-8', {}), ('gbk', {'errors': 'ignore'})):
                try:
                    with open(fp, 'r', encoding=enc[0], **enc[1]) as f:
                        opened = True
                        # 每次读取约 64KB 文本，按行缓冲处理；减小块大小以保持界面响应
                        while True:
                            chunk = f.read(64 * 1024)
                            if not chunk:
                                break
                            # 合并跨块尾行并切分
                            combined = self._moyu_chunk_buffer + chunk
                            parts = combined.splitlines(True)
                            if parts:
                                # 如果最后一段不是以换行结束，则保留为尾行缓冲
                                if not (parts[-1].endswith("\n") or parts[-1].endswith("\r")):
                                    self._moyu_chunk_buffer = parts[-1]
                                    commit_text = "".join(parts[:-1])
                                else:
                                    self._moyu_chunk_buffer = ""
                                    commit_text = "".join(parts)
                            else:
                                commit_text = combined
                                self._moyu_chunk_buffer = ""
                            if commit_text:
                                lines = self._wrap_text_to_lines(commit_text, width)
                                self._append_lines_to_pages(lines)
                                # 主动让出事件循环，避免“未响应”
                                try:
                                    QCoreApplication.processEvents()
                                except Exception:
                                    pass
                        # 文件末尾：提交尾行缓冲
                        if self._moyu_chunk_buffer:
                            tail_lines = self._wrap_text_to_lines(self._moyu_chunk_buffer, width)
                            self._append_lines_to_pages(tail_lines)
                            self._moyu_chunk_buffer = ""
                        try:
                            QCoreApplication.processEvents()
                        except Exception:
                            pass
                    break
                except Exception as e:
                    opened = False
                    # 尝试下一个编码
                    last_err = e
                    continue
            if not opened:
                self.history.addItem(f"[警告] 读取失败: {name}")
            # 文件结束后补一个空行分隔
            self._append_lines_to_pages([""])
            try:
                QCoreApplication.processEvents()
            except Exception:
                pass
        # 会话收尾：若有剩余行，形成最后一页
        self._finalize_pages_from_staging()
        # 展示恢复页并进入摸鱼模式
        try:
            restore_idx = self._restore_moyu_page()
            self._show_moyu_page(restore_idx)
            self.set_moyu_mode(True)
        except Exception:
            # 回退：若分页失败则直接显示第一页或空
            try:
                self.moyu_view.setPlainText(self._moyu_pages[0] if self._moyu_pages else "")
                self.moyu_view.setVisible(True)
                self.moyu_page_label.setVisible(True)
                self.set_moyu_mode(True)
            except Exception:
                pass
        # 更加隐形：不显示数量，仅提示“已加载”
        self.history.addItem("已加载")
        # 持久化路径
        try:
            settings = QSettings()
            settings.setValue("moyu_path", path)
        except Exception:
            pass
        # 若本面板路径框当前可见，加载后隐藏
        try:
            if self.moyu_path_edit.isVisible():
                self.moyu_path_edit.setVisible(False)
        except Exception:
            pass

    def _compute_moyu_pages_from_text(self, text: str) -> None:
        """
        函数: _compute_moyu_pages_from_text
        作用: 将完整文本按当前视图内容宽度进行物理换行，
              并固定每页为三行进行分页；当视图尚未布局时，
              回退使用容器宽度进行估算。
        参数:
            text: 完整文本内容。
        返回:
            无。（结果存入 self._moyu_pages）
        """
        try:
            width = self._get_moyu_content_width()
            lines = self._wrap_text_to_lines_doc(text, width)
        except Exception:
            # 回退：按原始行切分
            lines = text.splitlines()
        # 动态每页行数
        n = self._get_lines_per_page()
        n = max(1, int(n))
        pages = []
        buf = list(lines)
        while len(buf) >= n:
            pages.append("\n".join(buf[:n]))
            buf = buf[n:]
        if buf:
            pages.append("\n".join(buf))
        if not pages:
            pages = [""]
        self._moyu_pages = pages
        self._moyu_page_index = 0

    def _get_moyu_content_width(self) -> int:
        """
        函数: _get_moyu_content_width
        作用: 计算文本视图的内容可用宽度（减去文档边距），在视图未布局时回退到容器宽度。
        参数:
            无。
        返回:
            int: 内容像素宽度。
        """
        try:
            doc_m = int(self.moyu_view.document().documentMargin())
        except Exception:
            doc_m = 0
        vw = 0
        try:
            vw = int(self.moyu_view.viewport().width())
        except Exception:
            vw = 0
        if vw <= 1:
            try:
                vw = int(self.moyu_view.width())
            except Exception:
                vw = 0
        if vw <= 1:
            try:
                vw = int(self.moyu_box.width())
            except Exception:
                vw = 320
        return max(1, vw - doc_m * 2)

    def _wrap_text_to_lines(self, text: str, width: int) -> list:
        """
        函数: _wrap_text_to_lines
        作用: 使用 QTextLayout 按指定宽度对原始文本进行物理换行，返回行列表；
              保留空行，换行仅在单词边界或必要位置断开。
        参数:
            text: 原始文本。
            width: 目标内容宽度（像素）。
        返回:
            list[str]: 换行后的物理行列表。
        """
        # 构造缓存键：宽度 + 字体 + 文本长度（避免存储过大哈希）
        try:
            font = self.moyu_view.font()
            font_key = f"{font.family()}-{font.pointSize()}"
        except Exception:
            font_key = "default"
        try:
            content_key = hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()
        except Exception:
            content_key = f"len:{len(text)}"
        cache_key = (int(width), font_key, content_key)
        cached = self._moyu_line_cache.get(cache_key)
        if cached is not None:
            return cached
        opt = QTextOption()
        try:
            opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        except Exception:
            pass
        lines_out = []
        # 逐段处理，保持原始换行
        for para in text.splitlines():
            if para == "":
                lines_out.append("")
                continue
            try:
                layout = QTextLayout(para, self.moyu_view.font())
                layout.setTextOption(opt)
                layout.beginLayout()
                while True:
                    line = layout.createLine()
                    if not line.isValid():
                        break
                    line.setLineWidth(float(width))
                    start = int(line.textStart())
                    length = int(line.textLength())
                    lines_out.append(para[start:start+length])
                layout.endLayout()
            except Exception:
                # 回退：简单按字符估算长度换行
                try:
                    avg = max(1, int(self.moyu_view.fontMetrics().averageCharWidth()))
                    chars = max(1, int(width / avg))
                except Exception:
                    chars = 60
                i = 0
                while i < len(para):
                    lines_out.append(para[i:i+chars])
                    i += chars
        # 写入缓存
        self._moyu_line_cache[cache_key] = lines_out
        # 简单的缓存上限：仅保留最近一个键，防止内存累积
        try:
            if len(self._moyu_line_cache) > 3:
                # 移除非当前键的旧键
                for k in list(self._moyu_line_cache.keys()):
                    if k != cache_key:
                        self._moyu_line_cache.pop(k, None)
        except Exception:
            pass
        return lines_out

    def _show_moyu_page(self, index: int) -> None:
        """
        函数: _show_moyu_page
        作用: 显示指定页内容并更新页码标签。
        参数:
            index: 目标页索引（0基）。
        返回:
            无。
        """
        if not self._moyu_pages:
            self.moyu_view.setVisible(False)
            self.moyu_page_label.setVisible(False)
            return
        index = max(0, min(index, len(self._moyu_pages) - 1))
        self._moyu_page_index = index
        # 双缓冲效果：更新前暂时禁用绘制，减少闪烁
        try:
            self.moyu_view.setUpdatesEnabled(False)
        except Exception:
            pass
        self.moyu_view.setPlainText(self._moyu_pages[index])
        try:
            self.moyu_view.setUpdatesEnabled(True)
            self.moyu_view.viewport().update()
        except Exception:
            pass
        self.moyu_view.setVisible(True)
        self._update_moyu_page_label()
        try:
            self._prefetch_neighbors(index)
        except Exception:
            pass
        # 持久化当前页码
        self._persist_moyu_page()

    def _update_moyu_page_label(self) -> None:
        """
        函数: _update_moyu_page_label
        作用: 刷新“当前页/总页”显示。
        参数:
            无。
        返回:
            无。
        """
        try:
            total = len(self._moyu_pages) if self._moyu_pages else 0
            current = self._moyu_page_index + 1 if total > 0 else 0
            # 仅显示数字页码
            self.moyu_page_label.setText(f"{current} / {total}")
            self.moyu_page_label.setVisible(total >= 1)
        except Exception:
            pass

    def _persist_moyu_page(self) -> None:
        """
        函数: _persist_moyu_page
        作用: 将当前观看页码持久化到 QSettings，便于下次恢复。
        参数:
            无。
        返回:
            无。
        """
        try:
            settings = QSettings()
            settings.setValue("moyu_last_page", int(self._moyu_page_index))
        except Exception:
            pass

    def _restore_moyu_page(self) -> int:
        """
        函数: _restore_moyu_page
        作用: 从 QSettings 读取上次观看页码；读取失败返回 0。
        参数:
            无。
        返回:
            int: 恢复的页码索引（0基）。
        """
        try:
            settings = QSettings()
            val = settings.value("moyu_last_page", 0, type=int)
            return int(val) if isinstance(val, int) else 0
        except Exception:
            return 0

    def _get_lines_per_page(self) -> int:
        """
        函数: _get_lines_per_page
        作用: 按可见区域高度与字体行距，计算每页可显示行数；至少 1 行。
        参数:
            无。
        返回:
            int。
        """
        try:
            fm = self.moyu_view.fontMetrics()
            h = int(self.moyu_view.viewport().height())
            line_h = max(1, int(fm.lineSpacing()))
            n = max(1, (h // line_h) - 1)
            return int(n)
        except Exception:
            return 3

    def _wrap_text_to_lines_doc(self, text: str, width: int) -> list:
        """
        函数: _wrap_text_to_lines_doc
        作用: 使用 QTextDocument 进行段落布局并按指定宽度换行，返回物理行列表。
        参数:
            text: 原始文本。
            width: 内容宽度（像素）。
        返回:
            list[str]。
        """
        try:
            from PySide6.QtGui import QTextDocument, QTextOption
            doc = QTextDocument()
            doc.setDefaultFont(self.moyu_view.font())
            opt = QTextOption()
            try:
                opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            except Exception:
                pass
            doc.setDefaultTextOption(opt)
            doc.setPlainText(text)
            try:
                doc.setTextWidth(float(width))
            except Exception:
                pass
            lines = []
            blk = doc.firstBlock()
            while blk.isValid():
                lay = blk.layout()
                cnt = 0
                try:
                    cnt = lay.lineCount()
                except Exception:
                    cnt = 0
                for i in range(cnt):
                    try:
                        ln = lay.lineAt(i)
                        start = int(ln.textStart())
                        length = int(ln.textLength())
                        seg = blk.text()[start:start + length]
                        lines.append(seg)
                    except Exception:
                        pass
                blk = blk.next()
            if not lines:
                try:
                    return self._wrap_text_to_lines(text, width)
                except Exception:
                    pass
            return lines
        except Exception:
            return text.splitlines()

    def _prefetch_neighbors(self, index: int) -> None:
        """
        函数: _prefetch_neighbors
        作用: 预加载当前页的前后 2 页内容到缓存字典，提升翻页响应。
        参数:
            index: 当前页索引。
        返回:
            无。
        """
        try:
            for d in (-2, -1, 1, 2):
                j = index + d
                if 0 <= j < len(self._moyu_pages):
                    self._moyu_prefetch_cache[j] = self._moyu_pages[j]
        except Exception:
            pass

    def save_moyu_current_page(self) -> None:
        """
        函数: save_moyu_current_page
        作用: 主动保存当前页码（Esc 退出前调用）。
        参数:
            无。
        返回:
            无。
        """
        self._persist_moyu_page()

    def _append_lines_to_pages(self, lines: list) -> None:
        """
        函数: _append_lines_to_pages
        作用: 将传入的物理行列表与暂存行合并，按三行规则生成页并追加到分页结果；保留未满一页的行到暂存区。
        参数:
            lines: 物理行列表。
        返回:
            无。
        """
        try:
            n = self._get_lines_per_page()
            n = max(1, int(n))
            buf = self._moyu_line_staging + list(lines)
            while len(buf) >= n:
                self._moyu_pages.append("\n".join(buf[:n]))
                buf = buf[n:]
            self._moyu_line_staging = buf
        except Exception:
            pass

    def _finalize_pages_from_staging(self) -> None:
        """
        函数: _finalize_pages_from_staging
        作用: 将暂存区剩余的未满一页的行写入最后一页（若存在）。
        参数:
            无。
        返回:
            无。
        """
        try:
            if self._moyu_line_staging:
                self._moyu_pages.append("\n".join(self._moyu_line_staging))
                self._moyu_line_staging = []
        except Exception:
            pass

    def show_moyu_disguise(self) -> None:
        """
        函数: show_moyu_disguise
        作用: 在红框区域的文本视图中随机显示一段数学公式/等式，
              用于按下 Esc 退出摸鱼时的伪装显示；不显示页码。
        参数:
            无。
        返回:
            无。
        """
        try:
            samples = [
                "E = mc^2\n∫_0^∞ e^{-x} dx = 1\nlim_{n→∞} (1+1/n)^n = e",
                "x = (-b ± √(b^2 - 4ac)) / (2a)\na^2 + b^2 = c^2\nsin^2θ + cos^2θ = 1",
                "∑_{k=1}^{n} k = n(n+1)/2\nS_n = n(n+1)/2\n∑_{k=1}^{∞} 1/k^2 = π^2/6",
                "∫ sin x dx = -cos x + C\n∫ cos x dx = sin x + C\n∫ e^x dx = e^x + C",
                "det(A) ≠ 0 ⇒ A 可逆\nA^{-1}A = I\nrank(A) = rank(A^T)",
                "∇·E = ρ/ε0\n∇×E = -∂B/∂t\n∇·B = 0",
            ]
            txt = random.choice(samples)
            self.moyu_view.setPlainText(txt)
            self.moyu_page_label.setVisible(False)
            self.moyu_view.setVisible(True)
        except Exception:
            try:
                # 回退：若随机失败，显示固定伪装文本
                self.moyu_view.setPlainText("y = ax^2 + bx + c\nΔ = b^2 - 4ac")
                self.moyu_page_label.setVisible(False)
                self.moyu_view.setVisible(True)
            except Exception:
                pass

    def _load_moyu_texts_from_path(self) -> None:
        """
        函数: _load_moyu_texts_from_path
        作用: 兼容旧触发点——从本面板路径框读取目录并调用新的加载方法。
        参数:
            无。
        返回:
            无。
        """
        try:
            path = self.moyu_path_edit.text().strip()
            self.load_moyu_texts_from_path(path)
        except Exception:
            pass
class _MinimalReaderDialog(QDialog):
    """
    类: _MinimalReaderDialog
    作用: 极简阅读窗口，采用简洁界面显示三行分页内容，支持滚轮与方向键/W/S 翻页。
    """

    def __init__(self, parent: QWidget, pages: list, index: int = 0) -> None:
        """
        函数: __init__
        作用: 初始化极简阅读窗口，设置只读文本视图与初始页。
        参数:
            parent: 父窗口。
            pages: 分页内容列表。
            index: 初始页索引。
        返回:
            无。
        """
        super().__init__(parent)
        self._pages = pages
        self._index = max(0, min(int(index), len(self._pages) - 1))
        self.on_page_changed = None
        self._wheel_accum = 0
        try:
            self.setWindowFlag(Qt.FramelessWindowHint, True)
        except Exception:
            pass
        self._drag_offset = None
        self._view = QPlainTextEdit(self)
        self._view.setReadOnly(True)
        try:
            f2 = self._view.font()
            f2.setPointSize(13)
            self._view.setFont(f2)
        except Exception:
            pass
        self._view.setFrameStyle(QFrame.NoFrame)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        try:
            self._view.setTextInteractionFlags(Qt.NoTextInteraction)
            self._view.viewport().setCursor(Qt.ArrowCursor)
            self.setMouseTracking(True)
            self._view.setMouseTracking(True)
        except Exception:
            pass
        self._size_grip = QSizeGrip(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(4)
        root.addWidget(self._view)
        try:
            self.installEventFilter(self)
            self._view.installEventFilter(self)
            self._size_grip.installEventFilter(self)
        except Exception:
            pass
        try:
            self._show_border = False
            self._hover_hidden = False
            self._hover_enabled = True
            self._hover_hidden_opacity = 0.06
            self._hover_edge_px = 3
            self._hover_window_edge_px = 10
            self._hover_timer = QTimer(self)
            self._hover_timer.setInterval(160)
            self._hover_timer.timeout.connect(self._on_hover_timer)
            self._hover_show_delay_timer = QTimer(self)
            try:
                settings = QSettings()
                d = int(settings.value("minimal_hover_delay_ms", 1500, type=int))
            except Exception:
                d = 1500
            d = 0 if d < 0 else (10000 if d > 10000 else d)
            self._hover_delay_ms = int(d)
            self._hover_show_delay_timer.setInterval(int(d))
            self._hover_show_delay_timer.setSingleShot(True)
            self._hover_show_delay_timer.timeout.connect(self._hover_show_now)
            self._fade_anim = None
            self._edge_near_ticks = 0
            self._resizing = False
            self._resize_grid_px = 16
            self._resize_snap_px = 12
        except Exception:
            pass
        self._show_page(self._index)
        try:
            self._update_size_grip_geometry()
        except Exception:
            pass

    def _show_page(self, index: int) -> None:
        """
        函数: _show_page
        作用: 显示指定页内容并触发外部回调。
        参数:
            index: 目标页索引。
        返回:
            无。
        """
        if not self._pages:
            return
        self._index = max(0, min(int(index), len(self._pages) - 1))
        self._view.setPlainText(self._pages[self._index])
        if callable(self.on_page_changed):
            try:
                self.on_page_changed(self._index)
            except Exception:
                pass

    def keyPressEvent(self, event) -> None:
        """
        函数: keyPressEvent
        作用: 处理方向键/PageUp/PageDown/W/S 翻页。
        参数:
            event: 键盘事件。
        返回:
            无。
        """
        key = event.key()
        if key in (Qt.Key_PageUp, Qt.Key_Up, Qt.Key_Left, Qt.Key_W):
            self._show_page(self._index - 1)
            return
        if key in (Qt.Key_PageDown, Qt.Key_Down, Qt.Key_Right, Qt.Key_S):
            self._show_page(self._index + 1)
            return
        try:
            super().keyPressEvent(event)
        except Exception:
            pass

    def wheelEvent(self, event) -> None:
        """
        函数: wheelEvent
        作用: 处理鼠标滚轮翻页，采用 120 阈值累计方式确保一致一页一翻。
        参数:
            event: 滚轮事件。
        返回:
            无。
        """
        delta = 0
        try:
            delta = int(event.angleDelta().y())
        except Exception:
            delta = 0
        if delta == 0:
            try:
                delta = int(getattr(event.pixelDelta(), 'y', lambda: 0)())
            except Exception:
                delta = 0
        self._wheel_accum += delta
        step = 120
        moved = False
        while self._wheel_accum >= step:
            self._show_page(self._index - 1)
            self._wheel_accum -= step
            moved = True
        while self._wheel_accum <= -step:
            self._show_page(self._index + 1)
            self._wheel_accum += step
            moved = True
        if moved:
            return
        try:
            super().wheelEvent(event)
        except Exception:
            pass
    def eventFilter(self, obj, event):
        try:
            if obj is self or obj is self._view:
                et = event.type()
                if et == event.Type.Enter:
                    try:
                        self._hover_show()
                    except Exception:
                        pass
                    return False
                if et == event.Type.Leave:
                    try:
                        if obj is self:
                            if not getattr(self, "_resizing", False):
                                self._hover_hide()
                        # 忽略文本视图的 Leave，避免进入右下角尺寸区域时误判为移出窗口
                    except Exception:
                        pass
                    return False
                if et == event.Type.MouseButtonPress:
                    if event.buttons() & Qt.LeftButton:
                        try:
                            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                        except Exception:
                            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                        try:
                            self.raise_()
                            self.activateWindow()
                            self.setFocus(Qt.MouseFocusReason)
                        except Exception:
                            pass
                        return True
                if et == event.Type.MouseMove:
                    if self._drag_offset is not None and (event.buttons() & Qt.LeftButton):
                        try:
                            pos = event.globalPosition().toPoint() - self._drag_offset
                        except Exception:
                            pos = event.globalPos() - self._drag_offset
                        self.move(pos)
                        return True
                if et == event.Type.MouseButtonRelease:
                    self._drag_offset = None
                    return True
                if et == event.Type.Wheel:
                    try:
                        self.wheelEvent(event)
                        return True
                    except Exception:
                        pass
            # 尺寸吸附：监听右下角 QSizeGrip 拖拽事件
            if hasattr(self, "_size_grip") and obj is self._size_grip:
                et = event.type()
                if et == event.Type.MouseButtonPress:
                    self._resizing = True
                elif et == event.Type.MouseMove:
                    if self._resizing:
                        try:
                            self._apply_resize_snapping()
                        except Exception:
                            pass
                elif et == event.Type.MouseButtonRelease:
                    self._resizing = False
                    try:
                        self._apply_resize_snapping()
                    except Exception:
                        pass
        except Exception:
            pass
        return super().eventFilter(obj, event)
    def enterEvent(self, event) -> None:
        """
        函数: enterEvent
        作用: 鼠标移入时显示极简窗口（恢复设定透明度与边框）。
        参数:
            event: 进入事件。
        返回:
            无。
        """
        try:
            self._hover_show()
        except Exception:
            pass
        try:
            super().enterEvent(event)
        except Exception:
            pass
    def leaveEvent(self, event) -> None:
        """
        函数: leaveEvent
        作用: 鼠标移出时隐藏极简窗口（降低不透明度）。
        参数:
            event: 离开事件。
        返回:
            无。
        """
        try:
            if not getattr(self, "_resizing", False):
                self._hover_hide()
        except Exception:
            pass
        try:
            super().leaveEvent(event)
        except Exception:
            pass
    def _hover_show(self) -> None:
        """
        函数: _hover_show
        作用: 延迟触发显示（1.5秒），避免误触。仅启动显示计时，不立即更改透明度。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not getattr(self, "_hover_enabled", True):
                return
            if hasattr(self, "_hover_show_delay_timer") and self._hover_show_delay_timer is not None:
                if not self._hover_show_delay_timer.isActive():
                    self._hover_show_delay_timer.start()
        except Exception:
            pass
    def _hover_hide(self) -> None:
        """
        函数: _hover_hide
        作用: 立即触发隐藏动画，将不透明度渐变到隐藏值，保留交互与命中。
        参数:
            无。
        返回:
            无。
        """
        try:
            if getattr(self, "_resizing", False):
                return
            if not getattr(self, "_hover_enabled", True):
                return
            self._hover_hidden = True
            try:
                self._show_border = False
            except Exception:
                pass
            try:
                if hasattr(self, "_hover_show_delay_timer") and self._hover_show_delay_timer is not None:
                    if self._hover_show_delay_timer.isActive():
                        self._hover_show_delay_timer.stop()
            except Exception:
                pass
            try:
                target = float(getattr(self, "_hover_hidden_opacity", 0.06))
                self._animate_opacity(target, 150)
            except Exception:
                pass
            try:
                if hasattr(self, "_hover_timer") and self._hover_timer is not None:
                    if not self._hover_timer.isActive():
                        self._hover_timer.start()
            except Exception:
                pass
        except Exception:
            pass

    def _hover_show_now(self) -> None:
        """
        函数: _hover_show_now
        作用: 立即执行显示动画，按用户透明度设置恢复；透明特例下启用边框与文本半透明。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not getattr(self, "_hover_enabled", True):
                return
            settings = QSettings()
            percent = int(settings.value("minimal_opacity_percent", 100, type=int))
            percent = max(1, min(100, percent))
            if percent == 1:
                try:
                    self._show_border = True
                    self.setAttribute(Qt.WA_TranslucentBackground, True)
                except Exception:
                    pass
                try:
                    if hasattr(self, "_view") and self._view is not None:
                        eff = self._view.viewport().graphicsEffect()
                        if not eff:
                            eff = QGraphicsOpacityEffect(self._view.viewport())
                            self._view.viewport().setGraphicsEffect(eff)
                        eff.setOpacity(0.9)
                except Exception:
                    pass
                self._animate_opacity(1.0, 150)
            else:
                try:
                    self._show_border = False
                except Exception:
                    pass
                try:
                    if hasattr(self, "_view") and self._view is not None:
                        eff = self._view.viewport().graphicsEffect()
                        if not eff:
                            eff = QGraphicsOpacityEffect(self._view.viewport())
                            self._view.viewport().setGraphicsEffect(eff)
                        eff.setOpacity(0.5)
                except Exception:
                    pass
                self._animate_opacity(percent / 100.0, 150)
            self._hover_hidden = False
        except Exception:
            pass

    def _animate_opacity(self, target: float, duration: int = 300) -> None:
        """
        函数: _animate_opacity
        作用: 使用 QPropertyAnimation 对窗口不透明度进行渐变过渡。
        参数:
            target: 目标不透明度 (0.0~1.0)。
            duration: 动画时长毫秒。
        返回:
            无。
        """
        try:
            if target < 0.0:
                target = 0.0
            if target > 1.0:
                target = 1.0
            anim = QPropertyAnimation(self, b"windowOpacity")
            try:
                anim.setDuration(int(duration))
            except Exception:
                pass
            try:
                anim.setStartValue(float(self.windowOpacity()))
                anim.setEndValue(float(target))
            except Exception:
                pass
            try:
                anim.setEasingCurve(QEasingCurve.InOutQuad)
            except Exception:
                pass
            try:
                self._fade_anim = anim
                anim.start()
            except Exception:
                pass
        except Exception:
            pass

    def _apply_resize_snapping(self) -> None:
        """
        函数: _apply_resize_snapping
        作用: 在拖动 QSizeGrip 调整尺寸时，增加网格吸附与屏幕边缘贴靠。
        参数:
            无。
        返回:
            无。
        """
        try:
            grid = int(getattr(self, "_resize_grid_px", 16))
            snap_edge = int(getattr(self, "_resize_snap_px", 12))
            r = self.geometry()
            w = int(r.width())
            h = int(r.height())
            min_w = int(self.minimumWidth())
            min_h = int(self.minimumHeight())
            def snap_val(v: int, step: int, vmin: int) -> int:
                try:
                    if step <= 1:
                        return max(vmin, v)
                    sv = int(round(v / float(step)) * step)
                    return max(vmin, sv)
                except Exception:
                    return max(vmin, v)
            w2 = snap_val(w, grid, min_w)
            h2 = snap_val(h, grid, min_h)
            try:
                screen = QGuiApplication.primaryScreen()
                g = screen.geometry() if screen else None
            except Exception:
                g = None
            if g is not None:
                left = int(r.left())
                top = int(r.top())
                br_x = left + w2
                br_y = top + h2
                try:
                    if abs(int(g.right()) - br_x) <= snap_edge:
                        w2 = max(min_w, int(g.right() - left))
                    if abs(int(g.bottom()) - br_y) <= snap_edge:
                        h2 = max(min_h, int(g.bottom() - top))
                except Exception:
                    pass
            if w2 != w or h2 != h:
                try:
                    self.resize(int(w2), int(h2))
                except Exception:
                    pass
            try:
                self._update_size_grip_geometry()
            except Exception:
                pass
        except Exception:
            pass
    def _on_hover_timer(self) -> None:
        """
        函数: _on_hover_timer
        作用: 边缘唤醒定时器回调；当鼠标接近屏幕边缘或窗口边缘时，自动恢复显示。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not getattr(self, "_hover_hidden", False):
                try:
                    if self._hover_timer.isActive():
                        self._hover_timer.stop()
                except Exception:
                    pass
                return
            pos = None
            try:
                pos = QCursor.pos()
            except Exception:
                pass
            if pos is None:
                return
            # 精准唤醒：仅当靠近窗口边缘，且持续接近一段时间后触发延迟显示
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
        except Exception:
            pass
    def _is_near_window_edge(self, pos) -> bool:
        """
        函数: _is_near_window_edge
        作用: 判断鼠标是否接近当前窗口边缘（含一定缓冲距离）。
        参数:
            pos: 全局坐标 QPoint。
        返回:
            bool: True 表示接近窗口边缘。
        """
        try:
            edge = int(getattr(self, "_hover_window_edge_px", 10))
        except Exception:
            edge = 10
        try:
            r = self.frameGeometry().adjusted(-edge, -edge, edge, edge)
            return r.contains(pos)
        except Exception:
            return False
    def _is_near_screen_edge(self, pos) -> bool:
        """
        函数: _is_near_screen_edge
        作用: 判断鼠标是否接近当前屏幕边缘（用于“边缘唤醒”）。
        参数:
            pos: 全局坐标 QPoint。
        返回:
            bool: True 表示接近屏幕边缘。
        """
        try:
            screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        except Exception:
            screen = None
        if screen is None:
            return False
        try:
            edge = int(getattr(self, "_hover_edge_px", 3))
        except Exception:
            edge = 3
        try:
            g = screen.geometry()
            x = pos.x()
            y = pos.y()
            near_x = abs(x - g.left()) <= edge or abs(x - g.right()) <= edge
            near_y = abs(y - g.top()) <= edge or abs(y - g.bottom()) <= edge
            return near_x or near_y
        except Exception:
            return False
    def resizeEvent(self, event) -> None:
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        try:
            self._update_size_grip_geometry()
        except Exception:
            pass
    def paintEvent(self, event) -> None:
        """
        函数: paintEvent
        作用: 在透明模式（1%）下绘制整窗淡边框，并以极低透明度填充整窗，避免点击穿透。
        参数:
            event: 绘制事件。
        返回:
            无。
        """
        try:
            super().paintEvent(event)
        except Exception:
            pass
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing, True)
            # 仅在透明背景模式下填充命中层，避免非透明模式产生暗膜
            try:
                if self.testAttribute(Qt.WA_TranslucentBackground):
                    p.fillRect(self.rect(), QColor(0, 0, 0, 1))
            except Exception:
                pass
            # 边框颜色取当前主题背景色，保持一致
            col_str = None
            try:
                col_str = getattr(self, "_theme_bg", None)
            except Exception:
                col_str = None
            if not col_str:
                try:
                    settings = QSettings()
                    col_str = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
                except Exception:
                    col_str = "#F5F5F7"
            try:
                col = QColor(col_str)
                if self.testAttribute(Qt.WA_TranslucentBackground):
                    col.setAlpha(180)
                else:
                    col.setAlpha(255)
            except Exception:
                col = QColor(255, 255, 255, 180)
            pen = QPen(col)
            pen.setWidth(1)
            p.setPen(pen)
            r = self.rect().adjusted(0, 0, -1, -1)
            radius = 6
            p.drawRoundedRect(r, radius, radius)
            p.end()
        except Exception:
            pass
    def _update_size_grip_geometry(self) -> None:
        try:
            if not hasattr(self, "_size_grip") or self._size_grip is None:
                return
            r = self.rect()
            sz = self._size_grip.size()
            x = max(0, r.right() - sz.width())
            y = max(0, r.bottom() - sz.height())
            self._size_grip.move(x, y)
        except Exception:
            pass
