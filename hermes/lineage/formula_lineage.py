"""FormulaLineageAgent — 方剂溯源 across the corpus.

For a formula name: occurrences across books (ordered by dynasty), earliest
source, composition variants, related 加減方, indication contexts — each item
backed by source-unit evidence.
"""

from __future__ import annotations

from collections import defaultdict

from ..config import HermesConfig
from ..knowledge.lexicon import LEXICON
from ..rag.text_rag import ClassicalTextRAGAgent
from ..schemas import InitialRule
from ..utils import read_jsonl, write_json

_DYNASTY_ORDER = ["先秦", "漢", "東漢", "西漢", "晉", "東晉", "南北朝", "隋", "唐",
                  "五代", "宋", "北宋", "南宋", "金", "元", "明", "清", "民國", "現代"]


def dynasty_rank(d: str) -> int:
    for i, k in enumerate(_DYNASTY_ORDER):
        if d and k in d:
            return i
    return len(_DYNASTY_ORDER)


class FormulaLineageAgent:
    name = "FormulaLineageAgent"

    def __init__(self, config: HermesConfig | None = None,
                 rag: ClassicalTextRAGAgent | None = None) -> None:
        self.config = config or HermesConfig()
        self.rag = rag or ClassicalTextRAGAgent(self.config)

    def _book_meta(self) -> dict[str, dict]:
        from ..utils import read_json
        books = read_json(self.config.manifests_dir / "book_manifest.json", []) or []
        return {b["book_id"]: b for b in books}

    def _load_rules_for(self, formula: str) -> list[InitialRule]:
        from pathlib import Path
        rules = []
        for path in sorted(Path(self.config.rules_initial_dir).glob("BOOK_*.jsonl")):
            for d in read_jsonl(path):
                concl = d.get("then_conclusions", {})
                if formula in concl.get("formula", []):
                    rules.append(InitialRule.from_dict(d))
        return rules

    # ------------------------------------------------------------------
    def trace(self, formula: str) -> dict:
        meta = self._book_meta()
        rules = self._load_rules_for(formula)

        per_book: dict[str, dict] = defaultdict(
            lambda: {"mentions": 0, "indication_rules": [], "compositions": [],
                     "sample_quotes": []})
        # unlimited per-book mention count straight off the source units
        for u in self.rag.units:
            n = u.raw_text.count(formula)
            if n <= 0:
                continue
            b = per_book[u.book_id]
            b["mentions"] += n
            if len(b["sample_quotes"]) < 2:
                b["sample_quotes"].append({
                    "chapter": u.chapter_title,
                    "source_unit_id": u.source_unit_id,
                    "quote": u.raw_text[:160]})
        for r in rules:
            b = per_book[r.book_id]
            if r.rule_type == "formula_indication_rule":
                b["indication_rules"].append({
                    "rule_id": r.initial_rule_id,
                    "release_level": r.autonomous_review.release_level,
                    "conditions": {k: v for k, v in r.if_conditions.items() if v},
                    "evidence_span": r.evidence_span[:160]})
            elif r.rule_type == "formula_composition_rule":
                b["compositions"].append({
                    "rule_id": r.initial_rule_id,
                    "composition": r.then_conclusions.get("composition", [])})

        timeline = []
        for book_id, payload in per_book.items():
            bm = meta.get(book_id, {})
            timeline.append({
                "book_id": book_id,
                "book_title": bm.get("book_title", book_id),
                "author": bm.get("author", ""),
                "dynasty": bm.get("dynasty", ""),
                "book_type": bm.get("book_type", ""),
                "dynasty_rank": dynasty_rank(bm.get("dynasty", "")),
                **payload,
            })
        timeline.sort(key=lambda x: (x["dynasty_rank"], x["book_title"]))

        related = self._related_formulas(formula)
        earliest = timeline[0] if timeline else None
        report = {
            "formula": formula,
            "canonical_composition": LEXICON.formula_herbs(formula),
            "treatment_principles": LEXICON.formula_principles(formula),
            "earliest_source": ({"book_title": earliest["book_title"],
                                 "dynasty": earliest["dynasty"],
                                 "author": earliest["author"]} if earliest else None),
            "books_covered": len(timeline),
            "total_mentions": sum(t["mentions"] for t in timeline),
            "timeline": timeline,
            "related_formulas": related,
            "principle": "no source trace, no answer",
        }
        out = self.config.lineage_dir / f"lineage_{LEXICON.formula_slug(formula)}.json"
        write_json(out, report)
        return report

    def _related_formulas(self, formula: str) -> list[str]:
        base = formula.rstrip("湯散丸")
        related = []
        for name in LEXICON.canonical_formulas:
            if name == formula:
                continue
            stem = name.rstrip("湯散丸")
            if base and (base in stem or stem in base) and len(base) >= 2:
                related.append(name)
        return sorted(related)
