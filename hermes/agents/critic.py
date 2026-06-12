"""AdversarialCriticAgent — layer 4: the agent whose job is to break rules.

It never argues in favour of a rule.  Attack angles (v5 prompt): claim broader
than evidence; symptoms added that are not in the source; commentary treated
as original; over-generalized indication; ignored conditional/contraindication
clauses; variants mistaken for main text; 傷寒/金匱 context mixing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import HermesConfig
from ..knowledge.lexicon import LEXICON
from ..schemas import InitialRule, SourceUnit
from . import prompts
from .backends import HeuristicBackend

_SEVERITY_ORDER = {"pass": 0, "minor_issue": 1, "major_issue": 2, "fatal": 3}

# 金匱-specific disease contexts that should not be claimed from a 傷寒-only book
_JINGUI_MARKERS = ("胸痹", "痰飲", "水氣病", "黃疸", "瘧病", "奔豚", "虛勞", "肺痿",
                   "肺癰", "歷節", "血痹", "妊娠", "產後", "腸癰", "消渴")


@dataclass
class CriticReview:
    critic_result: str                       # pass | minor_issue | major_issue | fatal
    challenge_points: list[dict] = field(default_factory=list)
    must_repair: bool = False
    recommended_repair: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "critic_result": self.critic_result,
            "challenge_points": self.challenge_points,
            "must_repair": self.must_repair,
            "recommended_repair": self.recommended_repair,
        }


class AdversarialCriticAgent:
    name = "AdversarialCriticAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend or HeuristicBackend()

    def critique(self, rule: InitialRule, unit: SourceUnit | None) -> CriticReview:
        if getattr(self.backend, "kind", "heuristic") == "anthropic":
            try:
                return self._critique_llm(rule, unit)
            except Exception:
                pass
        return self._critique_heuristic(rule, unit)

    # ------------------------------------------------------------------
    def _critique_heuristic(self, rule: InitialRule, unit: SourceUnit | None) -> CriticReview:
        points: list[dict] = []
        repairs: list[dict] = []
        severity = "pass"

        def attack(level: str, ptype: str, message: str, repair: dict | None = None):
            nonlocal severity
            points.append({"type": ptype, "message": message})
            if repair:
                repairs.append(repair)
            if _SEVERITY_ORDER[level] > _SEVERITY_ORDER[severity]:
                severity = level

        span = rule.evidence_span or ""
        raw = unit.raw_text if unit else ""

        # 1) evidence integrity is non-negotiable
        if not span or (unit is not None and span not in raw):
            attack("fatal", "evidence_not_in_source",
                   "evidence_span 不是原文嚴格子串，規則不得進入合併。")
            return CriticReview("fatal", points, True, repairs)

        # 2) fabricated conditions (false-support detection)
        fabricated = [t for t in rule.all_condition_terms() if t and t not in span]
        if fabricated:
            level = "major_issue" if len(fabricated) > 2 else "minor_issue"
            attack(level, "unsupported_condition",
                   "下列條件未見於證據原文：" + "、".join(fabricated[:5]),
                   {"type": "drop_unsupported_conditions", "terms": fabricated})

        # 3) formula must literally appear in the evidence
        for formula in rule.then_conclusions.get("formula", []):
            if formula not in span:
                attack("fatal", "formula_not_in_evidence",
                       f"方劑「{formula}」未見於證據原文，屬嚴重錯配。")

        # 4) interpretation-level inflation: 治法 not stated in the text
        principles = rule.then_conclusions.get("treatment_principle", [])
        normalized = [p for p in principles if p not in span]
        if normalized and rule.interpretation_level == "original_text":
            attack("minor_issue", "interpretation_level_issue",
                   f"「{'、'.join(normalized[:3])}」為歸納性術語，不應標為原文直述。",
                   {"type": "relabel_interpretation_level", "to": "normalized",
                    "terms": normalized})

        # 5) commentary treated as original text
        if unit is not None and unit.text_type == "commentary" and \
                rule.evidence_type == "original_text":
            attack("major_issue", "commentary_contamination",
                   "證據出自注家文字，卻標記為仲景原文。",
                   {"type": "relabel_evidence_type", "to": "commentary"})
        if rule.evidence_type in ("commentary", "variant") and \
                rule.interpretation_level == "original_text":
            attack("minor_issue", "interpretation_level_issue",
                   "證據為注文/異文，interpretation_level 不應為原文直述。",
                   {"type": "relabel_interpretation_level",
                    "to": "later_commentary", "terms": []})
        if unit is not None and unit.text_type == "variant" and \
                rule.evidence_type != "variant":
            attack("major_issue", "variant_as_main_text",
                   "證據出自校勘/異文，不應作為正文規則。",
                   {"type": "relabel_evidence_type", "to": "variant"})

        # 6) dropped conditional / contraindication clauses around the span
        if unit is not None and raw and span in raw:
            idx = raw.find(span)
            context = raw[max(0, idx - 30):idx] + raw[idx + len(span):idx + len(span) + 30]
            dropped = [mk for mk in LEXICON.limiting_markers if mk in context]
            if dropped and rule.rule_type == "formula_indication_rule":
                attack("minor_issue", "conditional_clause_ignored",
                       "證據周邊存在限制詞（" + "、".join(sorted(set(dropped))[:4]) +
                       "）未納入規則，可能遺漏「若/不可/反/誤」等條件。")

        # 7) over-generalization markers in the claim but not the evidence
        claim_text = rule.interpretation + "".join(rule.all_conclusion_terms())
        general = [mk for mk in LEXICON.overgeneralization_markers
                   if mk in claim_text and mk not in span]
        if general:
            attack("minor_issue", "over_generalized_claim",
                   "規則表述含普遍化用語（" + "、".join(general) + "）超出單一條文證據。",
                   {"type": "soften_claim"})
        if rule.rule_type == "formula_indication_rule" and \
                not any(rule.if_conditions.get(k) for k in
                        ("disease", "symptoms", "pulse")):
            attack("minor_issue", "isolated_clause_generalization",
                   "無任何病證條件即斷言方劑主治，孤立條文不宜作普遍規律。")

        # 8) 傷寒/金匱 context mixing
        sub = rule.category_path[1] if len(rule.category_path) > 1 else ""
        if sub == "傷寒":
            mixed = [d for d in rule.if_conditions.get("disease", [])
                     if d in _JINGUI_MARKERS and d not in span]
            if mixed:
                attack("major_issue", "context_mixing",
                       "傷寒語境規則引入金匱病證（" + "、".join(mixed) + "）。")

        # 9) bloated evidence
        if len(span) > 220:
            attack("minor_issue", "evidence_span_too_long",
                   "證據片段過長，包含與結論無關內容。",
                   {"type": "trim_evidence_span"})

        must_repair = bool(repairs) or severity in ("major_issue", "fatal")
        return CriticReview(severity, points, must_repair, repairs)

    # ------------------------------------------------------------------
    def _critique_llm(self, rule: InitialRule, unit: SourceUnit | None) -> CriticReview:
        import json
        payload = json.dumps({"rule": rule.to_dict(),
                              "source_unit": unit.to_dict() if unit else None},
                             ensure_ascii=False)
        out = self.backend.complete_json(prompts.ADVERSARIAL_CRITIC_PROMPT, payload,
                                         role="critic")
        res = out.get("critic_result", "minor_issue")
        if res not in _SEVERITY_ORDER:
            res = "minor_issue"
        return CriticReview(
            critic_result=res,
            challenge_points=[p if isinstance(p, dict) else {"type": "llm", "message": str(p)}
                              for p in out.get("challenge_points", [])],
            must_repair=bool(out.get("must_repair")),
            recommended_repair=[r if isinstance(r, dict) else {"type": str(r)}
                                for r in out.get("recommended_repair", [])],
        )
