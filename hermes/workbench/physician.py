"""DoctorAssistantAgent — physician workbench (decision support only).

Capabilities: 方證匹配 (symptoms/pulse → candidate formula patterns with
evidence), 病案回源 (case text → classical evidence), 經典方鑑別 (formula
differential), 禁忌提醒.  All outputs are evidence-chained, release-level
labelled and wrapped in the physician disclaimer — Hermes never prescribes.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..agents.safety import SafetyGovernanceAgent
from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..rag.text_rag import ClassicalTextRAGAgent
from ..schemas import InitialRule
from ..utils import read_jsonl


class DoctorAssistantAgent:
    name = "DoctorAssistantAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.entities = EntityExtractorAgent()
        self.safety = SafetyGovernanceAgent()
        self.rag = ClassicalTextRAGAgent(self.config)
        self._rules: list[InitialRule] | None = None

    # ------------------------------------------------------------------
    def _released_rules(self) -> list[InitialRule]:
        if self._rules is None:
            rules = []
            for level in ("gold", "silver", "bronze"):
                for path in sorted(Path(self.config.rules_released_dir / level)
                                   .glob("BOOK_*.jsonl")):
                    rules.extend(InitialRule.from_dict(d) for d in read_jsonl(path))
            self._rules = rules
        return self._rules

    # ------------------------------------------------------------------
    def match_pattern(self, symptoms: list[str] | None = None,
                      pulse: list[str] | None = None,
                      disease: list[str] | None = None,
                      free_text: str = "", top: int = 6) -> dict:
        """方證匹配: clinical findings → ranked classical formula patterns."""
        if free_text:
            ents = self.entities.extract(free_text)
            symptoms = (symptoms or []) + ents["symptoms"]
            pulse = (pulse or []) + ents["pulse"]
            disease = (disease or []) + ents["disease"]
        q_sym = set(symptoms or [])
        q_pulse = set(pulse or [])
        q_dis = set(disease or [])
        q_all = q_sym | q_pulse | q_dis
        if not q_all:
            return {"error": "no recognizable findings",
                    "hint": "提供症状/脉象/病名，或一段四诊描述"}

        level_w = {"gold": 1.0, "silver": 0.92, "bronze": 0.75}
        per_formula: dict[str, list] = defaultdict(list)
        for r in self._released_rules():
            if r.rule_type != "formula_indication_rule":
                continue
            r_terms = set(r.all_condition_terms())
            if not r_terms:
                continue
            inter = q_all & r_terms
            if not inter:
                continue
            recall = len(inter) / len(q_all)
            precision = len(inter) / len(r_terms)
            score = (0.65 * recall + 0.35 * precision) \
                * level_w.get(r.autonomous_review.release_level, 0.6) \
                * (0.5 + 0.5 * r.autonomous_review.consensus_score)
            # very long evidence spans (tabular/compiled rows) are weak
            # support for a specific pattern match
            if len(r.evidence_span) > 200:
                score *= 0.8
            for f in r.then_conclusions.get("formula", []):
                per_formula[f].append((score, inter, r))

        ranked = []
        for formula, items in per_formula.items():
            items.sort(key=lambda x: -x[0])
            best = items[0]
            agg = min(1.0, best[0] + 0.05 * (len(items) - 1))
            ranked.append({
                "formula": formula,
                "match_score": round(agg, 3),
                "matched_findings": sorted(set().union(*(i[1] for i in items[:3]))),
                "unmatched_findings": sorted(q_all - set().union(
                    *(set(i[2].all_condition_terms()) for i in items[:3]))),
                "supporting_rules": [{
                    "rule_id": i[2].initial_rule_id,
                    "book_title": i[2].book_title,
                    "chapter_title": i[2].chapter_title,
                    "release_level": i[2].autonomous_review.release_level,
                    "consensus_score": i[2].autonomous_review.consensus_score,
                    "evidence_span": i[2].evidence_span,
                } for i in items[:3]],
                "contraindication_reminders": self._contraindications_for(formula),
            })
        ranked.sort(key=lambda x: -x["match_score"])
        ranked = ranked[:top]

        result = {
            "query": {"symptoms": sorted(q_sym), "pulse": sorted(q_pulse),
                      "disease": sorted(q_dis)},
            "candidates": ranked,
            "differential": (self.differentiate(ranked[0]["formula"],
                                                ranked[1]["formula"])
                             if len(ranked) >= 2 else None),
            "uncertainty_notes": [
                "匹配仅基于古籍条文词项重叠，未考虑舌象/病程/体质等完整四诊信息。",
            ],
            "disclaimer": self.safety.wrap_physician_answer("").strip(),
        }
        return result

    def _contraindications_for(self, formula: str) -> list[dict]:
        out = []
        for r in self._released_rules():
            if r.rule_type != "contraindication_rule":
                continue
            if formula in r.evidence_span or any(
                    d in r.evidence_span for d in (formula,)):
                out.append({"prohibition": r.then_conclusions.get("prohibition", []),
                            "book_title": r.book_title,
                            "evidence_span": r.evidence_span[:120],
                            "rule_id": r.initial_rule_id})
            if len(out) >= 3:
                break
        return out

    # ------------------------------------------------------------------
    def case_to_classics(self, case_text: str, top: int = 6) -> dict:
        """病案古籍回源: free-text case → matched patterns + clause evidence."""
        ents = self.entities.extract(case_text)
        pattern = self.match_pattern(symptoms=ents["symptoms"], pulse=ents["pulse"],
                                     disease=ents["disease"], top=top)
        clauses = self.rag.search_semantic(case_text, limit=top)
        pattern["classical_clauses"] = [h.evidence() for h in clauses]
        pattern["recognized_entities"] = {k: v for k, v in ents.items() if v}
        return pattern

    # ------------------------------------------------------------------
    def differentiate(self, formula_a: str, formula_b: str) -> dict:
        """經典方鑑別 from released rules + canonical compositions."""
        from ..knowledge.lexicon import LEXICON

        def profile(formula: str) -> dict:
            conds: dict[str, set] = {"disease": set(), "symptoms": set(),
                                     "pulse": set()}
            evidence = []
            for r in self._released_rules():
                if r.rule_type == "formula_indication_rule" and \
                        formula in r.then_conclusions.get("formula", []):
                    for k in conds:
                        conds[k] |= set(r.if_conditions.get(k, []))
                    if len(evidence) < 3:
                        evidence.append({"book_title": r.book_title,
                                         "evidence_span": r.evidence_span[:120],
                                         "rule_id": r.initial_rule_id,
                                         "release_level":
                                             r.autonomous_review.release_level})
            return {"conditions": {k: sorted(v) for k, v in conds.items()},
                    "herbs": LEXICON.formula_herbs(formula),
                    "principles": LEXICON.formula_principles(formula),
                    "evidence": evidence}

        pa, pb = profile(formula_a), profile(formula_b)
        sym_a = set(pa["conditions"]["symptoms"]) | set(pa["conditions"]["disease"])
        sym_b = set(pb["conditions"]["symptoms"]) | set(pb["conditions"]["disease"])
        herbs_a, herbs_b = set(pa["herbs"]), set(pb["herbs"])
        return {
            "formulas": [formula_a, formula_b],
            "shared_findings": sorted(sym_a & sym_b),
            "distinct_findings": {formula_a: sorted(sym_a - sym_b),
                                  formula_b: sorted(sym_b - sym_a)},
            "pulse": {formula_a: pa["conditions"]["pulse"],
                      formula_b: pb["conditions"]["pulse"]},
            "shared_herbs": sorted(herbs_a & herbs_b),
            "distinct_herbs": {formula_a: sorted(herbs_a - herbs_b),
                               formula_b: sorted(herbs_b - herbs_a)},
            "principles": {formula_a: pa["principles"], formula_b: pb["principles"]},
            "evidence": {formula_a: pa["evidence"], formula_b: pb["evidence"]},
        }
