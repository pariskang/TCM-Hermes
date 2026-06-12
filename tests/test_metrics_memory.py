"""Quality metrics, autonomous report, memory stores, themes."""

import conftest as fx
import pytest

from hermes import protocol
from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.agents.theme import ThemeInducerAgent
from hermes.memory.store import MemoryStore
from hermes.metrics.quality import QualityMetrics
from hermes.metrics.report import AutonomousReviewReporter
from hermes.utils import write_jsonl


@pytest.fixture()
def built(cfg):
    orch = AutonomousReviewOrchestrator(cfg)
    units = [
        fx.make_unit(fx.GUIZHI_CLAUSE),
        fx.make_unit(fx.TAIYANG_DEFINITION, su_id="SU_TEST_000002", seq=1),
        fx.make_unit(fx.CONTRA_CLAUSE, su_id="SU_TEST_000003", seq=2),
        fx.make_unit(fx.FORMULA_BLOCK, text_type="formula",
                     su_id="SU_TEST_000004", seq=3),
    ]
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl",
                [u.to_dict() for u in units])
    orch.process_book("BOOK_TEST")
    return cfg


def test_quality_metrics_complete(built):
    m = QualityMetrics(built).compute()
    for key in protocol.QUALITY_METRICS:
        assert key in m, key
    assert m["rules_total"] >= 4
    assert m["evidence_verification_rate"] == 1.0
    assert 0 <= m["consensus_score_mean"] <= 1


def test_report_structure(built):
    path = AutonomousReviewReporter(built).generate(scope_label="test scope")
    text = path.read_text(encoding="utf-8")
    for section in ("# Autonomous Review Report", "## Corpus Scope",
                    "## Extraction Statistics", "## Release Levels",
                    "## Main Critic Findings", "## Auto Repair Summary",
                    "## Residual Risks", "## Rules Ready for Skill Compilation"):
        assert section in text, section
    # no retired human metrics anywhere in the report
    for banned in protocol.BANNED_FIELDS:
        assert banned not in text


def test_memory_streams(built):
    store = MemoryStore(built)
    assert store.count("model_audit_memory") >= 4
    assert store.count("consensus_memory") >= 4
    assert store.count("release_memory") >= 4
    assert store.count("rule_memory") >= 4
    audit = next(store.iter("model_audit_memory"))
    for key in ("rule_id", "audit_summary", "agents_involved",
                "final_status", "release_level"):
        assert key in audit
    with pytest.raises(ValueError):
        store.add("expert_memory", {})       # not a memory type


def test_theme_induction(built):
    out = ThemeInducerAgent(built).run()
    assert out["chapter_themes"] >= 1
    assert out["book_themes"] >= 1
    assert out["category_themes"] >= 1
    from hermes.utils import read_jsonl
    themes = list(read_jsonl(built.rules_theme_dir / "book_themes.jsonl"))
    t = themes[0]
    assert t["supporting_initial_rules"]
    assert t["supporting_rules_by_release_level"]
    assert not t["supporting_rules_by_release_level"].get("bronze"), \
        "themes must not use bronze by default"
