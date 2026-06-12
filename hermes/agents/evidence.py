"""EvidenceVerifierAgent — layer 2: strict evidence grounding.

Core rule of the protocol:
    evidence_span MUST be an exact substring of the source unit's raw_text.
    If it is not, the rule may not proceed to merging — ever.

The verifier also locates the span (offsets), checks the source-unit linkage
and classifies the evidence type against the unit's text_type.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..schemas import InitialRule, SourceUnit


@dataclass
class EvidenceReview:
    evidence_valid: bool
    evidence_span_found: bool
    source_unit_match: bool
    evidence_type: str
    span_start: int = -1
    span_end: int = -1
    problems: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "evidence_valid": self.evidence_valid,
            "evidence_span_found": self.evidence_span_found,
            "source_unit_match": self.source_unit_match,
            "evidence_type": self.evidence_type,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "problems": self.problems,
        }


_EXPECTED = {"original": "original_text", "commentary": "commentary",
             "formula": "formula_block", "variant": "variant",
             "case": "case_record"}


class EvidenceVerifierAgent:
    name = "EvidenceVerifierAgent"

    def verify(self, rule: InitialRule, unit: SourceUnit | None) -> EvidenceReview:
        problems: list[str] = []

        source_match = unit is not None and unit.source_unit_id == rule.source_unit_id
        if not source_match:
            problems.append("source_unit_id does not resolve to a corpus unit")

        span = rule.evidence_span or ""
        found = False
        start = end = -1
        if not span.strip():
            problems.append("evidence_span is empty")
        elif unit is not None:
            idx = unit.raw_text.find(span)
            if idx >= 0:
                found, start, end = True, idx, idx + len(span)
            else:
                problems.append("evidence_span is not a strict substring of raw_text")

        expected = _EXPECTED.get(unit.text_type, "original_text") if unit else "original_text"
        if found and rule.evidence_type != expected:
            problems.append(
                f"evidence_type '{rule.evidence_type}' inconsistent with source "
                f"text_type '{unit.text_type}' (expected '{expected}')")

        valid = found and source_match
        return EvidenceReview(
            evidence_valid=valid,
            evidence_span_found=found,
            source_unit_match=source_match,
            evidence_type=expected,
            span_start=start,
            span_end=end,
            problems=problems,
        )
