"""SegmenterAgent — split books into chapters and evidence-bearing SourceUnits.

Each paragraph of a chapter becomes one SourceUnit whose raw_text is the
normalized paragraph text — the string against which every evidence_span is
later verified (strict substring).  Paragraphs are typed:
    formula     方劑塊 (composition + 煎服法)
    commentary  注家文字 (heuristics: 注/按/愚謂/方解 markers or commentary book)
    variant     校勘/異文
    case        醫案
    original    everything else in an original-text book
"""

from __future__ import annotations

import re

from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..protocol import category_path
from ..schemas import SourceUnit
from ..utils import write_jsonl
from .catalog import CatalogAgent

_FORMULA_BLOCK = re.compile(r"右[一二三四五六七八九十]+味")
_VARIANT_HINT = re.compile(r"(一作|一云|一方|或作|《[^》]*》作|校勘|異文)")
_COMMENT_HINT = re.compile(
    r"^(注|註|按|愚按|愚謂|方解|喻氏|程氏|柯氏|尤氏|錢氏|張氏|成氏|魏氏|沈氏|徐氏|"
    r"[一-鿿]{1,4}(曰|云|注云|按云))")
_CASE_HINT = re.compile(r"(診|初診|復診|二診|三診|某|男|女).{0,12}(年|歲|月|日)")


class SegmenterAgent:
    name = "SegmenterAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.catalog = CatalogAgent(self.config)
        self.entities = EntityExtractorAgent()

    def classify_paragraph(self, text: str, book_type: str, chapter_title: str) -> str:
        if any(h in chapter_title for h in ("序", "凡例", "目錄", "原序", "校序")):
            return "preface"
        if _FORMULA_BLOCK.search(text) or re.match(r"^[一-鿿]{2,10}[湯散丸]方", text):
            return "formula"
        if _VARIANT_HINT.search(text) and len(text) < 120:
            return "variant"
        if book_type == "case_collection" or _CASE_HINT.search(text[:40]):
            if book_type == "case_collection":
                return "case"
        if _COMMENT_HINT.search(text):
            return "commentary"
        if book_type == "commentary":
            # commentary books quote the classic then comment; long discursive
            # paragraphs without clause structure are treated as commentary
            if not re.search(r"(主之|為病|脈[一-鿿]{1,3}者)", text):
                return "commentary"
        return "original"

    # ------------------------------------------------------------------
    def segment_book(self, raw_category: str, book_dir) -> tuple[dict, list[SourceUnit]]:
        record, parsed = self.catalog.parse_book(raw_category, book_dir)
        units: list[SourceUnit] = []
        ch_idx, su_seq = 0, 0
        for sec in parsed.sections:
            if sec.level < 2 or not sec.paragraphs:
                continue
            ch_idx += 1
            chapter_id = f"CH_{record['book_short']}_{ch_idx:03d}"
            for p_i, para in enumerate(sec.paragraphs):
                su_seq += 1
                text = para["text"]
                ttype = self.classify_paragraph(text, record["book_type"], sec.title)
                units.append(SourceUnit(
                    source_unit_id=f"SU_{record['book_short']}_{su_seq:06d}",
                    category_path=category_path(raw_category),
                    book_id=record["book_id"],
                    book_title=record["book_title"],
                    book_type=record["book_type"],
                    chapter_id=chapter_id,
                    chapter_title=sec.title,
                    seq=p_i,
                    raw_text=text,
                    text_type=ttype,
                    clause_no=para.get("clause_no"),
                    entities=self.entities.extract(text),
                ))
        return record, units

    def run(self, books: list[str] | None = None, categories: list[str] | None = None) -> dict:
        """Segment the whole corpus (or a filtered subset) to JSONL stores."""
        out_dir = self.config.source_units_dir
        stats = {"books": 0, "source_units": 0, "by_type": {}}
        for raw_category, book_dir in self.catalog.iter_book_dirs():
            if categories and raw_category not in categories:
                continue
            if books and book_dir.name not in books:
                continue
            record, units = self.segment_book(raw_category, book_dir)
            write_jsonl(out_dir / f"{record['book_id']}.jsonl",
                        (u.to_dict() for u in units))
            stats["books"] += 1
            stats["source_units"] += len(units)
            for u in units:
                stats["by_type"][u.text_type] = stats["by_type"].get(u.text_type, 0) + 1
        return stats
