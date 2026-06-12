"""MergedHermesRule v5 — cross-book merged rule.

Merged rules never overwrite InitialRules: they reference them, preserve the
full evidence chain, per-level support, variants and conflicts.  Only
silver/gold InitialRules may support a merged rule (bronze opt-in by config;
rejected rules never)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class MergedHermesRule:
    merged_rule_id: str
    title: str
    merged_rule_type: str                       # formula_pattern | disease_pattern | ...
    abstracted_claim: str
    source_level: str = "model_inductive_summary"
    subject: str = ""                           # canonical formula / disease name
    if_profile: dict[str, list[dict]] = field(default_factory=dict)   # term → counts
    then_profile: dict[str, list[dict]] = field(default_factory=dict)
    supporting_initial_rules: list[str] = field(default_factory=list)
    supporting_rules_by_release_level: dict[str, list[str]] = field(default_factory=dict)
    evidence_chain: list[dict] = field(default_factory=list)   # per-rule book/chapter/span
    variant_set: list[dict] = field(default_factory=list)
    conflict_set: list[dict] = field(default_factory=list)
    autonomous_review: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MergedHermesRule":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})
