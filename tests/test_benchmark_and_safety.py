"""Gold-set extraction benchmark + herb incompatibility screening (十八反/十九畏)."""

import json
from pathlib import Path

import pytest

from hermes.knowledge.incompatibility import check_safety, formula_safety
from hermes.knowledge.lexicon import LEXICON
from hermes.metrics.benchmark import EVAL_TYPES, GoldBenchmark

GOLD = Path(__file__).resolve().parents[1] / "data" / "eval" / "shanghan_gold.jsonl"


# --- gold dataset integrity --------------------------------------------------

def _records():
    with open(GOLD, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_gold_dataset_integrity():
    records = _records()
    assert len(records) >= 50
    ids = [r["clause_id"] for r in records]
    assert len(ids) == len(set(ids))
    for r in records:
        assert r["raw_text"]
        for e in r["expected_rules"]:
            assert e["rule_type"] in EVAL_TYPES
            # annotation strings must be verbatim substrings of the clause
            for t in e.get("conditions", []):
                assert t in r["raw_text"], (r["clause_id"], t)
            if e.get("formula"):
                assert e["formula"] in r["raw_text"], (r["clause_id"], e["formula"])
    # includes at least one no-rule probe clause for spurious-rate measurement
    assert any(not r["expected_rules"] for r in records)


# --- benchmark harness -------------------------------------------------------

@pytest.fixture(scope="module")
def results(tmp_path_factory):
    from hermes.config import HermesConfig
    cfg = HermesConfig(root=tmp_path_factory.mktemp("bench"))
    bench = GoldBenchmark(cfg, dataset=GOLD)
    res = bench.run()
    res["_report_path"] = str(bench.report(res))
    return res


def test_benchmark_detection_quality(results):
    micro = results["micro"]
    assert micro["expected"] >= 55
    # baseline after the benchmark-driven extractor fixes: micro 0.98 —
    # regression guard a step below the measured values
    assert micro["precision"] >= 0.9
    assert micro["recall"] >= 0.9
    assert results["by_rule_type"]["formula_indication_rule"]["recall"] >= 0.95
    assert results["by_rule_type"]["contraindication_rule"]["precision"] >= 0.9
    assert results["by_rule_type"]["mistreatment_rule"]["recall"] >= 0.9
    assert results["by_rule_type"]["transmission_rule"]["recall"] >= 0.9


def test_benchmark_gate_calibration(results):
    gc = results["gate_calibration"]
    # separation only means anything with samples on both sides
    if gc["consensus_separation"] is not None and gc["spurious"]["rules"] >= 3:
        assert gc["consensus_separation"] > 0.05
    # gold/released precision are the primary calibration guards
    if gc["gold_precision"] is not None:
        assert gc["gold_precision"] >= 0.9
    assert gc["released_precision"] >= 0.9


def test_benchmark_report_written(results):
    text = Path(results["_report_path"]).read_text(encoding="utf-8")
    for section in ("Detection (micro)", "Per rule type",
                    "Release-gate calibration", "Missed expectations"):
        assert section in text


# --- 十八反 / 十九畏 / 毒性 / 妊娠 -------------------------------------------

def test_eighteen_antagonisms_detected():
    out = check_safety(["甘草", "甘遂"])
    assert out["risk_level"] == "high"
    assert any(p["type"] == "十八反" and p["rule"] == "甘草 × 甘遂"
               for p in out["incompatible_pairs"])


def test_aconite_group_membership():
    # 附子 hits the 烏頭類 rule against 半夏 and 貝母 derivatives
    out = check_safety(["附子", "半夏", "川貝母"])
    rules = {p["rule"] for p in out["incompatible_pairs"]}
    assert {"烏頭類 × 半夏", "烏頭類 × 貝母"} <= rules


def test_nineteen_incompatibilities_simplified_input():
    out = check_safety(["人参", "五灵脂"])          # simplified input
    assert any(p["type"] == "十九畏" for p in out["incompatible_pairs"])


def test_clean_formula_no_flags():
    out = check_safety(["桂枝", "白芍", "炙甘草", "生姜", "大枣"])
    assert out["incompatible_pairs"] == []
    assert out["risk_level"] == "none"


def test_toxicity_and_pregnancy_flags():
    out = check_safety(["附子", "巴豆"])
    toxic = {t["herb"]: t for t in out["toxic_herbs"]}
    assert toxic["附子"]["level"] == "high" and "炮製" in toxic["附子"]["note"]
    grades = {p["herb"]: p["grade"] for p in out["pregnancy_cautions"]}
    assert grades["巴豆"] == "禁用"
    assert out["disclaimer"]


def test_formula_safety_canonical_lookup():
    assert formula_safety("不存在之湯") is None
    aconite_formula = next(f for f, i in LEXICON.canonical_formulas.items()
                           if "附子" in i["herbs"])
    report = formula_safety(aconite_formula)
    assert report["risk_level"] in ("high", "caution")
    assert any(t["herb"] == "附子" for t in report["toxic_herbs"])


def test_match_prescription_carries_safety(cfg):
    from hermes.lineage.prescription import PrescriptionMatcherAgent
    out = PrescriptionMatcherAgent(cfg).match(["甘草", "甘遂", "大棗"])
    assert out["safety"]["risk_level"] == "high"
    assert any(p["type"] == "十八反" for p in out["safety"]["incompatible_pairs"])
