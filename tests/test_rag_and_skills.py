"""Classical text RAG + skill compilation/RAG round trip."""

import conftest as fx

from hermes.agents.merger import RuleMergerAgent
from hermes.agents.orchestrator import AutonomousReviewOrchestrator
from hermes.agents.skills import SkillBuilderAgent
from hermes.rag.skill_rag import SkillRAGAgent
from hermes.rag.text_rag import ClassicalTextRAGAgent
from hermes.utils import write_jsonl


def _build_corpus(cfg):
    orch = AutonomousReviewOrchestrator(cfg)
    u1 = fx.make_unit(fx.GUIZHI_CLAUSE)
    u2 = fx.make_unit("太陽病，頭痛發熱，汗出惡風者，桂枝湯主之。",
                      su_id="SU_TEST_000002", seq=1)
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl",
                [u1.to_dict(), u2.to_dict()])
    u3 = fx.make_unit("太陽中風，脈浮緊，發熱惡寒，身疼痛，不汗出而煩躁者，大青龍湯主之。",
                      su_id="SU_TES2_000001")
    u3.book_id, u3.book_title = "BOOK_TES2", "傷寒論(條文版)"
    u4 = fx.make_unit("傷寒脈浮緩，身不疼但重，乍有輕時，無少陰證者，大青龍湯發之。"
                      "頭痛發熱，汗出惡風者，桂枝湯主之。",
                      su_id="SU_TES2_000002", seq=1)
    u4.book_id, u4.book_title = "BOOK_TES2", "傷寒論(條文版)"
    write_jsonl(cfg.source_units_dir / "BOOK_TES2.jsonl",
                [u3.to_dict(), u4.to_dict()])
    orch.process_book("BOOK_TEST")
    orch.process_book("BOOK_TES2")
    return orch


def test_exact_search(cfg):
    _build_corpus(cfg)
    rag = ClassicalTextRAGAgent(cfg)
    hits = rag.search_exact("陽浮而陰弱")
    assert hits and "陽浮而陰弱" in hits[0].source_unit.raw_text
    none = rag.search_exact("此句絕不存在")
    assert none == []


def test_semantic_search_symptom_cluster(cfg):
    _build_corpus(cfg)
    rag = ClassicalTextRAGAgent(cfg)
    hits = rag.search_semantic("怕冷 發熱 惡寒 身疼痛 煩躁 無汗")
    assert hits
    assert any("大青龍湯" in h.source_unit.raw_text for h in hits[:2])


def test_filters(cfg):
    _build_corpus(cfg)
    rag = ClassicalTextRAGAgent(cfg)
    hits = rag.search_exact("桂枝湯", book="BOOK_TES2")
    assert hits and all(h.source_unit.book_id == "BOOK_TES2" for h in hits)


def test_answer_carries_evidence_chain(cfg):
    _build_corpus(cfg)
    ans = ClassicalTextRAGAgent(cfg).answer("桂枝湯")
    assert ans["evidence_chain"]
    for e in ans["evidence_chain"]:
        assert e["book_title"] and e["source_unit_id"] and e["quote"]


def test_skill_compile_and_ask(cfg):
    _build_corpus(cfg)
    RuleMergerAgent(cfg).run()
    out = SkillBuilderAgent(cfg).run()
    assert out["skills"] >= 1

    ans = SkillRAGAgent(cfg).ask("汗出惡風，桂枝湯可用否？")
    assert ans["selected_skill"] and ans["selected_skill"].startswith("hermes.")
    # the mandated answer surface
    for key in ("merged_rule", "release_level", "consensus_score",
                "supporting_initial_rules", "original_evidence",
                "variant_set", "conflict_set", "safety_notice"):
        assert key in ans, key
    assert ans["release_level"] in ("silver", "gold")
    assert ans["original_evidence"][0]["evidence_span"]


def test_bronze_only_groups_make_no_skill(cfg):
    """Merged rules built solely from bronze rules must not compile."""
    orch = AutonomousReviewOrchestrator(cfg)
    # single weak advisory clause → bronze-grade rule, and only one book
    u = fx.make_unit("與小柴胡湯。")
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl", [u.to_dict()])
    orch.process_book("BOOK_TEST")
    RuleMergerAgent(cfg).run()
    out = SkillBuilderAgent(cfg).run()
    assert out["skills"] == 0
