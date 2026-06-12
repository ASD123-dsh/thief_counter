# -*- coding: utf-8 -*-
"""
文件: src/core/book_loader.py
描述: 摸鱼阅读器的电子书加载逻辑，支持 TXT 与 EPUB 文本提取及章节目录解析。
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree as ET


SUPPORTED_BOOK_EXTENSIONS = (".txt", ".epub")

_HTML_MEDIA_TYPES = {
    "application/xhtml+xml",
    "text/html",
}

_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "body",
    "br",
    "caption",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}

_IGNORE_TAGS = {"head", "script", "style", "svg"}


@dataclass(frozen=True)
class BookChapter:
    title: str
    char_offset: int


@dataclass(frozen=True)
class BookContent:
    text: str
    chapters: list[BookChapter]


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._ignore_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = (tag or "").lower()
        if tag in _IGNORE_TAGS:
            self._ignore_depth += 1
            return
        if self._ignore_depth:
            return
        if tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = (tag or "").lower()
        if tag in _IGNORE_TAGS:
            if self._ignore_depth > 0:
                self._ignore_depth -= 1
            return
        if self._ignore_depth:
            return
        if tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignore_depth or not data:
            return
        text = data.replace("\xa0", " ")
        self._parts.append(text)

    def get_text(self) -> str:
        text = "".join(self._parts)
        text = text.replace("\r", "")
        text = re.sub(r"[ \t\f\v]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class _StructuredTextBuilder:
    def __init__(self) -> None:
        self._parts: list[str] = []
        self._length = 0
        self.anchors: dict[str, int] = {}

    @property
    def length(self) -> int:
        return self._length

    def append_break(self) -> None:
        if self._length <= 0:
            return
        self._trim_trailing_spaces()
        if self._length <= 0:
            return
        if self._endswith("\n"):
            return
        self._append_piece("\n")

    def append_text(self, text: str) -> None:
        if not text:
            return
        compact = re.sub(r"\s+", " ", text.replace("\xa0", " ").replace("\r", " "))
        if not compact:
            return
        if self._length <= 0 or self._endswith((" ", "\n")):
            compact = compact.lstrip()
        if not compact:
            return
        self._append_piece(compact)

    def mark_anchor(self, name: str) -> None:
        key = str(name or "").strip()
        if key and key not in self.anchors:
            self.anchors[key] = self._length

    def build_text(self) -> str:
        self._trim_trailing_spaces()
        while self._parts and self._parts[-1] == "\n":
            self._parts.pop()
            self._length -= 1
        return "".join(self._parts)

    def _append_piece(self, piece: str) -> None:
        if not piece:
            return
        self._parts.append(piece)
        self._length += len(piece)

    def _trim_trailing_spaces(self) -> None:
        while self._parts:
            tail = self._parts[-1]
            if not tail:
                self._parts.pop()
                continue
            trimmed = tail.rstrip(" ")
            if trimmed == tail:
                break
            self._length -= len(tail) - len(trimmed)
            if trimmed:
                self._parts[-1] = trimmed
                break
            self._parts.pop()

    def _endswith(self, suffix: str | tuple[str, ...]) -> bool:
        if not self._parts:
            return False
        tail = self._parts[-1]
        if not tail:
            return False
        return tail.endswith(suffix)


def is_supported_book_file(name: str) -> bool:
    lower_name = str(name or "").lower()
    return any(lower_name.endswith(ext) for ext in SUPPORTED_BOOK_EXTENSIONS)


def list_supported_book_files(path: str) -> list[str]:
    if not os.path.isdir(path):
        raise ValueError(f"非有效目录: {path}")
    try:
        entries = os.listdir(path)
    except Exception as exc:
        raise ValueError(f"读取目录失败: {exc}") from exc
    files = [
        name
        for name in entries
        if is_supported_book_file(name) and os.path.isfile(os.path.join(path, name))
    ]
    files.sort(key=lambda item: item.lower())
    return files


def load_book_content(file_path: str) -> BookContent:
    ext = os.path.splitext(str(file_path or ""))[1].lower()
    if ext == ".txt":
        return BookContent(text=_load_text_file(file_path), chapters=[])
    if ext == ".epub":
        return _load_epub_content(file_path)
    raise ValueError("不支持的电子书格式，仅支持 TXT 和 EPUB")


def load_book_text(file_path: str) -> str:
    return load_book_content(file_path).text


def iter_book_text_chunks(file_path: str, chunk_size: int = 64 * 1024):
    text = load_book_text(file_path)
    if not text:
        return
    step = max(1, int(chunk_size))
    for idx in range(0, len(text), step):
        yield text[idx:idx + step]


def _load_text_file(file_path: str) -> str:
    last_error: Exception | None = None
    for encoding, errors in (("utf-8", "strict"), ("gbk", "ignore")):
        try:
            with open(file_path, "r", encoding=encoding, errors=errors) as f:
                return f.read()
        except Exception as exc:
            last_error = exc
    raise ValueError(f"读取文本失败: {last_error}") from last_error


def _load_epub_content(file_path: str) -> BookContent:
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            opf_path = _find_opf_path(zf)
            manifest, spine, toc_id = _read_epub_manifest_and_spine(zf, opf_path)
            sections: list[dict[str, object]] = []
            joined_parts: list[str] = []
            total_len = 0
            seen_paths: set[str] = set()
            for doc_path in _iter_epub_document_paths(manifest, spine, opf_path):
                if doc_path in seen_paths:
                    continue
                seen_paths.add(doc_path)
                try:
                    raw = zf.read(doc_path)
                except KeyError:
                    continue
                text, anchors = _extract_document_text_and_anchors(_decode_document_bytes(raw))
                if not text:
                    continue
                if joined_parts:
                    joined_parts.append("\n\n")
                    total_len += 2
                start_offset = total_len
                sections.append({
                    "path": doc_path,
                    "start": start_offset,
                    "text": text,
                    "anchors": anchors,
                })
                joined_parts.append(text)
                total_len += len(text)
            if not sections:
                raise ValueError("EPUB 中未找到可阅读文本")
            chapters = _extract_epub_chapters(zf, manifest, spine, opf_path, toc_id, sections)
            return BookContent(text="".join(joined_parts), chapters=chapters)
    except ValueError:
        raise
    except zipfile.BadZipFile as exc:
        raise ValueError(f"EPUB 文件损坏或格式无效: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"读取 EPUB 失败: {exc}") from exc


def _find_opf_path(zf: zipfile.ZipFile) -> str:
    try:
        raw = zf.read("META-INF/container.xml")
        root = ET.fromstring(raw)
        rootfile = root.find(".//{*}rootfile")
        if rootfile is not None:
            full_path = str(rootfile.attrib.get("full-path", "") or "").strip()
            if full_path:
                return full_path
    except Exception:
        pass

    opf_candidates = [name for name in zf.namelist() if name.lower().endswith(".opf")]
    if len(opf_candidates) == 1:
        return opf_candidates[0]
    raise ValueError("EPUB 中未找到 OPF 包描述文件")


def _read_epub_manifest_and_spine(
    zf: zipfile.ZipFile,
    opf_path: str,
) -> tuple[dict[str, dict[str, str]], list[str], str]:
    root = ET.fromstring(zf.read(opf_path))
    manifest: dict[str, dict[str, str]] = {}

    for item in root.findall(".//{*}manifest/{*}item"):
        item_id = str(item.attrib.get("id", "") or "").strip()
        href = str(item.attrib.get("href", "") or "").strip()
        media_type = str(item.attrib.get("media-type", "") or "").strip().lower()
        properties = str(item.attrib.get("properties", "") or "").strip().lower()
        if item_id and href:
            manifest[item_id] = {
                "href": href,
                "media_type": media_type,
                "properties": properties,
            }

    spine_elem = root.find(".//{*}spine")
    spine = [
        str(itemref.attrib.get("idref", "") or "").strip()
        for itemref in root.findall(".//{*}spine/{*}itemref")
        if str(itemref.attrib.get("idref", "") or "").strip()
    ]
    toc_id = ""
    if spine_elem is not None:
        toc_id = str(spine_elem.attrib.get("toc", "") or "").strip()
    return manifest, spine, toc_id


def _iter_epub_document_paths(
    manifest: dict[str, dict[str, str]],
    spine: list[str],
    opf_path: str,
):
    opf_dir = posixpath.dirname(opf_path)
    yielded = False

    for item_id in spine:
        item = manifest.get(item_id)
        if not item:
            continue
        href = str(item.get("href", "") or "").strip()
        media_type = str(item.get("media_type", "") or "").strip().lower()
        if not href:
            continue
        if media_type not in _HTML_MEDIA_TYPES and not href.lower().endswith((".xhtml", ".html", ".htm")):
            continue
        yielded = True
        yield _join_zip_path(opf_dir, href)

    if yielded:
        return

    for item in manifest.values():
        href = str(item.get("href", "") or "").strip()
        media_type = str(item.get("media_type", "") or "").strip().lower()
        if not href:
            continue
        if media_type in _HTML_MEDIA_TYPES or href.lower().endswith((".xhtml", ".html", ".htm")):
            yield _join_zip_path(opf_dir, href)


def _join_zip_path(base_dir: str, href: str) -> str:
    return posixpath.normpath(posixpath.join(base_dir, href))


def _decode_document_bytes(raw: bytes) -> str:
    encodings: list[str] = []
    for pattern in (
        rb"encoding\s*=\s*['\"]([A-Za-z0-9._-]+)['\"]",
        rb"charset\s*=\s*['\"]?([A-Za-z0-9._-]+)",
    ):
        match = re.search(pattern, raw[:512], re.IGNORECASE)
        if match:
            try:
                encoding = match.group(1).decode("ascii", errors="ignore").strip()
            except Exception:
                encoding = ""
            if encoding:
                encodings.append(encoding)

    for encoding in encodings + ["utf-8", "utf-16", "gb18030"]:
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


def _html_to_text(html_text: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()
    return parser.get_text()


def _extract_document_text_and_anchors(html_text: str) -> tuple[str, dict[str, int]]:
    try:
        root = ET.fromstring(html_text)
    except Exception:
        return _html_to_text(html_text), {}
    builder = _StructuredTextBuilder()
    _walk_xml_text(root, builder)
    return builder.build_text(), builder.anchors


def _walk_xml_text(elem: ET.Element, builder: _StructuredTextBuilder) -> None:
    tag = _local_name(elem.tag).lower()
    if tag in _IGNORE_TAGS:
        return
    is_block = tag in _BLOCK_TAGS
    if is_block:
        builder.append_break()
    for attr_name, attr_value in elem.attrib.items():
        if _local_name(attr_name).lower() in {"id", "name"}:
            builder.mark_anchor(str(attr_value or "").strip())
    builder.append_text(str(elem.text or ""))
    for child in list(elem):
        _walk_xml_text(child, builder)
        builder.append_text(str(child.tail or ""))
    if is_block:
        builder.append_break()


def _extract_epub_chapters(
    zf: zipfile.ZipFile,
    manifest: dict[str, dict[str, str]],
    spine: list[str],
    opf_path: str,
    toc_id: str,
    sections: list[dict[str, object]],
) -> list[BookChapter]:
    toc_entries = _extract_epub_toc_entries(zf, manifest, opf_path, toc_id)
    if not toc_entries:
        return []
    section_map = {
        str(section["path"]): section
        for section in sections
        if section.get("path")
    }
    chapters: list[BookChapter] = []
    seen: set[tuple[str, int]] = set()
    for title, target in toc_entries:
        clean_title = _collapse_inline_text(title)
        if not clean_title:
            continue
        target_path, fragment = _split_target_ref(target)
        section = section_map.get(target_path)
        if not section:
            continue
        offset = int(section.get("start", 0) or 0)
        if fragment:
            anchors = section.get("anchors", {})
            if isinstance(anchors, dict) and fragment in anchors:
                try:
                    offset += int(anchors[fragment])
                except Exception:
                    pass
        key = (clean_title.lower(), offset)
        if key in seen:
            continue
        seen.add(key)
        chapters.append(BookChapter(clean_title, max(0, offset)))
    return chapters


def _extract_epub_toc_entries(
    zf: zipfile.ZipFile,
    manifest: dict[str, dict[str, str]],
    opf_path: str,
    toc_id: str,
) -> list[tuple[str, str]]:
    nav_entries = _extract_epub_nav_entries(zf, manifest, opf_path)
    if nav_entries:
        return nav_entries
    return _extract_epub_ncx_entries(zf, manifest, opf_path, toc_id)


def _extract_epub_nav_entries(
    zf: zipfile.ZipFile,
    manifest: dict[str, dict[str, str]],
    opf_path: str,
) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    nav_items = []
    for item in manifest.values():
        properties = str(item.get("properties", "") or "").lower().split()
        if "nav" in properties:
            nav_items.append(item)
    if not nav_items:
        for item in manifest.values():
            href = str(item.get("href", "") or "").lower()
            media_type = str(item.get("media_type", "") or "").lower()
            if media_type in _HTML_MEDIA_TYPES and "nav" in href:
                nav_items.append(item)
    opf_dir = posixpath.dirname(opf_path)
    for item in nav_items:
        href = str(item.get("href", "") or "").strip()
        if not href:
            continue
        nav_path = _join_zip_path(opf_dir, href)
        try:
            root = ET.fromstring(_decode_document_bytes(zf.read(nav_path)))
        except Exception:
            continue
        nav_nodes = [
            elem for elem in root.iter()
            if _local_name(elem.tag).lower() == "nav"
        ]
        toc_navs = []
        for nav in nav_nodes:
            nav_type = " ".join(
                str(val or "").strip().lower()
                for key, val in nav.attrib.items()
                if _local_name(key).lower() == "type"
            )
            if "toc" in nav_type.split():
                toc_navs.append(nav)
        if not toc_navs and nav_nodes:
            toc_navs = [nav_nodes[0]]
        for nav in toc_navs:
            for elem in nav.iter():
                if _local_name(elem.tag).lower() != "a":
                    continue
                href_val = str(elem.attrib.get("href", "") or "").strip()
                title = _collapse_inline_text("".join(elem.itertext()))
                if href_val and title:
                    entries.append((title, _resolve_relative_target(nav_path, href_val)))
        if entries:
            break
    return entries


def _extract_epub_ncx_entries(
    zf: zipfile.ZipFile,
    manifest: dict[str, dict[str, str]],
    opf_path: str,
    toc_id: str,
) -> list[tuple[str, str]]:
    ncx_item = None
    if toc_id:
        ncx_item = manifest.get(toc_id)
    if ncx_item is None:
        for item in manifest.values():
            if str(item.get("media_type", "") or "").lower() == "application/x-dtbncx+xml":
                ncx_item = item
                break
    if ncx_item is None:
        return []
    href = str(ncx_item.get("href", "") or "").strip()
    if not href:
        return []
    ncx_path = _join_zip_path(posixpath.dirname(opf_path), href)
    try:
        root = ET.fromstring(zf.read(ncx_path))
    except Exception:
        return []
    entries: list[tuple[str, str]] = []
    for nav_point in root.findall(".//{*}navPoint"):
        title = _collapse_inline_text("".join(text for text in nav_point.findtext(".//{*}text", default="").splitlines()))
        content = nav_point.find(".//{*}content")
        if content is None:
            continue
        src = str(content.attrib.get("src", "") or "").strip()
        if title and src:
            entries.append((title, _resolve_relative_target(ncx_path, src)))
    return entries


def _resolve_relative_target(base_path: str, href: str) -> str:
    raw = str(href or "").strip()
    if not raw:
        return ""
    path_part, fragment = _split_target_ref(raw)
    if path_part:
        resolved_path = _join_zip_path(posixpath.dirname(base_path), path_part)
    else:
        resolved_path = posixpath.normpath(base_path)
    if fragment:
        return f"{resolved_path}#{fragment}"
    return resolved_path


def _split_target_ref(target: str) -> tuple[str, str]:
    raw = str(target or "").strip()
    if "#" not in raw:
        return raw, ""
    path_part, fragment = raw.split("#", 1)
    return path_part, fragment


def _local_name(tag: object) -> str:
    text = str(tag or "")
    if "}" in text:
        return text.rsplit("}", 1)[-1]
    return text


def _collapse_inline_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").replace("\xa0", " ")).strip()
