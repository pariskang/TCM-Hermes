# Extraction Benchmark (Gold Set)

- Generated: 2026-07-03T02:22:14Z
- Dataset: data/eval/shanghan_gold.jsonl (55 clauses)
- Backend: heuristic

## Detection (micro)

| precision | recall | f1 |
| --- | --- | --- |
| 1.0 | 1.0 | 1.0 |

## Per rule type

| rule_type | expected | detected | extracted | correct | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| formula_indication_rule | 32 | 32 | 32 | 32 | 1.0 | 1.0 | 1.0 |
| contraindication_rule | 9 | 9 | 9 | 9 | 1.0 | 1.0 | 1.0 |
| mistreatment_rule | 1 | 1 | 1 | 1 | 1.0 | 1.0 | 1.0 |
| prognosis_rule | 3 | 3 | 3 | 3 | 1.0 | 1.0 | 1.0 |
| transmission_rule | 2 | 2 | 3 | 3 | 1.0 | 1.0 | 1.0 |
| disease_definition_rule | 6 | 6 | 6 | 6 | 1.0 | 1.0 | 1.0 |
| pulse_pattern_rule | 5 | 5 | 5 | 5 | 1.0 | 1.0 | 1.0 |
| formula_composition_rule | 2 | 2 | 2 | 2 | 1.0 | 1.0 | 1.0 |
| preparation_rule | 2 | 2 | 2 | 2 | 1.0 | 1.0 | 1.0 |

## Condition quality (matched formula rules)

- recall 0.833 / precision 0.669

## Release-gate calibration

- correct rules: 63, mean consensus 0.816, levels {'gold': 8, 'bronze': 16, 'silver': 34, 'rejected': 5}
- spurious rules: 0, mean consensus None, levels {}
- consensus separation (correct − spurious): None
- gold precision: 1.0 / released precision: 1.0

## Missed expectations

- none
