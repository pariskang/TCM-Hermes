"""Evidence and relevance review layer.

EvidenceSpanVerifierAgent binds every claim to a raw_text substring.  Three
independent reviewers (classical / dermatology / adversarial-differential) vote,
and ConsensusRelevanceJudgeAgent fuses the votes with a component score into a
release level.  Modern phenotype and classical semantics are kept apart: the
output is always a *candidate phenotype correspondence*, never a diagnosis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..config import HermesConfig
from ..schemas import SourceUnit
from ..utils import clamp, split_sentences
from .profiles import DiseaseProfile

# release thresholds (user spec): gold ≥0.90, silver 0.80–0.89, bronze 0.65–0.79
GOLD, SILVER, BRONZE = 0.90, 0.80, 0.65


class EvidenceSpanVerifierAgent:
    name = "EvidenceSpanVerifierAgent"

    def verify(self, unit: SourceUnit, supporting_terms: list[str]) -> dict:
        spans, valid = [], []
        for t in dict.fromkeys(supporting_terms):
            if t and t in unit.raw_text:
                spans.append(t)
                valid.append(t)
        # also keep the clause(s) that actually contain support, as context
        clauses = [s for s in split_sentences(unit.raw_text)
                   if any(t in s for t in valid)]
        return {"evidence_spans": spans,
                "evidence_clauses": clauses[:4],
                "claim_supported": bool(spans),
                "support_level": "phenotype_similarity" if spans else "none",
                "warning": "phenomenological correspondence only; not modern diagnosis"}


@dataclass
class ReviewerVote:
    reviewer: str
    label: str                 # include | uncertain | exclude
    score: float
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    model: str = "heuristic"

    def to_dict(self) -> dict:
        return {"reviewer": self.reviewer, "label": self.label,
                "score": round(self.score, 3), "reason": self.reason,
                "evidence": self.evidence, "model": self.model}


def _label(score: float) -> str:
    return "include" if score >= 0.6 else "uncertain" if score >= 0.4 else "exclude"


class RelevanceReviewPanel:
    """TCMClassicalReviewer + DermatologyReviewer + AdversarialDifferential."""
    name = "RelevanceReviewPanel"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend

    def review(self, unit: SourceUnit, profile: DiseaseProfile,
               annot: dict) -> list[ReviewerVote]:
        is_llm = self.backend is not None and \
            getattr(self.backend, "kind", "heuristic") != "heuristic"
        if is_llm:
            try:
                return self._review_llm(unit, profile, annot)
            except Exception:
                pass
        return self._review_heuristic(unit, profile, annot)

    # ------------------------------------------------------------------
    def _review_heuristic(self, unit, profile, annot) -> list[ReviewerVote]:
        text = unit.raw_text
        core_hits = annot["core"]["hit_terms"]
        pheno = annot["phenotype"]["best_support"]
        morph = annot["morphology"]["morphology_score"]
        excl = annot["exclusion"]
        patho = [p for p in profile.pathogenesis_terms if p in text]
        treat = [t for t in profile.treatment_terms if t in text]

        # 1) classical reviewer — ancient name source + classical context
        # a single strong core term (歷節 / 白疕 / 骨痿) already counts; a second
        # corroborating term saturates it
        ancient = min(1.0, 0.6 + 0.4 * (len(core_hits) - 1)) if core_hits else 0.0
        therapeutic = bool(treat) or any(m in text for m in ("主之", "主治", "主方"))
        c_score = clamp(ancient * 0.7 + (0.2 if patho else 0)
                        + (0.1 if therapeutic else 0))
        classical = ReviewerVote(
            "TCMClassicalReviewer", _label(c_score), c_score,
            f"核心古病名 {core_hits}；病机 {patho[:3]}；治法 {treat[:3]}",
            evidence=core_hits + patho[:2])

        # 2) dermatology reviewer — phenotype + morphology similarity
        d_score = clamp(0.65 * pheno + 0.35 * morph + (0.1 if pheno and morph else 0))
        derm = ReviewerVote(
            "DermatologyReviewer", _label(d_score), d_score,
            f"表型支持 {annot['phenotype']['candidate_modern_type']}({pheno})；"
            f"形态 {annot['morphology']['morphology_hits'][:4]}",
            evidence=annot["morphology"]["morphology_hits"][:4])

        # 3) adversarial differential — high score = looks like another disease
        if excl["exclude_flag"]:
            a_score = 0.85
            a = ReviewerVote("AdversarialDifferential", "exclude", a_score,
                             "命中强排除：" + "、".join(excl["matched_exclusion_terms"]),
                             evidence=excl["matched_exclusion_terms"])
        elif excl["soft_exclude"]:
            a_score = 0.4
            a = ReviewerVote("AdversarialDifferential", "uncertain", a_score,
                             "提及鉴别病但有对比语境", evidence=excl["matched_exclusion_terms"])
        else:
            a_score = clamp(0.25 - 0.1 * (pheno > 0.3))
            a = ReviewerVote("AdversarialDifferential", "include", a_score,
                             "未见明显鉴别病证据", evidence=[])
        return [classical, derm, a]

    # ------------------------------------------------------------------
    def _review_llm(self, unit, profile, annot) -> list[ReviewerVote]:
        ctx = json.dumps({
            "raw_text": unit.raw_text,
            "disease": profile.display_name,
            "modern_subtypes": profile.modern_subtypes,
            "differential_diseases": profile.exclusion_terms,
            "phenotype_annotation": annot["phenotype"],
        }, ensure_ascii=False)
        specs = [
            ("TCMClassicalReviewer", "relevance_classical",
             "你从中医古籍与训诂角度判断该条文是否与目标现代疾病相关（古病名源流、"
             "病机术语）。仅输出 JSON：{\"label\":\"include|uncertain|exclude\","
             "\"score\":0-1,\"reason\":\"...\",\"evidence\":[\"原文片段\"]}。"),
            ("DermatologyReviewer", "relevance_dermatology",
             "你从现代皮肤病学表型角度判断古籍描述是否与该病表型相似（鳞屑/红斑/"
             "脓疱/部位等）。仅输出上述 JSON。"),
            ("AdversarialDifferential", "relevance_adversarial",
             "你从反证角度判断该条文是否更可能属于其他皮肤病（真菌癣、疥疮、麻风、"
             "丹毒等）。score 越高代表越像鉴别病、越应排除。仅输出上述 JSON。"),
        ]
        votes = []
        for reviewer, role, system in specs:
            out = self.backend.complete_json(system, ctx, role=role)
            label = out.get("label", "uncertain")
            if label not in ("include", "uncertain", "exclude"):
                label = "uncertain"
            model = getattr(self.backend, "model_for", lambda r: "llm")(role)
            votes.append(ReviewerVote(
                reviewer, label, clamp(float(out.get("score", 0.5))),
                str(out.get("reason", "")),
                [str(e) for e in out.get("evidence", [])], str(model)))
        return votes


class ConsensusRelevanceJudgeAgent:
    name = "ConsensusRelevanceJudgeAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def judge(self, unit: SourceUnit, profile: DiseaseProfile, annot: dict,
              votes: list[ReviewerVote]) -> dict:
        text = unit.raw_text
        core_hits = annot["core"]["hit_terms"]
        pheno = annot["phenotype"]["best_support"]
        morph = annot["morphology"]["morphology_score"]
        excl = annot["exclusion"]
        patho = [p for p in profile.pathogenesis_terms if p in text]
        treat = [t for t in profile.treatment_terms if t in text]

        # component relevance score (user's formula)
        ancient = min(1.0, 0.6 + 0.4 * (len(core_hits) - 1)) if core_hits else 0.0
        therapeutic = bool(treat) or any(m in text for m in ("主之", "主治", "主方"))
        if patho and therapeutic:
            context = 1.0
        elif patho or therapeutic:
            context = 0.6
        else:
            context = 0.2
        credibility = {"original": 1.0, "formula": 1.0, "case": 0.8,
                       "commentary": 0.7, "variant": 0.6}.get(unit.text_type, 0.7)
        insufficient = (pheno == 0 and morph == 0)
        final = (0.20 * ancient + 0.25 * pheno + 0.20 * morph
                 + 0.15 * context + 0.10 * credibility + 0.10)
        if excl["exclude_flag"]:
            final -= 0.6
        elif excl["soft_exclude"]:
            final -= 0.1
        if insufficient:
            final -= 0.25
        final = round(clamp(final), 3)

        # blend reviewer agreement (adversarial inverted: high → less relevant)
        rscore = []
        includes = 0
        for v in votes:
            if v.reviewer == "AdversarialDifferential":
                rscore.append(1.0 - v.score)
                includes += (v.label == "include")
            else:
                rscore.append(v.score)
                includes += (v.label == "include")
        review_mean = sum(rscore) / max(len(rscore), 1)
        consensus = round(clamp(0.6 * final + 0.4 * review_mean), 3)

        adversarial_excludes = any(
            v.reviewer == "AdversarialDifferential" and v.label == "exclude"
            for v in votes)

        # release level (user spec) with hard exclusion gate
        if excl["exclude_flag"] or adversarial_excludes or consensus < BRONZE:
            level, label = "rejected", "exclude"
        elif (consensus >= GOLD and includes == 3 and not excl["soft_exclude"]):
            level, label = "gold", "include"
        elif consensus >= SILVER and includes >= 2:
            level, label = "silver", "include"
        elif consensus >= BRONZE:
            level, label = "bronze", "uncertain" if includes < 2 else "include"
        else:
            level, label = "rejected", "exclude"

        return {
            "tcm_reviewer_score": next((v.score for v in votes
                                        if v.reviewer == "TCMClassicalReviewer"), 0),
            "dermatology_reviewer_score": next((v.score for v in votes
                                                if v.reviewer == "DermatologyReviewer"), 0),
            "adversarial_score": next((v.score for v in votes
                                       if v.reviewer == "AdversarialDifferential"), 0),
            "component_score": final,
            "consensus_score": consensus,
            "label": label,
            "release_level": level,
            "reviewer_votes": {v.reviewer: v.label for v in votes},
            "votes_detail": [v.to_dict() for v in votes],
        }
