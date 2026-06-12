"""Multi-reviewer panel — turning single-model scoring into model debate.

This is the substantive answer to "consensus is just a formula, not a debate".
Instead of one reviewer + one critic, a *panel* of differently-prompted (and,
under an LLM backend, differently-modelled) reviewers each judges the rule from
its own stance:

    classical_conservative  仲景原文保守派 — only what the text literally says
    philology               訓詁/校勘     — original vs commentary vs variant
    formula_pattern         方證醫學      — formula↔pattern correspondence
    clinical_safety         臨床安全      — contraindications/mistreatment intact
    modern_translation      現代轉譯      — over-modernized interpretation
    adversarial             對抗式質疑    — actively tries to break the rule

Each profile returns the uniform verdict schema:
    {"profile", "stance", "verdict": support|warn|reject, "confidence",
     "issues": [{type, message}], "notes"}

Backends:
  * heuristic — verdicts are derived deterministically from the existing
    RuleReviewer + AdversarialCritic so the panel runs offline and the
    pipeline stays reproducible (the panel then has two grounded voices).
  * litellm / anthropic — each profile is a real LLM call, optionally on a
    different model per role, so the consensus is a genuine multi-model vote.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..config import HermesConfig
from ..schemas import InitialRule, SourceUnit
from .backends import HeuristicBackend
from .critic import AdversarialCriticAgent
from .reviewer import RuleReviewerAgent

VERDICTS = ("support", "warn", "reject")

PROFILES = {
    "classical_conservative": {
        "stance": "仲景原文保守派",
        "role": "relevance_classical",
        "system": (
            "你是伤寒金匮古籍规则的保守派审核者。只承认条文字面直接陈述的内容，"
            "任何归纳、引申、补全都要标为 warn。证据不在原文中即 reject。"
            "仅输出 JSON：{\"verdict\":\"support|warn|reject\",\"confidence\":0-1,"
            "\"issues\":[{\"type\":\"...\",\"message\":\"...\"}],\"notes\":\"...\"}。"),
    },
    "philology": {
        "stance": "訓詁/校勘",
        "role": "reviewer",
        "system": (
            "你是训诂校勘审核者。判断证据是原文、注家文字还是异文/校勘，"
            "若把注文或异文当作仲景原文则 reject 或 warn 并说明。仅输出上述 JSON。"),
    },
    "formula_pattern": {
        "stance": "方證醫學",
        "role": "reviewer",
        "system": (
            "你是方证医学审核者。判断方剂与证候的对应是否正确、是否过度扩大主治、"
            "治法是原文直述还是后世归纳。仅输出上述 JSON。"),
    },
    "clinical_safety": {
        "stance": "臨床安全",
        "role": "critic",
        "system": (
            "你是临床安全审核者。重点检查禁忌、误治、限制条件（若/不可/反/誤下/誤汗）"
            "是否被遗漏或被弱化为普遍适用，任何安全相关遗漏判为 reject 或 warn。"
            "仅输出上述 JSON。"),
    },
    "modern_translation": {
        "stance": "現代轉譯",
        "role": "reviewer",
        "system": (
            "你是现代转译审核者。判断解释是否把古义过度现代化/西医化，"
            "过度现代化判为 warn。仅输出上述 JSON。"),
    },
    "adversarial": {
        "stance": "對抗式質疑",
        "role": "relevance_adversarial",
        "system": (
            "你是对抗式审核者，任务是反驳规则：过度概括、症状虚增、注文冒充原文、"
            "主治扩大、限制条件遗漏、语境混淆。发现致命问题判 reject。仅输出上述 JSON。"),
    },
}


@dataclass
class ProfileVerdict:
    profile: str
    stance: str
    verdict: str                     # support | warn | reject
    confidence: float
    issues: list[dict] = field(default_factory=list)
    notes: str = ""
    model: str = "heuristic"

    def to_dict(self) -> dict:
        return {"profile": self.profile, "stance": self.stance,
                "verdict": self.verdict, "confidence": round(self.confidence, 3),
                "issues": self.issues, "notes": self.notes, "model": self.model}


@dataclass
class PanelResult:
    verdicts: list[ProfileVerdict]
    support: int = 0
    warn: int = 0
    reject: int = 0
    agreement: float = 0.0           # fraction agreeing with the majority verdict
    panel_score: float = 0.0         # confidence-weighted support score
    majority: str = "warn"

    def to_dict(self) -> dict:
        return {"verdicts": [v.to_dict() for v in self.verdicts],
                "support": self.support, "warn": self.warn, "reject": self.reject,
                "agreement": round(self.agreement, 3),
                "panel_score": round(self.panel_score, 3),
                "majority": self.majority}


class ReviewerPanel:
    name = "ReviewerPanel"

    def __init__(self, config: HermesConfig | None = None, backend=None,
                 profiles: list[str] | None = None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend or HeuristicBackend()
        self.profiles = profiles or list(PROFILES)
        self._reviewer = RuleReviewerAgent(self.config, HeuristicBackend())
        self._critic = AdversarialCriticAgent(self.config, HeuristicBackend())

    # ------------------------------------------------------------------
    def review(self, rule: InitialRule, unit: SourceUnit | None) -> PanelResult:
        is_llm = getattr(self.backend, "kind", "heuristic") != "heuristic"
        verdicts: list[ProfileVerdict] = []
        for name in self.profiles:
            spec = PROFILES[name]
            if is_llm:
                try:
                    verdicts.append(self._review_llm(name, spec, rule, unit))
                    continue
                except Exception:
                    pass  # fall through to deterministic voice
            verdicts.append(self._review_heuristic(name, spec, rule, unit))
        return self._aggregate(verdicts)

    # ------------------------------------------------------------------
    def _review_llm(self, name: str, spec: dict, rule: InitialRule,
                    unit: SourceUnit | None) -> ProfileVerdict:
        payload = json.dumps({"rule": rule.to_dict(),
                              "source_unit": unit.to_dict() if unit else None},
                             ensure_ascii=False)
        out = self.backend.complete_json(spec["system"], payload, role=spec["role"])
        verdict = out.get("verdict", "warn")
        if verdict not in VERDICTS:
            verdict = "warn"
        model = getattr(self.backend, "model_for", lambda r: "llm")(spec["role"])
        return ProfileVerdict(
            profile=name, stance=spec["stance"], verdict=verdict,
            confidence=_clamp(float(out.get("confidence", 0.5))),
            issues=[i if isinstance(i, dict) else {"type": "issue", "message": str(i)}
                    for i in out.get("issues", [])],
            notes=str(out.get("notes", "")), model=str(model))

    # ------------------------------------------------------------------
    def _review_heuristic(self, name: str, spec: dict, rule: InitialRule,
                          unit: SourceUnit | None) -> ProfileVerdict:
        sem = self._reviewer.review(rule, unit)
        crit = self._critic.critique(rule, unit)
        span = rule.evidence_span or ""
        issues: list[dict] = []

        if name == "classical_conservative":
            missing = [t for t in rule.all_condition_terms() if t and t not in span]
            unstated = [p for p in rule.then_conclusions.get("treatment_principle", [])
                        if p not in span]
            if unit is not None and span not in unit.raw_text:
                return ProfileVerdict(name, spec["stance"], "reject", 0.9,
                                      [{"type": "evidence_missing",
                                        "message": "证据非原文子串"}])
            if missing or unstated:
                issues = [{"type": "non_literal",
                           "message": "存在归纳/未直述内容：" + "、".join(
                               (missing + unstated)[:4])}]
                return ProfileVerdict(name, spec["stance"], "warn",
                                      0.6, issues)
            return ProfileVerdict(name, spec["stance"], "support", 0.85)

        if name == "philology":
            if sem.commentary_contamination_detected or rule.evidence_type in (
                    "commentary", "variant"):
                return ProfileVerdict(name, spec["stance"],
                                      "warn" if rule.interpretation_level != "original_text"
                                      else "reject", 0.7,
                                      [{"type": "source_layer",
                                        "message": "证据出自注文/异文"}])
            return ProfileVerdict(name, spec["stance"], "support", 0.8)

        if name == "formula_pattern":
            for f in rule.then_conclusions.get("formula", []):
                if f not in span:
                    return ProfileVerdict(name, spec["stance"], "reject", 0.85,
                                          [{"type": "formula_not_in_evidence",
                                            "message": f"方剂{f}未见于证据"}])
            v = "support" if sem.semantic_review_result == "pass" else "warn"
            return ProfileVerdict(name, spec["stance"], v,
                                  _clamp(sem.suggested_confidence))

        if name == "clinical_safety":
            from ..knowledge.lexicon import LEXICON
            ctx_drop = any(cp.get("type") == "conditional_clause_ignored"
                           for cp in crit.challenge_points)
            if crit.critic_result == "fatal":
                return ProfileVerdict(name, spec["stance"], "reject", 0.9,
                                      crit.challenge_points[:2])
            if ctx_drop or any(mk in span for mk in LEXICON.limiting_markers
                               if rule.rule_type == "formula_indication_rule"
                               and mk not in "".join(rule.all_condition_terms())):
                return ProfileVerdict(name, spec["stance"], "warn", 0.6,
                                      [{"type": "limiting_clause",
                                        "message": "限制/禁忌条件可能被忽略"}])
            return ProfileVerdict(name, spec["stance"], "support", 0.8)

        if name == "modern_translation":
            if sem.over_modernized_interpretation:
                return ProfileVerdict(name, spec["stance"], "warn", 0.6,
                                      [{"type": "over_modernized",
                                        "message": "解释过度现代化"}])
            return ProfileVerdict(name, spec["stance"], "support", 0.8)

        # adversarial
        v = {"pass": "support", "minor_issue": "warn",
             "major_issue": "warn", "fatal": "reject"}[crit.critic_result]
        conf = {"pass": 0.85, "minor_issue": 0.6,
                "major_issue": 0.7, "fatal": 0.9}[crit.critic_result]
        return ProfileVerdict(name, spec["stance"], v, conf,
                              crit.challenge_points[:3])

    # ------------------------------------------------------------------
    @staticmethod
    def _aggregate(verdicts: list[ProfileVerdict]) -> PanelResult:
        support = sum(v.verdict == "support" for v in verdicts)
        warn = sum(v.verdict == "warn" for v in verdicts)
        reject = sum(v.verdict == "reject" for v in verdicts)
        n = max(len(verdicts), 1)
        counts = {"support": support, "warn": warn, "reject": reject}
        majority = max(counts, key=counts.get)
        agreement = counts[majority] / n
        # confidence-weighted support score in [0,1]
        weight = {"support": 1.0, "warn": 0.5, "reject": 0.0}
        score = sum(weight[v.verdict] * (0.5 + 0.5 * v.confidence) for v in verdicts) \
            / sum(0.5 + 0.5 * v.confidence for v in verdicts)
        return PanelResult(verdicts=verdicts, support=support, warn=warn,
                           reject=reject, agreement=agreement,
                           panel_score=round(score, 3), majority=majority)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))
