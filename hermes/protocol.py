"""Hermes v5 protocol constants.

This module is the single source of truth for the autonomous model-review
protocol: rule statuses, release levels, gate thresholds, controlled
vocabularies and memory types.  No human-review concept exists anywhere in
the protocol — review is performed exclusively by the five-layer autonomous
pipeline (schema → evidence → semantic → adversarial → consensus).

Core principles
---------------
* autonomous_model_review_required — every rule passes the five-layer review.
* model_consensus_required        — release requires a consensus judgement.
* evidence_trace_required         — no evidence, no rule.
* release_gate_required           — nothing ships without a gate decision.
"""

from __future__ import annotations

PROTOCOL_VERSION = "hermes-v5"

CORE_PRINCIPLES = (
    "autonomous_model_review_required",
    "model_consensus_required",
    "evidence_trace_required",
    "release_gate_required",
)

# Field names of the retired human-review protocol.  They must never appear
# in any Hermes artifact; SchemaValidator rejects rules containing them and
# the test-suite scans every generated file for them.
BANNED_FIELDS = (
    "human_review_required",
    "expert_approved",
    "expert_approved_required",
    "needs_human",
    "human_review_queue",
    "reviewer_memory",
    "expert_feedback_memory",
    "human_review_resolution_rate",
    "expert_approval_rate",
)

# ---------------------------------------------------------------------------
# Rule lifecycle
# ---------------------------------------------------------------------------

RULE_STATUSES = (
    "extracted",
    "schema_validated",
    "evidence_verified",
    "model_reviewed",
    "critic_reviewed",
    "auto_repaired",
    "model_accepted",
    "model_low_confidence",
    "model_conflict",
    "model_rejected",
    "released_bronze",
    "released_silver",
    "released_gold",
)

REVIEW_STATUSES = (
    "model_accepted",
    "model_repaired_accepted",
    "model_low_confidence",
    "model_conflict",
    "model_rejected",
)

CRITIC_RESULTS = ("pass", "minor_issue", "major_issue", "fatal")
SEMANTIC_REVIEW_RESULTS = ("pass", "warn", "fail")

RELEASE_LEVELS = ("gold", "silver", "bronze", "rejected")

# Release-gate thresholds (section 八 of the protocol).
GOLD_MIN_CONSENSUS = 0.93
SILVER_MIN_CONSENSUS = 0.85
BRONZE_MIN_CONSENSUS = 0.75

# Autonomous loop termination (section 七).
LOOP_MIN_CONSENSUS = 0.75
MAX_REPAIR_ROUNDS = 2
# |extractor confidence - reviewer confidence| above this ⇒ model_conflict.
CONFLICT_DELTA = 0.35

# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------

RULE_TYPES = (
    "formula_indication_rule",      # 方证规则
    "pulse_pattern_rule",           # 脉证规则
    "symptom_rule",                 # 症状规则
    "pathomechanism_rule",          # 病机规则
    "treatment_principle_rule",     # 治法规则
    "contraindication_rule",        # 禁忌规则
    "mistreatment_rule",            # 误治规则
    "transmission_rule",            # 传变规则
    "prognosis_rule",               # 预后规则
    "dosage_rule",                  # 剂量规则
    "preparation_rule",             # 煎服法规则
    "formula_composition_rule",     # 方药组成规则
    "differential_diagnosis_rule",  # 鉴别诊断规则
    "disease_definition_rule",      # 病证定义规则
)

INTERPRETATION_LEVELS = (
    "original_text",        # 原文直述
    "normalized",           # 归纳/规范化解释
    "later_commentary",     # 后世注家解释
    "modern_interpretation",
)

EVIDENCE_TYPES = (
    "original_text",
    "commentary",
    "formula_block",
    "variant",
    "case_record",
)

SOURCE_TEXT_TYPES = (
    "original",
    "commentary",
    "formula",
    "variant",
    "case",
    "preface",
    "toc",
)

BOOK_TYPES = ("original", "commentary", "compilation", "case_collection")

# ---------------------------------------------------------------------------
# Memory system (section 六)
# ---------------------------------------------------------------------------

MEMORY_TYPES = (
    "corpus_memory",
    "terminology_memory",
    "rule_memory",
    "model_audit_memory",
    "critic_memory",
    "repair_memory",
    "consensus_memory",
    "release_memory",
    "skill_memory",
    "evaluation_memory",
    "user_workflow_memory",
)

# ---------------------------------------------------------------------------
# Quality metrics (section 九)
# ---------------------------------------------------------------------------

QUALITY_METRICS = (
    "autonomous_acceptance_rate",
    "model_repair_rate",
    "critic_rejection_rate",
    "evidence_verification_rate",
    "consensus_score_mean",
    "gold_rule_rate",
    "silver_rule_rate",
    "bronze_rule_rate",
    "model_conflict_rate",
    "false_support_detection_rate",
)

# ---------------------------------------------------------------------------
# Catalog (中醫笈成 傷寒金匱類)
# ---------------------------------------------------------------------------

ROOT_CATEGORY = "傷寒金匱類"

# raw manifest category → normalized sub-category
SUBCATEGORY_MAP = {
    "傷寒": "傷寒",
    "金匱": "金匱",
    "傷寒 金匱": "綜合",
    "醫案 傷寒 金匱": "醫案",
}

JICHENG_CORPUS_URL = "https://jicheng.tw/files/jcw/book-20180111.7z"


def category_path(subcategory: str) -> list[str]:
    if subcategory in SUBCATEGORY_MAP:
        return [ROOT_CATEGORY, SUBCATEGORY_MAP[subcategory]]
    # non-傷寒金匱 categories (外科/溫病/本草… — used by the disease corpus)
    # root under a generic 典籍 top so they don't masquerade as 傷寒金匱類
    return ["典籍", subcategory]
