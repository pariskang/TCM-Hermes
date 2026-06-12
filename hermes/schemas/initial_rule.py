"""InitialRule v5 — evidence-linked IF/THEN rule with full autonomous-review state."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from ..utils import utc_now


@dataclass
class AuditEvent:
    agent: str
    action: str
    timestamp: str = field(default_factory=utc_now)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        if not d.get("detail"):
            d.pop("detail", None)
        return d


@dataclass
class AutonomousReview:
    """Aggregated state of the five-layer autonomous review."""
    schema_valid: bool = False
    evidence_verified: bool = False
    semantic_review_result: str = "pending"      # pass | warn | fail
    critic_result: str = "pending"               # pass | minor_issue | major_issue | fatal
    auto_repair_applied: bool = False
    repair_round: int = 0
    consensus_score: float = 0.0
    binding_score: float = 1.0                   # Problem 2: span↔claim binding (0..1)
    binding_multi_formula: bool = False          # span asserts several formulas
    release_level: str = "rejected"              # gold | silver | bronze | rejected
    review_status: str = "pending"               # model_accepted | model_repaired_accepted | ...
    unsupported_inference_detected: bool = False
    commentary_contamination_detected: bool = False
    over_modernized_interpretation: bool = False
    interpretive_uncertainty_marked: bool = False
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InitialRule:
    initial_rule_id: str
    category_path: list[str]
    book_id: str
    book_title: str
    book_type: str
    chapter_id: str
    chapter_title: str
    source_unit_id: str
    rule_type: str
    if_conditions: dict[str, list[str]]      # disease/symptoms/pulse/pathomechanism/...
    then_conclusions: dict[str, list[str]]   # formula/treatment_principle/prohibition/...
    evidence_span: str
    evidence_type: str                       # original_text | commentary | formula_block | ...
    interpretation: str
    interpretation_level: str                # original_text | normalized | later_commentary | ...
    model_confidence: float
    status: str = "extracted"
    clause_no: str | None = None
    autonomous_review: AutonomousReview = field(default_factory=AutonomousReview)
    audit_trail: list[AuditEvent] = field(default_factory=list)
    review_records: dict[str, Any] = field(default_factory=dict)  # per-layer raw outputs
    extraction_pattern: str = ""             # which extraction rule fired (traceability)

    # ------------------------------------------------------------------
    def log(self, agent: str, action: str, **detail: Any) -> None:
        self.audit_trail.append(AuditEvent(agent=agent, action=action, detail=detail))

    def all_condition_terms(self) -> list[str]:
        out: list[str] = []
        for vals in self.if_conditions.values():
            out.extend(vals)
        return out

    def all_conclusion_terms(self) -> list[str]:
        out: list[str] = []
        for vals in self.then_conclusions.values():
            out.extend(vals)
        return out

    def to_dict(self) -> dict:
        d = asdict(self)
        d["autonomous_review"] = self.autonomous_review.to_dict()
        d["audit_trail"] = [e.to_dict() if isinstance(e, AuditEvent) else e
                            for e in self.audit_trail]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "InitialRule":
        d = dict(d)
        ar = d.get("autonomous_review") or {}
        if isinstance(ar, dict):
            known = {f for f in AutonomousReview.__dataclass_fields__}  # type: ignore[attr-defined]
            d["autonomous_review"] = AutonomousReview(
                **{k: v for k, v in ar.items() if k in known})
        trail = []
        for e in d.get("audit_trail") or []:
            if isinstance(e, dict):
                trail.append(AuditEvent(agent=e.get("agent", "?"),
                                        action=e.get("action", "?"),
                                        timestamp=e.get("timestamp", utc_now()),
                                        detail=e.get("detail", {}) or {}))
            else:
                trail.append(e)
        d["audit_trail"] = trail
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})
