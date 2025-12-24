# -*- coding: utf-8 -*-
"""
文件: src/ui/programmer_panel.py
描述: 程序员计算器面板，支持 32 位位运算、进制切换与历史记录/记忆功能。
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QLabel,
    QComboBox,
    QSpinBox,
)

from core.memory_store import MemoryStore
from core.programmer_engine import (
    parse_input,
    to_base_str,
    bit_and,
    bit_or,
    bit_xor,
    bit_not,
    shl,
    shr,
)


class ProgrammerPanel(QWidget):
    """
    类: ProgrammerPanel
    作用: 程序员模式界面，提供 A/B 两输入、进制选择、位运算与结果显示。
    """

    def __init__(self, memory_store: MemoryStore, bits: int = 32, parent: Optional[QWidget] = None) -> None:
        """
        函数: __init__
        作用: 初始化界面、绑定事件与默认位宽。
        参数:
            memory_store: 共享记忆存储实例。
            bits: 位宽（默认 32）。
            parent: 父级 QWidget。
        返回:
            无。
        """
        super().__init__(parent)
        self.memory_store = memory_store
        self.bits = bits

        # 顶部：进制选择与位移步长
        top = QWidget()
        top_h = QHBoxLayout(top)
        top_h.setContentsMargins(0, 0, 0, 0)
        top_h.setSpacing(8)

        self.base_combo = QComboBox()
        # 显示为中文，内部使用英文代码作为 userData
        self.base_combo.addItem("十进制", "DEC")
        self.base_combo.addItem("十六进制", "HEX")
        self.base_combo.addItem("二进制", "BIN")
        self.base_combo.addItem("八进制", "OCT")
        self.base_combo.setCurrentIndex(1)  # 默认十六进制
        self.base_combo.currentIndexChanged.connect(self.on_base_changed)

        lbl_bits = QLabel(f"位宽: {self.bits}")
        self.shift_step = QSpinBox()
        self.shift_step.setRange(1, 31)
        self.shift_step.setValue(1)
        self.shift_step.setSuffix(" 位移")

        top_h.addWidget(QLabel("进制:"))
        top_h.addWidget(self.base_combo)
        top_h.addSpacing(12)
        top_h.addWidget(lbl_bits)
        top_h.addSpacing(12)
        top_h.addWidget(self.shift_step)
        top_h.addStretch(1)

        # 中部：A/B 输入与按钮网格
        self.input_a = QLineEdit()
        self.input_a.setObjectName("display")
        self.input_b = QLineEdit()
        self.input_a.setPlaceholderText("输入 A")
        self.input_b.setPlaceholderText("输入 B（用于二元位运算）")
        self.input_a.setAlignment(Qt.AlignLeft)
        self.input_b.setAlignment(Qt.AlignLeft)

        grid = QGridLayout()
        grid.setSpacing(8)

        # 位运算按钮中文化
        btn_and = QPushButton("与")
        btn_or = QPushButton("或")
        btn_xor = QPushButton("异或")
        btn_not = QPushButton("非")
        btn_shl = QPushButton("左移(A)")
        btn_shr = QPushButton("右移(A)")

        btn_mc = QPushButton("MC")
        btn_mr = QPushButton("MR")
        btn_mplus = QPushButton("M+")
        btn_mminus = QPushButton("M-")

        # 清除类按键：合并为“清空”，退格作用于当前聚焦输入框
        btn_clear = QPushButton("清空")
        btn_back = QPushButton("退格")

        # 绑定事件
        btn_and.clicked.connect(lambda: self.apply_binary("AND"))
        btn_or.clicked.connect(lambda: self.apply_binary("OR"))
        btn_xor.clicked.connect(lambda: self.apply_binary("XOR"))
        btn_not.clicked.connect(lambda: self.apply_unary("NOT"))
        btn_shl.clicked.connect(lambda: self.apply_shift(True))
        btn_shr.clicked.connect(lambda: self.apply_shift(False))

        btn_mc.clicked.connect(lambda: self.on_memory("MC"))
        btn_mr.clicked.connect(lambda: self.on_memory("MR"))
        btn_mplus.clicked.connect(lambda: self.on_memory("M+"))
        btn_mminus.clicked.connect(lambda: self.on_memory("M-"))

        # 清除类事件
        btn_clear.clicked.connect(self.on_clear_all)
        btn_back.clicked.connect(self.on_backspace_active)

        # 布局按钮
        # 统一为每行 4 列，避免右侧空缺
        grid.addWidget(btn_and, 0, 0)
        grid.addWidget(btn_or, 0, 1)
        grid.addWidget(btn_xor, 0, 2)
        grid.addWidget(btn_not, 0, 3)

        grid.addWidget(btn_shl, 1, 0)
        grid.addWidget(btn_shr, 1, 1)
        grid.addWidget(btn_clear, 1, 2)
        grid.addWidget(btn_back, 1, 3)

        grid.addWidget(btn_mc, 2, 0)
        grid.addWidget(btn_mr, 2, 1)
        grid.addWidget(btn_mplus, 2, 2)
        grid.addWidget(btn_mminus, 2, 3)

        # 结果区：三种进制显示
        self.out_dec = QLineEdit()
        self.out_hex = QLineEdit()
        self.out_bin = QLineEdit()
        self.out_oct = QLineEdit()
        for w in (self.out_dec, self.out_hex, self.out_bin, self.out_oct):
            w.setReadOnly(True)
            w.setAlignment(Qt.AlignLeft)

        # 历史
        self.history = QListWidget()
        self.history.setMinimumWidth(240)

        # 根布局
        left = QWidget()
        left_v = QVBoxLayout(left)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)
        left_v.addWidget(top)
        left_v.addWidget(self.input_a)
        left_v.addWidget(self.input_b)
        left_v.addLayout(grid)
        left_v.addWidget(QLabel("十进制:"))
        left_v.addWidget(self.out_dec)
        left_v.addWidget(QLabel("十六进制:"))
        left_v.addWidget(self.out_hex)
        left_v.addWidget(QLabel("二进制:"))
        left_v.addWidget(self.out_bin)
        left_v.addWidget(QLabel("八进制:"))
        left_v.addWidget(self.out_oct)

        # 额外：A-F 输入键行，便于 HEX 输入
        af_row = QHBoxLayout()
        for ch in ["A", "B", "C", "D", "E", "F"]:
            btn = QPushButton(ch)
            btn.clicked.connect(lambda checked=False, t=ch: self.insert_digit(t))
            af_row.addWidget(btn)
        left_v.addLayout(af_row)

        # 监听输入与进制变化，自动更新 A 的进制转换显示
        self.input_a.textChanged.connect(self.on_input_changed)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addWidget(left, 1)
        root.addWidget(self.history, 0)

    def get_help_text(self) -> str:
        """
        函数: get_help_text
        作用: 返回程序员计算器的详细使用说明文本（简体中文）。
        参数:
            无。
        返回:
            使用说明字符串。
        """
        return (
            "【概述】\n"
            "- 提供 32 位无符号位运算、进制转换与记忆功能。\n"
            "- 两输入框 A/B；一元运算使用 A，二元运算使用 A 与 B。\n"
            "\n"
            "【进制选择】\n"
            "- 通过顶部‘进制’下拉选择解析进制（十进制/十六进制/二进制/八进制）。\n"
            "- 输入按所选进制解析；空输入按 0 处理；解析失败不会刷新结果。\n"
            "\n"
            "【输入与便捷键】\n"
            "- A 为主输入，B 为二元位运算的第二操作数。\n"
            "- A-F 快捷键用于十六进制快速录入（插入到 A）。\n"
            "\n"
            "【位运算】\n"
            "- 与(AND)、或(OR)、异或(XOR)、非(NOT A)、左移(A)、右移(A)。\n"
            "- 位移步长由‘位移’控制（1–31）。\n"
            "- 所有结果按 32 位裁剪显示为无符号（掩码 (1<<32)-1）。\n"
            "\n"
            "【清除与记忆】\n"
            "- 清空：一键清空 A 与 B，并将结果区重置为 0。\n"
            "- 退格：默认退格 A；当 B 获得焦点时退格 B。\n"
            "- MC/MR/M+/M-：以十进制值进行清除/读取/累加/累减记忆。\n"
            "\n"
            "【结果与历史】\n"
            "- 结果区实时显示十进制/十六进制/二进制/八进制。\n"
            "- 历史记录将以中文说明记录每次操作与十进制结果。\n"
            "\n"
            "【示例】\n"
            "- 选择‘十六进制’，A=5D -> 十进制=93，八进制=135，二进制=...01011101。\n"
            "- A=0F, B=33：‘与’ -> 十进制 3；‘或’ -> 63；‘异或’ -> 60。\n"
            "- A=0F：‘非(A)’ -> 十进制 4294967280 (HEX=FFFFFFF0)。\n"
        )

    def parse_a(self) -> int:
        """
        函数: parse_a
        作用: 根据当前进制解析输入 A 为整数。
        参数:
            无。
        返回:
            解析得到的整数。
        """
        # 使用内部 userData 作为解析进制
        base = self.base_combo.currentData()
        txt = self.input_a.text().strip()
        return parse_input(txt, base)

    def parse_b(self) -> int:
        """
        函数: parse_b
        作用: 根据当前进制解析输入 B 为整数。
        参数:
            无。
        返回:
            解析得到的整数。
        """
        base = self.base_combo.currentData()
        txt = self.input_b.text().strip()
        return parse_input(txt, base)

    def update_outputs(self, value: int) -> None:
        """
        函数: update_outputs
        作用: 将整型结果以三种进制显示到输出框。
        参数:
            value: 计算结果整型。
        返回:
            无。
        """
        self.out_dec.setText(to_base_str(value, "DEC", self.bits))
        self.out_hex.setText(to_base_str(value, "HEX", self.bits))
        self.out_bin.setText(to_base_str(value, "BIN", self.bits))
        self.out_oct.setText(to_base_str(value, "OCT", self.bits))

    def apply_binary(self, op: str) -> None:
        """
        函数: apply_binary
        作用: 对 A 与 B 执行二元位运算，并更新结果显示与历史。
        参数:
            op: 位运算类型（AND/OR/XOR）。
        返回:
            无。
        """
        try:
            a = self.parse_a()
            b = self.parse_b()
            if op == "AND":
                r = bit_and(a, b, self.bits)
            elif op == "OR":
                r = bit_or(a, b, self.bits)
            elif op == "XOR":
                r = bit_xor(a, b, self.bits)
            else:
                raise ValueError("未知运算")
            self.update_outputs(r)
            op_cn = {"AND": "与", "OR": "或", "XOR": "异或"}.get(op, op)
            self.history.addItem(f"{op_cn}: A 与 B -> 十进制 {to_base_str(r, 'DEC', self.bits)}")
        except Exception as e:
            self.history.addItem(f"[错误] 二元位运算: {e}")

    def insert_digit(self, t: str) -> None:
        """
        函数: insert_digit
        作用: 将数字或 A-F 字符插入 A 输入框，便于 HEX 输入。
        参数:
            t: 待插入字符。
        返回:
            无。
        """
        self.input_a.insert(t)

    def on_input_changed(self, _txt: str) -> None:
        """
        函数: on_input_changed
        作用: 当 A 输入变更时，解析其值并实时刷新各进制显示。
        参数:
            _txt: 当前文本（未用）。
        返回:
            无。
        """
        try:
            a = self.parse_a()
            self.update_outputs(a)
        except Exception:
            # 输入不合法时不更新
            pass

    def on_base_changed(self, _idx: int) -> None:
        """
        函数: on_base_changed
        作用: 进制切换时，尝试解析并更新显示，适配 BIN/OCT/DEC/HEX。
        参数:
            _idx: 下拉索引（未用）。
        返回:
            无。
        """
        self.on_input_changed(self.input_a.text())

    def on_clear_all(self) -> None:
        """
        函数: on_clear_all
        作用: 一键清空 A 与 B，并将结果显示重置为 0。
        参数:
            无。
        返回:
            无。
        """
        self.input_a.clear()
        self.input_b.clear()
        self.update_outputs(0)

    def on_backspace_active(self) -> None:
        """
        函数: on_backspace_active
        作用: 对当前聚焦的输入框执行退格；默认退格 A，若 B 获得焦点则退格 B。
        参数:
            无。
        返回:
            无。
        """
        target = self.input_b if self.input_b.hasFocus() else self.input_a
        target.backspace()
        # A 改动需要刷新四制显示；B 改动无需刷新
        if target is self.input_a:
            try:
                a = self.parse_a()
                self.update_outputs(a)
            except Exception:
                pass

    def apply_unary(self, op: str) -> None:
        """
        函数: apply_unary
        作用: 对 A 执行一元位运算（NOT）。
        参数:
            op: 位运算类型（NOT）。
        返回:
            无。
        """
        try:
            a = self.parse_a()
            if op == "NOT":
                r = bit_not(a, self.bits)
            else:
                raise ValueError("未知运算")
            self.update_outputs(r)
            op_cn = "非" if op == "NOT" else op
            self.history.addItem(f"{op_cn}: A -> 十进制 {to_base_str(r, 'DEC', self.bits)}")
        except Exception as e:
            self.history.addItem(f"[错误] 一元位运算: {e}")

    def apply_shift(self, is_left: bool) -> None:
        """
        函数: apply_shift
        作用: 对 A 进行位移（SHL/SHR），位移步长由界面选择。
        参数:
            is_left: True 表示左移，False 表示右移。
        返回:
            无。
        """
        try:
            a = self.parse_a()
            n = int(self.shift_step.value())
            r = shl(a, n, self.bits) if is_left else shr(a, n, self.bits)
            self.update_outputs(r)
            op = "SHL" if is_left else "SHR"
            op_cn = "左移" if is_left else "右移"
            self.history.addItem(f"{op_cn} {n}: A -> 十进制 {to_base_str(r, 'DEC', self.bits)}")
        except Exception as e:
            self.history.addItem(f"[错误] 位移运算: {e}")

    def on_memory(self, op: str) -> None:
        """
        函数: on_memory
        作用: 记忆功能在程序员模式下以 DEC 值进行累加/累减或读写。
        参数:
            op: 记忆操作（MC/MR/M+/M-）。
        返回:
            无。
        """
        try:
            current_dec = 0
            txt = self.out_dec.text().strip()
            if txt:
                current_dec = int(txt, 10)
            if op == "MC":
                self.memory_store.clear()
            elif op == "MR":
                # 将记忆值显示为 A 的 DEC 文本
                mem = int(self.memory_store.recall())
                self.input_a.setText(str(mem))
                self.update_outputs(mem)
            elif op == "M+":
                self.memory_store.add(float(current_dec))
            elif op == "M-":
                self.memory_store.subtract(float(current_dec))
        except Exception as e:
            self.history.addItem(f"[错误] 记忆操作: {e}")