"""RuleReviewerAgent — layer 3: autonomous semantic review.

Checks (per the v5 reviewer prompt): every condition/conclusion supported by
the evidence_span; correct use of the span; original/commentary mixing;
treatment principles directly stated vs normalized; over-extraction; suggests
a confidence adjustment.  Never approves a rule merely because it sounds
medically plausible — no evidence, no rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import HermesConfig
from ..schemas import InitialRule, SourceUnit
from ..utils import clamp
from . import prompts
from .backends import HeuristicBackend

_CONCLUSION_KEYS_VERBATIM = ("formula", "prohibition", "mistreatment",
                             "consequence", "prognosis", "transmission",
                             "pattern", "disease")


def term_supported(term: str, span: str) -> bool:
    """A conclusion term is supported if it appears verbatim, or via the
    classical definition grammar 「X之為病」 ⊨ disease 「X病」."""
    if not term:
        return True
    if term[:12] in span:
        return True
    if term.endswith("病") and f"{term[:-1]}之為病" in span:
        return True
    return False


@dataclass
class SemanticReview:
    semantic_review_result: str          # pass | warn | fail
    unsupported_inference_detected: bool = False
    commentary_contamination_detected: bool = False
    over_modernized_interpretation: bool = False
    suggested_confidence: float = 0.0
    review_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "semantic_review_result": self.semantic_review_result,
            "unsupported_inference_detected": self.unsupported_inference_detected,
            "commentary_contamination_detected": self.commentary_contamination_detected,
            "over_modernized_interpretation": self.over_modernized_interpretation,
            "suggested_confidence": self.suggested_confidence,
            "review_notes": self.review_notes,
        }


class RuleReviewerAgent:
    name = "RuleReviewerAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend or HeuristicBackend()

    def review(self, rule: InitialRule, unit: SourceUnit | None) -> SemanticReview:
        if getattr(self.backend, "kind", "heuristic") == "anthropic":
            try:
                return self._review_llm(rule, unit)
            except Exception:
                pass
        return self._review_heuristic(rule, unit)

    # ------------------------------------------------------------------
    def _review_heuristic(self, rule: InitialRule, unit: SourceUnit | None) -> SemanticReview:
        notes: list[str] = []
        span = rule.evidence_span or ""
        unsupported = False
        contamination = False
        over_modern = False
        conf = rule.model_confidence

        # 1) conditions must be visible in the evidence span
        missing_conditions = [t for t in rule.all_condition_terms() if t and t not in span]
        if missing_conditions:
            unsupported = True
            conf -= 0.12 * len(missing_conditions)
            notes.append("conditions not found in evidence_span: "
                         + "、".join(missing_conditions[:5]))

        # 2) verbatim conclusion classes must be visible in the evidence span
        for key in _CONCLUSION_KEYS_VERBATIM:
            for term in rule.then_conclusions.get(key, []):
                if not term_supported(term, span):
                    unsupported = True
                    conf -= 0.15
                    notes.append(f"conclusion '{term}' ({key}) not found in evidence_span")

        # 3) treatment principles: directly stated, or a normalization?
        principles = rule.then_conclusions.get("treatment_principle", [])
        stated = [p for p in principles if p in span]
        normalized = [p for p in principles if p not in span]
        if normalized and rule.interpretation_level == "original_text":
            notes.append("治法 '" + "、".join(normalized[:3]) +
                         "' 為歸納性術語，未見於原文，interpretation_level 應為 normalized")
            conf -= 0.03
        if stated:
            notes.append("治法 '" + "、".join(stated[:3]) + "' 為原文直述")

        # 4) original / commentary mixing
        if unit is not None and unit.text_type == "commentary" and \
                rule.evidence_type == "original_text":
            contamination = True
            conf -= 0.10
            notes.append("evidence drawn from commentary but labelled original_text")

        # 5) over-modernized interpretation
        modern_markers = ("现代", "現代", "西醫", "西医", "神經", "炎症", "细菌", "病毒")
        if any(mk in rule.interpretation for mk in modern_markers):
            over_modern = True
            conf -= 0.05
            notes.append("interpretation uses modern biomedical vocabulary")

        # 6) span sanity
        if len(span) > 220:
            conf -= 0.03
            notes.append("evidence_span unusually long; consider trimming")
        if 0 < len(span) < 6:
            conf -= 0.10
            notes.append("evidence_span too short to support the rule")

        result = "pass"
        if unsupported or contamination:
            result = "warn"
        if not span or (unit is not None and span not in unit.raw_text):
            result = "fail"
            conf = 0.0

        return SemanticReview(
            semantic_review_result=result,
            unsupported_inference_detected=unsupported,
            commentary_contamination_detected=contamination,
            over_modernized_interpretation=over_modern,
            suggested_confidence=round(clamp(conf), 3),
            review_notes=notes,
        )

    # ------------------------------------------------------------------
    def _review_llm(self, rule: InitialRule, unit: SourceUnit | None) -> SemanticReview:
        import json
        payload = json.dumps({"rule": rule.to_dict(),
                              "source_unit": unit.to_dict() if unit else None},
                             ensure_ascii=False)
        out = self.backend.complete_json(prompts.RULE_REVIEWER_PROMPT, payload,
                                         role="reviewer")
        return SemanticReview(
            semantic_review_result=out.get("semantic_review_result", "warn"),
            unsupported_inference_detected=bool(out.get("unsupported_inference_detected")),
            commentary_contamination_detected=bool(
                out.get("commentary_contamination_detected")),
            over_modernized_interpretation=bool(out.get("over_modernized_interpretation")),
            suggested_confidence=clamp(float(out.get("suggested_confidence", 0.5))),
            review_notes=[str(n) for n in out.get("review_notes", [])],
        )
