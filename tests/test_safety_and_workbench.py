"""Safety governance + patient/physician workbench boundaries."""

import conftest as fx

from hermes.agents.safety import SafetyGovernanceAgent
from hermes.workbench.patient import PatientEducationAgent
from hermes.workbench.physician import DoctorAssistantAgent
from hermes.lineage.prescription import PrescriptionMatcherAgent
from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.utils import write_jsonl


def test_patient_prescription_request_refused():
    safety = SafetyGovernanceAgent()
    v = safety.check_patient_query("我最近怕冷出汗，帮我开个方子吃什么药？")
    assert not v.allowed
    assert v.refusal_reason == "prescription_request"
    assert "不能提供" in v.notice


def test_patient_dosage_request_refused():
    v = SafetyGovernanceAgent().check_patient_query("桂枝汤剂量应该加倍吗？")
    assert not v.allowed


def test_risk_signal_triggers_urgent():
    v = SafetyGovernanceAgent().check_patient_query("我胸痛半小时不缓解还出冷汗")
    assert v.urgent and not v.allowed
    assert "急救" in v.notice or "就医" in v.notice


def test_patient_explain_is_educational(cfg):
    pt = PatientEducationAgent(cfg)
    out = pt.explain("医生说我营卫不和是什么意思？")
    assert out["allowed"]
    assert out["term"] == "營衛不和" or out["term"] == "营卫不和"
    answer = out["answer"]
    assert "不能替代医生" in answer          # disclaimer always appended
    for forbidden in ("我建议你服用", "每日三次", "你患的是"):
        assert forbidden not in answer


def test_patient_explain_refuses_prescription(cfg):
    out = PatientEducationAgent(cfg).explain("什么是太阳病？顺便帮我开点药")
    assert out["allowed"] is False


def test_visit_preparation(cfg):
    prep = PatientEducationAgent(cfg).visit_preparation(
        "最近两周怕冷、出汗、乏力", history="无慢性病")
    assert prep["主诉整理"]
    assert prep["建议询问医生的问题"]
    assert "不能替代医生" in prep["disclaimer"]


def test_physician_match_carries_evidence(cfg):
    orch = AutonomousReviewOrchestrator(cfg)
    u1 = fx.make_unit(fx.GUIZHI_CLAUSE)
    u2 = fx.make_unit("太陽病，頭痛發熱，汗出惡風者，桂枝湯主之。",
                      su_id="SU_TEST_000002", seq=1)
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl",
                [u1.to_dict(), u2.to_dict()])
    orch.process_book("BOOK_TEST")

    doc = DoctorAssistantAgent(cfg)
    res = doc.match_pattern(symptoms=["汗出", "惡風"], pulse=["陽浮"])
    assert res["candidates"]
    top = res["candidates"][0]
    assert top["formula"] == "桂枝湯"
    assert top["supporting_rules"][0]["evidence_span"]
    assert top["supporting_rules"][0]["release_level"] in ("gold", "silver", "bronze")
    assert "执业" in res["disclaimer"] or "資質" in res["disclaimer"]


def test_prescription_matcher(cfg):
    m = PrescriptionMatcherAgent(cfg).match(["桂枝", "白芍", "炙甘草", "生姜", "大枣"])
    assert m["matches"]
    assert m["matches"][0]["formula"] == "桂枝湯"
    assert m["matches"][0]["similarity"] > 0.8
    assert "桂枝加葛根湯" in m["matches"][0]["related_formulas"]


def test_prescription_matcher_xiaochaihu(cfg):
    m = PrescriptionMatcherAgent(cfg).match(
        ["柴胡", "黄芩", "半夏", "人参", "甘草", "生姜", "大枣"])
    assert m["matches"][0]["formula"] == "小柴胡湯"


def test_marketing_compliance():
    bad = SafetyGovernanceAgent().check_marketing_copy("本品可根治糖尿病，治愈率高")
    assert "根治" in bad and "治愈率" in bad
