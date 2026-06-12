"""Release-gate thresholds (section 八) and merged-rule support policy."""

import conftest as fx

from hermes.agents.release_gate import ReleaseGateAgent
from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.schemas import InitialRule
from hermes.schemas.initial_rule import AutonomousReview


def make_rule(**ar_kwargs) -> InitialRule:
    rule = InitialRule(
        initial_rule_id="IR_TEST_000001",
        category_path=["傷寒金匱類", "傷寒"],
        book_id="BOOK_TEST", book_title="傷寒論(宋本)", book_type="original",
        chapter_id="CH_TEST_001", chapter_title="辨太陽病脈證並治上",
        source_unit_id="SU_TEST_000001",
        rule_type="formula_indication_rule",
        if_conditions={"disease": ["太陽中風"]},
        then_conclusions={"formula": ["桂枝湯"]},
        evidence_span="桂枝湯主之",
        evidence_type="original_text",
        interpretation="",
        interpretation_level="original_text",
        model_confidence=0.9,
    )
    defaults = dict(schema_valid=True, evidence_verified=True,
                    semantic_review_result="pass", critic_result="pass",
                    review_status="model_accepted")
    defaults.update(ar_kwargs)
    rule.autonomous_review = AutonomousReview(**defaults)
    return rule


def gate(cfg):
    return ReleaseGateAgent(cfg)


def test_gold_gate(cfg):
    r = make_rule(consensus_score=0.95)
    assert gate(cfg).decide(r).release_level == "gold"


def test_gold_blocked_by_minor_critic(cfg):
    r = make_rule(consensus_score=0.95, critic_result="minor_issue",
                  auto_repair_applied=True)
    assert gate(cfg).decide(r).release_level == "silver"


def test_gold_blocked_by_unsupported_inference(cfg):
    r = make_rule(consensus_score=0.95, unsupported_inference_detected=True)
    assert gate(cfg).decide(r).release_level == "silver"


def test_silver_gate(cfg):
    r = make_rule(consensus_score=0.87)
    assert gate(cfg).decide(r).release_level == "silver"


def test_bronze_gate(cfg):
    r = make_rule(consensus_score=0.78, critic_result="minor_issue",
                  interpretive_uncertainty_marked=True)
    assert gate(cfg).decide(r).release_level == "bronze"


def test_reject_below_bronze(cfg):
    r = make_rule(consensus_score=0.70)
    assert gate(cfg).decide(r).release_level == "rejected"


def test_reject_on_evidence_failure(cfg):
    r = make_rule(consensus_score=0.99, evidence_verified=False)
    assert gate(cfg).decide(r).release_level == "rejected"


def test_reject_on_fatal_critic(cfg):
    r = make_rule(consensus_score=0.99, critic_result="fatal")
    assert gate(cfg).decide(r).release_level == "rejected"


def test_reject_on_schema_failure(cfg):
    r = make_rule(consensus_score=0.99, schema_valid=False)
    assert gate(cfg).decide(r).release_level == "rejected"


def test_conflict_not_released(cfg):
    r = make_rule(consensus_score=0.9, review_status="model_conflict")
    assert gate(cfg).decide(r).release_level == "rejected"


# ---------------------------------------------------------------------------
# merged rules: only silver/gold support; rejected never supports anything
# ---------------------------------------------------------------------------

def test_merged_rules_use_only_silver_gold(cfg):
    from hermes.agents.merger import RuleMergerAgent
    from hermes.utils import write_jsonl, read_jsonl

    orch = AutonomousReviewOrchestrator(cfg)
    unit = fx.make_unit(fx.GUIZHI_CLAUSE)
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl", [unit.to_dict()])
    orch.process_book("BOOK_TEST")

    # plant a second supporting book so the formula group has corroboration
    unit2 = fx.make_unit("太陽病，頭痛發熱，汗出惡風者，桂枝湯主之。",
                         su_id="SU_TES2_000001")
    unit2.book_id, unit2.book_title = "BOOK_TES2", "傷寒論(條文版)"
    write_jsonl(cfg.source_units_dir / "BOOK_TES2.jsonl", [unit2.to_dict()])
    orch.process_book("BOOK_TES2")

    RuleMergerAgent(cfg).run()
    merged = list(read_jsonl(cfg.rules_merged_dir / "merged_rules.jsonl"))
    guizhi = [m for m in merged if m.get("subject") == "桂枝湯"]
    assert guizhi, "桂枝湯 merged rule expected"
    m = guizhi[0]
    levels = m["supporting_rules_by_release_level"]
    assert not levels.get("bronze"), "bronze must not support merged rules by default"
    assert "rejected" not in levels
    assert m["supporting_initial_rules"]
    assert m["evidence_chain"], "merged rules must carry the evidence chain"
    assert all(e["evidence_span"] for e in m["evidence_chain"])
