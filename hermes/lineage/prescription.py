"""PrescriptionMatcherAgent — match an herb list against classical formulas.

Sources of comparison: canonical compositions (curated) + compositions mined
from the corpus (formula_composition_rules), so matches carry book evidence.
Similarity: Jaccard over normalized herb sets, with containment bonuses to
recognize 加減方 relationships.  Supports reverse tracing of a modern
prescription onto its classical sources.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import HermesConfig
from ..knowledge.lexicon import LEXICON
from ..utils import read_jsonl

_NORMALIZE = {
    "白芍": "芍藥", "赤芍": "芍藥", "炙甘草": "甘草", "生甘草": "甘草",
    "川芎": "芎藭", "丹皮": "牡丹皮", "瓜蔞": "栝蔞實", "天花粉": "栝蔞根",
    "香豉": "豆豉", "茵陳": "茵陳蒿", "代赭": "代赭石", "署蕷": "薯蕷",
    "生地黃": "乾地黃", "熟地黃": "乾地黃", "麥冬": "麥門冬",
}


def normalize_herb(h: str) -> str:
    from ..knowledge.s2t import to_traditional
    h = to_traditional(re.sub(r"[（(].*?[)）]", "", h).strip())
    h = re.sub(r"^(生|炙|炒|煨|焙|酒|薑|蜜|醋|鹽)?", "", h) if len(h) > 2 else h
    for full in sorted(LEXICON.herbs, key=len, reverse=True):
        if h == full or h.endswith(full):
            h = full
            break
    return _NORMALIZE.get(h, h)


class PrescriptionMatcherAgent:
    name = "PrescriptionMatcherAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    # ------------------------------------------------------------------
    def _corpus_compositions(self) -> dict[str, dict]:
        comp: dict[str, dict] = {}
        for path in sorted(Path(self.config.rules_initial_dir).glob("BOOK_*.jsonl")):
            for d in read_jsonl(path):
                if d.get("rule_type") != "formula_composition_rule":
                    continue
                level = d.get("autonomous_review", {}).get("release_level")
                if level == "rejected":
                    continue
                concl = d.get("then_conclusions", {})
                for f in concl.get("formula", []):
                    herbs = {normalize_herb(re.sub(r"[一二三四五六七八九十百半]+"
                                                   r"(兩|斤|升|合|枚|個|箇|把|尺|錢|分|銖|斗|字).*$",
                                                   "", c))
                             for c in concl.get("composition", [])}
                    herbs = {h for h in herbs if h}
                    if not herbs:
                        continue
                    cur = comp.get(f)
                    if cur is None or level == "gold":
                        comp[f] = {"herbs": herbs,
                                   "book_title": d.get("book_title"),
                                   "rule_id": d.get("initial_rule_id"),
                                   "release_level": level}
        return comp

    def _all_candidates(self) -> dict[str, dict]:
        candidates: dict[str, dict] = {}
        for name, info in LEXICON.canonical_formulas.items():
            herbs = {normalize_herb(h) for h in info["herbs"] if h}
            if herbs:
                candidates[name] = {"herbs": herbs, "source": "canonical",
                                    "book_title": None, "rule_id": None}
        for name, payload in self._corpus_compositions().items():
            if name in candidates:
                candidates[name].update(
                    {"book_title": payload["book_title"],
                     "rule_id": payload["rule_id"],
                     "release_level": payload.get("release_level")})
            else:
                candidates[name] = {"source": "corpus", **payload}
        return candidates

    # ------------------------------------------------------------------
    def match(self, herbs: list[str], top: int = 8) -> dict:
        q = {normalize_herb(h) for h in herbs if h.strip()}
        results = []
        for name, cand in self._all_candidates().items():
            c = cand["herbs"]
            inter = q & c
            if not inter:
                continue
            jaccard = len(inter) / len(q | c)
            containment = len(inter) / max(len(c), 1)
            score = 0.6 * jaccard + 0.4 * containment
            results.append({
                "formula": name,
                "similarity": round(score, 3),
                "jaccard": round(jaccard, 3),
                "matched_herbs": sorted(inter),
                "missing_from_input": sorted(c - q),
                "extra_in_input": sorted(q - c),
                "source": cand.get("source", "canonical"),
                "book_title": cand.get("book_title"),
                "evidence_rule_id": cand.get("rule_id"),
                "related_formulas": [],
            })
        results.sort(key=lambda r: -r["similarity"])
        results = results[:top]
        for r in results:
            base = r["formula"].rstrip("湯散丸")
            r["related_formulas"] = sorted(
                n for n in LEXICON.canonical_formulas
                if n != r["formula"] and base and base in n)[:6]
        decomposition = self._decompose(q, results)
        return {"input_herbs": sorted(q), "matches": results,
                "classical_decomposition": decomposition,
                "note": "相似度基于药物集合 Jaccard + 包含度；炮制与剂量差异未计入。"}

    def _decompose(self, q: set[str], results: list[dict]) -> list[dict]:
        """Greedy cover: which classical formulas explain the prescription."""
        remaining = set(q)
        parts = []
        for r in results:
            cand = set(r["matched_herbs"])
            overlap = remaining & cand
            if len(overlap) >= 2:
                parts.append({"formula": r["formula"],
                              "share": round(len(overlap) / max(len(q), 1), 2),
                              "herbs": sorted(overlap)})
                remaining -= overlap
            if not remaining:
                break
        return parts
