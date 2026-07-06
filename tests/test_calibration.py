"""Risk-controlled release-gate calibration: exact statistics + guarantees.

Verifies the distribution-free machinery (binomial CDF, Clopper–Pearson bound),
the calibration diagnostics (ECE), the dual precision/recall threshold ladder,
and the opt-in wiring into ReleaseGateAgent (default behaviour unchanged)."""

import json
from pathlib import Path

import pytest

from hermes.metrics.calibration import (
    binomial_cdf, clopper_pearson_upper, expected_calibration_error,
    selective_risk_curve, RiskControlledCalibrator, load_calibrated_thresholds,
    run_calibration)

GOLD = Path(__file__).resolve().parents[1] / "data" / "eval" / "shanghan_gold.jsonl"


# --- exact binomial statistics ----------------------------------------------

def test_binomial_cdf_edges():
    assert binomial_cdf(10, 10, 0.5) == 1.0          # P(X ≤ n) = 1
    assert binomial_cdf(0, 10, 0.5) == pytest.approx(0.5 ** 10, rel=1e-9)
    assert binomial_cdf(5, 10, 0.0) == 1.0
    assert binomial_cdf(4, 10, 1.0) == 0.0
    # symmetric sanity: P(X ≤ 5 | n=10, p=0.5) = 0.623046875
    assert binomial_cdf(5, 10, 0.5) == pytest.approx(0.6230, abs=1e-3)


def test_clopper_pearson_properties():
    # zero failures ⇒ closed-form upper bound 1 − δ^(1/n)
    assert clopper_pearson_upper(0, 10, 0.05) == pytest.approx(
        1 - 0.05 ** (1 / 10), abs=1e-3)
    # all failures ⇒ 1.0; bound is monotone non-decreasing in k
    assert clopper_pearson_upper(10, 10, 0.05) == 1.0
    ups = [clopper_pearson_upper(k, 20, 0.05) for k in range(21)]
    assert ups == sorted(ups)
    # the bound must actually cover: P(Bin(n, U) ≤ k) ≈ δ
    U = clopper_pearson_upper(3, 30, 0.05)
    assert binomial_cdf(3, 30, U) == pytest.approx(0.05, abs=1e-3)


# --- calibration diagnostics -------------------------------------------------

def test_ece_perfect_and_worst():
    assert expected_calibration_error([(1.0, True)] * 10)["ece"] == 0.0
    # confident-but-wrong ⇒ ECE = confidence
    assert expected_calibration_error([(0.9, False)] * 10)["ece"] == \
        pytest.approx(0.9, abs=1e-6)


def test_selective_risk_monotone_in_coverage():
    pairs = [(0.9, True), (0.8, True), (0.7, False), (0.6, False)]
    curve = selective_risk_curve(pairs, steps=4)
    assert curve[0]["risk"] <= curve[-1]["risk"]        # risk grows w/ coverage
    assert curve[-1]["coverage"] == 1.0


# --- risk-controlled thresholds ---------------------------------------------

def test_calibrator_ladder_is_monotone():
    # synthetic: clean high-score rules + a few wrong low-score ones
    pairs = [(0.95, True)] * 20 + [(0.85, True)] * 20 + [(0.78, True)] * 20 \
        + [(0.5, False)] * 10
    cal = RiskControlledCalibrator(delta=0.05).calibrate(pairs)
    thr = cal.thresholds()
    assert thr["gold"] >= thr["silver"] >= thr["bronze"]
    # a wrong rule at 0.5 must not be releasable into any certified tier
    for t in cal.tiers:
        if t.threshold is not None:
            assert t.threshold > 0.5 or t.empirical_precision is not None


def test_calibrator_reports_recall_and_precision_bounds():
    cal = RiskControlledCalibrator().calibrate(
        [(0.95, True)] * 30 + [(0.8, True)] * 20 + [(0.6, False)] * 10)
    gold = next(t for t in cal.tiers if t.tier == "gold")
    assert 0.0 <= gold.error_upper_bound <= 1.0
    assert 0.0 <= gold.miss_upper_bound <= 1.0
    assert gold.empirical_precision is not None


def test_run_calibration_on_gold_set(tmp_path):
    from hermes.config import HermesConfig
    cfg = HermesConfig(root=tmp_path)
    payload = run_calibration(cfg, dataset=GOLD)
    cal = payload["calibration"]
    assert cal["n_calibration"] >= 55
    assert cal["confidence"] == 0.95
    thr = cal["calibrated_thresholds"]
    assert thr["gold"] >= thr["silver"] >= thr["bronze"]
    # headline finding: the fixed Gold threshold releases far fewer rules than
    # the risk-controlled one, with a much looser (useless) error bound
    base = payload["fixed_threshold_baseline"]
    gold_cal = next(t for t in cal["tiers"] if t["tier"] == "gold")
    assert gold_cal["n_released"] > base["gold"]["n_released"]
    assert gold_cal["error_upper_bound"] < base["gold"]["error_upper_bound"]
    # report + machine-readable thresholds written
    assert (cfg.reports_dir / "calibration_report_latest.md").exists()
    assert (cfg.data_dir / "eval" / "calibrated_gate.json").exists()


# --- opt-in wiring into the release gate ------------------------------------

def _write_calibrated_gate(cfg, thresholds):
    d = cfg.data_dir / "eval"
    d.mkdir(parents=True, exist_ok=True)
    (d / "calibrated_gate.json").write_text(
        json.dumps({"calibrated_thresholds": thresholds}), encoding="utf-8")


def test_load_thresholds_opt_in(cfg, monkeypatch):
    _write_calibrated_gate(cfg, {"gold": 0.87, "silver": 0.77, "bronze": 0.0})
    monkeypatch.delenv("HERMES_CALIBRATED_GATE", raising=False)
    assert load_calibrated_thresholds(cfg) is None          # disabled by default
    monkeypatch.setenv("HERMES_CALIBRATED_GATE", "1")
    assert load_calibrated_thresholds(cfg) == {
        "gold": 0.87, "silver": 0.77, "bronze": 0.0}


def test_gate_uses_calibrated_thresholds(cfg, guizhi_unit, monkeypatch):
    from hermes.agents.orchestrator import AutonomousReviewOrchestrator
    from hermes.agents.release_gate import ReleaseGateAgent
    orch = AutonomousReviewOrchestrator(cfg)
    rule = [r for r in orch.extractor.extract(guizhi_unit)
            if r.rule_type == "formula_indication_rule"][0]
    orch.review_rule(rule, guizhi_unit)
    score = rule.autonomous_review.consensus_score
    assert 0.85 <= score < 0.93          # lands in silver under fixed gate

    monkeypatch.delenv("HERMES_CALIBRATED_GATE", raising=False)
    assert ReleaseGateAgent(cfg).decide(rule).release_level == "silver"

    # calibrated Gold floor below the rule's score promotes it to gold
    _write_calibrated_gate(cfg, {"gold": 0.80, "silver": 0.77, "bronze": 0.0})
    monkeypatch.setenv("HERMES_CALIBRATED_GATE", "1")
    gate = ReleaseGateAgent(cfg)
    assert gate.calibrated
    assert gate.decide(rule).release_level == "gold"
