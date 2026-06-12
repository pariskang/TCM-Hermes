"""ClassicalTextRAGAgent — the evidence engine over source units.

Retrieval modes:
  * exact   — strict substring search (formula/herb/symptom/原文片段);
  * semantic— lexicon-entity overlap + character-bigram similarity, mapping
              symptom clusters and patient-style descriptions to clauses;
  * filters — category / book / chapter / text_type include & exclude.

Every hit carries the full evidence chain (book, chapter, unit id, quote),
because an answer without a source trace is not an answer (no source trace,
no answer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..schemas import SourceUnit
from ..utils import read_jsonl


@dataclass
class RAGHit:
    score: float
    source_unit: SourceUnit
    match_type: str
    matched_terms: list[str] = field(default_factory=list)

    def evidence(self) -> dict:
        u = self.source_unit
        return {
            "book_title": u.book_title,
            "chapter_title": u.chapter_title,
            "source_unit_id": u.source_unit_id,
            "text_type": u.text_type,
            "clause_no": u.clause_no,
            "quote": u.raw_text[:300],
            "score": round(self.score, 3),
            "matched_terms": self.matched_terms,
            "category_path": u.category_path,
        }


def _bigrams(s: str) -> set[str]:
    s = "".join(ch for ch in s if "一" <= ch <= "鿿")
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s} if s else set()


class ClassicalTextRAGAgent:
    name = "ClassicalTextRAGAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.entities = EntityExtractorAgent()
        self._units: list[SourceUnit] | None = None

    # ------------------------------------------------------------------
    def load(self, book_ids: list[str] | None = None) -> int:
        units: list[SourceUnit] = []
        for path in sorted(Path(self.config.source_units_dir).glob("BOOK_*.jsonl")):
            if book_ids and path.stem not in book_ids:
                continue
            units.extend(SourceUnit.from_dict(d) for d in read_jsonl(path))
        self._units = units
        return len(units)

    @property
    def units(self) -> list[SourceUnit]:
        if self._units is None:
            self.load()
        return self._units or []

    # ------------------------------------------------------------------
    def _filter(self, units, subcategory=None, book=None, chapter=None,
                text_types=None, exclude_text_types=None):
        for u in units:
            if subcategory and (len(u.category_path) < 2
                                or u.category_path[1] != subcategory):
                continue
            if book and book not in (u.book_id, u.book_title):
                continue
            if chapter and chapter not in (u.chapter_id, u.chapter_title):
                continue
            if text_types and u.text_type not in text_types:
                continue
            if exclude_text_types and u.text_type in exclude_text_types:
                continue
            yield u

    # ------------------------------------------------------------------
    def search_exact(self, query: str, limit: int = 20, **filters) -> list[RAGHit]:
        hits = []
        for u in self._filter(self.units, **filters):
            if query in u.raw_text:
                # short clauses that contain the query are stronger evidence
                score = 1.0 + min(0.5, 50 / max(len(u.raw_text), 1))
                hits.append(RAGHit(score, u, "exact", [query]))
        hits.sort(key=lambda h: -h.score)
        return hits[:limit]

    def search_semantic(self, query: str, limit: int = 20, **filters) -> list[RAGHit]:
        q_entities = self.entities.extract(query)
        q_terms = [t for vals in q_entities.values() for t in vals]
        q_bi = _bigrams(query)
        hits = []
        for u in self._filter(self.units, **filters):
            matched = [t for t in q_terms if t in u.raw_text]
            ent_score = len(matched) / max(len(q_terms), 1) if q_terms else 0.0
            u_bi = _bigrams(u.raw_text[:400])
            jac = len(q_bi & u_bi) / max(len(q_bi | u_bi), 1)
            score = 0.75 * ent_score + 0.25 * min(1.0, jac * 8)
            if score > 0.15:
                hits.append(RAGHit(score, u, "semantic", matched))
        hits.sort(key=lambda h: -h.score)
        return hits[:limit]

    def search(self, query: str, mode: str = "auto", limit: int = 20,
               **filters) -> list[RAGHit]:
        if mode in ("exact", "auto"):
            exact = self.search_exact(query, limit, **filters)
            if mode == "exact" or exact:
                return exact
        return self.search_semantic(query, limit, **filters)

    # ------------------------------------------------------------------
    def unit_by_id(self, source_unit_id: str) -> SourceUnit | None:
        for u in self.units:
            if u.source_unit_id == source_unit_id:
                return u
        return None

    def answer(self, query: str, limit: int = 8, **filters) -> dict:
        hits = self.search(query, "auto", limit, **filters)
        return {
            "query": query,
            "evidence_chain": [h.evidence() for h in hits],
            "books": sorted({h.source_unit.book_title for h in hits}),
            "principle": "no source trace, no answer",
        }
