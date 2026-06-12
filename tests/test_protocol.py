"""The v5 protocol itself: principles, vocabularies, no human-review remnants."""

import json
from pathlib import Path

from hermes import protocol


def test_core_principles_are_autonomous():
    assert "autonomous_model_review_required" in protocol.CORE_PRINCIPLES
    assert "model_consensus_required" in protocol.CORE_PRINCIPLES
    assert "evidence_trace_required" in protocol.CORE_PRINCIPLES
    assert "release_gate_required" in protocol.CORE_PRINCIPLES
    # the retired principles are not principles
    assert "human_review_required" not in protocol.CORE_PRINCIPLES
    assert "expert_approved_required" not in protocol.CORE_PRINCIPLES


def test_statuses_match_spec():
    for s in ("extracted", "schema_validated", "evidence_verified",
              "model_reviewed", "critic_reviewed", "auto_repaired",
              "model_accepted", "model_low_confidence", "model_conflict",
              "model_rejected", "released_bronze", "released_silver",
              "released_gold"):
        assert s in protocol.RULE_STATUSES
    for banned in ("pending", "needs_human", "expert_approved"):
        assert banned not in protocol.RULE_STATUSES


def test_thresholds():
    assert protocol.GOLD_MIN_CONSENSUS == 0.93
    assert protocol.SILVER_MIN_CONSENSUS == 0.85
    assert protocol.BRONZE_MIN_CONSENSUS == 0.75
    assert protocol.LOOP_MIN_CONSENSUS == 0.75
    assert protocol.MAX_REPAIR_ROUNDS == 2


def test_memory_types_dehumanized():
    for mt in ("corpus_memory", "terminology_memory", "rule_memory",
               "model_audit_memory", "critic_memory", "repair_memory",
               "consensus_memory", "release_memory", "skill_memory",
               "evaluation_memory"):
        assert mt in protocol.MEMORY_TYPES
    assert "reviewer_memory" not in protocol.MEMORY_TYPES
    assert "expert_feedback_memory" not in protocol.MEMORY_TYPES


def test_quality_metrics_dehumanized():
    assert "autonomous_acceptance_rate" in protocol.QUALITY_METRICS
    assert "false_support_detection_rate" in protocol.QUALITY_METRICS
    assert "human_review_resolution_rate" not in protocol.QUALITY_METRICS
    assert "expert_approval_rate" not in protocol.QUALITY_METRICS


def test_no_banned_fields_in_source_tree():
    """The codebase must not *use* retired human-review fields.

    The only place a banned name may appear is the BANNED_FIELDS blocklist
    itself (protocol.py) and the validator/tests that enforce it.
    """
    root = Path(__file__).resolve().parents[1] / "hermes"
    offenders = []
    for py in root.rglob("*.py"):
        if py.name == "protocol.py":
            continue
        text = py.read_text(encoding="utf-8")
        for banned in protocol.BANNED_FIELDS:
            if f'"{banned}"' in text or f"'{banned}'" in text:
                offenders.append((str(py), banned))
    assert not offenders, offenders
