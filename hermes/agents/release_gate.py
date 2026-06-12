"""ReleaseGateAgent — automatic release-level classification (section 八).

Gold:   evidence_verified ∧ consensus ≥ 0.93 ∧ critic pass ∧ no unsupported
        inference ∧ no commentary contamination
Silver: evidence_verified ∧ consensus ≥ 0.85 ∧ critic ∈ {pass, minor_issue}
        ∧ minor issues repaired or explicitly marked
Bronze: evidence_verified ∧ consensus ≥ 0.75 ∧ critic ≠ fatal ∧ interpretive
        uncertainty explicitly marked
Rejected otherwise — preserved in data/rules_rejected/ for audit.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import HermesConfig
from ..schemas import InitialRule


@dataclass
class GateDecision:
    release_level: str
    reasons: list[str]

    def to_dict(self) -> dict:
        return {"release_level": self.release_level, "reasons": self.reasons}


class ReleaseGateAgent:
    name = "ReleaseGateAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def decide(self, rule: InitialRule) -> GateDecision:
        ar = rule.autonomous_review
        cfg = self.config
        reasons: list[str] = []

        if not ar.schema_valid:
            return GateDecision("rejected", ["schema_valid = false"])
        if not ar.evidence_verified:
            return GateDecision("rejected", ["evidence_verified = false"])
        if ar.review_status in ("model_rejected",):
            return GateDecision("rejected", [f"review_status = {ar.review_status}"])
        if ar.review_status == "model_conflict":
            return GateDecision("rejected",
                                ["model_conflict：多路判斷分歧，未獲一致性裁決"])
        if ar.critic_result == "fatal":
            return GateDecision("rejected", ["critic_result = fatal"])

        score = ar.consensus_score
        unsupported = ar.unsupported_inference_detected
        contamination = ar.commentary_contamination_detected

        if (score >= cfg.gold_min_consensus and ar.critic_result == "pass"
                and not unsupported and not contamination
                and ar.review_status in ("model_accepted", "model_repaired_accepted")):
            return GateDecision("gold", [
                f"consensus {score:.2f} ≥ {cfg.gold_min_consensus}",
                "critic pass，無未支持推理，無注文污染"])

        minor_ok = ar.critic_result in ("pass", "minor_issue") and (
            ar.critic_result == "pass" or ar.auto_repair_applied
            or ar.interpretive_uncertainty_marked)
        if (score >= cfg.silver_min_consensus and minor_ok
                and ar.review_status in ("model_accepted", "model_repaired_accepted")):
            return GateDecision("silver", [
                f"consensus {score:.2f} ≥ {cfg.silver_min_consensus}",
                f"critic {ar.critic_result}（已修復或已標記）"])

        if score >= cfg.bronze_min_consensus and ar.critic_result != "fatal":
            if not ar.interpretive_uncertainty_marked and \
                    rule.interpretation_level == "original_text" and \
                    ar.critic_result != "pass":
                reasons.append("解釋不確定性已自動標記")
                ar.interpretive_uncertainty_marked = True
            return GateDecision("bronze", reasons + [
                f"consensus {score:.2f} ≥ {cfg.bronze_min_consensus}",
                f"critic {ar.critic_result} ≠ fatal"])

        return GateDecision("rejected",
                            [f"consensus {score:.2f} 低於 bronze 門檻或審核未通過"])
