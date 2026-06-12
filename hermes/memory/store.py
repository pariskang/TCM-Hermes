"""Hermes memory system (section 六 — fully de-humanized).

Memory types: corpus, terminology, rule, model_audit, critic, repair,
consensus, release, skill, evaluation, user_workflow.  JSONL-backed, one file
per type.  The retired reviewer/expert-feedback memories do not exist.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from .. import protocol
from ..config import HermesConfig
from ..utils import append_jsonl, read_jsonl, utc_now


class MemoryStore:
    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def _path(self, memory_type: str) -> Path:
        if memory_type not in protocol.MEMORY_TYPES:
            raise ValueError(f"unknown memory type: {memory_type} "
                             f"(allowed: {protocol.MEMORY_TYPES})")
        return self.config.memory_dir / f"{memory_type}.jsonl"

    def add(self, memory_type: str, record: dict[str, Any]) -> dict:
        rec = {"memory_type": memory_type, "recorded_at": utc_now(), **record}
        append_jsonl(self._path(memory_type), rec)
        return rec

    def iter(self, memory_type: str) -> Iterator[dict]:
        yield from read_jsonl(self._path(memory_type))

    def count(self, memory_type: str) -> int:
        return sum(1 for _ in self.iter(memory_type))


class MemoryCuratorAgent:
    """Curates cross-rule pattern memories out of raw audit streams."""
    name = "MemoryCuratorAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.store = MemoryStore(self.config)

    # ------------------------------------------------------------------
    def record_rule_audit(self, rule) -> None:
        """ModelAuditMemory for one finished rule."""
        ar = rule.autonomous_review
        agents = sorted({e.agent for e in rule.audit_trail})
        self.store.add("model_audit_memory", {
            "rule_id": rule.initial_rule_id,
            "audit_summary": ar.reason,
            "agents_involved": agents,
            "final_status": ar.review_status,
            "release_level": ar.release_level,
            "consensus_score": ar.consensus_score,
            "critic_result": ar.critic_result,
            "repair_round": ar.repair_round,
        })

    def record_critic_pattern(self, rule, challenge_points: list[dict]) -> None:
        for cp in challenge_points:
            self.store.add("critic_memory", {
                "pattern": cp.get("type", "unknown"),
                "message": cp.get("message", ""),
                "rule_id": rule.initial_rule_id,
                "recommended_action": _critic_action(cp.get("type", "")),
                "applies_to_rule_types": [rule.rule_type],
            })

    def record_repairs(self, rule, repairs: list[dict]) -> None:
        for rep in repairs:
            self.store.add("repair_memory", {
                "problem_type": rep.get("type", "unknown"),
                "repair_strategy": _repair_strategy(rep.get("type", "")),
                "example_rule_id": rule.initial_rule_id,
                "detail": {k: v for k, v in rep.items() if k != "type"},
            })

    def record_consensus(self, rule, judgement) -> None:
        self.store.add("consensus_memory", {
            "rule_id": rule.initial_rule_id,
            "status": judgement.autonomous_review_status,
            "consensus_score": judgement.consensus_score,
            "reason": judgement.reason,
        })

    def record_release(self, rule, decision) -> None:
        self.store.add("release_memory", {
            "rule_id": rule.initial_rule_id,
            "release_level": decision.release_level,
            "reasons": decision.reasons,
        })

    def record_corpus(self, summary: dict) -> None:
        self.store.add("corpus_memory", summary)

    def record_terminology(self, term: str, kind: str, context: dict | None = None) -> None:
        self.store.add("terminology_memory",
                       {"term": term, "kind": kind, "context": context or {}})

    def record_rule_summary(self, rule) -> None:
        self.store.add("rule_memory", {
            "rule_id": rule.initial_rule_id,
            "rule_type": rule.rule_type,
            "book_id": rule.book_id,
            "release_level": rule.autonomous_review.release_level,
            "formula": rule.then_conclusions.get("formula", []),
            "disease": rule.if_conditions.get("disease", []),
        })

    def record_skill(self, skill_id: str, detail: dict) -> None:
        self.store.add("skill_memory", {"skill_id": skill_id, **detail})

    def record_evaluation(self, metrics: dict) -> None:
        self.store.add("evaluation_memory", metrics)

    # ------------------------------------------------------------------
    def critic_pattern_digest(self, top: int = 10) -> list[dict]:
        c = Counter(m.get("pattern", "?") for m in self.store.iter("critic_memory"))
        return [{"pattern": p, "count": n} for p, n in c.most_common(top)]

    def repair_pattern_digest(self, top: int = 10) -> list[dict]:
        c = Counter(m.get("problem_type", "?") for m in self.store.iter("repair_memory"))
        return [{"problem_type": p, "count": n} for p, n in c.most_common(top)]


def _critic_action(pattern: str) -> str:
    return {
        "interpretation_level_issue":
            "将 interpretation_level 标记为 normalized 或 later_commentary",
        "unsupported_condition": "删去证据未支持的条件并在 interpretation 中记录",
        "commentary_contamination": "split original evidence and later interpretation",
        "conditional_clause_ignored": "扩展证据片段以包含限制条件或在解释中注明",
        "over_generalized_claim": "弱化普遍化表述，限定为本条文证据范围",
        "evidence_span_too_long": "裁剪证据片段至结论所在句群",
        "formula_not_in_evidence": "拒绝规则：方剂与条文严重错配",
        "context_mixing": "校正类目语境或拒绝跨语境断言",
    }.get(pattern, "复核证据与表述")


def _repair_strategy(problem_type: str) -> str:
    return {
        "relabel_interpretation_level": "relabel interpretation level",
        "changed interpretation_level from original_text to normalized":
            "relabel interpretation level",
        "evidence_type_relabelled": "split original evidence and later interpretation",
        "dropped_unsupported_conditions": "drop unsupported conditions, keep audit note",
        "evidence_span_trimmed": "trim evidence span to clause boundary",
        "evidence_span_relocated": "re-anchor evidence span on raw text",
        "confidence_adjusted": "average extractor and reviewer confidence",
        "confidence_clamped": "clamp confidence to [0,1]",
        "rule_type_corrected": "remap rule_type from controlled vocabulary",
        "claim_softened": "remove over-generalization markers",
    }.get(problem_type, problem_type)
