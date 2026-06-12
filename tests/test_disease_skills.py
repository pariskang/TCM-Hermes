"""New disease profiles (osteoporosis / RA), Disease-Skill compilation, and
integration of disease skills into the existing Skill RAG surface."""

import conftest as fx
import pytest

from hermes.disease.pipeline import DiseaseHermesPipeline
from hermes.disease.profiles import (DISEASE_PROFILES, OSTEOPOROSIS,
                                     RHEUMATOID, get_profile)
from hermes.disease.skills import DiseaseSkillBuilder
from hermes.rag.skill_rag import SkillRAGAgent
from hermes.schemas import SourceUnit
from hermes.utils import write_jsonl


# --- profiles migrate with zero agent-code change -------------------------

def test_new_profiles_registered():
    assert get_profile("骨质疏松") is OSTEOPOROSIS
    assert get_profile("骨痿") is OSTEOPOROSIS
    assert get_profile("类风湿") is RHEUMATOID
    assert get_profile("历节") is RHEUMATOID
    # terms normalized to traditional (corpus script)
    assert "骨痿" in OSTEOPOROSIS.core_terms
    assert "歷節" in RHEUMATOID.core_terms          # 历节 → 歷節
    assert "腰脊不舉" in OSTEOPOROSIS.morphology_terms  # 腰脊不举 → 腰脊不舉
    assert "鶴膝風" in RHEUMATOID.core_terms          # 鹤膝风 → 鶴膝風


def test_osteoporosis_pipeline_on_sample(cfg):
    summary = DiseaseHermesPipeline(cfg).run("骨质疏松")
    assert summary["candidates"] >= 5
    # 内经骨痿 / 脈要精微论 are strong → at least one silver
    assert summary["by_level"].get("silver", 0) >= 1


def test_rheumatoid_uses_real_corpus(cfg):
    """RA genuinely maps onto 金匮 中风历节病 — feed real corpus units."""
    # synthetic stand-ins for 金匮 历节 formula lines (clearly constructed)
    units = []
    from hermes.knowledge.entities import EntityExtractorAgent
    ent = EntityExtractorAgent()
    texts = [
        ("諸肢節疼痛，身體尪羸，腳腫如脫，頭眩短氣，溫溫欲吐，桂枝芍藥知母湯主之。"
         "桂枝、芍藥、甘草、麻黃、生薑、白朮、知母、防風、附子。"),
        "病歷節不可屈伸，疼痛，烏頭湯主之。烏頭、麻黃、芍藥、黃耆、甘草。",
        "歷節風，肢節腫痛，屈伸不利，風寒濕痹，宜祛風散寒除濕通絡。",
    ]
    for i, t in enumerate(texts, 1):
        units.append(SourceUnit(
            source_unit_id=f"SU_RA_{i:04d}", category_path=["傷寒金匱類", "金匱"],
            book_id="BOOK_JGYL_FANGLUN", book_title="金匱要略方論",
            book_type="original", chapter_id="CH_LIJIE", chapter_title="中風歷節病脈證並治",
            seq=0, raw_text=t, text_type="formula", entities=ent.extract(t),
            meta={"dynasty": "漢"}))
    write_jsonl(cfg.source_units_dir / "BOOK_JGYL_FANGLUN.jsonl",
                [u.to_dict() for u in units])
    summary = DiseaseHermesPipeline(cfg, include_bronze=True).run(
        "类风湿", use_corpus=True, use_sample=False)
    assert summary["candidates"] >= 3
    # the canonical formula lines yield real herb co-occurrence
    assert summary["network_nodes"] > 0
    assert {"桂枝", "芍藥", "甘草"} & set(summary["core_herbs"])


# --- Disease-Skill compilation + Skill RAG integration --------------------

def test_disease_skill_compilation_and_rag(cfg):
    DiseaseHermesPipeline(cfg, include_bronze=True).run("银屑病")
    out = DiseaseSkillBuilder(cfg, include_bronze=True).run("银屑病")
    assert out["skills_compiled"] >= 1
    assert any(sid.startswith("hermes.disease.psoriasis") for sid in out["skill_ids"])

    # per-skill JSON written + disease index created
    idx = (cfg.skills_dir / "disease_skill_index.json")
    assert idx.exists()

    # queryable through the SAME Skill RAG surface, with the mandated fields
    rag = SkillRAGAgent(cfg)
    ans = rag.ask("白疕 鳞屑 脱屑 血燥")
    assert ans["selected_skill"].startswith("hermes.disease.psoriasis")
    assert ans["skill_kind"] == "disease"
    for key in ("release_level", "consensus_score", "supporting_initial_rules",
                "original_evidence", "variant_set", "conflict_set",
                "safety_notice", "ancient_disease_names", "mapping_caveat"):
        assert key in ans, key
    assert "非诊断" in ans["mapping_caveat"]
    # evidence回源: each evidence span is real text from a candidate
    assert ans["original_evidence"][0]["evidence_span"]


def test_disease_skills_do_not_clobber_main_index(cfg):
    """Re-running the main SkillBuilder must not drop disease skills."""
    from hermes.agents.orchestrator import AutonomousReviewOrchestrator
    from hermes.agents.merger import RuleMergerAgent
    from hermes.agents.skills import SkillBuilderAgent
    # build a couple of formula skills from the corpus
    u1 = fx.make_unit(fx.GUIZHI_CLAUSE)
    u2 = fx.make_unit("太陽病，頭痛發熱，汗出惡風者，桂枝湯主之。",
                      su_id="SU_TEST_000002", seq=1)
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl",
                [u1.to_dict(), u2.to_dict()])
    AutonomousReviewOrchestrator(cfg).process_book("BOOK_TEST")
    RuleMergerAgent(cfg).run()
    SkillBuilderAgent(cfg).run()                       # writes skill_index.json

    DiseaseHermesPipeline(cfg, include_bronze=True).run("银屑病")
    DiseaseSkillBuilder(cfg, include_bronze=True).run("银屑病")

    # re-run the main skill builder (rewrites skill_index.json)
    SkillBuilderAgent(cfg).run()

    # both formula and disease skills are visible to the RAG index
    rag = SkillRAGAgent(cfg)
    ids = {e["skill_id"] for e in rag.index()}
    assert any(i.startswith("hermes.disease.psoriasis") for i in ids)
    assert any(i.startswith("hermes.formula.") for i in ids)
