"""
模块: services
作用: 集中管理小游戏的悬隐与主题参数与对话框配色，统一读取 QSettings 并提供默认值与钳制。
"""

from typing import Optional
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox


class HoverConfig:
    """
    类: HoverConfig
    作用: 提供悬隐相关配置的集中读取接口。
    参数:
        无。
    返回:
        无。
    """

    @staticmethod
    def delay_ms() -> int:
        """
        函数: delay_ms
        作用: 获取悬隐显示延迟毫秒数，读取键 `minimal_hover_delay_ms` 并进行 0~10000 钳制。
        参数:
            无。
        返回:
            延迟毫秒数。
        """
        try:
            settings = QSettings()
            v = int(settings.value("minimal_hover_delay_ms", 1500, type=int))
        except Exception:
            v = 1500
        return 0 if v < 0 else (10000 if v > 10000 else v)

    @staticmethod
    def hidden_opacity() -> float:
        """
        函数: hidden_opacity
        作用: 获取悬隐隐藏状态的不透明度值，读取键 `minimal_hover_hidden_opacity`，默认 0.06，并钳制到 0.0~1.0。
        参数:
            无。
        返回:
            不透明度。
        """
        try:
            settings = QSettings()
            v = float(settings.value("minimal_hover_hidden_opacity", 0.06))
        except Exception:
            v = 0.06
        if v < 0.0:
            v = 0.0
        if v > 1.0:
            v = 1.0
        return v

    @staticmethod
    def edge_margin_px() -> int:
        """
        函数: edge_margin_px
        作用: 获取窗口边缘唤醒的边距像素，读取键 `minimal_hover_window_edge_px`，默认 10，并钳制到 0~48。
        参数:
            无。
        返回:
            边距像素。
        """
        try:
            settings = QSettings()
            v = int(settings.value("minimal_hover_window_edge_px", 10, type=int))
        except Exception:
            v = 10
        return 0 if v < 0 else (48 if v > 48 else v)


def apply_message_box_theme(msg: QMessageBox, dark: Optional[bool] = None) -> None:
    """
    函数: apply_message_box_theme
    作用: 根据主程序模式为 QMessageBox 应用一致的黑夜/白天配色样式。
    参数:
        msg: 要应用样式的 QMessageBox。
        dark: 可选，指定是否使用深色模式；为 None 时从 QSettings 读取。
    返回:
        无。
    """
    try:
        if dark is None:
            settings = QSettings()
            dark = bool(settings.value("dark_mode", False, type=bool))
    except Exception:
        dark = False
    try:
        if bool(dark):
            msg.setStyleSheet(
                """
                QMessageBox { background: #1f242b; }
                QLabel { color: #e8eaed; }
                QPushButton { background: #3a4048; border: 1px solid #505761; border-radius: 6px; padding: 6px 10px; color: #e8eaed; }
                QPushButton:hover { background: #454c55; }
                QPushButton:pressed { background: #58606b; }
                """
            )
        else:
            msg.setStyleSheet(
                """
                QMessageBox { background: #f5f7fa; }
                QLabel { color: #2c3e50; }
                QPushButton { background: #e9eef3; border: 1px solid #d0d7de; border-radius: 6px; padding: 6px 10px; color: #2c3e50; }
                QPushButton:hover { background: #dde4ea; }
                QPushButton:pressed { background: #cfd6dc; }
                """
            )
    except Exception:
        pass

    


class ThemeService:
    """
    类: ThemeService
    作用: 集中管理小游戏的前景色读取与应用。
    参数:
        无。
    返回:
        无。
    """

    @staticmethod
    def minimal_fg(default: str = "#1E1E1E") -> str:
        """
        函数: minimal_fg
        作用: 读取极简模式的前景色配置键 `minimal_theme_fg`。
        参数:
            default: 读取失败时的默认颜色。
        返回:
            颜色字符串。
        """
        try:
            settings = QSettings()
            fg = str(settings.value("minimal_theme_fg", default, type=str))
        except Exception:
            fg = default
        return fg
