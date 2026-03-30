# -*- coding: utf-8 -*-
"""
文件: src/core/settings_service.py
描述: QSettings 轻量封装，统一常用配置键与范围校验逻辑。
"""

from __future__ import annotations

from typing import Dict

from PySide6.QtCore import QSettings


class SettingsService:
    """
    类: SettingsService
    作用: 提供常用配置项的统一读写入口，减少键名散落与重复钳制逻辑。
    """

    @staticmethod
    def _settings() -> QSettings:
        return QSettings()

    @staticmethod
    def dark_mode(default: bool = False) -> bool:
        try:
            return bool(SettingsService._settings().value("dark_mode", bool(default), type=bool))
        except Exception:
            return bool(default)

    @staticmethod
    def set_dark_mode(on: bool) -> None:
        SettingsService._settings().setValue("dark_mode", bool(on))

    @staticmethod
    def always_on_top(default: bool = False) -> bool:
        try:
            return bool(SettingsService._settings().value("always_on_top", bool(default), type=bool))
        except Exception:
            return bool(default)

    @staticmethod
    def set_always_on_top(on: bool) -> None:
        SettingsService._settings().setValue("always_on_top", bool(on))

    @staticmethod
    def moyu_path(default: str = "") -> str:
        try:
            return str(SettingsService._settings().value("moyu_path", default, type=str) or "")
        except Exception:
            return default

    @staticmethod
    def set_moyu_path(path: str) -> None:
        SettingsService._settings().setValue("moyu_path", str(path or ""))

    @staticmethod
    def moyu_last_file(default: str = "") -> str:
        try:
            return str(SettingsService._settings().value("moyu_last_file", default, type=str) or "")
        except Exception:
            return default

    @staticmethod
    def set_moyu_last_file(name: str) -> None:
        SettingsService._settings().setValue("moyu_last_file", str(name or ""))

    @staticmethod
    def minimal_opacity_percent(default: int = 100) -> int:
        try:
            val = int(SettingsService._settings().value("minimal_opacity_percent", int(default), type=int))
        except Exception:
            val = int(default)
        return 1 if val < 1 else (100 if val > 100 else val)

    @staticmethod
    def set_minimal_opacity_percent(percent: int) -> int:
        val = 1 if int(percent) < 1 else (100 if int(percent) > 100 else int(percent))
        SettingsService._settings().setValue("minimal_opacity_percent", val)
        return val

    @staticmethod
    def minimal_hover_delay_ms(default: int = 1500) -> int:
        try:
            val = int(SettingsService._settings().value("minimal_hover_delay_ms", int(default), type=int))
        except Exception:
            val = int(default)
        return 0 if val < 0 else (10000 if val > 10000 else val)

    @staticmethod
    def set_minimal_hover_delay_ms(delay_ms: int) -> int:
        val = 0 if int(delay_ms) < 0 else (10000 if int(delay_ms) > 10000 else int(delay_ms))
        SettingsService._settings().setValue("minimal_hover_delay_ms", val)
        return val

    @staticmethod
    def minimal_theme_defaults() -> Dict[str, str]:
        return {
            "id": "saved",
            "name": "已保存",
            "emoji": "🎨",
            "bg": "#F5F5F7",
            "fg": "#1E1E1E",
            "accent": "#3B82F6",
        }

    @staticmethod
    def minimal_theme() -> Dict[str, str]:
        defaults = SettingsService.minimal_theme_defaults()
        try:
            settings = SettingsService._settings()
            bg = str(settings.value("minimal_theme_bg", defaults["bg"], type=str))
            fg = str(settings.value("minimal_theme_fg", defaults["fg"], type=str))
            accent = str(settings.value("minimal_theme_accent", defaults["accent"], type=str))
            name = str(settings.value("minimal_theme_name", defaults["name"], type=str))
            return {
                "id": "saved",
                "name": name or defaults["name"],
                "emoji": "🎨",
                "bg": bg or defaults["bg"],
                "fg": fg or defaults["fg"],
                "accent": accent or defaults["accent"],
            }
        except Exception:
            return defaults
