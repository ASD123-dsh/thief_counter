# -*- coding: utf-8 -*-
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.expr_parser import safe_eval
from core.checksum_engine import (
    append_checksum_bytes,
    calculate_checksum_bundle,
    checksum_value_to_bytes,
    format_checksum_bytes,
    get_checksum_algorithm,
    get_checksum_value,
    normalize_hex_string,
    parse_checksum_input,
    parse_expected_checksum,
    sum_checksum,
    twos_complement_checksum,
    xor_checksum,
)
from core.programmer_engine import (
    bit_and,
    bit_not,
    bit_or,
    bit_xor,
    parse_input,
    shl,
    shr,
    to_base_str,
)
from core.scientific_engine import get_functions, get_variables


class TestExprParser(unittest.TestCase):
    def test_safe_eval_basic_arithmetic(self) -> None:
        self.assertAlmostEqual(safe_eval("(1+2)*3-4/2"), 7.0)

    def test_safe_eval_blocks_unknown_name(self) -> None:
        with self.assertRaises(ValueError):
            safe_eval("unknown(1)")

    def test_safe_eval_scientific_context(self) -> None:
        fns = get_functions("deg")
        vars_ = get_variables()
        result = safe_eval("sin(30)+log(100)", functions=fns, variables=vars_)
        self.assertAlmostEqual(result, 2.5, places=6)


class TestScientificEngine(unittest.TestCase):
    def test_deg_and_rad_modes(self) -> None:
        deg = get_functions("deg")
        rad = get_functions("rad")
        self.assertAlmostEqual(deg["sin"](30), 0.5, places=6)
        self.assertAlmostEqual(rad["sin"](math.pi / 6), 0.5, places=6)

    def test_factorial_guard(self) -> None:
        funcs = get_functions("deg")
        with self.assertRaises(ValueError):
            funcs["fact"](1.5)


class TestProgrammerEngine(unittest.TestCase):
    def test_base_parse_and_format(self) -> None:
        self.assertEqual(parse_input("FF", "HEX"), 255)
        self.assertEqual(parse_input("1111 1111", "BIN"), 255)
        self.assertEqual(to_base_str(255, "HEX"), "FF")
        self.assertEqual(to_base_str(5, "BIN", bits=8), "00000101")

    def test_bit_ops(self) -> None:
        self.assertEqual(bit_and(0b1010, 0b1100), 0b1000)
        self.assertEqual(bit_or(0b1010, 0b1100), 0b1110)
        self.assertEqual(bit_xor(0b1010, 0b1100), 0b0110)
        self.assertEqual(bit_not(0), 0xFFFFFFFF)
        self.assertEqual(shl(1, 3), 8)
        self.assertEqual(shr(8, 3), 1)


class TestChecksumEngine(unittest.TestCase):
    def test_checksum_algorithm_metadata(self) -> None:
        meta = get_checksum_algorithm("sum16")
        self.assertEqual(meta["id"], "SUM16")
        self.assertEqual(meta["bits"], 16)

    def test_parse_hex_text_and_decimal_inputs(self) -> None:
        self.assertEqual(parse_checksum_input("68 65 6C 6C 6F", "HEX"), b"hello")
        self.assertEqual(parse_checksum_input("68656C6C6F", "HEX"), b"hello")
        self.assertEqual(parse_checksum_input("104 101 108 108 111", "DEC"), b"hello")
        self.assertEqual(parse_checksum_input("hello", "TEXT"), b"hello")

    def test_checksum_algorithms(self) -> None:
        data = parse_checksum_input("01 02 03", "HEX")
        self.assertEqual(xor_checksum(data), 0x00)
        self.assertEqual(sum_checksum(data, 8), 0x06)
        self.assertEqual(sum_checksum(data, 16), 0x0006)
        self.assertEqual(twos_complement_checksum(data, 8), 0xFA)

    def test_checksum_bundle_and_normalize(self) -> None:
        data = parse_checksum_input("0x10 0x20 0x30", "HEX")
        bundle = calculate_checksum_bundle(data)
        self.assertEqual(normalize_hex_string(data), "10 20 30")
        self.assertEqual(bundle["xor"], 0x00)
        self.assertEqual(bundle["sum8"], 0x60)
        self.assertEqual(bundle["sum16"], 0x0060)
        self.assertEqual(bundle["sum32"], 0x00000060)
        self.assertEqual(bundle["ones8"], 0x9F)
        self.assertEqual(bundle["twos8"], 0xA0)
        self.assertEqual(get_checksum_value(bundle, "SUM16"), 0x0060)

    def test_invalid_checksum_input_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_checksum_input("123", "HEX")
        with self.assertRaises(ValueError):
            parse_checksum_input("300", "DEC")

    def test_parse_expected_checksum(self) -> None:
        self.assertEqual(parse_expected_checksum("A0", "HEX", 8), 0xA0)
        self.assertEqual(parse_expected_checksum("00 A0", "HEX", 16), 0x00A0)
        self.assertEqual(parse_expected_checksum("160", "DEC", 8), 160)
        with self.assertRaises(ValueError):
            parse_expected_checksum("1FF", "HEX", 8)

    def test_checksum_bytes_and_append(self) -> None:
        self.assertEqual(checksum_value_to_bytes(0x1234, 16, "big"), b"\x12\x34")
        self.assertEqual(checksum_value_to_bytes(0x1234, 16, "little"), b"\x34\x12")
        self.assertEqual(format_checksum_bytes(0x1234, 16, "little"), "34 12")
        self.assertEqual(append_checksum_bytes(b"\x68\x01", 0xA0, 8, "big"), b"\x68\x01\xA0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
