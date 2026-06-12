# Autonomous Review Report

- Generated: 2026-06-12T04:53:56Z
- Protocol: hermes-v5 (autonomous model review — no human review nodes)
- Corpus version: jicheng-2026-06-12

## Corpus Scope

- Category: 傷寒金匱類 / 傷寒; 傷寒金匱類 / 綜合; 傷寒金匱類 / 醫案; 傷寒金匱類 / 金匱
- Scope label: pipeline run
- Books: 60
- Chapters: 2750
- SourceUnits with rules: 19548

## Extraction Statistics

- InitialRules extracted: 28475
- Schema valid: 20650
- Evidence verified: 28475
- Model accepted: 9733
- Model repaired accepted: 7915
- Model low confidence: 0
- Model conflict: 0
- Model rejected: 10827

## Release Levels

- Gold: 1441
- Silver: 5789
- Bronze: 10418
- Rejected: 10827 (preserved in data/rules_rejected/)

## Quality Metrics

- autonomous_acceptance_rate: 0.6198
- model_repair_rate: 0.516
- critic_rejection_rate: 0.0209
- evidence_verification_rate: 1.0
- consensus_score_mean: 0.5822
- gold_rule_rate: 0.0506
- silver_rule_rate: 0.2033
- bronze_rule_rate: 0.3659
- model_conflict_rate: 0.0
- false_support_detection_rate: 0.0214

## Main Critic Findings

1. interpretation_level_issue × 16789
2. isolated_clause_generalization × 5075
3. conditional_clause_ignored × 4732
4. evidence_span_too_long × 1799
5. formula_not_in_evidence × 596
6. unsupported_condition × 93
7. over_generalized_claim × 4
8. context_mixing × 2

## Auto Repair Summary

- changed interpretation_level from original_text to normalized × 7616
- changed interpretation_level from original_text to later_commentary × 6996
- changed interpretation_level from normalized to later_commentary × 2177
- evidence_span_trimmed × 151
- dropped_unsupported_conditions × 93
- confidence_adjusted × 89
- claim_softened × 2

## Residual Risks

- 当前轮次无显著残余风险；持续监控 critic_memory 模式漂移。

## Rules Ready for Skill Compilation

- Silver/Gold InitialRules: 7230
- Coverage: 57 books, 1438 chapters

---
原则：自主审核 ≠ 无审核；自主审核 = 多模型、多轮、多证据、多门控的自动化审核。
No evidence, no rule. No source trace, no answer.
