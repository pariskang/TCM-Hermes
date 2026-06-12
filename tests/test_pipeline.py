"""End-to-end behaviour of the five-layer autonomous review loop."""

import conftest as fx
import pytest

from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.schemas import InitialRule


@pytest.fixture()
def orch(cfg):
    return AutonomousReviewOrchestrator(cfg)


def test_guizhi_clause_full_loop(orch, guizhi_unit):
    rules = orch.extractor.extract(guizhi_unit)
    indication = [r for r in rules if r.rule_type == "formula_indication_rule"]
    assert len(indication) == 1
    r = orch.review_rule(indication[0], guizhi_unit)

    # extraction quality (the spec's worked example)
    assert r.then_conclusions["formula"] == ["桂枝湯"]
    assert "太陽中風" in r.if_conditions["disease"]
    assert {"陽浮", "陰弱"} <= set(r.if_conditions["pulse"])
    assert "鼻鳴" in r.if_conditions["symptoms"]
    assert r.evidence_span in guizhi_unit.raw_text

    # autonomous review outcome
    ar = r.autonomous_review
    assert ar.schema_valid and ar.evidence_verified
    assert ar.review_status == "model_repaired_accepted"
    assert ar.auto_repair_applied
    # 治法 was a normalization → critic flagged → repaired
    assert r.interpretation_level == "normalized"
    assert ar.release_level in ("silver", "gold")
    assert ar.consensus_score >= 0.85

    # audit trail covers extractor, critic, repair, judge, gate
    agents = {e.agent for e in r.audit_trail}
    assert {"InitialRuleExtractorAgent", "AdversarialCriticAgent",
            "RuleRepairAgent", "ConsensusJudgeAgent",
            "ReleaseGateAgent"} <= agents


def test_disease_definition(orch):
    unit = fx.make_unit(fx.TAIYANG_DEFINITION, su_id="SU_TEST_000002")
    rules = orch.extractor.extract(unit)
    defs = [r for r in rules if r.rule_type == "disease_definition_rule"]
    assert defs
    r = orch.review_rule(defs[0], unit)
    assert r.then_conclusions["disease"] == ["太陽病"]
    assert "頭項強痛" in r.if_conditions["symptoms"]
    assert r.autonomous_review.release_level == "gold"   # all terms verbatim


def test_contraindication(orch):
    unit = fx.make_unit(fx.CONTRA_CLAUSE, su_id="SU_TEST_000003")
    rules = orch.extractor.extract(unit)
    contra = [r for r in rules if r.rule_type == "contraindication_rule"]
    assert contra
    r = orch.review_rule(contra[0], unit)
    assert r.then_conclusions["prohibition"] == ["不可發汗"]
    assert r.autonomous_review.evidence_verified


def test_mistreatment(orch):
    unit = fx.make_unit(fx.MISTREAT_CLAUSE, su_id="SU_TEST_000004")
    rules = orch.extractor.extract(unit)
    mt = [r for r in rules if r.rule_type == "mistreatment_rule"]
    assert mt
    r = orch.review_rule(mt[0], unit)
    assert "若下" in r.then_conclusions["mistreatment"][0]
    assert r.autonomous_review.evidence_verified


def test_formula_block_composition(orch):
    unit = fx.make_unit(fx.FORMULA_BLOCK, text_type="formula",
                        su_id="SU_TEST_000005")
    rules = orch.extractor.extract(unit)
    types = {r.rule_type for r in rules}
    assert "formula_composition_rule" in types
    assert "preparation_rule" in types
    comp = next(r for r in rules if r.rule_type == "formula_composition_rule")
    r = orch.review_rule(comp, unit)
    assert any("桂枝" in c for c in r.then_conclusions["composition"])
    assert r.autonomous_review.schema_valid          # empty IF is legal here
    assert r.autonomous_review.release_level == "gold"


def test_fabricated_evidence_is_rejected(orch, guizhi_unit):
    rules = orch.extractor.extract(guizhi_unit)
    r = rules[0]
    r.evidence_span = "此句不在原文之中也"
    orch.review_rule(r, guizhi_unit)
    assert not r.autonomous_review.evidence_verified
    assert r.autonomous_review.review_status == "model_rejected"
    assert r.autonomous_review.release_level == "rejected"


def test_fabricated_condition_detected_and_repaired(orch, guizhi_unit):
    rules = orch.extractor.extract(guizhi_unit)
    r = [x for x in rules if x.rule_type == "formula_indication_rule"][0]
    r.if_conditions["symptoms"].append("頭眩")     # not in this clause
    orch.review_rule(r, guizhi_unit)
    # the critic's false-support detection fires; repair drops the term
    assert "頭眩" not in r.if_conditions["symptoms"]
    assert any("頭眩" in e.detail.get("terms", [])
               for e in r.audit_trail
               if e.action == "dropped_unsupported_conditions")


def test_commentary_contamination_relabelled(orch):
    unit = fx.make_unit(fx.COMMENTARY_TEXT, text_type="commentary",
                        book_type="commentary", su_id="SU_TEST_000006")
    rules = orch.extractor.extract(unit)
    assert rules
    r = orch.review_rule(rules[0], unit)
    assert r.evidence_type == "commentary"
    assert r.interpretation_level == "later_commentary"
    assert r.autonomous_review.release_level != "gold"


def test_rejected_rules_are_preserved(orch, cfg, guizhi_unit, tmp_path):
    from hermes.utils import write_jsonl, read_jsonl
    # build a corpus of one unit, inject a broken rule via low confidence
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl", [guizhi_unit.to_dict()])
    stats = orch.process_book("BOOK_TEST")
    assert stats["rules_extracted"] >= 1
    # all stores exist; rejected dir is reserved even if empty this run
    assert (cfg.rules_initial_dir / "BOOK_TEST.jsonl").exists()
    total_released = sum(
        1 for level in ("gold", "silver", "bronze")
        for _ in read_jsonl(cfg.rules_released_dir / level / "BOOK_TEST.jsonl"))
    rejected = sum(1 for _ in read_jsonl(cfg.rules_rejected_dir / "BOOK_TEST.jsonl"))
    assert total_released + rejected == stats["rules_extracted"]


def test_serialization_roundtrip(orch, guizhi_unit):
    r = orch.review_rule(orch.extractor.extract(guizhi_unit)[0], guizhi_unit)
    d = r.to_dict()
    r2 = InitialRule.from_dict(d)
    assert r2.initial_rule_id == r.initial_rule_id
    assert r2.autonomous_review.consensus_score == r.autonomous_review.consensus_score
    assert len(r2.audit_trail) == len(r.audit_trail)
