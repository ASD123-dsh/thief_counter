# -*- coding: utf-8 -*-
"""
文件: src/core/expr_parser.py
描述: 使用 AST 白名单方式安全解析与计算数学表达式，支持基本运算与有限函数。
"""

import ast
import math
from typing import Any, Callable, Dict, Optional


ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}

ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}


def safe_eval(expr: str,
              functions: Optional[Dict[str, Callable[..., Any]]] = None,
              variables: Optional[Dict[str, Any]] = None) -> float:
    """
    函数: safe_eval
    作用: 安全计算表达式，禁止 eval，允许基本算术与指定函数。
    参数:
        expr: 字符串表达式，例如 "(1+2)*3"、"sin(30)+log10(100)"。
        functions: 可用函数映射，如 {"sin": sin_fn, "sqrt": sqrt_fn}。
        variables: 可用变量映射，如 {"pi": math.pi}。
    返回:
        计算结果（浮点数）。
    """

    if functions is None:
        functions = {}
    if variables is None:
        variables = {"pi": math.pi, "e": math.e}

    try:
        tree = ast.parse(expr, mode="eval")
    except Exception as e:
        raise ValueError(f"表达式解析失败: {e}")

    def _eval(node: ast.AST) -> float:
        """
        函数: _eval
        作用: 递归计算 AST 节点，仅支持白名单内的节点与操作。
        参数:
            node: AST 节点。
        返回:
            节点计算结果（浮点）。
        """
        if isinstance(node, ast.Expression):
            return _eval(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("仅允许数字常量")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in ALLOWED_BINOPS:
                raise ValueError("不支持的二元运算")
            left = _eval(node.left)
            right = _eval(node.right)
            return float(ALLOWED_BINOPS[op_type](left, right))

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in ALLOWED_UNARYOPS:
                raise ValueError("不支持的一元运算")
            operand = _eval(node.operand)
            return float(ALLOWED_UNARYOPS[op_type](operand))

        if isinstance(node, ast.Call):
            # 仅允许函数名调用，不允许属性与复杂结构
            if not isinstance(node.func, ast.Name):
                raise ValueError("不支持的函数调用形式")
            func_name = node.func.id
            if func_name not in functions:
                raise ValueError(f"不允许的函数: {func_name}")
            args = [_eval(arg) for arg in node.args]
            # 关键字参数不允许
            if node.keywords:
                raise ValueError("不支持关键字参数")
            result = functions[func_name](*args)
            return float(result)

        if isinstance(node, ast.Name):
            name = node.id
            if name in variables:
                val = variables[name]
                if isinstance(val, (int, float)):
                    return float(val)
                raise ValueError("变量值必须为数字")
            raise ValueError(f"未定义标识符: {name}")

        # 其它节点一律不允许
        raise ValueError("表达式包含不支持的语法")

    try:
        return _eval(tree)
    except ZeroDivisionError:
        raise ValueError("除零错误")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"计算失败: {e}")