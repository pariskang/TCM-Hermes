"""Quality metrics for the autonomous-review protocol (section 九).

All metrics are computed from persisted rule stores, so they are reproducible
from artifacts alone.  The retired human metrics do not exist here.
"""

from __future__ import annotations

from pathlib import Path

from ..config import HermesConfig
from ..schemas import InitialRule
from ..utils import read_jsonl


class QualityMetrics:
    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def load_all_rules(self, book_ids: list[str] | None = None) -> list[InitialRule]:
        rules = []
        for path in sorted(Path(self.config.rules_initial_dir).glob("BOOK_*.jsonl")):
            if book_ids and path.stem not in book_ids:
                continue
            rules.extend(InitialRule.from_dict(d) for d in read_jsonl(path))
        return rules

    def compute(self, rules: list[InitialRule] | None = None,
                book_ids: list[str] | None = None) -> dict:
        rules = rules if rules is not None else self.load_all_rules(book_ids)
        n = len(rules)
        if n == 0:
            return {"rules_total": 0}

        def rate(pred) -> float:
            return round(sum(1 for r in rules if pred(r)) / n, 4)

        accepted = lambda r: r.autonomous_review.review_status in (
            "model_accepted", "model_repaired_accepted")
        scores = [r.autonomous_review.consensus_score for r in rules]

        # false-support detection: critic/reviewer caught conditions that were
        # not actually in the evidence (the protocol's key安全 metric)
        def false_support(r: InitialRule) -> bool:
            if r.autonomous_review.unsupported_inference_detected:
                return True
            return any(cp.get("type") in ("unsupported_condition",
                                          "formula_not_in_evidence")
                       for cp in r.review_records.get("critic", {})
                       .get("challenge_points", []))

        return {
            "rules_total": n,
            "autonomous_acceptance_rate": rate(accepted),
            "model_repair_rate": rate(lambda r: r.autonomous_review.auto_repair_applied),
            "critic_rejection_rate": rate(
                lambda r: r.autonomous_review.critic_result == "fatal"),
            "evidence_verification_rate": rate(
                lambda r: r.autonomous_review.evidence_verified),
            "consensus_score_mean": round(sum(scores) / n, 4),
            "gold_rule_rate": rate(
                lambda r: r.autonomous_review.release_level == "gold"),
            "silver_rule_rate": rate(
                lambda r: r.autonomous_review.release_level == "silver"),
            "bronze_rule_rate": rate(
                lambda r: r.autonomous_review.release_level == "bronze"),
            "model_conflict_rate": rate(
                lambda r: r.autonomous_review.review_status == "model_conflict"),
            "false_support_detection_rate": rate(false_support),
        }
