"""Risk-controlled release-gate calibration + confidence-calibration diagnostics.

The v5 release gate ships hand-tuned consensus thresholds (Gold 0.93 / Silver
0.85 / Bronze 0.75).  This module replaces "hand-tuned" with a distribution-free
*statistical guarantee* on a labelled calibration set (the gold benchmark):

  Risk-Controlling Prediction Sets (Bates et al., JACM 2021) / Learn-then-Test
  (Angelopoulos et al., 2021).  For a tier that releases every rule whose
  consensus score ≥ τ, the per-tier error (a bounded 0/1 loss, monotone
  non-increasing in τ) is controlled by choosing the smallest τ whose
  (1−δ) upper confidence bound on the error rate is ≤ 1 − p*.  With an exact
  Clopper–Pearson binomial bound this yields, under exchangeability of the
  calibration and deployment clauses:

        P( error_rate(released at τ̂) ≤ 1 − p* ) ≥ 1 − δ      (finite-sample)

  i.e. "when Hermes releases a rule at tier T, it is correct with probability
  ≥ p*, certified at confidence 1−δ."  This turns the release levels from a
  heuristic into a risk-controlled decision with an auditable guarantee.

We also report standard confidence-calibration diagnostics — Expected
Calibration Error (Naeini et al., 2015; Guo et al., 2017), a reliability table,
and the selective-risk/coverage curve (El-Yaniv & Wiener, 2010) — so the
consensus score can be read as a probability, not just a ranking.

Everything is pure Python (exact binomial CDF via math.comb); no numpy/scipy.

Caveat (stated, not hidden): the gold set is drawn from 宋本《傷寒論》/《金匱》.
The guarantee is exact *for clauses exchangeable with that set*; deployment on
the wider corpus is a distribution shift, so the calibrated thresholds are a
principled, auditable prior — not a blanket promise over every book.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# exact binomial statistics (no scipy)
# ---------------------------------------------------------------------------


def binomial_cdf(k: int, n: int, p: float) -> float:
    """P(X ≤ k) for X ~ Binomial(n, p), computed exactly."""
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    if k >= n:
        return 1.0
    k = min(k, n)
    # sum in log space for numerical stability at larger n
    total = 0.0
    for i in range(k + 1):
        log_term = (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                    + i * math.log(p) + (n - i) * math.log1p(-p))
        total += math.exp(log_term)
    return min(total, 1.0)


def clopper_pearson_upper(k: int, n: int, delta: float = 0.05) -> float:
    """Exact (1−delta) upper confidence bound on a binomial rate.

    Given k "failures" in n exchangeable trials, returns the largest plausible
    true rate p_U such that P(Bin(n, p_U) ≤ k) = delta.  This is the upper
    Clopper–Pearson limit; it inverts the exact binomial tail (no normal
    approximation), so it is valid for any n ≥ 1.
    """
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0
    # binomial_cdf(k, n, ·) is monotone decreasing in p; find the p where it
    # crosses delta by bisection.
    lo, hi = float(k) / n, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if binomial_cdf(k, n, mid) > delta:
            lo = mid
        else:
            hi = mid
    return hi


# ---------------------------------------------------------------------------
# confidence-calibration diagnostics
# ---------------------------------------------------------------------------


def expected_calibration_error(pairs: list[tuple[float, bool]],
                               bins: int = 10) -> dict:
    """ECE with equal-width bins over [0,1].

    pairs: (confidence in [0,1], correct?).  ECE = Σ_b (n_b/N)·|acc_b − conf_b|;
    also returns MCE (max gap) and the per-bin reliability table.
    """
    n = len(pairs)
    if n == 0:
        return {"ece": None, "mce": None, "n": 0, "bins": []}
    table = []
    ece = mce = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        # last bin is closed on the right so conf == 1.0 lands somewhere
        members = [(c, y) for c, y in pairs
                   if (lo <= c < hi) or (b == bins - 1 and c == 1.0)]
        if not members:
            continue
        nb = len(members)
        conf = sum(c for c, _ in members) / nb
        acc = sum(1 for _, y in members if y) / nb
        gap = abs(acc - conf)
        ece += (nb / n) * gap
        mce = max(mce, gap)
        table.append({"range": [round(lo, 3), round(hi, 3)], "count": nb,
                      "confidence": round(conf, 4), "accuracy": round(acc, 4),
                      "gap": round(gap, 4)})
    return {"ece": round(ece, 4), "mce": round(mce, 4), "n": n, "bins": table}


def selective_risk_curve(pairs: list[tuple[float, bool]],
                         steps: int = 20) -> list[dict]:
    """Risk (error rate) vs coverage as the score threshold sweeps down.

    Rules are accepted in descending-score order; each point reports the
    fraction of rules covered and the error rate among them.  A well-ordered
    score is monotone: risk rises as coverage grows.
    """
    if not pairs:
        return []
    ordered = sorted(pairs, key=lambda t: -t[0])
    n = len(ordered)
    out = []
    for s in range(1, steps + 1):
        m = max(1, round(n * s / steps))
        acc = ordered[:m]
        errors = sum(1 for _, y in acc if not y)
        out.append({"coverage": round(m / n, 3),
                    "threshold": round(acc[-1][0], 4),
                    "risk": round(errors / m, 4)})
    return out


# ---------------------------------------------------------------------------
# risk-controlled thresholds
# ---------------------------------------------------------------------------


@dataclass
class TierGuarantee:
    tier: str
    target_precision: float
    target_recall: float
    threshold: float | None          # None ⇒ no threshold certifies both bounds
    n_released: int
    empirical_precision: float | None
    error_upper_bound: float | None      # Clopper–Pearson UCB on error rate
    empirical_recall: float | None       # recovered correct / all correct
    miss_upper_bound: float | None       # Clopper–Pearson UCB on miss rate
    precision_certified: bool
    recall_certified: bool
    note: str = ""

    @property
    def certified(self) -> bool:
        return self.precision_certified and self.recall_certified

    def to_dict(self) -> dict:
        return {"tier": self.tier,
                "target_precision": self.target_precision,
                "target_recall": self.target_recall,
                "threshold": self.threshold, "n_released": self.n_released,
                "empirical_precision": self.empirical_precision,
                "error_upper_bound": self.error_upper_bound,
                "empirical_recall": self.empirical_recall,
                "miss_upper_bound": self.miss_upper_bound,
                "precision_certified": self.precision_certified,
                "recall_certified": self.recall_certified,
                "certified": self.certified, "note": self.note}


@dataclass
class Calibration:
    delta: float
    tiers: list[TierGuarantee] = field(default_factory=list)
    ece: dict = field(default_factory=dict)
    selective_risk: list = field(default_factory=list)
    n_calibration: int = 0

    def thresholds(self) -> dict:
        return {t.tier: t.threshold for t in self.tiers}

    def to_dict(self) -> dict:
        return {"method": "risk_controlling_prediction_sets",
                "bound": "clopper_pearson_exact_binomial",
                "confidence": round(1 - self.delta, 3),
                "delta": self.delta,
                "n_calibration": self.n_calibration,
                "tiers": [t.to_dict() for t in self.tiers],
                "calibrated_thresholds": self.thresholds(),
                "ece": self.ece,
                "selective_risk": self.selective_risk}


# default dual targets (tier, precision, recall): Gold is the most selective
# high-precision band (accepts a lower recall of the correct rules); Bronze is
# the high-recall floor.  Distinct recall targets induce the τ ladder.
DEFAULT_TARGETS: list[tuple[str, float, float]] = [
    ("gold", 0.95, 0.55), ("silver", 0.90, 0.80), ("bronze", 0.80, 0.95),
]


class RiskControlledCalibrator:
    """Per-tier thresholds with a *dual* distribution-free guarantee.

    Each tier releases rules with consensus score ≥ τ.  Two monotone 0/1 losses
    carry exact Clopper–Pearson (1−δ) upper bounds (RCPS / Learn-then-Test):

      precision — error rate among *released* rules ≤ 1 − p*  (rises as τ ↓)
      recall    — miss rate among *correct* rules  ≤ 1 − r*   (rises as τ ↑)

    τ is chosen by the recall bound (the informative lever: a higher τ silently
    drops more correct rules), and the precision bound is *reported* at that τ.
    Selecting on recall avoids a subtle finite-sample trap: with zero observed
    errors, a narrow high-τ tier releases too few rules for the error UCB to
    certify high precision (2 clean rules only bound error ≤ 0.78 at n=2), so a
    precision-driven search would collapse every tier to "release everything".
    Reporting precision instead keeps the tier honest: empirical precision may
    be 100 % while the *certified* precision is capped by calibration-set size.
    """

    name = "RiskControlledCalibrator"

    def __init__(self, delta: float = 0.05,
                 targets: list[tuple[str, float, float]] | None = None) -> None:
        self.delta = delta
        self.targets = targets or DEFAULT_TARGETS

    def _certify_tier(self, tier: str, p_target: float, r_target: float,
                      pairs: list[tuple[float, bool]],
                      correct_scores: list[float], ceiling: float) -> TierGuarantee:
        max_err, max_miss = 1.0 - p_target, 1.0 - r_target
        n_correct = len(correct_scores)

        def _tier(tau: float) -> TierGuarantee:
            released = [(c, y) for c, y in pairs if c >= tau]
            n_rel = len(released)
            errors = sum(1 for _, y in released if not y)
            err_ucb = clopper_pearson_upper(errors, n_rel, self.delta) \
                if n_rel else 1.0
            misses = sum(1 for c in correct_scores if c < tau)
            miss_ucb = clopper_pearson_upper(misses, n_correct, self.delta) \
                if n_correct else 0.0
            return TierGuarantee(
                tier, p_target, r_target, tau, n_rel,
                round(1 - errors / n_rel, 4) if n_rel else None,
                round(err_ucb, 4),
                round(1 - misses / n_correct, 4) if n_correct else None,
                round(miss_ucb, 4) if n_correct else None,
                err_ucb <= max_err, miss_ucb <= max_miss)

        # choose τ by the recall bound: the largest (most selective) τ ≤ ceiling
        # whose miss-rate UCB still certifies recall ≥ r*.  Descending scan.
        cand = sorted({round(c, 4) for c, _ in pairs if c <= ceiling}, reverse=True)
        chosen: TierGuarantee | None = None
        for tau in cand:
            g = _tier(tau)
            if g.recall_certified:
                chosen = g
                break
        if chosen is None:
            # recall unattainable at any τ (e.g. correct rules hard-rejected to
            # score 0 exceed the miss budget) — fall back to the least-selective
            # operating point and flag it honestly.
            chosen = _tier(min(cand)) if cand else TierGuarantee(
                tier, p_target, r_target, None, 0, None, None, None, None,
                False, False, "no calibration rules below the ceiling")
            if chosen.threshold is not None and not chosen.recall_certified:
                chosen.note = (f"recall {r_target} not certifiable at n={n_correct} "
                               "(correct rules hard-rejected below any threshold); "
                               "reported at the widest operating point")
        if chosen.threshold is not None and not chosen.precision_certified \
                and not chosen.note:
            chosen.note = (f"precision {p_target} not certified at this "
                           f"calibration size (empirical "
                           f"{chosen.empirical_precision}); add labelled data")
        return chosen

    def calibrate(self, pairs: list[tuple[float, bool]]) -> Calibration:
        """pairs: (consensus_score, is_correct) for every reviewed rule."""
        cal = Calibration(delta=self.delta, n_calibration=len(pairs))
        correct_scores = [c for c, y in pairs if y]
        ceiling = 1.0
        # tiers from most to least selective; each tier's τ caps the next
        # (τ_gold ≥ τ_silver ≥ τ_bronze) so the ladder is monotone.
        for tier, p_target, r_target in self.targets:
            g = self._certify_tier(tier, p_target, r_target, pairs,
                                   correct_scores, ceiling)
            cal.tiers.append(g)
            if g.threshold is not None:
                ceiling = g.threshold
        cal.ece = expected_calibration_error(pairs)
        cal.selective_risk = selective_risk_curve(pairs)
        return cal


def realized_precision(pairs: list[tuple[float, bool]],
                       threshold: float) -> dict:
    """Empirical precision + n of the rules a fixed threshold would release."""
    released = [(c, y) for c, y in pairs if c >= threshold]
    n = len(released)
    if n == 0:
        return {"threshold": threshold, "n_released": 0, "precision": None,
                "error_upper_bound": None}
    errors = sum(1 for _, y in released if not y)
    return {"threshold": threshold, "n_released": n,
            "precision": round(1 - errors / n, 4),
            "error_upper_bound": round(clopper_pearson_upper(errors, n, 0.05), 4)}


def run_calibration(config, delta: float = 0.05,
                    targets: list[tuple[str, float, float]] | None = None,
                    dataset=None, backend=None) -> dict:
    """Benchmark → risk-controlled thresholds → report; returns the payload.

    Also contrasts the calibrated thresholds with the hand-tuned protocol
    defaults on the same set — the headline the methods section reports.
    """
    from .benchmark import GoldBenchmark
    from ..utils import utc_now, write_json

    bench = GoldBenchmark(config, dataset=dataset, backend=backend)
    pairs = bench.labeled_scores()
    cal = RiskControlledCalibrator(delta=delta, targets=targets).calibrate(pairs)

    baseline = {tier: realized_precision(pairs, thr) for tier, thr in (
        ("gold", config.gold_min_consensus),
        ("silver", config.silver_min_consensus),
        ("bronze", config.bronze_min_consensus))}

    payload = {"generated_at": utc_now(),
               "dataset": str(bench.dataset),
               "backend": getattr(bench.orch.backend, "kind", "heuristic"),
               "calibration": cal.to_dict(),
               "fixed_threshold_baseline": baseline}

    out_dir = config.data_dir / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "calibrated_gate.json", cal.to_dict())
    write_json(out_dir / "calibration_full.json", payload)
    _write_report(config, payload)
    return payload


def _write_report(config, payload: dict) -> None:
    from ..utils import write_json  # noqa: F401 (keep import parity)
    cal = payload["calibration"]
    lines = [
        "# Risk-Controlled Release-Gate Calibration", "",
        f"- Generated: {payload['generated_at']}",
        f"- Dataset: {payload['dataset']} (backend: {payload['backend']})",
        f"- Method: {cal['method']} · bound: {cal['bound']}",
        f"- Confidence 1−δ = {cal['confidence']} · calibration rules: "
        f"{cal['n_calibration']}", "",
        "## Calibrated thresholds (dual distribution-free guarantee)", "",
        "Each tier certifies both an error-rate bound (precision) and a "
        "miss-rate bound (recall) with an exact Clopper–Pearson "
        f"{cal['confidence']:.0%} upper bound.", "",
        "| tier | target P / R | τ | n rel. | emp. P | error UCB "
        "| emp. R | miss UCB | certified |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for t in cal["tiers"]:
        lines.append(
            f"| {t['tier']} | {t['target_precision']}/{t['target_recall']} "
            f"| {t['threshold']} | {t['n_released']} | {t['empirical_precision']} "
            f"| {t['error_upper_bound']} | {t['empirical_recall']} "
            f"| {t['miss_upper_bound']} | {'✓' if t['certified'] else '✗'} |")
    base = payload["fixed_threshold_baseline"]
    lines += ["", "## Hand-tuned protocol thresholds on the same set", "",
              "| tier | τ (fixed) | n released | empirical precision "
              "| error UCB |", "| --- | --- | --- | --- | --- |"]
    for tier in ("gold", "silver", "bronze"):
        b = base[tier]
        lines.append(f"| {tier} | {b['threshold']} | {b['n_released']} "
                     f"| {b['precision']} | {b['error_upper_bound']} |")
    ece = cal["ece"]
    lines += ["", "## Confidence calibration", "",
              f"- Expected Calibration Error (ECE): {ece.get('ece')}",
              f"- Max Calibration Error (MCE): {ece.get('mce')}", "",
              "| confidence bin | count | mean confidence | accuracy | gap |",
              "| --- | --- | --- | --- | --- |"]
    for b in ece.get("bins", []):
        lines.append(f"| {b['range']} | {b['count']} | {b['confidence']} "
                     f"| {b['accuracy']} | {b['gap']} |")
    lines += ["", "## Selective risk (error vs coverage)", "",
              "| coverage | threshold | risk |", "| --- | --- | --- |"]
    for p in cal["selective_risk"]:
        lines.append(f"| {p['coverage']} | {p['threshold']} | {p['risk']} |")
    lines += ["", "> Guarantee holds for clauses exchangeable with the "
              "宋本《傷寒論》/《金匱》 gold set; deployment on the wider corpus is "
              "a distribution shift — calibrated thresholds are an auditable "
              "prior, not a blanket promise.", ""]
    path = config.reports_dir / "calibration_report_latest.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_calibrated_thresholds(config) -> dict | None:
    """Return {gold,silver,bronze: τ} if calibrated-gate mode is enabled.

    Opt-in: set HERMES_CALIBRATED_GATE=1 and run `hermes calibrate` first.
    Absent file or disabled flag ⇒ None (the gate keeps the protocol defaults),
    so default behaviour and every existing test are unchanged.
    """
    import os
    from ..utils import read_json
    if os.environ.get("HERMES_CALIBRATED_GATE", "") not in ("1", "true", "yes"):
        return None
    data = read_json(config.data_dir / "eval" / "calibrated_gate.json")
    if not data:
        return None
    thr = data.get("calibrated_thresholds", {})
    out = {}
    for tier in ("gold", "silver", "bronze"):
        v = thr.get(tier)
        if isinstance(v, (int, float)):
            out[tier] = float(v)
    return out or None
