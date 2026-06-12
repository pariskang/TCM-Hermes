# Autonomous Review Report

- Generated: 2026-06-12T05:05:46Z
- Protocol: hermes-v5 (autonomous model review — no human review nodes)
- Corpus version: jicheng-2026-06-12

## Corpus Scope

- Category: 傷寒金匱類 / 傷寒; 傷寒金匱類 / 綜合; 傷寒金匱類 / 醫案; 傷寒金匱類 / 金匱
- Scope label: pipeline run
- Books: 60
- Chapters: 2747
- SourceUnits with rules: 19512

## Extraction Statistics

- InitialRules extracted: 28421
- Schema valid: 20616
- Evidence verified: 28421
- Model accepted: 9670
- Model repaired accepted: 7949
- Model low confidence: 0
- Model conflict: 0
- Model rejected: 10802

## Release Levels

- Gold: 1434
- Silver: 5798
- Bronze: 10387
- Rejected: 10802 (preserved in data/rules_rejected/)

## Quality Metrics

- autonomous_acceptance_rate: 0.6199
- model_repair_rate: 0.5191
- critic_rejection_rate: 0.0209
- evidence_verification_rate: 1.0
- consensus_score_mean: 0.5824
- gold_rule_rate: 0.0505
- silver_rule_rate: 0.204
- bronze_rule_rate: 0.3655
- model_conflict_rate: 0.0
- false_support_detection_rate: 0.0214

## Main Critic Findings

1. interpretation_level_issue × 16850
2. isolated_clause_generalization × 5085
3. conditional_clause_ignored × 4746
4. evidence_span_too_long × 1800
5. formula_not_in_evidence × 593
6. unsupported_condition × 94
7. over_generalized_claim × 4
8. context_mixing × 2

## Auto Repair Summary

- changed interpretation_level from original_text to normalized × 7689
- changed interpretation_level from original_text to later_commentary × 6984
- changed interpretation_level from normalized to later_commentary × 2177
- evidence_span_trimmed × 153
- dropped_unsupported_conditions × 94
- confidence_adjusted × 90
- claim_softened × 2

## Residual Risks

- 当前轮次无显著残余风险；持续监控 critic_memory 模式漂移。

## Rules Ready for Skill Compilation

- Silver/Gold InitialRules: 7232
- Coverage: 57 books, 1438 chapters

---
原则：自主审核 ≠ 无审核；自主审核 = 多模型、多轮、多证据、多门控的自动化审核。
No evidence, no rule. No source trace, no answer.
