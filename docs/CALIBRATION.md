# Risk-Controlled Release Gate — distribution-free guarantees

Hermes ships a five-layer autonomous review whose final step, the
**ReleaseGateAgent**, sorts every rule into Gold / Silver / Bronze / Rejected by
its `consensus_score`.  The v5 thresholds (0.93 / 0.85 / 0.75) were hand-tuned.
This document describes how `hermes calibrate` replaces "hand-tuned" with a
**distribution-free, finite-sample statistical guarantee**, and the confidence-
calibration diagnostics it reports alongside.

Everything is pure Python (exact binomial statistics via `math.comb`/`lgamma`);
no numpy/scipy, no network.

## 1. The problem with fixed thresholds

A fixed cut-off makes an *implicit* claim ("rules ≥ 0.93 are Gold-quality")
that is never checked against ground truth, and it has no notion of confidence:
if only 8 rules clear 0.93, their true precision could be anywhere from 69% to
100% and you would not know. The gate should instead certify what it promises.

## 2. Method

We treat the labelled gold benchmark (`data/eval/shanghan_gold.jsonl`) as an
exchangeable **calibration set**: for every extracted+reviewed rule we have its
`consensus_score` and a correctness label (does it match a human-annotated
expectation of the same clause?). A tier releases every rule with score ≥ τ.
Two bounded, monotone 0/1 losses are controlled with an **exact Clopper–Pearson
(1−δ) upper confidence bound** on a binomial rate:

- **precision loss** — the error rate among *released* rules. Rises as τ falls
  (a looser gate lets in more mistakes). Certifying it ≤ 1−p\* gives
  *"a released rule is correct with probability ≥ p\*, at confidence 1−δ."*
- **recall loss** — the miss rate among *correct* rules (correct rules scoring
  below τ). Rises as τ rises (a tighter gate silently drops good rules).
  Certifying it ≤ 1−r\* guarantees the tier recovers ≥ r\* of the correct rules.

This is the **Risk-Controlling Prediction Sets** construction (Bates et al.,
JACM 2021) / **Learn-then-Test** (Angelopoulos et al., 2021); the loss-curve
view is **Conformal Risk Control** (Angelopoulos et al., ICLR 2024). Under
exchangeability of the calibration and deployment clauses the guarantee is
*finite-sample* — it holds for any n ≥ 1, with no distributional assumptions
and no normal approximation.

The threshold is chosen by the **recall** bound (the informative lever) and the
**precision** bound is *reported* at that τ. Selecting on recall avoids a
finite-sample trap: with zero observed errors, a narrow high-τ tier releases too
few rules for the error UCB to certify high precision (2 clean rules bound the
error rate only to ≤ 0.78 at n = 2), so a precision-driven search collapses
every tier to "release everything." Reporting precision instead keeps each tier
honest — empirical precision can be 100% while the *certified* precision is
capped by calibration-set size.

The three tiers use distinct recall targets, which induces a monotone ladder
τ_gold ≥ τ_silver ≥ τ_bronze (each tier's τ caps the next tier's search).

## 3. Confidence calibration diagnostics

The same labelled set yields standard trustworthy-AI diagnostics so the
consensus score can be read as a probability, not just a ranking:

- **Expected / Max Calibration Error** (ECE / MCE; Guo et al., 2017) — binned
  |accuracy − confidence|.
- **Reliability table** — per-bin confidence vs accuracy.
- **Selective risk–coverage curve** (El-Yaniv & Wiener, 2010) — error rate as
  the score threshold sweeps down.

## 4. What the current gold set shows

`hermes calibrate` (heuristic backend, 63 calibration rules, δ = 0.05) reports
three honest, reproducible findings:

1. **The hand-tuned Gold threshold is statistically unjustified.** τ = 0.93
   releases only 8 rules; with 0 observed errors the Clopper–Pearson bound still
   admits an error rate up to **0.31** — it certifies almost nothing — while
   dropping **87%** of the correct rules. The risk-controlled τ = 0.87 releases
   42 rules at the same empirical precision (100%), tightens the error bound to
   **0.07**, and certifies recall ≥ 55%.
2. **The consensus score is under-confident** (ECE **0.18**): every reliability
   bin has accuracy above its mean confidence.
3. **~8% of correct rules are hard-rejected** to score 0 (MCE **1.0**) — no
   release threshold can recover them, which pinpoints the false-rejection of
   the hard gates as the next improvement target.

The certified Gold *precision* target (0.95) is honestly flagged as
**not certifiable at n = 63** — the calibration set is too small and too clean
(no errors) to prove a 5%-error tail. Growing and diversifying the calibration
set (harder/ambiguous clauses, real negatives) is the stated path to tighter
certified tiers.

## 5. Usage

```bash
python3 -m hermes calibrate                       # default targets, δ = 0.05
python3 -m hermes calibrate --delta 0.1 \
    --targets gold=0.95:0.55 silver=0.90:0.80 bronze=0.80:0.95   # precision:recall

# opt in to the calibrated thresholds (default OFF — protocol constants unchanged)
export HERMES_CALIBRATED_GATE=1
python3 -m hermes pipeline
```

Outputs: `data/reports/calibration_report_latest.md` (human-readable),
`data/eval/calibrated_gate.json` (machine-readable thresholds the gate loads).

## 6. Honest scope

The guarantee is exact **for clauses exchangeable with the 宋本《傷寒論》/
《金匱》 gold set**. Deployment on the wider 66-book corpus is a distribution
shift, so the calibrated thresholds are a principled, auditable prior — not a
blanket promise over every book. The `HERMES_CALIBRATED_GATE` flag defaults to
off, so the shipped behaviour and every protocol invariant test are unchanged.
The calibrated gate re-tiers rules that already cleared the review loop's
`loop_min_consensus` floor; it does not itself resurrect loop-rejected rules.

## References

- Bates, Angelopoulos, Lei, Malik, Jordan. *Distribution-Free, Risk-Controlling
  Prediction Sets.* JACM 2021.
- Angelopoulos, Bates, Candès, Jordan, Lei. *Learn then Test: Calibrating
  Predictive Algorithms to Achieve Risk Control.* 2021.
- Angelopoulos, Bates, Fisch, Lei, Schuster. *Conformal Risk Control.* ICLR 2024.
- Angelopoulos & Bates. *A Gentle Introduction to Conformal Prediction and
  Distribution-Free Uncertainty Quantification.* 2023.
- Guo, Pleiss, Sun, Weinberger. *On Calibration of Modern Neural Networks.*
  ICML 2017.
- El-Yaniv & Wiener. *On the Foundations of Noise-free Selective Classification.*
  JMLR 2010.
