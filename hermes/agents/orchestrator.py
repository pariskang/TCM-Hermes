"""AutonomousReviewOrchestrator — the v5 InitialRule autonomous loop.

    SourceUnit
      → InitialRuleExtractorAgent
      → SchemaValidator
      → EvidenceVerifierAgent
      → RuleReviewerAgent
      → AdversarialCriticAgent
      → ConsensusJudgeAgent
      → RuleRepairAgent (if needed) → re-review (≤ MAX_REPAIR_ROUNDS)
      → ReleaseGateAgent
      → RuleMemory + ModelAuditMemory

Termination: schema_valid ∧ evidence_verified ∧ consensus ≥ 0.75 ∧ critic ≠
fatal ∧ repair_round ≤ 2.  Failures: evidence invalid / critic fatal /
consensus < 0.75 ⇒ model_rejected; repair budget exhausted ⇒
model_low_confidence.  Rejected rules are preserved in data/rules_rejected/.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..config import HermesConfig
from ..memory.store import MemoryCuratorAgent
from ..schemas import InitialRule, SourceUnit
from ..schemas.validation import SchemaValidator
from ..utils import read_jsonl, write_jsonl
from .backends import get_backend
from .binding import check_binding
from .critic import AdversarialCriticAgent
from .consensus import ConsensusJudgeAgent
from .evidence import EvidenceVerifierAgent
from .extractor import InitialRuleExtractorAgent
from .release_gate import ReleaseGateAgent
from .repair import RuleRepairAgent
from .reviewer import RuleReviewerAgent
from .reviewer_profiles import ReviewerPanel


class AutonomousReviewOrchestrator:
    name = "AutonomousReviewOrchestrator"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend if backend is not None else get_backend(self.config)
        self.extractor = InitialRuleExtractorAgent(self.config, self.backend)
        self.schema_validator = SchemaValidator()
        self.evidence_verifier = EvidenceVerifierAgent()
        self.reviewer = RuleReviewerAgent(self.config, self.backend)
        self.critic = AdversarialCriticAgent(self.config, self.backend)
        self.judge = ConsensusJudgeAgent(self.config, self.backend)
        self.repairer = RuleRepairAgent(self.config, self.backend)
        self.gate = ReleaseGateAgent(self.config)
        self.memory = MemoryCuratorAgent(self.config)
        self.panel = ReviewerPanel(self.config, self.backend)
        # panel debate runs under an LLM backend, or whenever explicitly asked;
        # "auto" keeps the offline heuristic run identical to before
        mode = getattr(self.config, "consensus_mode", "auto")
        self.use_panel = mode == "panel" or (
            mode == "auto" and getattr(self.backend, "kind", "heuristic") != "heuristic")

    # ------------------------------------------------------------------
    def review_rule(self, rule: InitialRule, unit: SourceUnit | None) -> InitialRule:
        """Run the full autonomous review loop on one rule (in place)."""
        cfg = self.config
        ar = rule.autonomous_review
        repaired_overall = False
        last = {}

        for round_no in range(cfg.max_repair_rounds + 2):
            ar.repair_round = round_no

            # L1 schema --------------------------------------------------
            schema_res = self.schema_validator.validate(rule)
            ar.schema_valid = schema_res.schema_valid
            last["schema"] = schema_res
            if schema_res.schema_valid:
                rule.status = "schema_validated"

            # L2 evidence --------------------------------------------------
            evidence_res = self.evidence_verifier.verify(rule, unit)
            ar.evidence_verified = evidence_res.evidence_valid
            last["evidence"] = evidence_res
            if evidence_res.evidence_valid:
                rule.status = "evidence_verified"

            # L3 semantic --------------------------------------------------
            semantic_res = self.reviewer.review(rule, unit)
            ar.semantic_review_result = semantic_res.semantic_review_result
            ar.unsupported_inference_detected = semantic_res.unsupported_inference_detected
            ar.commentary_contamination_detected = \
                semantic_res.commentary_contamination_detected
            ar.over_modernized_interpretation = semantic_res.over_modernized_interpretation
            last["semantic"] = semantic_res
            rule.status = "model_reviewed"
            rule.log(self.reviewer.name, "semantic_review",
                     result=semantic_res.semantic_review_result,
                     suggested_confidence=semantic_res.suggested_confidence)

            # L4 adversarial ----------------------------------------------
            critic_res = self.critic.critique(rule, unit)
            ar.critic_result = critic_res.critic_result
            last["critic"] = critic_res
            rule.status = "critic_reviewed"
            if critic_res.challenge_points:
                rule.log(self.critic.name, "flagged " + "; ".join(
                    p["type"] for p in critic_res.challenge_points[:3]),
                    points=len(critic_res.challenge_points))
                self.memory.record_critic_pattern(rule, critic_res.challenge_points)

            needs_repair = (
                (not schema_res.schema_valid)
                or (not evidence_res.evidence_valid and round_no == 0)
                or critic_res.must_repair
                or semantic_res.semantic_review_result == "warn"
            )

            # fatal critic verdict cannot be repaired away
            if critic_res.critic_result == "fatal":
                break
            if not needs_repair or round_no >= cfg.max_repair_rounds:
                break

            repairs = self.repairer.repair(rule, unit, schema_res, evidence_res,
                                           semantic_res, critic_res)
            if not repairs:
                break
            repaired_overall = True
            self.memory.record_repairs(rule, repairs)
            # loop back: every repair is re-reviewed by all layers

        # Problem 2: span↔claim binding (deterministic, always on)
        binding = check_binding(rule)
        ar.binding_score = binding.binding_score
        ar.binding_multi_formula = binding.multi_formula
        last["binding"] = binding

        # Problem 3: multi-reviewer panel debate (LLM backend or panel mode)
        panel_res = self.panel.review(rule, unit) if self.use_panel else None
        if panel_res is not None:
            last["panel"] = panel_res
            rule.log(self.panel.name, "panel_debate",
                     support=panel_res.support, warn=panel_res.warn,
                     reject=panel_res.reject, agreement=round(panel_res.agreement, 3))

        # L5 consensus ----------------------------------------------------
        judgement = self.judge.judge(rule, last["evidence"], last["semantic"],
                                     last["critic"], ar.repair_round,
                                     repaired_overall,
                                     schema_valid=last["schema"].schema_valid,
                                     binding=binding, panel=panel_res)
        ar.consensus_score = judgement.consensus_score
        ar.review_status = judgement.autonomous_review_status
        ar.reason = judgement.reason
        rule.status = judgement.autonomous_review_status
        rule.log(self.judge.name, "consensus_judged",
                 status=judgement.autonomous_review_status,
                 score=judgement.consensus_score)
        self.memory.record_consensus(rule, judgement)

        # mark interpretive uncertainty for the bronze gate
        if rule.interpretation_level in ("normalized", "later_commentary"):
            ar.interpretive_uncertainty_marked = True

        # Release gate ------------------------------------------------------
        decision = self.gate.decide(rule)
        ar.release_level = decision.release_level
        if decision.release_level != "rejected":
            rule.status = f"released_{decision.release_level}"
        rule.log(self.gate.name, "release_gate",
                 level=decision.release_level, reasons=decision.reasons)
        self.memory.record_release(rule, decision)

        rule.review_records = {
            "schema": last["schema"].to_dict(),
            "evidence": last["evidence"].to_dict(),
            "semantic": last["semantic"].to_dict(),
            "critic": last["critic"].to_dict(),
            "binding": binding.to_dict(),
            "consensus": judgement.to_dict(),
            "release_gate": decision.to_dict(),
        }
        if panel_res is not None:
            rule.review_records["panel"] = panel_res.to_dict()
        self.memory.record_rule_audit(rule)
        self.memory.record_rule_summary(rule)
        return rule

    # ------------------------------------------------------------------
    def process_book(self, book_id: str) -> dict:
        """Extract + review every rule of one segmented book; persist stores."""
        su_path = self.config.source_units_dir / f"{book_id}.jsonl"
        units = [SourceUnit.from_dict(d) for d in read_jsonl(su_path)]
        rules: list[InitialRule] = []
        for unit in units:
            for rule in self.extractor.extract(unit):
                self.review_rule(rule, unit)
                rules.append(rule)

        write_jsonl(self.config.rules_initial_dir / f"{book_id}.jsonl",
                    (r.to_dict() for r in rules))
        by_level: dict[str, list[InitialRule]] = {}
        for r in rules:
            by_level.setdefault(r.autonomous_review.release_level, []).append(r)
        for level in ("gold", "silver", "bronze"):
            path = self.config.rules_released_dir / level / f"{book_id}.jsonl"
            if by_level.get(level):
                write_jsonl(path, (r.to_dict() for r in by_level[level]))
            elif path.exists():
                path.unlink()
        rej_path = self.config.rules_rejected_dir / f"{book_id}.jsonl"
        if by_level.get("rejected"):
            # rejected rules are never deleted — they feed audit memory and
            # future error analysis (but a re-run replaces the same book file)
            write_jsonl(rej_path, (r.to_dict() for r in by_level["rejected"]))

        status_counts = Counter(r.autonomous_review.review_status for r in rules)
        level_counts = Counter(r.autonomous_review.release_level for r in rules)
        return {
            "book_id": book_id,
            "source_units": len(units),
            "rules_extracted": len(rules),
            "schema_valid": sum(r.autonomous_review.schema_valid for r in rules),
            "evidence_verified": sum(r.autonomous_review.evidence_verified for r in rules),
            "auto_repaired": sum(r.autonomous_review.auto_repair_applied for r in rules),
            "by_status": dict(status_counts),
            "by_level": dict(level_counts),
        }

    def process_corpus(self, book_ids: list[str] | None = None) -> dict:
        su_dir = self.config.source_units_dir
        all_books = sorted(p.stem for p in Path(su_dir).glob("BOOK_*.jsonl"))
        targets = [b for b in all_books if not book_ids or b in book_ids]
        per_book = []
        for book_id in targets:
            per_book.append(self.process_book(book_id))
        totals = Counter()
        levels = Counter()
        statuses = Counter()
        for s in per_book:
            totals.update({k: s[k] for k in
                           ("source_units", "rules_extracted", "schema_valid",
                            "evidence_verified", "auto_repaired")})
            levels.update(s["by_level"])
            statuses.update(s["by_status"])
        summary = {"books": len(per_book), **dict(totals),
                   "by_level": dict(levels), "by_status": dict(statuses),
                   "per_book": per_book}
        self.memory.record_corpus({"event": "autonomous_review_run", **{
            k: v for k, v in summary.items() if k != "per_book"}})
        return summary
