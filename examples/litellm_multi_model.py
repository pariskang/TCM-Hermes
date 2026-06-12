#!/usr/bin/env python3
"""Example: drive Hermes with a multi-model litellm backend.

Each agent role is bound to a different model, so the five-layer review's
reviewer panel and consensus become a genuine multi-model vote rather than one
model judging itself.  Requires `pip install litellm` and the relevant provider
API keys (OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY / …).

Run:
    export OPENAI_API_KEY=...   ANTHROPIC_API_KEY=...   GEMINI_API_KEY=...
    python3 examples/litellm_multi_model.py
"""

from __future__ import annotations

from hermes.config import HermesConfig
from hermes.agents.backends import LiteLLMBackend
from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.schemas import SourceUnit
from hermes.knowledge.entities import EntityExtractorAgent


def main() -> None:
    cfg = HermesConfig(root=".", backend="litellm", consensus_mode="panel")

    # different model per agent role → real multi-model debate
    backend = LiteLLMBackend(cfg, role_models={
        "extractor": "gpt-4o",
        "reviewer": "claude-sonnet-4-6",
        "critic": "claude-opus-4-8",
        "judge": "gemini/gemini-1.5-pro",
        "repair": "gpt-4o-mini",
    })

    orch = AutonomousReviewOrchestrator(cfg, backend=backend)

    ent = EntityExtractorAgent()
    raw = ("太陽中風，陽浮而陰弱，陽浮者，熱自發，陰弱者，汗自出。"
           "嗇嗇惡寒，淅淅惡風，翕翕發熱，鼻鳴乾嘔者，桂枝湯主之。")
    unit = SourceUnit(
        source_unit_id="SU_DEMO_0001",
        category_path=["傷寒金匱類", "傷寒"],
        book_id="BOOK_SHL_SONGBEN", book_title="傷寒論(宋本)",
        book_type="original", chapter_id="CH_DEMO", chapter_title="辨太陽病脈證並治上",
        seq=0, raw_text=raw, text_type="original", entities=ent.extract(raw))

    for rule in orch.extractor.extract(unit):
        orch.review_rule(rule, unit)
        ar = rule.autonomous_review
        print(f"\n{rule.rule_type} → {rule.then_conclusions.get('formula')}")
        print(f"  release_level   : {ar.release_level}")
        print(f"  consensus_score : {ar.consensus_score}")
        print(f"  binding_score   : {ar.binding_score}")
        panel = rule.review_records.get("panel")
        if panel:
            print(f"  panel           : {panel['support']}支持/"
                  f"{panel['warn']}存疑/{panel['reject']}否决"
                  f"（一致度 {panel['agreement']:.0%}）")
            for v in panel["verdicts"]:
                print(f"     - {v['stance']:<8} [{v['model']}] "
                      f"{v['verdict']} ({v['confidence']})")


if __name__ == "__main__":
    main()
