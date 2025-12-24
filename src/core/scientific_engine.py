# -*- coding: utf-8 -*-
"""
文件: src/core/scientific_engine.py
描述: 科学计算相关函数封装，支持角度/弧度模式以及常用数学函数。
"""

import math
from typing import Dict, Callable


def _wrap_trig(fn: Callable[[float], float], angle_mode: str) -> Callable[[float], float]:
    """
    函数: _wrap_trig
    作用: 根据角度模式包装三角函数，角度模式下自动转换为弧度。
    参数:
        fn: 目标三角函数（如 math.sin）。
        angle_mode: "deg" 或 "rad"。
    返回:
        可直接在表达式中调用的函数。
    """
    def inner(x: float) -> float:
        if angle_mode == "deg":
            return fn(math.radians(x))
        return fn(x)
    return inner


def get_functions(angle_mode: str = "deg") -> Dict[str, Callable[..., float]]:
    """
    函数: get_functions
    作用: 返回科学模式可用函数映射，根据角度模式提供正确的三角函数实现。
    参数:
        angle_mode: 角度单位模式，"deg" 为角度，"rad" 为弧度。
    返回:
        函数名到可调用对象的字典。
    """
    def _fact(x: float) -> float:
        # 仅允许非负整数阶乘
        n = int(x)
        if n < 0 or abs(x - n) > 1e-9:
            raise ValueError("阶乘仅支持非负整数")
        return float(math.factorial(n))

    def _square(x: float) -> float:
        return x * x

    def _inv(x: float) -> float:
        if x == 0:
            raise ValueError("除零错误")
        return 1.0 / x

    def _pow10(x: float) -> float:
        return math.pow(10.0, x)

    return {
        "sin": _wrap_trig(math.sin, angle_mode),
        "cos": _wrap_trig(math.cos, angle_mode),
        "tan": _wrap_trig(math.tan, angle_mode),
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "sqrt": math.sqrt,
        "log": math.log10,  # 以 10 为底
        "ln": math.log,     # 自然对数
        "exp": math.exp,
        "pow": math.pow,
        "square": _square,
        "inv": _inv,
        "fact": _fact,
        "pow10": _pow10,
    }


def get_variables() -> Dict[str, float]:
    """
    函数: get_variables
    作用: 提供常用数学常量，供表达式中直接使用。
    参数:
        无。
    返回:
        包含常量的字典，如 {"pi": 3.1415..., "e": 2.718...}。
    """
    return {"pi": math.pi, "e": math.e}