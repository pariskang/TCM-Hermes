# Extraction Benchmark (Gold Set)

- Generated: 2026-07-03T02:07:18Z
- Dataset: data/eval/shanghan_gold.jsonl (55 clauses)
- Backend: heuristic

## Detection (micro)

| precision | recall | f1 |
| --- | --- | --- |
| 0.883 | 0.883 | 0.883 |

## Per rule type

| rule_type | expected | detected | extracted | correct | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| formula_indication_rule | 32 | 31 | 32 | 31 | 0.969 | 0.969 | 0.969 |
| contraindication_rule | 9 | 8 | 8 | 8 | 1.0 | 0.889 | 0.941 |
| mistreatment_rule | 1 | 0 | 4 | 0 | 0.0 | 0.0 | None |
| prognosis_rule | 3 | 3 | 3 | 3 | 1.0 | 1.0 | 1.0 |
| transmission_rule | 2 | 0 | 0 | 0 | None | 0.0 | None |
| disease_definition_rule | 6 | 5 | 5 | 5 | 1.0 | 0.833 | 0.909 |
| pulse_pattern_rule | 3 | 2 | 4 | 2 | 0.5 | 0.667 | 0.571 |
| formula_composition_rule | 2 | 2 | 2 | 2 | 1.0 | 1.0 | 1.0 |
| preparation_rule | 2 | 2 | 2 | 2 | 1.0 | 1.0 | 1.0 |

## Condition quality (matched formula rules)

- recall 0.83 / precision 0.664

## Release-gate calibration

- correct rules: 53, mean consensus 0.829, levels {'gold': 7, 'bronze': 9, 'silver': 33, 'rejected': 4}
- spurious rules: 7, mean consensus 0.714, levels {'bronze': 5, 'silver': 1, 'rejected': 1}
- consensus separation (correct − spurious): 0.115
- gold precision: 1.0 / released precision: 0.891

## Missed expectations

- SHL_180: disease_definition_rule (陽明病)
- SHL_273: mistreatment_rule (下之)
- SHL_004: transmission_rule ()
- SHL_185: transmission_rule (轉屬陽明)
- SHL_351: formula_indication_rule (當歸四逆湯)
- SHL_063: contraindication_rule (不可更行)
- JGY_SB: pulse_pattern_rule (濕痹)
