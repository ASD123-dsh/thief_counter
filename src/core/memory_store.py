# -*- coding: utf-8 -*-
"""
文件: src/core/memory_store.py
描述: 提供跨面板共享的记忆存储（MC/MR/M+/M-）。
"""

from typing import Optional


class MemoryStore:
    """
    类: MemoryStore
    作用: 管理计算器的记忆功能，支持清除、读取、累加与累减。
    """

    def __init__(self) -> None:
        """
        函数: __init__
        作用: 初始化记忆存储，默认值为 0。
        参数:
            无。
        返回:
            无。
        """
        self._value: float = 0.0

    def clear(self) -> None:
        """
        函数: clear
        作用: 清除记忆值，置为 0。
        参数:
            无。
        返回:
            无。
        """
        self._value = 0.0

    def recall(self) -> float:
        """
        函数: recall
        作用: 返回当前记忆值。
        参数:
            无。
        返回:
            当前记忆值（浮点）。
        """
        return self._value

    def add(self, value: float) -> None:
        """
        函数: add
        作用: 将传入数值累加到记忆值。
        参数:
            value: 需要累加的数值。
        返回:
            无。
        """
        self._value += float(value)

    def subtract(self, value: float) -> None:
        """
        函数: subtract
        作用: 将传入数值从记忆值中累减。
        参数:
            value: 需要累减的数值。
        返回:
            无。
        """
        self._value -= float(value)