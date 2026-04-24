# -*- coding: utf-8 -*-
"""
文件: src/ui/checksum_panel.py
描述: 校验和计算模式界面，支持常见字节流校验、校验验证与附加报文生成。
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.checksum_engine import (
    append_checksum_bytes,
    calculate_checksum_bundle,
    format_checksum_bytes,
    format_checksum_value,
    get_checksum_algorithm,
    get_checksum_algorithms,
    get_checksum_value,
    normalize_hex_string,
    parse_checksum_input,
    parse_expected_checksum,
)
from core.memory_store import MemoryStore


class ChecksumPanel(QWidget):
    """
    类: ChecksumPanel
    作用: 提供字节流输入、校验和计算、校验验证、附加报文预览与历史记录。
    """

    def __init__(self, memory_store: MemoryStore, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.memory_store = memory_store
        self._last_data: bytes = b""
        self._last_bundle: dict[str, int] = calculate_checksum_bundle(b"")

        self._build_ui()
        self.on_input_mode_changed(self.input_mode.currentIndex())
        self.on_expected_mode_changed(self.expected_mode.currentIndex())
        self.reset_outputs()

    def _build_ui(self) -> None:
        top = QWidget()
        top_v = QVBoxLayout(top)
        top_v.setContentsMargins(0, 0, 0, 0)
        top_v.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        info_row = QHBoxLayout()
        info_row.setContentsMargins(0, 0, 0, 0)
        info_row.setSpacing(8)

        self.input_mode = QComboBox()
        self.input_mode.addItem("十六进制字节", "HEX")
        self.input_mode.addItem("十进制字节", "DEC")
        self.input_mode.addItem("文本字节", "TEXT")
        self.input_mode.currentIndexChanged.connect(self.on_input_mode_changed)

        self.auto_calc = QCheckBox("实时计算")
        self.auto_calc.setChecked(True)

        self.byte_count_label = QLabel("字节数：0")

        top_row.addWidget(QLabel("输入格式："))
        top_row.addWidget(self.input_mode)
        top_row.addStretch(1)

        info_row.addWidget(self.auto_calc)
        info_row.addWidget(self.byte_count_label)
        info_row.addStretch(1)

        top_v.addLayout(top_row)
        top_v.addLayout(info_row)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setObjectName("display")
        self.input_edit.textChanged.connect(self.on_input_text_changed)

        btn_grid = QGridLayout()
        btn_grid.setContentsMargins(0, 0, 0, 0)
        btn_grid.setHorizontalSpacing(8)
        btn_grid.setVerticalSpacing(8)

        btn_calc = QPushButton("计算")
        btn_sample = QPushButton("示例")
        btn_clear = QPushButton("清空")
        btn_clear_history = QPushButton("清历史")

        btn_calc.clicked.connect(lambda: self.calculate_checksums(record_history=True))
        btn_sample.clicked.connect(self.load_example)
        btn_clear.clicked.connect(self.clear_inputs)

        btn_grid.addWidget(btn_calc, 0, 0)
        btn_grid.addWidget(btn_sample, 0, 1)
        btn_grid.addWidget(btn_clear, 1, 0)
        btn_grid.addWidget(btn_clear_history, 1, 1)

        self.status_label = QLabel("请输入需要参与校验的字节流。")
        self.status_label.setWordWrap(True)

        left = QWidget()
        left_v = QVBoxLayout(left)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)
        left_v.addWidget(top)
        left_v.addWidget(QLabel("原始数据："))
        left_v.addWidget(self.input_edit, 1)
        left_v.addLayout(btn_grid)
        left_v.addWidget(self.status_label)

        self.normalized_hex = QPlainTextEdit()
        self.normalized_hex.setReadOnly(True)
        self.normalized_hex.setMaximumHeight(88)
        self.normalized_hex.setPlaceholderText("这里显示规范化后的十六进制字节流")

        self.out_xor = self._create_output_edit()
        self.out_sum8 = self._create_output_edit()
        self.out_sum16 = self._create_output_edit()
        self.out_sum32 = self._create_output_edit()
        self.out_ones8 = self._create_output_edit()
        self.out_twos8 = self._create_output_edit()

        result_form = QFormLayout()
        result_form.setContentsMargins(0, 0, 0, 0)
        result_form.setSpacing(8)
        result_form.addRow("异或校验：", self.out_xor)
        result_form.addRow("八位求和校验：", self.out_sum8)
        result_form.addRow("十六位求和校验：", self.out_sum16)
        result_form.addRow("三十二位求和校验：", self.out_sum32)
        result_form.addRow("八位反码校验：", self.out_ones8)
        result_form.addRow("八位补码校验：", self.out_twos8)

        self.algorithm_combo = QComboBox()
        for meta in get_checksum_algorithms():
            self.algorithm_combo.addItem(str(meta["label"]), str(meta["id"]))
        self.algorithm_combo.currentIndexChanged.connect(self.on_algorithm_changed)

        self.byteorder_combo = QComboBox()
        self.byteorder_combo.addItem("高位在前", "big")
        self.byteorder_combo.addItem("低位在前", "little")
        self.byteorder_combo.currentIndexChanged.connect(self.on_algorithm_changed)

        self.selected_value_edit = self._create_output_edit()
        self.selected_bytes_edit = self._create_output_edit()

        self.expected_mode = QComboBox()
        self.expected_mode.addItem("十六进制", "HEX")
        self.expected_mode.addItem("十进制", "DEC")
        self.expected_mode.currentIndexChanged.connect(self.on_expected_mode_changed)

        self.expected_edit = QLineEdit()
        self.expected_edit.setPlaceholderText("输入目标校验值，例如 A0 或 160")

        expected_row = QWidget()
        expected_h = QHBoxLayout(expected_row)
        expected_h.setContentsMargins(0, 0, 0, 0)
        expected_h.setSpacing(8)
        expected_h.addWidget(self.expected_mode)
        expected_h.addWidget(self.expected_edit, 1)

        action_grid = QGridLayout()
        action_grid.setContentsMargins(0, 0, 0, 0)
        action_grid.setHorizontalSpacing(8)
        action_grid.setVerticalSpacing(6)
        action_grid.addWidget(QLabel("当前算法："), 0, 0)
        action_grid.addWidget(QLabel("字节顺序："), 0, 1)
        action_grid.addWidget(self.algorithm_combo, 1, 0)
        action_grid.addWidget(self.byteorder_combo, 1, 1)
        action_grid.addWidget(QLabel("当前结果："), 2, 0)
        action_grid.addWidget(QLabel("校验字节："), 2, 1)
        action_grid.addWidget(self.selected_value_edit, 3, 0)
        action_grid.addWidget(self.selected_bytes_edit, 3, 1)
        action_grid.addWidget(QLabel("目标值："), 4, 0, 1, 2)
        action_grid.addWidget(expected_row, 5, 0, 1, 2)
        action_grid.setColumnStretch(0, 1)
        action_grid.setColumnStretch(1, 1)

        op_btn_grid = QGridLayout()
        op_btn_grid.setContentsMargins(0, 0, 0, 0)
        op_btn_grid.setHorizontalSpacing(8)
        op_btn_grid.setVerticalSpacing(8)

        btn_verify = QPushButton("验证")
        btn_append = QPushButton("附加")
        btn_copy_checksum = QPushButton("复制校验")
        btn_copy_frame = QPushButton("复制报文")

        btn_verify.clicked.connect(self.verify_selected_checksum)
        btn_append.clicked.connect(self.generate_appended_frame)
        btn_copy_checksum.clicked.connect(self.copy_selected_checksum)
        btn_copy_frame.clicked.connect(self.copy_appended_frame)

        op_btn_grid.addWidget(btn_verify, 0, 0)
        op_btn_grid.addWidget(btn_append, 0, 1)
        op_btn_grid.addWidget(btn_copy_checksum, 1, 0)
        op_btn_grid.addWidget(btn_copy_frame, 1, 1)

        self.verify_label = QLabel("校验验证：等待输入")
        self.verify_label.setWordWrap(True)

        self.appended_hex = QPlainTextEdit()
        self.appended_hex.setReadOnly(True)
        self.appended_hex.setMaximumHeight(88)
        self.appended_hex.setPlaceholderText("这里显示附加校验字节后的报文")

        self.history = QListWidget()
        self.history.setMinimumWidth(100)
        btn_clear_history.clicked.connect(self.history.clear)

        result_tab = QWidget()
        result_v = QVBoxLayout(result_tab)
        result_v.setContentsMargins(8, 8, 8, 8)
        result_v.setSpacing(8)
        result_v.addWidget(QLabel("规范十六进制："))
        result_v.addWidget(self.normalized_hex)
        result_v.addWidget(QLabel("结果明细："))
        result_v.addLayout(result_form)
        result_v.addStretch(1)

        tool_tab = QWidget()
        tool_v = QVBoxLayout(tool_tab)
        tool_v.setContentsMargins(8, 8, 8, 8)
        tool_v.setSpacing(8)
        tool_v.addLayout(action_grid)
        tool_v.addLayout(op_btn_grid)
        tool_v.addWidget(self.verify_label)
        tool_v.addWidget(QLabel("附加报文："))
        tool_v.addWidget(self.appended_hex)
        tool_v.addStretch(1)

        history_tab = QWidget()
        history_v = QVBoxLayout(history_tab)
        history_v.setContentsMargins(8, 8, 8, 8)
        history_v.setSpacing(8)
        history_v.addWidget(QLabel("历史记录："))
        history_v.addWidget(self.history, 1)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("checksumPageStack")
        self.page_stack.addWidget(result_tab)
        self.page_stack.addWidget(tool_tab)
        self.page_stack.addWidget(history_tab)

        nav_bar = QWidget()
        nav_bar.setObjectName("checksumNavBar")
        nav_h = QHBoxLayout(nav_bar)
        nav_h.setContentsMargins(0, 0, 0, 0)
        nav_h.setSpacing(8)

        self.nav_result_btn = self._create_nav_button("结果", 0)
        self.nav_tool_btn = self._create_nav_button("工具", 1)
        self.nav_history_btn = self._create_nav_button("历史", 2)

        nav_h.addWidget(self.nav_result_btn, 1)
        nav_h.addWidget(self.nav_tool_btn, 1)
        nav_h.addWidget(self.nav_history_btn, 1)

        right = QWidget()
        right_v = QVBoxLayout(right)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(8)
        right_v.addWidget(nav_bar)
        right_v.addWidget(self.page_stack, 1)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([360, 320])

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(splitter)

        self.nav_result_btn.setChecked(True)
        self.page_stack.setCurrentIndex(0)

    def get_help_text(self) -> str:
        return (
            "【概览】\n"
            "- 用于对字节流计算常见校验值，适合串口报文、协议帧、设备指令等场景。\n"
            "- 当前提供异或校验、八位求和校验、十六位求和校验、三十二位求和校验、八位反码校验、八位补码校验。\n"
            "\n"
            "【输入格式】\n"
            "- 十六进制字节：支持“68 65 6C 6C 6F”“68,65,6C”“68656C6C6F”“0x68 0x65”等写法。\n"
            "- 十进制字节：按 0 到 255 输入，例如“104 101 108 108 111”。\n"
            "- 文本字节：直接输入文本，程序会按 UTF-8 编码后参与计算。\n"
            "\n"
            "【工具操作】\n"
            "- 当前算法可切换要用于验证、复制和附加报文的校验算法。\n"
            "- 字节顺序会影响多字节结果追加到报文末尾时的排列顺序。\n"
            "- 目标值支持十六进制和十进制，两者都会与当前算法结果进行对比。\n"
            "- 生成附加报文会把当前算法的校验字节追加到原始报文末尾。\n"
            "\n"
            "【便捷操作】\n"
            "- 打开实时计算后，输入变化会自动刷新结果，但不会重复写入历史。\n"
            "- 复制校验会复制当前算法对应的校验字节。\n"
            "- 复制报文会复制追加校验后的完整十六进制报文。\n"
        )

    def on_input_mode_changed(self, _idx: int) -> None:
        mode = self.input_mode.currentData()
        if mode == "HEX":
            self.input_edit.setPlaceholderText("请输入十六进制字节，例如：68 65 6C 6C 6F 或 68656C6C6F")
            self.status_label.setText("支持空格、逗号、换行分隔；连续十六进制字符串会按每两位拆成一个字节。")
        elif mode == "DEC":
            self.input_edit.setPlaceholderText("请输入十进制字节，例如：104 101 108 108 111")
            self.status_label.setText("十进制模式下每个字节都必须处于 0 到 255 范围。")
        else:
            self.input_edit.setPlaceholderText("请输入文本内容，程序会按 UTF-8 字节流参与校验计算")
            self.status_label.setText("文本模式会保留换行，并按 UTF-8 编码后参与计算。")

    def on_expected_mode_changed(self, _idx: int) -> None:
        if self.expected_mode.currentData() == "HEX":
            self.expected_edit.setPlaceholderText("输入目标校验值，例如：A0 或 00 A0")
        else:
            self.expected_edit.setPlaceholderText("输入目标校验值，例如：160")

    def on_input_text_changed(self) -> None:
        if not self.input_edit.toPlainText():
            self.byte_count_label.setText("字节数：0")
            self.status_label.setText("请输入需要参与校验的字节流。")
            self.reset_outputs()
            return

        if self.auto_calc.isChecked():
            self.calculate_checksums(record_history=False)
        else:
            self.status_label.setText("输入已更新，点击“计算”即可刷新结果。")

    def on_algorithm_changed(self, _idx: int) -> None:
        self.refresh_selected_algorithm_outputs()

    def load_example(self) -> None:
        mode = self.input_mode.currentData()
        if mode == "HEX":
            sample = "68 65 6C 6C 6F"
        elif mode == "DEC":
            sample = "104 101 108 108 111"
        else:
            sample = "hello"
        self.input_edit.setPlainText(sample)
        self.calculate_checksums(record_history=True)

    def clear_inputs(self) -> None:
        self.input_edit.clear()
        self.expected_edit.clear()
        self.reset_outputs()
        self.byte_count_label.setText("字节数：0")
        self.status_label.setText("请输入需要参与校验的字节流。")

    def calculate_checksums(self, record_history: bool = True) -> bool:
        raw_text = self.input_edit.toPlainText()
        input_mode = str(self.input_mode.currentData() or "HEX")
        mode_name = self.input_mode.currentText()
        try:
            data = parse_checksum_input(raw_text, input_mode)
            bundle = calculate_checksum_bundle(data)

            self._last_data = data
            self._last_bundle = bundle

            self.byte_count_label.setText(f"字节数：{len(data)}")
            self.normalized_hex.setPlainText(normalize_hex_string(data))
            self.out_xor.setText(format_checksum_value(bundle["xor"], 8))
            self.out_sum8.setText(format_checksum_value(bundle["sum8"], 8))
            self.out_sum16.setText(format_checksum_value(bundle["sum16"], 16))
            self.out_sum32.setText(format_checksum_value(bundle["sum32"], 32))
            self.out_ones8.setText(format_checksum_value(bundle["ones8"], 8))
            self.out_twos8.setText(format_checksum_value(bundle["twos8"], 8))

            self.refresh_selected_algorithm_outputs()
            self.status_label.setText(f"已按“{mode_name}”解析完成，共 {len(data)} 字节。")

            if record_history:
                self.history.addItem(
                    f"{mode_name} | {len(data)} 字节 | "
                    f"异或=0x{bundle['xor']:02X} | 八位求和=0x{bundle['sum8']:02X} | 八位补码=0x{bundle['twos8']:02X}"
                )
            return True
        except Exception as exc:
            self.status_label.setText(f"输入解析失败：{exc}")
            self.verify_label.setText("校验验证：等待重新计算")
            self.appended_hex.clear()
            if record_history:
                self.history.addItem(f"[错误] {mode_name}：{exc}")
            return False

    def refresh_selected_algorithm_outputs(self) -> None:
        meta = self._current_algorithm_meta()
        bits = int(meta["bits"])
        value = get_checksum_value(self._last_bundle, str(meta["id"]))
        byteorder = str(self.byteorder_combo.currentData() or "big")

        self.selected_value_edit.setText(format_checksum_value(value, bits))
        self.selected_bytes_edit.setText(format_checksum_bytes(value, bits, byteorder))

        if self._last_data:
            frame = append_checksum_bytes(self._last_data, value, bits, byteorder)
            self.appended_hex.setPlainText(normalize_hex_string(frame))
        else:
            self.appended_hex.clear()

    def verify_selected_checksum(self) -> None:
        if not self.calculate_checksums(record_history=False):
            return

        meta = self._current_algorithm_meta()
        bits = int(meta["bits"])
        actual = get_checksum_value(self._last_bundle, str(meta["id"]))
        expected_mode = str(self.expected_mode.currentData() or "HEX")
        algorithm_label = str(meta["label"])

        try:
            expected = parse_expected_checksum(self.expected_edit.text(), expected_mode, bits)
        except Exception as exc:
            self.verify_label.setText(f"校验验证：目标值无效，{exc}")
            return

        if expected == actual:
            self.verify_label.setText(f"校验验证：通过，{algorithm_label}结果与目标值一致。")
            self.history.addItem(
                f"验证通过 | {algorithm_label} | 目标值=0x{expected:0{max(2, (bits + 3) // 4)}X}"
            )
        else:
            self.verify_label.setText(
                f"校验验证：不匹配，当前={format_checksum_value(actual, bits)}，"
                f"目标={format_checksum_value(expected, bits)}。"
            )
            self.history.addItem(
                f"验证失败 | {algorithm_label} | 当前=0x{actual:0{max(2, (bits + 3) // 4)}X} "
                f"| 目标=0x{expected:0{max(2, (bits + 3) // 4)}X}"
            )

    def generate_appended_frame(self) -> None:
        if not self.calculate_checksums(record_history=False):
            return

        meta = self._current_algorithm_meta()
        bits = int(meta["bits"])
        byteorder = str(self.byteorder_combo.currentData() or "big")
        value = get_checksum_value(self._last_bundle, str(meta["id"]))
        frame = append_checksum_bytes(self._last_data, value, bits, byteorder)
        frame_text = normalize_hex_string(frame)
        self.appended_hex.setPlainText(frame_text)
        self.status_label.setText(f"已生成“{meta['label']}”附加报文，字节顺序为 {self.byteorder_combo.currentText()}。")
        self.history.addItem(f"附加报文 | {meta['label']} | {self.byteorder_combo.currentText()} | {frame_text}")

    def copy_selected_checksum(self) -> None:
        if not self.calculate_checksums(record_history=False):
            return
        QApplication.clipboard().setText(self.selected_bytes_edit.text().strip())
        self.status_label.setText("已复制当前校验字节到剪贴板。")

    def copy_appended_frame(self) -> None:
        if not self.calculate_checksums(record_history=False):
            return
        QApplication.clipboard().setText(self.appended_hex.toPlainText().strip())
        self.status_label.setText("已复制附加报文到剪贴板。")

    def reset_outputs(self) -> None:
        self._last_data = b""
        self._last_bundle = calculate_checksum_bundle(b"")
        self.normalized_hex.clear()
        self.out_xor.setText(format_checksum_value(0, 8))
        self.out_sum8.setText(format_checksum_value(0, 8))
        self.out_sum16.setText(format_checksum_value(0, 16))
        self.out_sum32.setText(format_checksum_value(0, 32))
        self.out_ones8.setText(format_checksum_value(0, 8))
        self.out_twos8.setText(format_checksum_value(0, 8))
        self.verify_label.setText("校验验证：等待输入")
        self.appended_hex.clear()
        self.refresh_selected_algorithm_outputs()

    def _create_nav_button(self, text: str, index: int) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("checksumNavBtn")
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        button.clicked.connect(lambda checked=False, i=index, b=button: self._switch_page(i, b))
        return button

    def _switch_page(self, index: int, button: QPushButton) -> None:
        for btn in (self.nav_result_btn, self.nav_tool_btn, self.nav_history_btn):
            btn.setChecked(btn is button)
        self.page_stack.setCurrentIndex(index)

    def _current_algorithm_meta(self) -> dict[str, object]:
        return get_checksum_algorithm(str(self.algorithm_combo.currentData() or "XOR"))

    def _create_output_edit(self) -> QLineEdit:
        widget = QLineEdit()
        widget.setReadOnly(True)
        widget.setAlignment(Qt.AlignLeft)
        return widget
