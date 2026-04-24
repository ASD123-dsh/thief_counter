# -*- coding: utf-8 -*-
"""
文件: src/core/checksum_engine.py
描述: 校验和计算模式的核心逻辑，提供字节流解析、常见校验算法与结果辅助工具。
"""

from __future__ import annotations

import re


_BYTE_SPLIT_PATTERN = re.compile(r"[\s,;，；]+")

_CHECKSUM_ALGORITHMS = (
    {"id": "XOR", "label": "异或校验", "bits": 8, "bundle_key": "xor"},
    {"id": "SUM8", "label": "八位求和校验", "bits": 8, "bundle_key": "sum8"},
    {"id": "SUM16", "label": "十六位求和校验", "bits": 16, "bundle_key": "sum16"},
    {"id": "SUM32", "label": "三十二位求和校验", "bits": 32, "bundle_key": "sum32"},
    {"id": "ONES8", "label": "八位反码校验", "bits": 8, "bundle_key": "ones8"},
    {"id": "TWOS8", "label": "八位补码校验", "bits": 8, "bundle_key": "twos8"},
)


def get_checksum_algorithms() -> list[dict[str, object]]:
    """
    函数: get_checksum_algorithms
    作用: 返回界面展示用的校验算法定义列表。
    参数:
        无。
    返回:
        算法定义列表。
    """
    return [dict(item) for item in _CHECKSUM_ALGORITHMS]


def get_checksum_algorithm(algorithm_id: str) -> dict[str, object]:
    """
    函数: get_checksum_algorithm
    作用: 根据算法编号获取算法定义。
    参数:
        algorithm_id: 算法编号。
    返回:
        算法定义字典。
    """
    target = str(algorithm_id or "").strip().upper()
    for item in _CHECKSUM_ALGORITHMS:
        if item["id"] == target:
            return dict(item)
    raise ValueError("不支持的校验算法")


def parse_checksum_input(raw_text: str, input_mode: str = "HEX") -> bytes:
    """
    函数: parse_checksum_input
    作用: 按输入模式将文本解析为字节流。
    参数:
        raw_text: 原始输入文本。
        input_mode: 输入模式，支持 HEX / DEC / TEXT。
    返回:
        解析后的 bytes。
    """
    mode = (input_mode or "HEX").upper()
    if mode == "TEXT":
        return raw_text.encode("utf-8") if raw_text else b""

    text = raw_text.strip()
    if not text:
        return b""

    if mode == "HEX":
        return _parse_hex_bytes(text)
    if mode == "DEC":
        return _parse_decimal_bytes(text)
    raise ValueError("不支持的输入模式")


def parse_expected_checksum(raw_text: str, input_mode: str = "HEX", bits: int | None = None) -> int:
    """
    函数: parse_expected_checksum
    作用: 将用户输入的目标校验值解析为整数。
    参数:
        raw_text: 原始输入文本。
        input_mode: 解析模式，支持 HEX / DEC。
        bits: 可选位宽限制。
    返回:
        解析后的整数。
    """
    text = str(raw_text or "").strip()
    if not text:
        raise ValueError("目标校验值不能为空")

    mode = (input_mode or "HEX").upper()
    if mode == "HEX":
        value = _parse_expected_hex_value(text)
    elif mode == "DEC":
        compact = text.replace(" ", "")
        try:
            value = int(compact, 10)
        except ValueError as exc:
            raise ValueError("十进制目标校验值无法解析") from exc
    else:
        raise ValueError("不支持的目标校验值格式")

    if value < 0:
        raise ValueError("目标校验值不能为负数")
    if bits is not None:
        max_value = (1 << bits) - 1
        if value > max_value:
            raise ValueError(f"目标校验值超出 {bits} 位范围")
    return value


def normalize_hex_string(data: bytes) -> str:
    """
    函数: normalize_hex_string
    作用: 将字节流格式化为以空格分隔的大写 HEX 字符串。
    参数:
        data: 字节流。
    返回:
        规范化后的字符串。
    """
    return " ".join(f"{byte:02X}" for byte in data)


def xor_checksum(data: bytes) -> int:
    """
    函数: xor_checksum
    作用: 计算 8 位异或校验值。
    参数:
        data: 字节流。
    返回:
        0-255 范围内的校验值。
    """
    result = 0
    for byte in data:
        result ^= byte
    return result


def sum_checksum(data: bytes, bits: int = 8) -> int:
    """
    函数: sum_checksum
    作用: 计算指定位宽的求和校验值。
    参数:
        data: 字节流。
        bits: 位宽，常用 8 / 16 / 32。
    返回:
        指定位宽掩码后的累加和。
    """
    if bits <= 0:
        raise ValueError("位宽必须大于 0")
    mask = (1 << bits) - 1
    return sum(data) & mask


def ones_complement_checksum(data: bytes, bits: int = 8) -> int:
    """
    函数: ones_complement_checksum
    作用: 计算指定位宽的反码校验值。
    参数:
        data: 字节流。
        bits: 位宽。
    返回:
        反码校验结果。
    """
    mask = (1 << bits) - 1
    return (~sum_checksum(data, bits)) & mask


def twos_complement_checksum(data: bytes, bits: int = 8) -> int:
    """
    函数: twos_complement_checksum
    作用: 计算指定位宽的补码校验值，8 位场景常作为 LRC 使用。
    参数:
        data: 字节流。
        bits: 位宽。
    返回:
        补码校验结果。
    """
    mask = (1 << bits) - 1
    return (-sum(data)) & mask


def format_checksum_value(value: int, bits: int = 8) -> str:
    """
    函数: format_checksum_value
    作用: 将校验值格式化为 HEX + DEC 文本，便于界面显示。
    参数:
        value: 校验值。
        bits: 位宽。
    返回:
        格式化文本，例如 0x0F（15）。
    """
    width = max(2, (bits + 3) // 4)
    return f"0x{value:0{width}X}（{value}）"


def get_checksum_value(bundle: dict[str, int], algorithm_id: str) -> int:
    """
    函数: get_checksum_value
    作用: 从结果字典中取出指定算法的校验值。
    参数:
        bundle: 结果字典。
        algorithm_id: 算法编号。
    返回:
        校验值。
    """
    meta = get_checksum_algorithm(algorithm_id)
    return int(bundle[str(meta["bundle_key"])])


def checksum_value_to_bytes(value: int, bits: int = 8, byteorder: str = "big") -> bytes:
    """
    函数: checksum_value_to_bytes
    作用: 将校验值转换为指定字节序的字节串。
    参数:
        value: 校验值。
        bits: 位宽。
        byteorder: 字节序，支持 big / little。
    返回:
        对应字节串。
    """
    if bits <= 0:
        raise ValueError("位宽必须大于 0")
    order = _normalize_byteorder(byteorder)
    width = max(1, (bits + 7) // 8)
    max_value = (1 << bits) - 1
    if not 0 <= value <= max_value:
        raise ValueError("校验值超出位宽范围")
    return int(value).to_bytes(width, byteorder=order, signed=False)


def format_checksum_bytes(value: int, bits: int = 8, byteorder: str = "big") -> str:
    """
    函数: format_checksum_bytes
    作用: 将校验值按字节序格式化为 HEX 字节串文本。
    参数:
        value: 校验值。
        bits: 位宽。
        byteorder: 字节序。
    返回:
        例如 "A0" 或 "12 34"。
    """
    return normalize_hex_string(checksum_value_to_bytes(value, bits, byteorder))


def append_checksum_bytes(data: bytes, value: int, bits: int = 8, byteorder: str = "big") -> bytes:
    """
    函数: append_checksum_bytes
    作用: 将校验字节追加到原始报文末尾。
    参数:
        data: 原始字节流。
        value: 校验值。
        bits: 位宽。
        byteorder: 字节序。
    返回:
        追加后的字节流。
    """
    return bytes(data) + checksum_value_to_bytes(value, bits, byteorder)


def calculate_checksum_bundle(data: bytes) -> dict[str, int]:
    """
    函数: calculate_checksum_bundle
    作用: 一次性计算页面展示所需的常用校验结果。
    参数:
        data: 字节流。
    返回:
        结果字典。
    """
    return {
        "xor": xor_checksum(data),
        "sum8": sum_checksum(data, 8),
        "sum16": sum_checksum(data, 16),
        "sum32": sum_checksum(data, 32),
        "ones8": ones_complement_checksum(data, 8),
        "twos8": twos_complement_checksum(data, 8),
    }


def _parse_hex_bytes(text: str) -> bytes:
    has_separator = bool(re.search(r"[\s,;，；]", text))
    tokens = [token for token in _BYTE_SPLIT_PATTERN.split(text) if token]

    if not has_separator and len(tokens) == 1:
        token = _strip_hex_prefix(tokens[0])
        if len(token) <= 2:
            return bytes([_parse_hex_token(token)])
        if len(token) % 2 != 0:
            raise ValueError("连续十六进制字符串长度必须为偶数")
        return bytes(int(token[i:i + 2], 16) for i in range(0, len(token), 2))

    values = [_parse_hex_token(token) for token in tokens]
    return bytes(values)


def _parse_decimal_bytes(text: str) -> bytes:
    tokens = [token for token in _BYTE_SPLIT_PATTERN.split(text) if token]
    values = []
    for token in tokens:
        try:
            value = int(token, 10)
        except ValueError as exc:
            raise ValueError(f"十进制字节 '{token}' 无法解析") from exc
        if not 0 <= value <= 0xFF:
            raise ValueError(f"十进制字节 '{token}' 超出 0-255 范围")
        values.append(value)
    return bytes(values)


def _parse_hex_token(token: str) -> int:
    value_text = _strip_hex_prefix(token)
    if not value_text:
        raise ValueError("存在空的十六进制字节")
    try:
        value = int(value_text, 16)
    except ValueError as exc:
        raise ValueError(f"十六进制字节 '{token}' 无法解析") from exc
    if not 0 <= value <= 0xFF:
        raise ValueError(f"十六进制字节 '{token}' 超出单字节范围")
    return value


def _parse_expected_hex_value(text: str) -> int:
    tokens = [token for token in _BYTE_SPLIT_PATTERN.split(text) if token]
    if len(tokens) > 1:
        value = 0
        for token in tokens:
            value = (value << 8) | _parse_hex_token(token)
        return value

    compact = _strip_hex_prefix(text.replace(" ", ""))
    try:
        return int(compact, 16)
    except ValueError as exc:
        raise ValueError("十六进制目标校验值无法解析") from exc


def _normalize_byteorder(byteorder: str) -> str:
    order = str(byteorder or "big").strip().lower()
    if order not in ("big", "little"):
        raise ValueError("字节序只支持 big 或 little")
    return order


def _strip_hex_prefix(token: str) -> str:
    return token[2:] if token.lower().startswith("0x") else token
