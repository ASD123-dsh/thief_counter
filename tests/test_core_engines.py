# -*- coding: utf-8 -*-
import math
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.book_loader import (
    is_supported_book_file,
    list_supported_book_files,
    load_book_content,
    load_book_text,
)
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


class TestBookLoader(unittest.TestCase):
    def test_supported_book_file_detection(self) -> None:
        self.assertTrue(is_supported_book_file("novel.txt"))
        self.assertTrue(is_supported_book_file("novel.EPUB"))
        self.assertFalse(is_supported_book_file("novel.pdf"))

    def test_list_supported_book_files_filters_and_sorts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.epub").write_bytes(b"epub")
            (root / "A.txt").write_text("txt", encoding="utf-8")
            (root / "ignore.md").write_text("md", encoding="utf-8")
            files = list_supported_book_files(str(root))
            self.assertEqual(files, ["A.txt", "b.epub"])

    def test_load_book_text_reads_epub_in_spine_order(self) -> None:
        with TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "sample.epub"
            with zipfile.ZipFile(epub_path, "w") as zf:
                zf.writestr(
                    "META-INF/container.xml",
                    """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
                )
                zf.writestr(
                    "OPS/content.opf",
                    """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="chap1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chap2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chap1"/>
    <itemref idref="chap2"/>
  </spine>
</package>
""",
                )
                zf.writestr(
                    "OPS/chapter1.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>第一章</h1>
    <p>你好，世界。</p>
  </body>
</html>
""",
                )
                zf.writestr(
                    "OPS/chapter2.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>第二章</h1>
    <p>继续阅读。</p>
  </body>
</html>
""",
                )

            text = load_book_text(str(epub_path))
            self.assertIn("第一章", text)
            self.assertIn("你好，世界。", text)
            self.assertIn("第二章", text)
            self.assertIn("继续阅读。", text)
            self.assertLess(text.index("第一章"), text.index("第二章"))

    def test_load_book_content_reads_epub_nav_chapters(self) -> None:
        with TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "nav.epub"
            with zipfile.ZipFile(epub_path, "w") as zf:
                zf.writestr(
                    "META-INF/container.xml",
                    """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
                )
                zf.writestr(
                    "OPS/package.opf",
                    """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="chap1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chap2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chap1"/>
    <itemref idref="chap2"/>
  </spine>
</package>
""",
                )
                zf.writestr(
                    "OPS/nav.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <body>
    <nav epub:type="toc">
      <ol>
        <li><a href="chapter1.xhtml#c1">开篇</a></li>
        <li><a href="chapter2.xhtml#c2">终章</a></li>
      </ol>
    </nav>
  </body>
</html>
""",
                )
                zf.writestr(
                    "OPS/chapter1.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1 id="c1">第一章</h1>
    <p>这里是开篇。</p>
  </body>
</html>
""",
                )
                zf.writestr(
                    "OPS/chapter2.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1 id="c2">第二章</h1>
    <p>这里是终章。</p>
  </body>
</html>
""",
                )

            content = load_book_content(str(epub_path))
            self.assertEqual([chapter.title for chapter in content.chapters], ["开篇", "终章"])
            self.assertLess(content.chapters[0].char_offset, content.chapters[1].char_offset)
            self.assertIn("第一章", content.text)
            self.assertIn("第二章", content.text)

    def test_load_book_content_reads_epub_ncx_chapters(self) -> None:
        with TemporaryDirectory() as tmp:
            epub_path = Path(tmp) / "ncx.epub"
            with zipfile.ZipFile(epub_path, "w") as zf:
                zf.writestr(
                    "META-INF/container.xml",
                    """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
                )
                zf.writestr(
                    "OPS/content.opf",
                    """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="chap1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chap2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chap1"/>
    <itemref idref="chap2"/>
  </spine>
</package>
""",
                )
                zf.writestr(
                    "OPS/toc.ncx",
                    """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="n1" playOrder="1">
      <navLabel><text>序章</text></navLabel>
      <content src="chapter1.xhtml#intro"/>
    </navPoint>
    <navPoint id="n2" playOrder="2">
      <navLabel><text>尾章</text></navLabel>
      <content src="chapter2.xhtml#finale"/>
    </navPoint>
  </navMap>
</ncx>
""",
                )
                zf.writestr(
                    "OPS/chapter1.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h2 id="intro">序章标题</h2>
    <p>正文一。</p>
  </body>
</html>
""",
                )
                zf.writestr(
                    "OPS/chapter2.xhtml",
                    """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h2 id="finale">尾章标题</h2>
    <p>正文二。</p>
  </body>
</html>
""",
                )

            content = load_book_content(str(epub_path))
            self.assertEqual([chapter.title for chapter in content.chapters], ["序章", "尾章"])
            self.assertLess(content.chapters[0].char_offset, content.chapters[1].char_offset)
            self.assertIn("正文一。", content.text)
            self.assertIn("正文二。", content.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
