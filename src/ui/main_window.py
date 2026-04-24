# -*- coding: utf-8 -*-
"""
文件: src/ui/main_window.py
描述: 计算器主窗口，负责模式切换与整体布局管理。
"""

from typing import Optional

from PySide6.QtCore import Qt, QSettings, QSize
from PySide6.QtGui import (
    QIcon,
    QPainter,
    QPixmap,
    QFont,
    QTransform,
    QColor,
    QPen,
    QPalette,
    QPainterPath,
    QFontMetrics,
    QShortcut,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QToolButton,
    QMenu,
    QWidgetAction,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QMessageBox,
    QApplication,
    QSizeGrip,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QGridLayout,
    QPushButton,
    QColorDialog,
    QFrame,
)
import os
import sys
import ctypes

from core.memory_store import MemoryStore
from core.settings_service import SettingsService
from ui.checksum_panel import ChecksumPanel
from ui.normal_panel import NormalPanel
from ui.programmer_panel import ProgrammerPanel
from ui.scientific_panel import ScientificPanel


class MainWindow(QMainWindow):
    """
    类: MainWindow
    作用: 应用主窗口，提供左上角模式按钮以切换三种计算器模式，
         并承载自适应布局的主内容区域。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化主窗口，创建模式切换按钮与三种面板。
        参数:
            parent: 父窗口。
        返回:
            无。
        """
        super().__init__(parent)
        self.setWindowTitle("计算器")
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        except Exception:
            pass

        # 共享记忆存储，供各面板使用
        self.memory_store = MemoryStore()

        # 主题状态：读取持久化设置（默认浅色）
        self.dark_mode: bool = SettingsService.dark_mode(False)
        # 置顶状态：读取持久化设置（默认不置顶）
        self.pin_on_top: bool = SettingsService.always_on_top(False)

        # 顶部工具区（模式切换按钮）
        header = self._create_header()
        # 自绘系统标题栏（1:1 替换原系统边框，不改变原有内容布局）
        title_bar = self._create_title_bar()

        # 主内容堆栈：普通 / 程序员 / 科学
        self.stack = QStackedWidget()
        self.normal_panel = NormalPanel(self.memory_store)
        self.programmer_panel = ProgrammerPanel(self.memory_store, bits=32)
        self.checksum_panel = ChecksumPanel(self.memory_store)
        self.scientific_panel = ScientificPanel(self.memory_store, default_angle_mode="deg")
        self.stack.addWidget(self.normal_panel)
        self.stack.addWidget(self.programmer_panel)
        self.stack.addWidget(self.checksum_panel)
        self.stack.addWidget(self.scientific_panel)

        # 根布局
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(10)
        vbox.addWidget(title_bar, 0)
        vbox.addWidget(header, 0)
        vbox.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        try:
            self._create_size_grip()
        except Exception:
            pass

        # 默认显示程序员计算器
        self.stack.setCurrentWidget(self.programmer_panel)
        # 应用默认置顶状态（若用户曾开启置顶）
        try:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, self.pin_on_top)
        except Exception:
            pass
        # 启用无边框与自绘标题栏
        try:
            self._enable_frameless_titlebar()
        except Exception:
            pass
        # Windows 标题栏与页面主题一致
        try:
            self._apply_windows_dark_titlebar(self.dark_mode)
        except Exception:
            pass

        # 全局快捷键：Ctrl+M 进入摸鱼模式；Esc 退出摸鱼模式
        try:
            self._shortcut_moyu = QShortcut(QKeySequence("Ctrl+M"), self)
            self._shortcut_moyu.setContext(Qt.WindowShortcut)
            self._shortcut_moyu.activated.connect(self._shortcut_quick_moyu)

            self._shortcut_exit = QShortcut(QKeySequence("Esc"), self)
            self._shortcut_exit.setContext(Qt.WindowShortcut)
            self._shortcut_exit.activated.connect(self._shortcut_exit_moyu)
        except Exception:
            pass

    def _create_size_grip(self) -> None:
        """
        函数: _create_size_grip
        作用: 在窗口右下角添加尺寸手柄（QSizeGrip），支持拖动动态调节大小。
        参数:
            无。
        返回:
            无。
        """
        try:
            self._size_grip = QSizeGrip(self)
            self._size_grip.setToolTip("拖动调整窗口大小")
            try:
                # 统一手柄尺寸，便于点击与拖动
                self._size_grip.setFixedSize(QSize(18, 18))
            except Exception:
                pass
            self._update_size_grip_geometry()
            self._size_grip.show()
        except Exception:
            pass

    def _update_size_grip_geometry(self) -> None:
        """
        函数: _update_size_grip_geometry
        作用: 将尺寸手柄定位到窗口右下角，考虑到窗口边距与 DPI 缩放。
        参数:
            无。
        返回:
            无。
        """
        try:
            if not hasattr(self, "_size_grip") or self._size_grip is None:
                return
            r = self.rect()
            sz = self._size_grip.size()
            x = max(0, r.right() - sz.width() - 2)
            y = max(0, r.bottom() - sz.height() - 2)
            self._size_grip.move(x, y)
        except Exception:
            pass

    def resizeEvent(self, event) -> None:
        """
        函数: resizeEvent
        作用: 窗口尺寸变化时重新定位右下角尺寸手柄，确保始终可拖动。
        参数:
            event: 尺寸变更事件。
        返回:
            无。
        """
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        try:
            self._update_size_grip_geometry()
        except Exception:
            pass

    def _create_header(self) -> QWidget:
        """
        函数: _create_header
        作用: 创建顶部栏，包含左上角模式切换按钮与标题。
        参数:
            无。
        返回:
            顶部栏 QWidget。
        """
        header = QWidget()
        try:
            self._header = header
        except Exception:
            pass
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(8)

        self.mode_btn = QToolButton()
        self.mode_btn.setText("模式")
        self.mode_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self.mode_btn)
        act_normal = menu.addAction("普通计算器")
        act_programmer = menu.addAction("程序员计算器")
        act_checksum = menu.addAction("校验和计算")
        act_scientific = menu.addAction("科学计算器")
        self.mode_btn.setMenu(menu)

        act_normal.triggered.connect(self._switch_to_normal)
        act_programmer.triggered.connect(self._switch_to_programmer)
        act_checksum.triggered.connect(self._switch_to_checksum)
        act_scientific.triggered.connect(self._switch_to_scientific)

        self.title_label = QLabel("程序员计算器")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.game_btn = QToolButton()
        self.game_btn.setText("选择")
        self.game_btn.setToolTip("隐藏游戏选择")
        self.game_btn.setVisible(False)
        try:
            self.game_btn.clicked.connect(self._open_game_selector_via_scientific)
        except Exception:
            pass

        # 隐藏摸鱼设置按钮：初始隐藏，解锁后显示，位于“模式”按钮之后
        self.moyu_btn = QToolButton()
        self.moyu_btn.setText("设置")
        self.moyu_btn.setToolTip("摸鱼设置：指定TXT目录")
        self.moyu_btn.setVisible(False)
        try:
            # 取消下拉菜单模式，改为点击弹出设置对话框
            self.moyu_btn.setPopupMode(QToolButton.DelayedPopup)
        except Exception:
            pass
        try:
            self.moyu_btn.clicked.connect(self._open_moyu_settings_dialog)
        except Exception:
            pass

        # 摸鱼路径粘贴框：位于当前模式标题之后，默认隐藏
        self.moyu_path_edit = QLineEdit()
        self.moyu_path_edit.setPlaceholderText("粘贴TXT目录路径后按回车确认")
        self.moyu_path_edit.setVisible(False)
        self.moyu_path_edit.returnPressed.connect(self._confirm_moyu_path)
        # 预填持久化路径
        try:
            saved = SettingsService.moyu_path("")
            if saved:
                self.moyu_path_edit.setText(saved)
        except Exception:
            pass

        # 右上角：置顶按钮、日/夜切换按钮与帮助按钮
        self.pin_btn = QToolButton()
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(self.pin_on_top)
        self.pin_btn.setToolTip("窗口置顶")
        self.pin_btn.clicked.connect(self._toggle_pin)
        self._update_pin_button_label()

        # 日/夜切换
        self.theme_btn = QToolButton()
        self.theme_btn.setToolTip("浅色/深色切换")
        self.theme_btn.clicked.connect(self._toggle_theme)
        # 初始化图标/提示（稍后统一按钮尺寸后再设置 iconSize）

        # 帮助按钮
        self.help_btn = QToolButton()
        self.help_btn.setText("?")
        self.help_btn.setToolTip("使用说明")
        self.help_btn.clicked.connect(self._show_help)

        # 统一四个按钮的固定尺寸（模式后的“设置”、置顶、主题、帮助）
        size_hint_moyu = self.moyu_btn.sizeHint()
        size_hint_pin = self.pin_btn.sizeHint()
        size_hint_theme = self.theme_btn.sizeHint()
        size_hint_help = self.help_btn.sizeHint()
        fixed_w = max(size_hint_moyu.width(), size_hint_pin.width(), size_hint_theme.width(), size_hint_help.width())
        fixed_h = max(size_hint_moyu.height(), size_hint_pin.height(), size_hint_theme.height(), size_hint_help.height())
        fixed_size = QSize(fixed_w, fixed_h)
        self.moyu_btn.setFixedSize(fixed_size)
        self.game_btn.setFixedSize(fixed_size)
        self.pin_btn.setFixedSize(fixed_size)
        self.theme_btn.setFixedSize(fixed_size)
        self.help_btn.setFixedSize(fixed_size)

        # 在相同按钮尺寸下，增大主题按钮的 iconSize（占按钮高度约 82%）
        icon_dim = int(fixed_h * 0.90)
        self.theme_btn.setIconSize(QSize(icon_dim, icon_dim))
        self._update_theme_button_label()

        hbox.addWidget(self.mode_btn)
        hbox.addWidget(self.moyu_btn)
        hbox.addWidget(self.title_label, 1)
        hbox.addWidget(self.game_btn)
        hbox.addWidget(self.moyu_path_edit, 2)
        hbox.addWidget(self.pin_btn)
        hbox.addWidget(self.theme_btn)
        hbox.addWidget(self.help_btn)
        try:
            header.installEventFilter(self)
        except Exception:
            pass
        return header

    def _create_title_bar(self) -> QWidget:
        """
        函数: _create_title_bar
        作用: 创建自绘的系统标题栏（无边框模式下使用），
              高度与系统标题栏保持一致，包含最小化/最大化/关闭按钮；
              不修改原有内容布局，实现 1:1 替换。
        参数:
            无。
        返回:
            顶部标题栏 QWidget。
        """
        bar = QWidget()
        try:
            bar.setObjectName("titleBar")
        except Exception:
            pass
        try:
            self._title_bar = bar
        except Exception:
            pass
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(6, 0, 0, 0)
        lay.setSpacing(0)
        # 左侧窗口标题
        lbl = QLabel(self.windowTitle())
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # 右侧系统控制按钮
        self.min_btn = QToolButton()
        try:
            self.min_btn.setIcon(self._make_caption_icon("min"))
        except Exception:
            self.min_btn.setText("—")
        self.min_btn.setToolTip("最小化")
        self.min_btn.clicked.connect(self._on_minimize)
        try:
            self.min_btn.setObjectName("winMinBtn")
            self.min_btn.setAutoRaise(True)
        except Exception:
            pass

        self.max_btn = QToolButton()
        try:
            self.max_btn.setIcon(self._make_caption_icon("max"))
        except Exception:
            self.max_btn.setText("□")
        self.max_btn.setToolTip("最大化/还原")
        self.max_btn.clicked.connect(self._on_toggle_max_restore)
        try:
            self.max_btn.setObjectName("winMaxBtn")
            self.max_btn.setAutoRaise(True)
        except Exception:
            pass

        self.close_btn = QToolButton()
        try:
            self.close_btn.setIcon(self._make_caption_icon("close"))
        except Exception:
            self.close_btn.setText("×")
        self.close_btn.setToolTip("关闭")
        self.close_btn.clicked.connect(self.close)
        try:
            self.close_btn.setObjectName("winCloseBtn")
            self.close_btn.setAutoRaise(True)
        except Exception:
            pass

        # 与右上角按钮统一尺寸风格
        w, h = self._system_caption_button_size()
        fixed_size = QSize(max(24, w), max(20, h))
        self.min_btn.setFixedSize(fixed_size)
        self.max_btn.setFixedSize(fixed_size)
        self.close_btn.setFixedSize(fixed_size)
        try:
            # 图标尺寸按按钮高度设置，确保缩小但清晰
            icon_dim = max(12, int(fixed_size.height() * 0.85))
            self.min_btn.setIconSize(QSize(icon_dim, icon_dim))
            self.max_btn.setIconSize(QSize(icon_dim, icon_dim))
            self.close_btn.setIconSize(QSize(icon_dim, icon_dim))
        except Exception:
            pass

        lay.addWidget(lbl, 1)
        lay.addWidget(self.min_btn)
        lay.addWidget(self.max_btn)
        lay.addWidget(self.close_btn)
        try:
            bar.installEventFilter(self)
        except Exception:
            pass
        # 依据系统标题栏高度设定固定高度
        try:
            h = self._system_caption_height()
            if h > 0:
                bar.setFixedHeight(h)
        except Exception:
            pass
        return bar

    def _switch_to_normal(self) -> None:
        """
        函数: _switch_to_normal
        作用: 切换到标准（普通）计算器模式，并更新标题文案。
        参数:
            无。
        返回:
            无。
        """
        self.stack.setCurrentWidget(self.normal_panel)
        try:
            self.game_btn.setVisible(False)
        except Exception:
            pass
        self.title_label.setText("标准计算器")

    def _switch_to_programmer(self) -> None:
        """
        函数: _switch_to_programmer
        作用: 切换到程序员计算器模式，并更新标题文案。
        参数:
            无。
        返回:
            无。
        """
        self.stack.setCurrentWidget(self.programmer_panel)
        try:
            self.game_btn.setVisible(False)
        except Exception:
            pass
        self.title_label.setText("程序员计算器")

    def _switch_to_checksum(self) -> None:
        """
        函数: _switch_to_checksum
        作用: 切换到校验和计算模式，并更新标题文案。
        参数:
            无。
        返回:
            无。
        """
        self.stack.setCurrentWidget(self.checksum_panel)
        try:
            self.game_btn.setVisible(False)
        except Exception:
            pass
        self.title_label.setText("校验和计算")

    def _switch_to_scientific(self) -> None:
        """
        函数: _switch_to_scientific
        作用: 切换到科学计算器模式，并更新标题文案。
        参数:
            无。
        返回:
            无。
        """
        self.stack.setCurrentWidget(self.scientific_panel)
        try:
            self.game_btn.setVisible(False)
        except Exception:
            pass
        self.title_label.setText("科学计算器")

    def _show_help(self) -> None:
        """
        函数: _show_help
        作用: 弹出当前计算模式的使用说明对话框，支持点击“反馈”显示二维码。
        参数:
            无。
        返回:
            无。
        """
        widget = self.stack.currentWidget()
        title = f"使用说明 - {self.title_label.text()}"
        text = "暂无使用说明"
        try:
            # 标准计算器处于摸鱼模式时，显示摸鱼说明；否则显示各面板的普通说明
            if widget is self.normal_panel and hasattr(self.normal_panel, "is_in_moyu_mode") and self.normal_panel.is_in_moyu_mode() and hasattr(self.normal_panel, "get_moyu_help_text"):
                text = self.normal_panel.get_moyu_help_text()
            elif hasattr(widget, "get_help_text"):
                text = widget.get_help_text()
        except Exception:
            pass
        
        # 创建自定义对话框
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.resize(400, 300)

        layout = QVBoxLayout(dlg)
        
        # 文本区域
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # 滚动区域（防止文本过长）
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(lbl)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)

        # 底部按钮区
        btn_box = QHBoxLayout()
        btn_feedback = QPushButton("反馈")
        btn_feedback.setToolTip("点击查看反馈方式")
        btn_feedback.clicked.connect(self._show_feedback_qrcode)
        
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(dlg.accept)
        
        btn_box.addWidget(btn_feedback)
        btn_box.addStretch()
        btn_box.addWidget(btn_ok)
        
        layout.addLayout(btn_box)
        dlg.exec()

    def _show_feedback_qrcode(self) -> None:
        """
        函数: _show_feedback_qrcode
        作用: 弹出对话框显示 '联系我.jpg' 二维码图片。
        参数:
            无。
        返回:
            无。
        """
        try:
            # 定位图片路径
            if hasattr(sys, "_MEIPASS"):
                base_dir = sys._MEIPASS
            else:
                # 假设 img 在项目根目录，与 src 同级
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
            img_path = os.path.join(base_dir, "img", "联系我.jpg")
            
            if not os.path.exists(img_path):
                QMessageBox.warning(self, "提示", f"未找到反馈图片：\n{img_path}")
                return

            # 创建图片弹窗
            dlg = QDialog(self)
            dlg.setWindowTitle("扫码反馈")
            dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            
            vbox = QVBoxLayout(dlg)
            lbl_img = QLabel()
            pix = QPixmap(img_path)
            
            # 限制显示尺寸，避免图片过大
            if pix.width() > 400 or pix.height() > 400:
                pix = pix.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
            lbl_img.setPixmap(pix)
            lbl_img.setAlignment(Qt.AlignCenter)
            
            lbl_hint = QLabel("请扫描二维码联系作者反馈问题")
            lbl_hint.setAlignment(Qt.AlignCenter)
            
            vbox.addWidget(lbl_img)
            vbox.addWidget(lbl_hint)
            
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法显示图片：{e}")

    def _update_theme_button_label(self) -> None:
        """
        函数: _update_theme_button_label
        作用: 根据当前主题状态更新日/夜按钮的☯图标（旋转 180°）与提示。
        参数:
            无。
        返回:
            无。
        """
        angle = 180 if self.dark_mode else 0
        self.theme_btn.setIcon(self._make_yinyang_icon(angle))
        self.theme_btn.setIconSize(self.theme_btn.iconSize())
        if self.dark_mode:
            self.theme_btn.setToolTip("切换为浅色主题")
        else:
            self.theme_btn.setToolTip("切换为深色主题")

    def _toggle_theme(self) -> None:
        """
        函数: _toggle_theme
        作用: 在浅色与深色主题间切换，并应用对应 QSS。
        参数:
            无。
        返回:
            无。
        """
        self._apply_theme(not self.dark_mode)

    def reveal_moyu_button(self) -> None:
        """
        函数: reveal_moyu_button
        作用: 显示顶部的摸鱼设置按钮（位于“模式”后），保持与右侧按钮一致大小。
        参数:
            无。
        返回:
            无。
        """
        try:
            self.moyu_btn.setVisible(True)
        except Exception:
            pass

    def reveal_game_button(self) -> None:
        """
        函数: reveal_game_button
        作用: 显示顶部的隐藏游戏选择按钮（位于“科学计算器”标题之后）。
        参数:
            无。
        返回:
            无。
        """
        try:
            self.game_btn.setVisible(True)
        except Exception:
            pass

    def _open_moyu_settings(self) -> None:
        """
        函数: _open_moyu_settings
        作用: 兼容旧逻辑占位（保留函数以避免外部调用报错）。不再使用下拉菜单。
        参数:
            无。
        返回:
            无。
        """
        try:
            self._open_moyu_settings_dialog()
        except Exception:
            pass

    def _open_moyu_settings_dialog(self) -> None:
        """
        函数: _open_moyu_settings_dialog
        作用: 点击“设置”按钮后，弹出包含 TXT 目录与极简透明度的设置对话框，
              提供“确定/取消/应用”按钮；确定后应用并隐藏设置按钮。
        参数:
            无。
        返回:
            无。
        """
        try:
            if self.stack.currentWidget() is not self.normal_panel:
                self._switch_to_normal()
            init_path = SettingsService.moyu_path("")
            init_opacity = SettingsService.minimal_opacity_percent(100)
            init_delay = SettingsService.minimal_hover_delay_ms(1500)
            dlg = _MoyuSettingsDialog(self, init_path, init_opacity, init_delay)
            res = dlg.exec()
            if res == QDialog.Accepted:
                theme = getattr(dlg, "selected_scheme", None)
                ok = self._apply_moyu_settings(
                    dlg.path_edit.text().strip(),
                    int(dlg.opacity_spin.value()),
                    hide_button=True,
                    theme=theme,
                    hover_delay_ms=int(getattr(dlg, "hover_delay_spin", None).value()) if hasattr(dlg, "hover_delay_spin") else None,
                )
                if ok:
                    pass
                else:
                    # 验证失败：保持对话框不隐藏设置按钮（用户可再次打开设置）
                    try:
                        self.moyu_btn.setVisible(True)
                    except Exception:
                        pass
            else:
                # 取消：恢复持久化透明度预览，并隐藏设置按钮
                current = SettingsService.minimal_opacity_percent(100)
                try:
                    if hasattr(self.normal_panel, "set_minimal_reader_opacity"):
                        self.normal_panel.set_minimal_reader_opacity(int(current))
                except Exception:
                    pass
                d_saved = SettingsService.minimal_hover_delay_ms(1500)
                try:
                    if hasattr(self.normal_panel, "preview_minimal_reader_hover_delay"):
                        self.normal_panel.preview_minimal_reader_hover_delay(int(d_saved))
                except Exception:
                    pass
                try:
                    theme_saved = self._get_saved_theme_for_preview()
                    if hasattr(self.normal_panel, "preview_minimal_reader_theme"):
                        self.normal_panel.preview_minimal_reader_theme(theme_saved)
                except Exception:
                    pass
                try:
                    self.moyu_btn.setVisible(False)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_moyu_settings(self, path: str, opacity: int, hide_button: bool, theme: dict | None = None, hover_delay_ms: int | None = None) -> bool:
        """
        函数: _apply_moyu_settings
        作用: 应用摸鱼设置：保存路径与透明度，并即时加载/应用效果。
        参数:
            path: TXT 目录路径。
            opacity: 极简阅读透明度（1~100）。
            hide_button: 是否在确认后隐藏设置按钮。
        返回:
            bool: True 表示应用成功；False 表示验证失败（例如路径无效）。
        """
        try:
            # 透明度持久化与即时应用
            p = SettingsService.set_minimal_opacity_percent(int(opacity))
            try:
                if hasattr(self.normal_panel, "set_minimal_reader_opacity"):
                    self.normal_panel.set_minimal_reader_opacity(p)
            except Exception:
                pass
            # 路径校验并加载
            if path:
                if os.path.isdir(path):
                    SettingsService.set_moyu_path(path)
                    if hasattr(self.normal_panel, "load_moyu_texts_from_path"):
                        self.normal_panel.load_moyu_texts_from_path(path)
                else:
                    QMessageBox.warning(self, "错误", f"非有效目录: {path}")
                    return False
            if theme:
                try:
                    if hasattr(self.normal_panel, "set_minimal_reader_theme"):
                        self.normal_panel.set_minimal_reader_theme(theme, persist=True)
                except Exception:
                    pass
            if hover_delay_ms is not None:
                try:
                    if hasattr(self.normal_panel, "set_minimal_reader_hover_delay"):
                        self.normal_panel.set_minimal_reader_hover_delay(int(hover_delay_ms))
                except Exception:
                    pass
            if hide_button:
                try:
                    self._confirm_apply_and_hide_settings("设置已保存")
                except Exception:
                    # 回退：直接隐藏按钮与顶部路径框
                    try:
                        self.moyu_btn.setVisible(False)
                    except Exception:
                        pass
                    try:
                        self.moyu_path_edit.setVisible(False)
                    except Exception:
                        pass
            return True
        except Exception:
            return False

    def _get_saved_theme_for_preview(self) -> dict:
        """
        函数: _get_saved_theme_for_preview
        作用: 从设置读取已保存主题用于取消时的预览恢复。
        参数:
            无。
        返回:
            dict 主题字典。
        """
        try:
            scheme = SettingsService.minimal_theme()
            return {
                "bg": scheme.get("bg", "#F5F5F7"),
                "fg": scheme.get("fg", "#1E1E1E"),
                "accent": scheme.get("accent", "#3B82F6"),
                "name": scheme.get("name", "已保存"),
            }
        except Exception:
            return {"bg": "#F5F5F7", "fg": "#1E1E1E", "accent": "#3B82F6", "name": "默认"}

    def _confirm_moyu_path(self) -> None:
        """
        函数: _confirm_moyu_path
        作用: 从顶部路径框读取目录并交由标准计算器面板加载TXT内容；成功后隐藏路径框与设置按钮。
        参数:
            无。
        返回:
            无。
        """
        try:
            path = self.moyu_path_edit.text().strip()
            if not path:
                QMessageBox.information(self, "提示", "请输入TXT目录路径")
                return
            if not os.path.isdir(path):
                QMessageBox.warning(self, "错误", f"非有效目录: {path}")
                return
            # 调用标准面板加载逻辑
            if hasattr(self.normal_panel, "load_moyu_texts_from_path"):
                self.normal_panel.load_moyu_texts_from_path(path)
            # 成功后隐藏路径框与设置按钮
            self.moyu_path_edit.setVisible(False)
            self.moyu_btn.setVisible(False)
        except Exception:
            pass

    def _shortcut_quick_moyu(self) -> None:
        """
        函数: _shortcut_quick_moyu
        作用: 处理 Ctrl+M 快捷键；若存在已保存路径，直接进入标准计算器并显示对应TXT内容；否则显示顶部路径输入框。
        参数:
            无。
        返回:
            无。
        """
        try:
            # 切到标准计算器以便显示摸鱼文本窗口
            if self.stack.currentWidget() is not self.normal_panel:
                self._switch_to_normal()
            # 尝试读取持久化路径
            saved = SettingsService.moyu_path("")
            if saved and os.path.isdir(saved):
                last = SettingsService.moyu_last_file("")
                try:
                    if last:
                        fp = os.path.join(saved, last)
                        if os.path.isfile(fp):
                            try:
                                setattr(self.normal_panel, "_moyu_force_file", str(last))
                            except Exception:
                                pass
                except Exception:
                    pass
                if hasattr(self.normal_panel, "load_moyu_texts_from_path"):
                    self.normal_panel.load_moyu_texts_from_path(saved)
                # 保持顶部路径框隐藏，用户需要再配置时可点击“设置”
                self.moyu_path_edit.setVisible(False)
            else:
                # 未保存路径或路径无效，引导用户输入
                self.moyu_path_edit.setVisible(True)
                self.moyu_path_edit.setFocus()
        except Exception:
            pass

    def _shortcut_exit_moyu(self) -> None:
        """
        函数: _shortcut_exit_moyu
        作用: 处理 Esc 快捷键；退出摸鱼模式，隐藏TXT窗口与顶部路径框，恢复正常计算。
        参数:
            无。
        返回:
            无。
        """
        try:
            # 退出摸鱼模式标志（用于帮助说明恢复）
            if hasattr(self.normal_panel, "set_moyu_mode"):
                try:
                    self.normal_panel.set_moyu_mode(False)
                except Exception:
                    pass
            # 退出前先保存当前页码，便于下次恢复
            if hasattr(self.normal_panel, "save_moyu_current_page"):
                try:
                    self.normal_panel.save_moyu_current_page()
                except Exception:
                    pass
            # 退出摸鱼时进行伪装：显示随机数学公式，隐藏页码
            if hasattr(self.normal_panel, "show_moyu_disguise"):
                try:
                    self.normal_panel.show_moyu_disguise()
                except Exception:
                    # 回退策略：若伪装失败则仍隐藏文本视图
                    if hasattr(self.normal_panel, "moyu_view"):
                        self.normal_panel.moyu_view.setVisible(False)
            elif hasattr(self.normal_panel, "moyu_view"):
                # 无伪装能力时回退为隐藏
                self.normal_panel.moyu_view.setVisible(False)
            # 隐藏标准面板内的路径框（若存在且可见）
            if hasattr(self.normal_panel, "moyu_path_edit"):
                try:
                    self.normal_panel.moyu_path_edit.setVisible(False)
                except Exception:
                    pass
            # 隐藏页码标签（伪装文本不显示页码）
            if hasattr(self.normal_panel, "moyu_page_label"):
                try:
                    self.normal_panel.moyu_page_label.setVisible(False)
                except Exception:
                    pass
            self.moyu_path_edit.setVisible(False)
            # 保持当前模式不变（若用户在标准模式则继续保留）
        except Exception:
            pass

    def _toggle_pin(self) -> None:
        """
        函数: _toggle_pin
        作用: 切换窗口置顶状态（始终在最上层）。
        参数:
            无。
        返回:
            无。
        """
        self._apply_pin(not self.pin_on_top)

    def _apply_theme(self, dark: bool) -> None:
        """
        函数: _apply_theme
        作用: 根据布尔值选择并应用浅色或深色 QSS 样式。
        参数:
            dark: True 表示应用深色主题，False 表示浅色主题。
        返回:
            无。
        """
        app = QApplication.instance()
        if app is None:
            return
        qss_name = "style_dark.qss" if dark else "style.qss"
        qss = self._read_qss(qss_name)
        if qss:
            app.setStyleSheet(qss)
            self.dark_mode = dark
            # 持久化主题选择
            SettingsService.set_dark_mode(dark)
            self._update_theme_button_label()
            # 主题切换后重算摸鱼区域高度，避免字体变化导致三行显示不完整
            try:
                if hasattr(self.normal_panel, "adjust_moyu_box_height"):
                    self.normal_panel.adjust_moyu_box_height()
            except Exception:
                pass
            # 同步 Windows 标题栏颜色
            try:
                self._apply_windows_dark_titlebar(dark)
            except Exception:
                pass
            # 同步标题栏三键图标颜色（尤其是最小化短横线）
            try:
                self.min_btn.setIcon(self._make_caption_icon("min"))
                self.max_btn.setIcon(self._make_caption_icon("restore" if self.isMaximized() else "max"))
                self.close_btn.setIcon(self._make_caption_icon("close"))
            except Exception:
                pass

    def _apply_pin(self, on_top: bool) -> None:
        """
        函数: _apply_pin
        作用: 应用窗口置顶状态（WindowStaysOnTopHint），并持久化设置。
        参数:
            on_top: True 表示置顶，False 表示取消置顶。
        返回:
            无。
        """
        self.pin_on_top = on_top
        # Windows 下优先使用 Win32 API 切换置顶，避免窗口重建导致的闪烁
        applied = False
        if sys.platform.startswith("win"):
            applied = self._set_topmost_win32(on_top)
        if not applied:
            # 其他平台或 Win32 调用失败时，回退到 Qt 标志位方案
            self.setWindowFlag(Qt.WindowStaysOnTopHint, on_top)
            try:
                self.show()
            except Exception:
                pass
        SettingsService.set_always_on_top(on_top)
        # 保持按钮选中状态与文案同步
        try:
            self.pin_btn.setChecked(on_top)
        except Exception:
            pass
        self._update_pin_button_label()
        # 主程序置顶时，取消极简窗口置顶；避免两者抢占前台
        try:
            if on_top:
                if hasattr(self, "normal_panel") and hasattr(self.normal_panel, "_minimal_reader"):
                    dlg = getattr(self.normal_panel, "_minimal_reader")
                    if dlg is not None:
                        try:
                            dlg.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                            dlg.show()
                        except Exception:
                            pass
        except Exception:
            pass

        # 与所有小游戏窗口置顶互斥：
        # - 主窗置顶时取消所有已打开小游戏置顶；主窗取消置顶时恢复小游戏置顶
        try:
            if hasattr(self, "scientific_panel"):
                for name in ("_game_2048_dialog", "_game_snake_dialog", "_game_minesweeper_dialog", "_game_gomoku_dialog"):
                    try:
                        dlg = getattr(self.scientific_panel, name, None)
                    except Exception:
                        dlg = None
                    if dlg is not None:
                        try:
                            dlg.setWindowFlag(Qt.WindowStaysOnTopHint, not on_top)
                            dlg.show()
                        except Exception:
                            pass
        except Exception:
            pass

    def _set_topmost_win32(self, on_top: bool) -> bool:
        """
        函数: _set_topmost_win32
        作用: 在 Windows 平台通过 Win32 API 无闪烁地切换窗口置顶状态。
        参数:
            on_top: True 表示置顶（TOPMOST），False 表示取消置顶（NOTOPMOST）。
        返回:
            True 表示已成功通过 Win32 API 应用；False 表示失败或非 Windows 平台。
        """
        try:
            # 常量定义
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            hwnd = int(self.winId())
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            hpos = HWND_TOPMOST if on_top else HWND_NOTOPMOST
            res = ctypes.windll.user32.SetWindowPos(hwnd, hpos, 0, 0, 0, 0, flags)
            return bool(res)
        except Exception:
            return False

    def _read_qss(self, file_name: str) -> str:
        """
        函数: _read_qss
        作用: 读取 resources 目录下的 QSS 文件内容。
        参数:
            file_name: QSS 文件名，例如 "style.qss" 或 "style_dark.qss"。
        返回:
            读取到的样式字符串，若失败则返回空字符串。
        """
        # 兼容开发与打包后的资源路径
        if hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        qss_path = os.path.join(base_dir, "resources", file_name)
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _apply_windows_dark_titlebar(self, dark: bool) -> None:
        """
        函数: _apply_windows_dark_titlebar
        作用: 在 Windows 10/11 上切换沉浸式深色标题栏，使其与页面主题一致。
        参数:
            dark: True 使用深色标题栏；False 使用浅色标题栏。
        返回:
            无。
        """
        if not sys.platform.startswith("win"):
            return
        try:
            hwnd = int(self.winId())
        except Exception:
            return
        # 应用层偏好：优先开启应用暗色模式（Win10 1809+）
        try:
            uxtheme = ctypes.windll.uxtheme
            if hasattr(uxtheme, "SetPreferredAppMode"):
                # 2=ForceDark, 1=AllowDarkMode；浅色时回退为 Allow 以跟随系统
                uxtheme.SetPreferredAppMode(2 if dark else 1)
        except Exception:
            pass
        # 允许窗口使用暗色标题栏
        try:
            uxtheme = ctypes.windll.uxtheme
            if hasattr(uxtheme, "AllowDarkModeForWindow"):
                uxtheme.AllowDarkModeForWindow(hwnd, 1 if dark else 0)
        except Exception:
            pass
        # DWM 属性：优先 20，再尝试 19；分别测试 int 与 bool 形参
        try:
            val_i = ctypes.c_int(1 if dark else 0)
            sz_i = ctypes.sizeof(ctypes.c_int)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val_i), sz_i)
            return
        except Exception:
            pass
        try:
            val_b = ctypes.c_bool(bool(dark))
            sz_b = ctypes.sizeof(ctypes.c_bool)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val_b), sz_b)
            return
        except Exception:
            pass
        try:
            val_i = ctypes.c_int(1 if dark else 0)
            sz_i = ctypes.sizeof(ctypes.c_int)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val_i), sz_i)
        except Exception:
            pass

    def _make_yinyang_icon(self, angle: int = 0) -> QIcon:
        """
        函数: _make_yinyang_icon
        作用: 生成“☯”图标：带圆形底纹、半透明描边、抗锯齿，并按角度旋转（用于日/夜切换按钮）。
        参数:
            angle: 旋转角度（0 或 180）。
        返回:
            QIcon 图标对象。
        """
        # 以按钮当前 iconSize 为基准，确保与“?”按钮一致
        icon_sz = self.theme_btn.iconSize()
        size = max(16, max(icon_sz.width(), icon_sz.height()))
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # 底纹：使用按钮颜色并根据主题进行明暗调整
        pal = self.palette()
        bg = pal.color(QPalette.Button)
        if self.dark_mode:
            bg = bg.lighter(120)  # 暗色下略提亮
        else:
            bg = bg.darker(115)   # 浅色下略加深
        painter.setBrush(bg)
        edge_col = bg.darker(130)
        edge_col.setAlpha(140)
        painter.setPen(QPen(edge_col, 1))
        painter.drawEllipse(pix.rect().adjusted(2, 2, -2, -2))

        # 前景：根据主题选择高对比色，并使用半透明描边
        fg = QColor(255, 255, 255) if self.dark_mode else QColor(0, 0, 0)
        outline = QColor(fg)
        outline.setAlpha(120)
        font = QFont()
        # 字体大小按尺寸比例设置
        font.setPointSize(int(size * 0.82))
        metrics = QFontMetrics(font)
        path = QPainterPath()
        # 先在 (0, ascent) 处创建路径，再整体居中平移
        path.addText(0, metrics.ascent(), font, "☯")
        rectp = path.boundingRect()
        dx = (size - rectp.width()) / 2 - rectp.x()
        dy = (size - rectp.height()) / 2 - rectp.y()
        path.translate(dx, dy)

        painter.setBrush(fg)
        painter.setPen(QPen(outline, 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
        painter.end()
        if angle % 360 != 0:
            tfm = QTransform()
            tfm.rotate(angle)
            pix = pix.transformed(tfm)
        return QIcon(pix)

    def _make_caption_icon(self, kind: str) -> QIcon:
        """
        函数: _make_caption_icon
        作用: 生成标题栏系统按钮的小型图标（目前支持 minimize），
              使用短横线以降低突兀感，并随主题切换颜色。
        参数:
            kind: 图标类型（"min"）。
        返回:
            QIcon 图标对象。
        """
        sz_w, sz_h = self._system_caption_button_size()
        size = max(16, int(sz_h * 0.9))
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        try:
            p.setRenderHint(QPainter.Antialiasing, True)
            col = QColor(255, 255, 255) if self.dark_mode else QColor(0, 0, 0)
            # 在深色下略提亮，浅色下略加深
            if self.dark_mode:
                col = col.lighter(110)
            else:
                col = col.darker(130)
            pen = QPen(col, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
            try:
                pen.setWidthF(1.2)
            except Exception:
                pass
            p.setPen(pen)
            if kind == "min":
                # 短横线：长度为图标宽度的 50%，居中，垂直位置略靠下
                w = int(size * 0.50)
                x = int((size - w) / 2)
                y = int(size * 0.50)
                p.drawLine(x, y, x + w, y)
            elif kind == "max":
                # 正方形边框，略大以提升存在感
                w = int(size * 0.68)
                x = int((size - w) / 2)
                y = x
                p.drawRect(x, y, w, w)
            elif kind == "restore":
                # 两个重叠方框，模拟系统还原图标
                w = int(size * 0.60)
                d = int(size * 0.14)
                x = int((size - w) / 2)
                y = x
                # 背后方框（左上偏移）
                p.drawRect(x - d, y - d, w, w)
                # 前方框
                p.drawRect(x, y, w, w)
            elif kind == "close":
                # 关闭图标：对角短线交叉，边距留白，避免过度刺眼
                m = int(size * 0.28)
                p.drawLine(m, m, size - m, size - m)
                p.drawLine(size - m, m, m, size - m)
        finally:
            p.end()
        return QIcon(pix)

    def _update_pin_button_label(self) -> None:
        """
        函数: _update_pin_button_label
        作用: 根据置顶状态更新置顶按钮文本与提示。
        参数:
            无。
        返回:
            无。
        """
        if self.pin_on_top:
            self.pin_btn.setText("📌")
            self.pin_btn.setToolTip("取消置顶")
        else:
            self.pin_btn.setText("📍")
            self.pin_btn.setToolTip("置顶到最前")
    def _setup_moyu_menu(self) -> None:
        """
        函数: _setup_moyu_menu
        作用: 旧实现保留（不再使用），防止外部引用报错。
        参数:
            无。
        返回:
            无。
        """
        try:
            self._moyu_menu = None
            self._moyu_path_in_menu = None
        except Exception:
            pass

    def _on_moyu_menu_load_path(self) -> None:
        """
        函数: _on_moyu_menu_load_path
        作用: 旧实现保留（不再使用）。
        参数:
            无。
        返回:
            无。
        """
        try:
            pass
        except Exception:
            pass

    def _on_moyu_menu_opacity(self) -> None:
        """
        函数: _on_moyu_menu_opacity
        作用: 旧实现保留（不再使用）。
        参数:
            无。
        返回:
            无。
        """
        try:
            pass
        except Exception:
            pass

    def _confirm_apply_and_hide_settings(self, text: str) -> None:
        """
        函数: _confirm_apply_and_hide_settings
        作用: 弹窗提示设置已应用；点击确认后隐藏“设置”按钮与路径框，下次需再次输入密钥显示。
        参数:
            text: 提示文本。
        返回:
            无。
        """
        try:
            QMessageBox.information(self, "提示", text)
        except Exception:
            pass
        try:
            self.moyu_btn.setVisible(False)
        except Exception:
            pass
        try:
            self.moyu_path_edit.setVisible(False)
        except Exception:
            pass
        try:
            if hasattr(self, "_moyu_menu") and self._moyu_menu is not None:
                self._moyu_menu.close()
        except Exception:
            pass

    def _open_game_selector_via_scientific(self) -> None:
        """
        函数: _open_game_selector_via_scientific
        作用: 通过主窗口顶部按钮调用科学面板的游戏选择窗口，必要时切换到科学模式。
        参数:
            无。
        返回:
            无。
        """
        try:
            if self.stack.currentWidget() is not self.scientific_panel:
                self._switch_to_scientific()
            if hasattr(self.scientific_panel, "open_game_selector"):
                self.scientific_panel.open_game_selector()
            elif hasattr(self.scientific_panel, "_open_game_selector"):
                self.scientific_panel._open_game_selector()
        except Exception:
            pass
    def showEvent(self, event) -> None:
        """
        函数: showEvent
        作用: 窗口显示后再次尝试应用 Windows 标题栏暗色属性与边框设置，
              部分 Win10 版本需要窗口可见后调用才会生效。
        参数:
            event: 显示事件。
        返回:
            无。
        """
        try:
            super().showEvent(event)
        except Exception:
            pass
        try:
            self._apply_windows_dark_titlebar(self.dark_mode)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """
        函数: eventFilter
        作用: 处理自绘标题栏的拖动与双击最大化，以及边缘系统缩放。
        参数:
            obj: 事件源对象。
            event: 事件。
        返回:
            bool: True 表示事件已处理。
        """
        try:
            if obj is getattr(self, "_title_bar", None):
                et = event.type()
                if et == event.Type.MouseButtonDblClick:
                    self._on_toggle_max_restore()
                    return True
                if et == event.Type.MouseButtonPress and event.button() == Qt.LeftButton:
                    try:
                        wh = self.windowHandle()
                        if wh is not None:
                            wh.startSystemMove()
                            return True
                    except Exception:
                        pass
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event) -> None:
        """
        函数: mousePressEvent
        作用: 在无边框模式下，按住窗口边缘发起系统缩放（支持四边与四角）。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            if event.button() == Qt.LeftButton:
                edges = self._edges_for_pos(event.pos())
                if int(edges) != 0:
                    wh = self.windowHandle()
                    if wh is not None:
                        try:
                            wh.startSystemResize(edges)
                            return
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            super().mousePressEvent(event)
        except Exception:
            pass

    def mouseMoveEvent(self, event) -> None:
        """
        函数: mouseMoveEvent
        作用: 根据鼠标靠近边缘的位置显示对应的缩放光标形状。
        参数:
            event: 鼠标事件。
        返回:
            无。
        """
        try:
            edges = self._edges_for_pos(event.pos())
            self._apply_resize_cursor(edges)
        except Exception:
            pass
        try:
            super().mouseMoveEvent(event)
        except Exception:
            pass

    def leaveEvent(self, event) -> None:
        """
        函数: leaveEvent
        作用: 鼠标离开窗口时恢复普通光标。
        参数:
            event: 离开事件。
        返回:
            无。
        """
        try:
            self.unsetCursor()
        except Exception:
            pass
        try:
            super().leaveEvent(event)
        except Exception:
            pass

    def _edges_for_pos(self, pos) -> Qt.Edges:
        """
        函数: _edges_for_pos
        作用: 命中测试，返回靠近的窗口边缘组合，用于系统缩放。
        参数:
            pos: 鼠标位置（相对窗口）。
        返回:
            Qt.Edges: 需要缩放的边缘组合。
        """
        try:
            m = 6
            r = self.rect()
            left = pos.x() <= m
            right = (r.width() - pos.x()) <= m
            top = pos.y() <= m
            bottom = (r.height() - pos.y()) <= m
            edges = Qt.Edges()
            if left:
                edges |= Qt.LeftEdge
            if right:
                edges |= Qt.RightEdge
            if top:
                edges |= Qt.TopEdge
            if bottom:
                edges |= Qt.BottomEdge
            return edges
        except Exception:
            return Qt.Edges()

    def _apply_resize_cursor(self, edges: Qt.Edges) -> None:
        """
        函数: _apply_resize_cursor
        作用: 根据边缘组合设置合适的系统缩放光标。
        参数:
            edges: 命中边缘组合。
        返回:
            无。
        """
        try:
            e = int(edges)
            if e == 0:
                self.unsetCursor()
                return
            left = bool(edges & Qt.LeftEdge)
            right = bool(edges & Qt.RightEdge)
            top = bool(edges & Qt.TopEdge)
            bottom = bool(edges & Qt.BottomEdge)
            if (left and top) or (right and bottom):
                self.setCursor(Qt.SizeFDiagCursor)
            elif (right and top) or (left and bottom):
                self.setCursor(Qt.SizeBDiagCursor)
            elif left or right:
                self.setCursor(Qt.SizeHorCursor)
            elif top or bottom:
                self.setCursor(Qt.SizeVerCursor)
        except Exception:
            pass

    def _enable_frameless_titlebar(self) -> None:
        """
        函数: _enable_frameless_titlebar
        作用: 启用无边框窗口并使用自绘标题栏；支持系统移动与边缘缩放。
        参数:
            无。
        返回:
            无。
        """
        try:
            flags = self.windowFlags() | Qt.FramelessWindowHint | Qt.Window
            self.setWindowFlags(flags)
            try:
                self.show()
            except Exception:
                pass
        except Exception:
            pass

    def _system_caption_height(self) -> int:
        """
        函数: _system_caption_height
        作用: 获取当前 DPI 下的系统标题栏高度，用于 1:1 替换。
        参数:
            无。
        返回:
            int: 像素高度，失败返回 32 的合理默认值。
        """
        if not sys.platform.startswith("win"):
            return 32
        try:
            # 优先使用按窗口 DPI 的度量
            hwnd = int(self.winId())
            try:
                dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
            except Exception:
                dpi = 96
            try:
                SM_CYCAPTION = 4
                h = ctypes.windll.user32.GetSystemMetricsForDpi(SM_CYCAPTION, dpi)
                return int(h)
            except Exception:
                # 回退到默认度量（不考虑 DPI 缩放）
                SM_CYCAPTION = 4
                h = ctypes.windll.user32.GetSystemMetrics(SM_CYCAPTION)
                return int(h)
        except Exception:
            return 32

    def _system_caption_button_size(self) -> tuple:
        """
        函数: _system_caption_button_size
        作用: 获取系统标题栏按钮的标准宽高（按 DPI），用于统一三键尺寸。
        参数:
            无。
        返回:
            (width, height): 像素尺寸，失败返回 (36, 28)。
        """
        if not sys.platform.startswith("win"):
            return (36, 28)
        try:
            hwnd = int(self.winId())
            try:
                dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
            except Exception:
                dpi = 96
            try:
                SM_CXSIZE = 30
                SM_CYSIZE = 31
                w = ctypes.windll.user32.GetSystemMetricsForDpi(SM_CXSIZE, dpi)
                h = ctypes.windll.user32.GetSystemMetricsForDpi(SM_CYSIZE, dpi)
                return (int(w), int(h))
            except Exception:
                SM_CXSIZE = 30
                SM_CYSIZE = 31
                w = ctypes.windll.user32.GetSystemMetrics(SM_CXSIZE)
                h = ctypes.windll.user32.GetSystemMetrics(SM_CYSIZE)
                return (int(w), int(h))
        except Exception:
            return (36, 28)

    def _on_minimize(self) -> None:
        """
        函数: _on_minimize
        作用: 最小化窗口。
        参数:
            无。
        返回:
            无。
        """
        try:
            self.showMinimized()
        except Exception:
            pass

    def _on_toggle_max_restore(self) -> None:
        """
        函数: _on_toggle_max_restore
        作用: 切换窗口最大化与还原。
        参数:
            无。
        返回:
            无。
        """
        try:
            if self.isMaximized():
                self.showNormal()
                try:
                    self.max_btn.setIcon(self._make_caption_icon("max"))
                except Exception:
                    self.max_btn.setText("□")
            else:
                self.showMaximized()
                try:
                    self.max_btn.setIcon(self._make_caption_icon("restore"))
                except Exception:
                    self.max_btn.setText("❐")
        except Exception:
            pass
class _MoyuSettingsDialog(QDialog):
    """
    类: _MoyuSettingsDialog
    作用: 摸鱼设置对话框，提供 TXT 目录与极简透明度输入，
          并包含“确定/取消/应用”按钮。
    """

    def __init__(self, parent: QWidget, init_path: str, init_opacity: int, init_delay_ms: int) -> None:
        """
        函数: __init__
        作用: 初始化设置对话框，填充初始路径与透明度。
        参数:
            parent: 父窗口。
            init_path: 初始 TXT 目录路径。
            init_opacity: 初始透明度（1~100）。
        返回:
            无。
        """
        super().__init__(parent)
        try:
            self.setWindowTitle("摸鱼设置")
        except Exception:
            pass
        self.apply_requested = None
        # 表单
        self.path_edit = QLineEdit(self)
        try:
            self.path_edit.setPlaceholderText("粘贴TXT目录路径后按回车或点击应用")
            if init_path:
                self.path_edit.setText(init_path)
        except Exception:
            pass
        self.opacity_spin = QSpinBox(self)
        try:
            self.opacity_spin.setRange(1, 100)
            val = 1 if int(init_opacity) < 1 else (100 if int(init_opacity) > 100 else int(init_opacity))
            self.opacity_spin.setValue(val)
        except Exception:
            pass
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)
        try:
            form.addRow("TXT目录", self.path_edit)
            form.addRow("极简透明度(1~100)", self.opacity_spin)
            self.hover_delay_spin = QSpinBox(self)
            self.hover_delay_spin.setRange(0, 10000)
            self.hover_delay_spin.setSuffix(" ms")
            self.hover_delay_spin.setValue(int(init_delay_ms))
            form.addRow("移入显示延迟(0~10000 ms)", self.hover_delay_spin)
        except Exception:
            pass
        # 按钮区
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Help, parent=self)
        try:
            btns.accepted.connect(self._on_accept)
            btns.rejected.connect(self.reject)
            help_btn = btns.button(QDialogButtonBox.Help)
            if help_btn is not None:
                help_btn.clicked.connect(self._on_help)
        except Exception:
            pass
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)
        root.addLayout(form)
        # 外观：基础方案网格
        self.selected_scheme = None
        self._custom1_scheme = None
        self._build_appearance_section(root)
        root.addWidget(btns)
        # 透明度实时预览：仅应用到极简窗口显示，不持久化
        try:
            self.opacity_spin.valueChanged.connect(self._on_preview_opacity_change)
        except Exception:
            pass
        try:
            self.hover_delay_spin.valueChanged.connect(self._on_preview_hover_delay_change)
        except Exception:
            pass

    def _on_accept(self) -> None:
        """
        函数: _on_accept
        作用: 处理“确定”事件：先应用设置，再关闭对话框。
        参数:
            无。
        返回:
            无。
        """
        try:
            if callable(self.apply_requested):
                self.apply_requested()
        except Exception:
            pass
        try:
            self.accept()
        except Exception:
            pass

    def _on_help(self) -> None:
        """
        函数: _on_help
        作用: 显示设置参数的详细说明，包括功能、取值范围与默认值。
        参数:
            无。
        返回:
            无。
        """
        try:
            txt = (
                "【参数说明】\n"
                "- TXT目录：指定包含 .txt 文件的本地文件夹；确认后加载并保存路径。\n"
                "  范围：任意有效文件夹路径；默认值：上次保存的路径或为空。\n"
                "- 极简透明度(1~100)：设置极简阅读窗口的不透明度。\n"
                "  范围：1~100；默认值：100。\n"
                "  特例：输入 1 启用透明背景，文本始终半透明 0.9；在设置界面调整时即时预览。\n"
                "- 主题方案：在设置对话框中选择极简窗口主题；边框颜色与背景保持一致。\n"
                "\n"
                "【极简行为说明】\n"
                "- 悬隐：鼠标移入延迟 1.5 秒显示；移出立即渐隐（300ms 动画过渡）。\n"
                "- 唤醒：仅当鼠标靠近窗口边缘或停留窗口区域时唤醒；屏幕边缘不触发。\n"
                "- 尺寸：右下角拖动支持 16px 网格吸附，距屏幕边缘 ≤12px 自动贴靠。\n"
                "- 外观：极简窗口边框颜色与背景一致；右下角尺寸手柄（QSizeGrip）颜色与背景一致。\n"
            )
            QMessageBox.information(self, "帮助", txt)
        except Exception:
            pass

    def _on_preview_opacity_change(self, value: int) -> None:
        """
        函数: _on_preview_opacity_change
        作用: 在对话框中调整透明度时进行即时预览，不持久化。
        参数:
            value: 当前透明度值。
        返回:
            无。
        """
        try:
            p = 1 if int(value) < 1 else (100 if int(value) > 100 else int(value))
            parent = self.parentWidget()
            if parent is not None:
                if hasattr(parent, "normal_panel"):
                    np = parent.normal_panel
                    if hasattr(np, "set_minimal_reader_opacity"):
                        np.set_minimal_reader_opacity(p)
                    theme = getattr(self, "selected_scheme", None)
                    if theme is None:
                        settings = QSettings()
                        bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
                        fg = str(settings.value("minimal_theme_fg", "#1E1E1E", type=str))
                        ac = str(settings.value("minimal_theme_accent", "#3B82F6", type=str))
                        theme = {"bg": bg, "fg": fg, "accent": ac}
                    if hasattr(np, "preview_minimal_reader_theme"):
                        np.preview_minimal_reader_theme(theme)
                if hasattr(parent, "scientific_panel"):
                    sp = parent.scientific_panel
                    if hasattr(sp, "preview_game_2048_opacity"):
                        sp.preview_game_2048_opacity(p)
                    theme = getattr(self, "selected_scheme", None)
                    if theme is None:
                        settings = QSettings()
                        bg = str(settings.value("minimal_theme_bg", "#F5F5F7", type=str))
                        fg = str(settings.value("minimal_theme_fg", "#1E1E1E", type=str))
                        ac = str(settings.value("minimal_theme_accent", "#3B82F6", type=str))
                        theme = {"bg": bg, "fg": fg, "accent": ac}
                    if hasattr(sp, "preview_game_2048_theme"):
                        sp.preview_game_2048_theme(theme)
        except Exception:
            pass
    def _on_preview_hover_delay_change(self, value: int) -> None:
        """
        函数: _on_preview_hover_delay_change
        作用: 在对话框中调整移入显示延迟时进行即时预览，不持久化。
        参数:
            value: 当前延迟毫秒值。
        返回:
            无。
        """
        try:
            parent = self.parentWidget()
            if parent is not None and hasattr(parent, "normal_panel"):
                np = parent.normal_panel
                if hasattr(np, "preview_minimal_reader_hover_delay"):
                    np.preview_minimal_reader_hover_delay(int(value))
        except Exception:
            pass

    def _build_appearance_section(self, parent_layout: QVBoxLayout) -> None:
        """
        函数: _build_appearance_section
        作用: 构建“外观”分类，包含基础方案网格、进阶折叠与自定义颜色。
        参数:
            parent_layout: 对话框根布局。
        返回:
            无。
        """
        self._schemes_basic = [
            {"id": "day", "name": "白天默认", "emoji": "🌞", "bg": "#FDF6E3", "fg": "#1F2937", "accent": "#D97706"},
            {"id": "night", "name": "夜间护眼", "emoji": "🌙", "bg": "#0F172A", "fg": "#F1F5F9", "accent": "#60A5FA"},
            {"id": "paper", "name": "纸质仿真", "emoji": "📜", "bg": "#F4ECD8", "fg": "#2D1B1B", "accent": "#B85450"},
            {"id": "stealth", "name": "摸鱼隐蔽", "emoji": "🕶️", "bg": "#F8FAFC", "fg": "#334155", "accent": "#64748B"},
        ]
        self._schemes_adv = [
            {"id": "green", "name": "护眼绿色", "emoji": "🌿", "bg": "#F0FDF4", "fg": "#14532D", "accent": "#16A34A"},
            {"id": "contrast", "name": "专业学术", "emoji": "🎓", "bg": "#EFF6FF", "fg": "#1F2937", "accent": "#2563EB"},
            {"id": "dark", "name": "现代科技", "emoji": "💻", "bg": "#111827", "fg": "#F3F4F6", "accent": "#2DD4BF"},
            {"id": "pink", "name": "柔和粉色", "emoji": "🌸", "bg": "#FFF1F2", "fg": "#1F2937", "accent": "#F43F5E"},
        ]
        box = QVBoxLayout()
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)
        lbl = QLabel("外观")
        box.addWidget(lbl)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        self._scheme_buttons_basic = []
        for i, sc in enumerate(self._schemes_basic):
            btn = QToolButton(self)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.setIcon(self._make_swatch_icon(sc["bg"], sc["accent"], False))
            btn.setText(f"{sc['emoji']} {sc['name']}")
            btn.clicked.connect(lambda checked=False, s=sc: self._on_select_scheme(s))
            r = i // 2
            c = i % 2
            grid.addWidget(btn, r, c)
            self._scheme_buttons_basic.append((btn, sc))
        box.addLayout(grid)
        # 进阶方案（不折叠，直接展示）
        box.addWidget(QLabel("进阶方案"))
        adv = QWidget(self)
        adv_l = QGridLayout(adv)
        adv_l.setContentsMargins(0, 0, 0, 0)
        adv_l.setSpacing(6)
        self._scheme_buttons_adv = []
        for i, sc in enumerate(self._schemes_adv):
            btn = QToolButton(self)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.setIcon(self._make_swatch_icon(sc["bg"], sc["accent"], False))
            btn.setText(f"{sc['emoji']} {sc['name']}")
            btn.clicked.connect(lambda checked=False, s=sc: self._on_select_scheme(s))
            r = i // 2
            c = i % 2
            adv_l.addWidget(btn, r, c)
            self._scheme_buttons_adv.append((btn, sc))
        adv.setVisible(True)
        box.addWidget(adv)
        # 自定义
        cust_box = QFormLayout()
        cust_box.setContentsMargins(0, 0, 0, 0)
        cust_box.setSpacing(6)
        self.custom_bg = QLineEdit(self)
        self.custom_fg = QLineEdit(self)
        self.custom_accent = QLineEdit(self)
        pick_bg = QPushButton("选择背景", self)
        pick_fg = QPushButton("选择文本", self)
        pick_ac = QPushButton("选择强调", self)
        pick_bg.clicked.connect(lambda: self._pick_color(self.custom_bg))
        pick_fg.clicked.connect(lambda: self._pick_color(self.custom_fg))
        pick_ac.clicked.connect(lambda: self._pick_color(self.custom_accent))
        bg_row = QHBoxLayout()
        bg_row.addWidget(self.custom_bg)
        bg_row.addWidget(pick_bg)
        fg_row = QHBoxLayout()
        fg_row.addWidget(self.custom_fg)
        fg_row.addWidget(pick_fg)
        ac_row = QHBoxLayout()
        ac_row.addWidget(self.custom_accent)
        ac_row.addWidget(pick_ac)
        cust_box.addRow("自定义背景", bg_row)
        cust_box.addRow("自定义文本", fg_row)
        cust_box.addRow("自定义强调", ac_row)
        save_btn = QPushButton("保存为自定义方案", self)
        save_btn.clicked.connect(self._on_save_custom)
        box.addLayout(cust_box)
        box.addWidget(save_btn)
        try:
            settings = QSettings()
            c_bg = str(settings.value("minimal_theme_custom1_bg", "", type=str))
            c_fg = str(settings.value("minimal_theme_custom1_fg", "", type=str))
            c_ac = str(settings.value("minimal_theme_custom1_accent", "", type=str))
            has_custom = bool(c_bg and c_fg and c_ac)
        except Exception:
            c_bg = c_fg = c_ac = ""
            has_custom = False
        custom1_row = QHBoxLayout()
        custom1_lbl = QLabel("已保存自定义方案")
        self._btn_custom1 = QToolButton(self)
        self._btn_custom1.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._btn_custom1.setEnabled(has_custom)
        if has_custom:
            self._btn_custom1.setIcon(self._make_swatch_icon(c_bg, c_ac, False))
            self._btn_custom1.setText("🎨 自定义方案")
            sc = {"id": "custom1", "name": "自定义方案", "emoji": "🎨", "bg": c_bg, "fg": c_fg, "accent": c_ac}
            self._custom1_scheme = dict(sc)
            self._btn_custom1.clicked.connect(lambda checked=False, s=sc: self._on_select_scheme(s))
        else:
            self._btn_custom1.setText("暂无已保存")
            self._custom1_scheme = None
        custom1_row.addWidget(custom1_lbl)
        custom1_row.addWidget(self._btn_custom1)
        box.addLayout(custom1_row)
        cont = QFrame(self)
        cont.setLayout(box)
        parent_layout.addWidget(cont)

    def _make_swatch_icon(self, bg: str, accent: str, checked: bool = False) -> QIcon:
        """
        函数: _make_swatch_icon
        作用: 创建 16x16 色块图标，背景用 bg，边框用 accent；选中时在色块上打勾。
        参数:
            bg: 背景色HEX。
            accent: 强调色HEX。
            checked: 是否显示选中勾。
        返回:
            QIcon 图标。
        """
        try:
            pix = QPixmap(16, 16)
            pix.fill(QColor(bg))
            p = QPainter(pix)
            pen = QPen(QColor(accent))
            pen.setWidth(2)
            p.setPen(pen)
            p.drawRect(1, 1, 14, 14)
            if checked:
                # 勾选颜色：优先用强调色，若与背景对比度不足则选黑/白中对比更高者
                chk_color = QColor(accent)
                try:
                    if self._contrast_ratio(bg, accent) < 3.0:
                        c_black = self._contrast_ratio(bg, "#000000")
                        c_white = self._contrast_ratio(bg, "#FFFFFF")
                        chk_color = QColor("#000000" if c_black >= c_white else "#FFFFFF")
                except Exception:
                    pass
                pen2 = QPen(chk_color)
                pen2.setWidth(2)
                p.setPen(pen2)
                # 画一个简单的对号
                p.drawLine(4, 9, 7, 12)
                p.drawLine(7, 12, 12, 5)
            p.end()
            return QIcon(pix)
        except Exception:
            return QIcon()

    def _on_select_scheme(self, scheme: dict) -> None:
        """
        函数: _on_select_scheme
        作用: 选择并即时应用配色方案，标记为已应用。
        参数:
            scheme: 方案字典。
        返回:
            无。
        """
        try:
            self.selected_scheme = dict(scheme)
            parent = self.parentWidget()
            if parent is not None:
                if hasattr(parent, "normal_panel"):
                    parent.normal_panel.preview_minimal_reader_theme(self.selected_scheme)
                if hasattr(parent, "scientific_panel"):
                    parent.scientific_panel.preview_game_2048_theme(self.selected_scheme)
            self._refresh_scheme_icons(str(scheme.get("id", "")))
        except Exception:
            pass

    def _refresh_scheme_icons(self, selected_id: str) -> None:
        """
        函数: _refresh_scheme_icons
        作用: 刷新所有方案按钮图标勾选状态（基础/进阶/自定义）。
        参数:
            selected_id: 当前选中的方案 id。
        返回:
            无。
        """
        sid = str(selected_id or "").strip()
        try:
            for btn, sc in getattr(self, "_scheme_buttons_basic", []):
                checked = str(sc.get("id", "")) == sid
                btn.setIcon(self._make_swatch_icon(sc["bg"], sc["accent"], checked))
                btn.setText(f"{sc['emoji']} {sc['name']}")
        except Exception:
            pass
        try:
            for btn, sc in getattr(self, "_scheme_buttons_adv", []):
                checked = str(sc.get("id", "")) == sid
                btn.setIcon(self._make_swatch_icon(sc["bg"], sc["accent"], checked))
                btn.setText(f"{sc['emoji']} {sc['name']}")
        except Exception:
            pass
        try:
            btn = getattr(self, "_btn_custom1", None)
            sc = getattr(self, "_custom1_scheme", None)
            if btn is not None and isinstance(sc, dict):
                checked = str(sc.get("id", "")) == sid
                btn.setIcon(self._make_swatch_icon(str(sc.get("bg", "#F5F5F7")), str(sc.get("accent", "#3B82F6")), checked))
                btn.setText(f"{sc.get('emoji', '🎨')} {sc.get('name', '自定义方案')}")
        except Exception:
            pass

    def _pick_color(self, target_edit: QLineEdit) -> None:
        """
        函数: _pick_color
        作用: 打开颜色选择器，将选择结果写入目标输入框并预览。
        参数:
            target_edit: 目标输入框。
        返回:
            无。
        """
        try:
            col = QColorDialog.getColor(QColor(target_edit.text() or "#FFFFFF"), self, "选择颜色")
            if col.isValid():
                target_edit.setText(col.name())
                self._preview_custom_current()
        except Exception:
            pass

    def _preview_custom_current(self) -> None:
        """
        函数: _preview_custom_current
        作用: 读取自定义颜色并进行预览，非法输入忽略。
        参数:
            无。
        返回:
            无。
        """
        try:
            bg = self.custom_bg.text().strip()
            fg = self.custom_fg.text().strip()
            ac = self.custom_accent.text().strip() or "#3B82F6"
            if not (self._valid_color(bg) and self._valid_color(fg) and self._valid_color(ac)):
                return
            scheme = {"id": "custom1", "name": "自定义方案1", "emoji": "🎨", "bg": bg, "fg": fg, "accent": ac}
            parent = self.parentWidget()
            if parent is not None:
                if hasattr(parent, "normal_panel"):
                    parent.normal_panel.preview_minimal_reader_theme(scheme)
                if hasattr(parent, "scientific_panel"):
                    parent.scientific_panel.preview_game_2048_theme(scheme)
            self.selected_scheme = scheme
        except Exception:
            pass

    def _on_save_custom(self) -> None:
        """
        函数: _on_save_custom
        作用: 持久化保存自定义配色方案，要求符合对比度标准。
        参数:
            无。
        返回:
            无。
        """
        try:
            bg = self.custom_bg.text().strip()
            fg = self.custom_fg.text().strip()
            ac = self.custom_accent.text().strip() or "#3B82F6"
            if not (self._valid_color(bg) and self._valid_color(fg) and self._valid_color(ac)):
                QMessageBox.warning(self, "错误", "请输入有效 HEX/RGB 颜色值")
                return
            if self._contrast_ratio(bg, fg) < 4.5:
                QMessageBox.warning(self, "错误", "颜色对比度未达 AA 标准 (≥4.5)")
                return
            settings = QSettings()
            settings.setValue("minimal_theme_custom1_bg", bg)
            settings.setValue("minimal_theme_custom1_fg", fg)
            settings.setValue("minimal_theme_custom1_accent", ac)
            self.selected_scheme = {"id": "custom1", "name": "自定义方案1", "emoji": "🎨", "bg": bg, "fg": fg, "accent": ac}
            self._custom1_scheme = dict(self.selected_scheme)
            try:
                if hasattr(self, "_btn_custom1") and self._btn_custom1 is not None:
                    self._btn_custom1.setEnabled(True)
                    self._btn_custom1.setText("🎨 自定义方案1")
                    sc = dict(self.selected_scheme)
                    try:
                        for c in self._btn_custom1.clicked.connections():
                            pass
                    except Exception:
                        pass
                    try:
                        self._btn_custom1.clicked.disconnect()
                    except Exception:
                        pass
                    self._btn_custom1.clicked.connect(lambda checked=False, s=sc: self._on_select_scheme(s))
            except Exception:
                pass
            try:
                self._refresh_scheme_icons("custom1")
            except Exception:
                pass
            QMessageBox.information(self, "提示", "自定义方案已保存")
        except Exception:
            pass

    def _valid_color(self, s: str) -> bool:
        """
        函数: _valid_color
        作用: 判断字符串是否为合法的 HEX 或 rgb(r,g,b) 颜色。
        参数:
            s: 输入字符串。
        返回:
            bool。
        """
        try:
            if not s:
                return False
            if s.startswith("#") and len(s) in (4, 7):
                return True
            t = s.lower().replace(" ", "")
            if t.startswith("rgb(") and t.endswith(")"):
                parts = t[4:-1].split(",")
                if len(parts) == 3:
                    vals = [int(x) for x in parts]
                    return all(0 <= v <= 255 for v in vals)
            return False
        except Exception:
            return False

    def _contrast_ratio(self, bg: str, fg: str) -> float:
        """
        函数: _contrast_ratio
        作用: 计算两颜色的对比度，依据 WCAG 2.1。
        参数:
            bg: 背景色。
            fg: 文本色。
        返回:
            浮点对比度值。
        """
        try:
            def to_rgb(s):
                if s.startswith("#"):
                    c = QColor(s)
                    return (c.red(), c.green(), c.blue())
                t = s.lower().replace(" ", "")
                if t.startswith("rgb(") and t.endswith(")"):
                    p = [int(x) for x in t[4:-1].split(",")]
                    return (p[0], p[1], p[2])
                c = QColor(s)
                return (c.red(), c.green(), c.blue())
            def rel_lum(rgb):
                def f(u):
                    u = u / 255.0
                    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
                r, g, b = rgb
                return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
            L1 = rel_lum(to_rgb(fg))
            L2 = rel_lum(to_rgb(bg))
            if L1 < L2:
                L1, L2 = L2, L1
            return (L1 + 0.05) / (L2 + 0.05)
        except Exception:
            return 0.0
