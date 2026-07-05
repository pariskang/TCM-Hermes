# Risk-Controlled Release-Gate Calibration

- Generated: 2026-07-04T16:16:08Z
- Dataset: data/eval/shanghan_gold.jsonl (backend: heuristic)
- Method: risk_controlling_prediction_sets · bound: clopper_pearson_exact_binomial
- Confidence 1−δ = 0.95 · calibration rules: 63

## Calibrated thresholds (dual distribution-free guarantee)

Each tier certifies both an error-rate bound (precision) and a miss-rate bound (recall) with an exact Clopper–Pearson 95% upper bound.

| tier | target P / R | τ | n rel. | emp. P | error UCB | emp. R | miss UCB | certified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gold | 0.95/0.55 | 0.87 | 42 | 1.0 | 0.0688 | 0.6667 | 0.4435 | ✗ |
| silver | 0.9/0.8 | 0.77 | 58 | 1.0 | 0.0503 | 0.9206 | 0.1597 | ✓ |
| bronze | 0.8/0.95 | 0.0 | 63 | 1.0 | 0.0464 | 1.0 | 0.0464 | ✓ |

## Hand-tuned protocol thresholds on the same set

| tier | τ (fixed) | n released | empirical precision | error UCB |
| --- | --- | --- | --- | --- |
| gold | 0.93 | 8 | 1.0 | 0.3123 |
| silver | 0.85 | 42 | 1.0 | 0.0688 |
| bronze | 0.75 | 58 | 1.0 | 0.0503 |

## Confidence calibration

- Expected Calibration Error (ECE): 0.1836
- Max Calibration Error (MCE): 1.0

| confidence bin | count | mean confidence | accuracy | gap |
| --- | --- | --- | --- | --- |
| [0.0, 0.1] | 5 | 0.0 | 1.0 | 1.0 |
| [0.7, 0.8] | 5 | 0.7764 | 1.0 | 0.2236 |
| [0.8, 0.9] | 14 | 0.8295 | 1.0 | 0.1705 |
| [0.9, 1.0] | 39 | 0.9215 | 1.0 | 0.0785 |

## Selective risk (error vs coverage)

| coverage | threshold | risk |
| --- | --- | --- |
| 0.048 | 0.94 | 0.0 |
| 0.095 | 0.94 | 0.0 |
| 0.143 | 0.92 | 0.0 |
| 0.206 | 0.92 | 0.0 |
| 0.254 | 0.92 | 0.0 |
| 0.302 | 0.92 | 0.0 |
| 0.349 | 0.92 | 0.0 |
| 0.397 | 0.92 | 0.0 |
| 0.444 | 0.92 | 0.0 |
| 0.508 | 0.92 | 0.0 |
| 0.556 | 0.9 | 0.0 |
| 0.603 | 0.9 | 0.0 |
| 0.651 | 0.876 | 0.0 |
| 0.698 | 0.82 | 0.0 |
| 0.746 | 0.82 | 0.0 |
| 0.794 | 0.82 | 0.0 |
| 0.857 | 0.796 | 0.0 |
| 0.905 | 0.77 | 0.0 |
| 0.952 | 0.0 | 0.0 |
| 1.0 | 0.0 | 0.0 |

> Guarantee holds for clauses exchangeable with the 宋本《傷寒論》/《金匱》 gold set; deployment on the wider corpus is a distribution shift — calibrated thresholds are an auditable prior, not a blanket promise.

