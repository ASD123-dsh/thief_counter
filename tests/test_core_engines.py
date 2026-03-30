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


if __name__ == "__main__":
    unittest.main(verbosity=2)
