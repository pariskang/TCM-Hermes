"""LiteLLM backend, multi-reviewer panel, span↔claim binding, panel consensus.

litellm itself is not importable in this sandbox, so the backend is exercised
through an injected fake `litellm` module — this verifies role→model
resolution, json mode, retry and parsing without any network call.
"""

import sys
import types

import conftest as fx
import pytest

from hermes.agents.backends import (LiteLLMBackend, HeuristicBackend,
                                    get_backend, BackendError)
from hermes.agents.binding import check_binding
from hermes.agents.consensus import ConsensusJudgeAgent
from hermes.agents.critic import AdversarialCriticAgent
from hermes.agents.evidence import EvidenceVerifierAgent
from hermes.agents.extractor import InitialRuleExtractorAgent
from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.agents.reviewer import RuleReviewerAgent
from hermes.agents.reviewer_profiles import ReviewerPanel, PROFILES


# --- fake litellm ----------------------------------------------------------

class _FakeLiteLLM(types.ModuleType):
    drop_params = False
    suppress_debug_info = False

    def __init__(self):
        super().__init__("litellm")
        self.calls = []

    def completion(self, **kwargs):
        self.calls.append(kwargs)
        sys_prompt = kwargs["messages"][0]["content"]
        # echo a verdict shaped by the prompt so the panel sees variety
        if "保守" in sys_prompt:
            content = '{"verdict":"warn","confidence":0.6,"issues":[],"notes":"x"}'
        elif "对抗" in sys_prompt:
            content = '{"verdict":"support","confidence":0.7}'
        else:
            content = '```json\n{"verdict":"support","confidence":0.85}\n```'
        return {"choices": [{"message": {"content": content}}]}


@pytest.fixture()
def fake_litellm(monkeypatch):
    fake = _FakeLiteLLM()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    return fake


def test_get_backend_default_is_heuristic(cfg):
    assert isinstance(get_backend(cfg), HeuristicBackend)


def test_litellm_backend_role_models(fake_litellm, cfg, monkeypatch):
    monkeypatch.setenv("HERMES_LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("HERMES_LLM_MODEL_CRITIC", "claude-sonnet-4-6")
    b = LiteLLMBackend(cfg)
    assert b.model_for("critic") == "claude-sonnet-4-6"
    assert b.model_for("reviewer") == "gpt-4o-mini"
    out = b.complete_json("system", "user", role="reviewer")
    assert out["verdict"] == "support"
    # json mode requested + model routed
    assert fake_litellm.calls[-1]["response_format"] == {"type": "json_object"}
    assert fake_litellm.calls[-1]["model"] == "gpt-4o-mini"


def test_litellm_backend_missing_dependency(monkeypatch, cfg):
    monkeypatch.setitem(sys.modules, "litellm", None)  # force import failure
    with pytest.raises(BackendError):
        LiteLLMBackend(cfg)


def test_litellm_text_completion(fake_litellm, cfg):
    b = LiteLLMBackend(cfg)
    assert isinstance(b.complete_text("s", "u", role="writer"), str)
    assert fake_litellm.calls[-1].get("response_format") is None


# --- binding (Problem 2) ---------------------------------------------------

def test_binding_flags_multi_formula(cfg):
    unit = fx.make_unit(
        "太陽病，頭痛發熱，桂枝湯主之。若脈浮緊無汗者，麻黃湯主之。")
    orch = AutonomousReviewOrchestrator(cfg)
    rules = orch.extractor.extract(unit)
    by_formula = {r.then_conclusions["formula"][0]: check_binding(r)
                  for r in rules if r.then_conclusions.get("formula")}
    # 桂枝湯 anchored with its own conditions → tight; 麻黃湯 borrows the
    # first clause's conditions → multi-formula, looser binding
    assert by_formula["麻黃湯"].multi_formula
    assert by_formula["麻黃湯"].binding_score < by_formula["桂枝湯"].binding_score
    assert by_formula["麻黃湯"].weakly_bound_terms


def test_binding_single_clause_is_tight(cfg, guizhi_unit):
    orch = AutonomousReviewOrchestrator(cfg)
    r = [x for x in orch.extractor.extract(guizhi_unit)
         if x.rule_type == "formula_indication_rule"][0]
    b = check_binding(r)
    assert b.binding_score >= 0.7
    assert not b.multi_formula


# --- panel (Problems 1 & 3) ------------------------------------------------

class _MockLLM:
    kind = "litellm"

    def __init__(self, verdicts):
        self._v = verdicts

    def model_for(self, role):
        return f"mock/{role}"

    def complete_json(self, system, user, role=""):
        for key, val in self._v.items():
            if key in system:
                return val
        return {"verdict": "support", "confidence": 0.8}


def test_panel_multi_model_vote(cfg, guizhi_unit):
    orch = AutonomousReviewOrchestrator(cfg)
    rule = [x for x in orch.extractor.extract(guizhi_unit)
            if x.rule_type == "formula_indication_rule"][0]
    backend = _MockLLM({"保守": {"verdict": "warn", "confidence": 0.6},
                        "对抗": {"verdict": "support", "confidence": 0.7}})
    panel = ReviewerPanel(cfg, backend)
    res = panel.review(rule, guizhi_unit)
    assert len(res.verdicts) == len(PROFILES)
    assert res.support >= 1 and res.warn >= 1
    # each verdict records which model produced it (real multi-model vote)
    assert all(v.model.startswith("mock/") for v in res.verdicts)
    assert res.majority in ("support", "warn", "reject")


def test_panel_reject_majority_blocks_release(cfg, guizhi_unit):
    orch = AutonomousReviewOrchestrator(cfg)
    rule = [x for x in orch.extractor.extract(guizhi_unit)
            if x.rule_type == "formula_indication_rule"][0]
    backend = _MockLLM({"": {"verdict": "reject", "confidence": 0.9}})
    panel = ReviewerPanel(cfg, backend).review(rule, guizhi_unit)
    judge = ConsensusJudgeAgent(cfg)
    evidence = EvidenceVerifierAgent().verify(rule, guizhi_unit)
    semantic = RuleReviewerAgent(cfg).review(rule, guizhi_unit)
    critic = AdversarialCriticAgent(cfg).critique(rule, guizhi_unit)
    j = judge.judge(rule, evidence, semantic, critic, 0, False,
                    binding=check_binding(rule), panel=panel)
    assert j.autonomous_review_status == "model_rejected"


def test_panel_mode_orchestrator(cfg, guizhi_unit):
    cfg.consensus_mode = "panel"
    backend = _MockLLM({"保守": {"verdict": "support", "confidence": 0.9}})
    orch = AutonomousReviewOrchestrator(cfg, backend=backend)
    assert orch.use_panel
    rule = [x for x in orch.extractor.extract(guizhi_unit)
            if x.rule_type == "formula_indication_rule"][0]
    orch.review_rule(rule, guizhi_unit)
    # panel debate is recorded in the audit trail and review records
    assert "panel" in rule.review_records
    assert any(e.agent == "ReviewerPanel" for e in rule.audit_trail)
    assert rule.review_records["binding"]["binding_score"] >= 0
