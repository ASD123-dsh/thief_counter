# -*- coding: utf-8 -*-
"""
文件: src/core/programmer_engine.py
描述: 程序员计算器核心逻辑，提供进制转换与位运算（32位裁剪）。
"""

from typing import Tuple


def crop_to_word(value: int, bits: int = 32) -> int:
    """
    函数: crop_to_word
    作用: 对整数进行指定位宽裁剪，默认 32 位，返回无符号效果。
    参数:
        value: 输入整数。
        bits: 位宽，默认 32。
    返回:
        裁剪后的整数（无符号表现）。
    """
    mask = (1 << bits) - 1
    return value & mask


def to_base_str(value: int, base: str = "DEC", bits: int = 32) -> str:
    """
    函数: to_base_str
    作用: 将整数按指定进制格式化为字符串。
    参数:
        value: 整数值。
        base: 进制，"DEC"、"HEX" 或 "BIN"。
        bits: 位宽（用于二进制显示填充）。
    返回:
        进制表示的字符串。
    """
    v = crop_to_word(value, bits)
    if base == "DEC":
        return str(v)
    if base == "HEX":
        return format(v, "X")
    if base == "BIN":
        return format(v, f"0{bits}b")
    if base == "OCT":
        # 八进制根据位宽动态计算填充长度：32位需要11位八进制（2位最高位+3*10），但简单起见我们按位数向上取整填充
        # 32位最大值 4294967295 -> 37777777777 (11位)
        # 64位最大值 -> 1777777777777777777777 (22位)
        # 粗略估算：bits / 3 向上取整
        width = (bits + 2) // 3
        return format(v, f"0{width}o")
    return str(v)


def parse_input(input_str: str, base: str = "DEC") -> int:
    """
    函数: parse_input
    作用: 将字符串按进制解析为整数。自动去除输入中的空格。
    参数:
        input_str: 输入字符串。
        base: 进制，"DEC"、"HEX" 或 "BIN"。
    返回:
        解析得到的整数。
    """
    if not input_str:
        return 0
    # 去除所有空格，支持 "0000 0001" 这种格式输入
    clean_str = input_str.replace(" ", "")
    if not clean_str:
        return 0
        
    if base == "DEC":
        return int(clean_str, 10)
    if base == "HEX":
        return int(clean_str, 16)
    if base == "BIN":
        return int(clean_str, 2)
    if base == "OCT":
        return int(clean_str, 8)
    return int(clean_str, 10)


def bit_and(a: int, b: int, bits: int = 32) -> int:
    return crop_to_word(a & b, bits)


def bit_or(a: int, b: int, bits: int = 32) -> int:
    return crop_to_word(a | b, bits)


def bit_xor(a: int, b: int, bits: int = 32) -> int:
    return crop_to_word(a ^ b, bits)


def bit_not(a: int, bits: int = 32) -> int:
    return crop_to_word(~a, bits)


def shl(a: int, n: int = 1, bits: int = 32) -> int:
    return crop_to_word(a << n, bits)


def shr(a: int, n: int = 1, bits: int = 32) -> int:
    # 无符号右移（Python >> 对负数是算术右移，但我们裁剪后视为无符号）
    return crop_to_word(a >> n, bits)