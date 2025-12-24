# -*- coding: utf-8 -*-
"""
文件: scripts/quick_sanity.py
描述: 快速运行核心逻辑的健全性检查（不依赖 UI）。
"""

import sys


def main():
    """
    函数: main
    作用: 运行表达式解析、科学函数与程序员计算器的快速验证并打印结果。
    参数:
        无。
    返回:
        无（打印检查输出）。
    """
    sys.path.append("src")
    from core.expr_parser import safe_eval
    from core.scientific_engine import get_functions, get_variables
    from core.programmer_engine import (
        to_base_str,
        parse_input,
        bit_and,
        bit_or,
        bit_xor,
        bit_not,
        shl,
        shr,
    )

    funcs_deg = get_functions("deg")
    funcs_rad = get_functions("rad")
    vars_ = get_variables()

    # 科学表达式
    res1 = safe_eval("sin(30)+log(100)", functions=funcs_deg, variables=vars_)
    res2 = safe_eval("sin(pi/6)+ln(e)", functions=funcs_rad, variables=vars_)

    # 程序员逻辑
    v_hex = to_base_str(255, "HEX")
    v_bin = to_base_str(5, "BIN", bits=8)
    parsed = parse_input("FF", "HEX")
    mask_and = bit_and(0b1010, 0b1100)
    mask_or = bit_or(0b1010, 0b1100)
    mask_xor = bit_xor(0b1010, 0b1100)
    mask_not = bit_not(0)
    shift_l = shl(1, 3)
    shift_r = shr(8, 3)

    print("SCI:", round(res1, 6), round(res2, 6))
    print("PROG:", v_hex, v_bin, parsed)
    print("BIT:", mask_and, mask_or, mask_xor, mask_not, shift_l, shift_r)


if __name__ == "__main__":
    main()