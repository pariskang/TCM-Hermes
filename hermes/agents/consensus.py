"""ConsensusJudgeAgent — layer 5: integrate the independent judgements.

Inputs (at least three independent signals, per protocol):
    * extractor self-confidence
    * reviewer suggested confidence
    * critic severity
    * evidence verifier result
Decides review_status ∈ {model_accepted, model_repaired_accepted,
model_low_confidence, model_conflict, model_rejected} and a consensus_score.

Hard rules: evidence failure ⇒ reject; critic fatal ⇒ reject;
consensus < 0.75 ⇒ reject; repair budget exhausted ⇒ low confidence.
No human review exists in this protocol.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import HermesConfig
from ..schemas import InitialRule
from ..utils import clamp
from . import prompts
from .backends import HeuristicBackend
from .critic import CriticReview
from .evidence import EvidenceReview
from .reviewer import SemanticReview

_CRITIC_PENALTY = {"pass": 0.0, "minor_issue": 0.05, "major_issue": 0.15, "fatal": 1.0}


@dataclass
class ConsensusJudgement:
    autonomous_review_status: str
    consensus_score: float
    reason: str

    def to_dict(self) -> dict:
        return {
            "autonomous_review_status": self.autonomous_review_status,
            "consensus_score": self.consensus_score,
            "reason": self.reason,
        }


class ConsensusJudgeAgent:
    name = "ConsensusJudgeAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend or HeuristicBackend()

    def judge(self, rule: InitialRule, evidence: EvidenceReview,
              semantic: SemanticReview, critic: CriticReview,
              repair_round: int, repaired: bool,
              schema_valid: bool = True, binding=None, panel=None
              ) -> ConsensusJudgement:
        cfg = self.config

        # hard gates first — these cannot be argued away by any score
        if not schema_valid:
            return ConsensusJudgement("model_rejected", 0.0,
                                      "結構審核未通過且不可修復（如 IF 條件缺失），拒絕。")
        if not evidence.evidence_valid:
            return ConsensusJudgement("model_rejected", 0.0,
                                      "證據回源失敗：evidence_span 非原文子串或來源不匹配。")
        if critic.critic_result == "fatal":
            return ConsensusJudgement("model_rejected", 0.0,
                                      "對抗式審核致命缺陷：" +
                                      "；".join(p["message"] for p in
                                                critic.challenge_points[:2]))
        if semantic.semantic_review_result == "fail":
            return ConsensusJudgement("model_rejected", 0.0, "語義審核不通過。")
        # panel hard gate: a strong reject majority cannot be overridden
        if panel is not None and panel.reject > panel.support and \
                panel.majority == "reject" and panel.agreement >= 0.5:
            return ConsensusJudgement(
                "model_rejected", round(clamp(panel.panel_score), 3),
                f"評審小組多數否決（reject {panel.reject}/支持 {panel.support}）。")

        extractor_conf = clamp(rule.model_confidence)
        reviewer_conf = clamp(semantic.suggested_confidence)

        # independent-judgement disagreement ⇒ conflict
        if abs(extractor_conf - reviewer_conf) > cfg.conflict_delta:
            score = round(min(extractor_conf, reviewer_conf), 3)
            return ConsensusJudgement(
                "model_conflict", score,
                f"抽取置信 {extractor_conf:.2f} 與審核置信 {reviewer_conf:.2f} 分歧過大。")

        score = 0.5 * extractor_conf + 0.5 * reviewer_conf
        score -= _CRITIC_PENALTY[critic.critic_result]
        if semantic.unsupported_inference_detected:
            score -= 0.05
        if semantic.commentary_contamination_detected:
            score -= 0.05
        if evidence.evidence_type == "original_text":
            score += 0.02

        # Problem 2: loose span↔claim binding lightly penalizes the score; the
        # *release level* is capped by the gate (binding limits how strong a
        # claim the rule may make, it does not by itself reject valid evidence).
        # A rule that cleared the loop threshold pre-binding is floored there so
        # binding downgrades it (to bronze at worst) rather than rejecting it.
        binding_note = ""
        if binding is not None:
            penalized = score - 0.12 * (1.0 - binding.binding_score)
            score = max(penalized, cfg.loop_min_consensus) \
                if score >= cfg.loop_min_consensus else penalized
            if binding.multi_formula:
                binding_note = "；證據含多方並述，結合度受限（封頂 silver）"
            elif binding.binding_score < 0.6:
                binding_note = "；條件與結論結合較鬆"

        # Problem 3: blend the multi-reviewer panel vote into the score and
        # treat panel disagreement as a genuine conflict signal
        panel_note = ""
        if panel is not None:
            score = 0.6 * score + 0.4 * panel.panel_score
            panel_note = (f"；評審小組 {panel.support}支持/{panel.warn}存疑/"
                          f"{panel.reject}否決，一致度 {panel.agreement:.0%}")
            if panel.agreement < 0.5 and panel.support and panel.reject:
                return ConsensusJudgement(
                    "model_conflict", round(clamp(score), 3),
                    "評審小組分歧顯著（無多數一致）" + panel_note + "。")

        score = round(clamp(score), 3)

        # repair budget exhausted but still standing ⇒ low confidence
        if repair_round > cfg.max_repair_rounds:
            return ConsensusJudgement(
                "model_low_confidence", score,
                f"修復輪次超過上限（{cfg.max_repair_rounds}），降為低置信。")

        if score < cfg.loop_min_consensus:
            return ConsensusJudgement(
                "model_rejected", score,
                f"consensus_score {score:.2f} 低於 {cfg.loop_min_consensus}，拒絕。")

        status = "model_repaired_accepted" if repaired else "model_accepted"
        bits = ["證據有效"]
        if critic.critic_result == "pass":
            bits.append("對抗審核無異議")
        else:
            bits.append(f"對抗審核 {critic.critic_result}")
        if repaired:
            bits.append("問題已自動修復")
        return ConsensusJudgement(status, score,
                                  "，".join(bits) + binding_note + panel_note + "。")

    # ------------------------------------------------------------------
    def judge_llm(self, rule: InitialRule, evidence: EvidenceReview,
                  semantic: SemanticReview, critic: CriticReview,
                  repair_round: int, repaired: bool) -> ConsensusJudgement:
        import json
        payload = json.dumps({
            "rule": rule.to_dict(),
            "evidence_review": evidence.to_dict(),
            "semantic_review": semantic.to_dict(),
            "critic_review": critic.to_dict(),
            "repair_round": repair_round,
            "auto_repair_applied": repaired,
        }, ensure_ascii=False)
        out = self.backend.complete_json(prompts.CONSENSUS_JUDGE_PROMPT, payload,
                                         role="judge")
        status = out.get("autonomous_review_status", "model_low_confidence")
        return ConsensusJudgement(status,
                                  clamp(float(out.get("consensus_score", 0.0))),
                                  str(out.get("reason", "")))
