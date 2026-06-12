"""Parser for 中醫笈成 wiki-style book files.

File format (observed in book-20180111):
  ======書名======                  level-1 heading (book title)
  <book>書名=…\n作者=…\n分類=…</book>  metadata block
  =====卷/篇=====                   level-2 heading
  ====章節====                      level-3 heading
  <#/> / <#1/> / <# +2.5em/>        modern clause-number markers (條文版)
  <j>弘</j>                          variant-char markup
  [[book:傷寒論_條文版:]]            cross references
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..utils import normalize_text

_BOOK_BLOCK = re.compile(r"<book>(.*?)</book>", re.S)
_HEADING = re.compile(r"^(={2,6})\s*([^=]+?)\s*\1\s*$", re.M)
_CLAUSE_NO = re.compile(r"<#\s*([0-9]*)[^>/]*/>")
_INLINE_TAG = re.compile(r"</?[a-zA-Z~][^>]*>|<~[^>]*/>")
_WIKILINK = re.compile(r"\[\[(?:book|category)?:?([^\]\|]*?):?(?:\|[^\]]*)?\]\]")

COMMENTARY_BOOK_HINTS = ("注", "註", "箋", "疏", "解", "辨", "辯", "廣注", "條辨", "貫珠",
                         "溯源", "來蘇", "纘論", "緒論", "懸解", "輯義", "述義", "心典",
                         "淺註", "歌括", "方歌", "金鑒", "金鑑", "集註", "析義", "醫訣",
                         "翼", "指掌", "審證", "明理")
CASE_BOOK_HINTS = ("醫案", "實驗錄", "九十論")


@dataclass
class ParsedSection:
    level: int
    title: str
    paragraphs: list[dict] = field(default_factory=list)  # {text, clause_no}


@dataclass
class ParsedBook:
    title: str
    meta: dict[str, str]
    sections: list[ParsedSection] = field(default_factory=list)

    @property
    def author(self) -> str: return self.meta.get("作者", "")

    @property
    def dynasty(self) -> str: return self.meta.get("朝代", "")

    @property
    def raw_category(self) -> str: return self.meta.get("分類", "")

    def book_type(self) -> str:
        t = self.title
        if any(h in t for h in CASE_BOOK_HINTS):
            return "case_collection"
        if any(h in t for h in COMMENTARY_BOOK_HINTS):
            return "commentary"
        if "合刊" in t or "全書" in t or "六書" in t:
            return "compilation"
        return "original"


def strip_markup(text: str) -> str:
    """Remove inline wiki markup but keep textual content byte-stable."""
    text = _CLAUSE_NO.sub("", text)
    text = _INLINE_TAG.sub("", text)
    text = _WIKILINK.sub(lambda m: m.group(1) or "", text)
    return text


def parse_book_text(raw: str, fallback_title: str = "") -> ParsedBook:
    raw = normalize_text(raw)

    meta: dict[str, str] = {}
    m = _BOOK_BLOCK.search(raw)
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if "=" in line:
                k, _, v = line.partition("=")
                meta[k.strip()] = v.strip()
        raw = raw[:m.start()] + raw[m.end():]

    title = meta.get("書名", "") or fallback_title

    # split by headings
    sections: list[ParsedSection] = []
    pos = 0
    headings = list(_HEADING.finditer(raw))
    if not headings:
        sections.append(ParsedSection(level=3, title=fallback_title or title or "正文"))
        _fill_paragraphs(sections[-1], raw)
        return ParsedBook(title=title or fallback_title, meta=meta, sections=sections)

    # preface text before first heading
    pre = raw[:headings[0].start()].strip()
    if pre:
        sec = ParsedSection(level=2, title="卷首")
        _fill_paragraphs(sec, pre)
        sections.append(sec)

    for i, h in enumerate(headings):
        level = 7 - len(h.group(1))  # ====== → 1, ===== → 2, ==== → 3
        sec_title = strip_markup(h.group(2)).strip()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(raw)
        body = raw[h.end():end]
        sec = ParsedSection(level=level, title=sec_title)
        _fill_paragraphs(sec, body)
        if level == 1 and not title:
            title = sec_title
        if sec.paragraphs or level >= 2:
            sections.append(sec)
        pos = end

    return ParsedBook(title=title or fallback_title, meta=meta, sections=sections)


def _fill_paragraphs(sec: ParsedSection, body: str) -> None:
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        clause_no = None
        mn = _CLAUSE_NO.search(block)
        if mn:
            clause_no = mn.group(1) or None
        text = strip_markup(block)
        text = re.sub(r"\n+", "", text).strip()
        if len(text) < 4:
            continue
        sec.paragraphs.append({"text": text, "clause_no": clause_no})


# ---------------------------------------------------------------------------
# book id aliases for well-known editions (spec-style readable ids)
# ---------------------------------------------------------------------------

BOOK_ALIASES = {
    "傷寒論_宋本": "SHL_SONGBEN",
    "傷寒論(宋本)": "SHL_SONGBEN",
    "傷寒論_條文版": "SHL_TIAOWEN",
    "傷寒論(條文版)": "SHL_TIAOWEN",
    "傷寒論": "SHL_TIAOWEN",
    "傷寒雜病論_桂本": "SHL_GUIBEN",
    "傷寒論_千金翼方版": "SHL_QJYF",
    "金匱要略方論": "JGYL_FANGLUN",
    "金匱要略方論(條文版)": "JGYL_FANGLUN",
    "金匱要略_條文版": "JGYL_TIAOWEN",
    "金匱要略心典": "JGYL_XINDIAN",
    "金匱要略淺註": "JGYL_QIANZHU",
    "金匱玉函經二注": "JGYH_ERZHU",
    "金匱玉函要略輯義": "JGYL_JIYI",
    "金匱玉函要略述義": "JGYL_SHUYI",
    "金匱方歌括": "JG_FANGGEKUO",
    "高注金匱要略": "JGYL_GAOZHU",
    "註解傷寒論": "SHL_ZHUJIE",
    "傷寒論注": "SHL_LUNZHU",
    "傷寒來蘇集": "SHL_LAISU",
    "傷寒貫珠集": "SHL_GUANZHU",
    "傷寒論類方": "SHL_LEIFANG",
    "經方實驗錄": "JF_SHIYANLU",
    "曹氏傷寒金匱發微合刊": "CAOSHI_FAWEI",
    "傷寒明理論": "SHL_MINGLI",
    "傷寒溯源集": "SHL_SUYUAN",
}


def book_short_id(dir_name: str, title: str) -> str:
    for key in (dir_name, title):
        if key in BOOK_ALIASES:
            return BOOK_ALIASES[key]
    from ..utils import short_hash
    return "B" + short_hash(dir_name or title, 8)
