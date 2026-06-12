"""TCM-Disease-Hermes multi-agent pipeline (psoriasis worked example)."""

import conftest as fx
import pytest

from hermes.disease.pipeline import DiseaseHermesPipeline
from hermes.disease.profiles import PSORIASIS, get_profile
from hermes.disease.retrieval import ExclusionDifferentialAgent
from hermes.schemas import SourceUnit
from hermes.utils import read_jsonl, write_jsonl


def test_profile_normalized_to_traditional():
    p = get_profile("银屑病")
    assert p is PSORIASIS
    assert "白疕" in p.core_terms
    assert "乾癬" in p.core_terms          # 干癣 → 乾癬
    assert "牛皮癬" in p.core_terms          # 牛皮癣 → 牛皮癬
    assert "金錢癬" in p.exclusion_terms     # 金钱癣 → 金錢癬


def test_exclusion_headword_is_hard():
    scr = ExclusionDifferentialAgent()
    # 圓癬 as subject → hard exclude despite 與白疕不同
    r = scr.screen("圓癬者，狀如錢文，俗名金錢癬，與白疕不同。", PSORIASIS)
    assert r["exclude_flag"]
    # exclusion only mentioned as contrast, target is subject → soft
    r2 = scr.screen("白疕，色白而癢，非金錢癬之比也。", PSORIASIS)
    assert not r2["exclude_flag"]
    assert r2["soft_exclude"]


def test_pipeline_on_sample(cfg):
    pipe = DiseaseHermesPipeline(cfg)
    summary = pipe.run("psoriasis", use_corpus=False, use_sample=True)
    assert summary["candidates"] == 10
    ws = cfg.data_dir / "disease" / "psoriasis"
    cands = {(_book(d), d["review"]["release_level"]): d
             for d in read_jsonl(ws / "candidates.jsonl")}
    # the canonical 乾癬候 description is the strongest vulgaris match → silver+
    qian = next(d for d in read_jsonl(ws / "candidates.jsonl")
                if "乾癬" in d["source"]["chapter"])
    assert qian["review"]["release_level"] in ("silver", "gold")
    assert qian["phenotype_evidence"]["candidate_modern_type"] == "vulgaris"
    # every supporting feature is a raw_text substring (evidence回源)
    for span in qian["phenotype_evidence"]["supporting_features"]:
        assert span in qian["raw_text"]
    # the 圓癬/金錢癬 differential definition is rejected
    yuan = next(d for d in read_jsonl(ws / "candidates.jsonl")
                if "圓癬" in d["source"]["chapter"])
    assert yuan["review"]["release_level"] == "rejected"


def test_pipeline_outputs_exist(cfg):
    DiseaseHermesPipeline(cfg).run("psoriasis")
    ws = cfg.data_dir / "disease" / "psoriasis"
    for f in ("plan.json", "ancient_names.json", "candidates.jsonl",
              "relations.jsonl", "network.json", "network.dot",
              "temporal.json", "summary.json", "report.md"):
        assert (ws / f).exists(), f
    report = (ws / "report.md").read_text(encoding="utf-8")
    assert "银屑病" in report
    assert "T1 核心古病名" in report
    assert "非诊断" in report                  # safety framing present


def test_ontology_and_relations(cfg):
    DiseaseHermesPipeline(cfg).run("psoriasis")
    ws = cfg.data_dir / "disease" / "psoriasis"
    qian = next(d for d in read_jsonl(ws / "candidates.jsonl")
                if "乾癬" in d["source"]["chapter"])
    ont = qian["ontology"]
    assert "乾癬" in ont["ancient_disease_name"]
    assert ont["pathogenesis"]                # 風濕/寒濕/血氣相搏
    assert any(tr[1] == "has_symptom" for tr in qian["extracted_relations"])
    assert any(tr[1] == "maps_to_candidate" for tr in qian["extracted_relations"])


def _book(d):
    return d["source"]["book"]


# --- herb network on synthetic, clearly-constructed fixtures ---------------

def _herb_units():
    """Constructed test units (synthetic, not historical quotes) carrying
    explicit herb lists so the co-occurrence network can be exercised."""
    texts = [
        "白疕血燥風盛，治以養血潤燥祛風，方用當歸、生地黃、防風、白芷、苦參。",
        "白疕日久血燥，宜養血祛風，當歸、生地黃、荊芥、防風、白鮮皮。",
        "牛皮癬頑厚，風濕生蟲，外用苦參、蛇床子、白鮮皮、地膚子殺蟲止癢。",
        "白疕風熱血燥，當歸、防風、白芷、苦參、蝉蜕，養血祛風止癢。",
    ]
    units = []
    from hermes.knowledge.entities import EntityExtractorAgent
    ent = EntityExtractorAgent()
    for i, t in enumerate(texts, 1):
        units.append(SourceUnit(
            source_unit_id=f"SU_PSOTEST_{i:04d}",
            category_path=["傷寒金匱類", "外科"],
            book_id="BOOK_PSOTEST", book_title="测试外科方书",
            book_type="original", chapter_id=f"CH_{i}", chapter_title="白疕",
            seq=0, raw_text=t, text_type="original",
            entities=ent.extract(t),
            meta={"dynasty": "清", "sample": True}))
    return units


def test_herb_network(cfg, monkeypatch):
    # write synthetic herb-bearing units as the corpus source units
    write_jsonl(cfg.source_units_dir / "BOOK_PSOTEST.jsonl",
                [u.to_dict() for u in _herb_units()])
    pipe = DiseaseHermesPipeline(cfg, include_bronze=True)
    summary = pipe.run("psoriasis", use_corpus=True, use_sample=False)
    assert summary["network_nodes"] > 0
    assert summary["network_edges"] > 0
    ws = cfg.data_dir / "disease" / "psoriasis"
    import json
    net = json.loads((ws / "network.json").read_text(encoding="utf-8"))
    core = net["core_herbs"]
    assert core
    # centralities present and well-formed
    top = core[0]
    for k in ("degree", "betweenness", "eigenvector", "pagerank"):
        assert k in top and 0.0 <= top[k] <= 1.0 + 1e-6
    # 當歸/防風 recur across formulas → should be central
    names = {c["herb"] for c in core[:6]}
    assert names & {"當歸", "防風", "苦參"}


def test_temporal_evolution(cfg):
    write_jsonl(cfg.source_units_dir / "BOOK_PSOTEST.jsonl",
                [u.to_dict() for u in _herb_units()])
    DiseaseHermesPipeline(cfg, include_bronze=True).run(
        "psoriasis", use_corpus=True, use_sample=False)
    import json
    ws = cfg.data_dir / "disease" / "psoriasis"
    temporal = json.loads((ws / "temporal.json").read_text(encoding="utf-8"))
    assert "清" in temporal["dynasty_trends"]


def test_resume(cfg):
    pipe = DiseaseHermesPipeline(cfg)
    s1 = pipe.run("psoriasis")
    s2 = pipe.run("psoriasis", resume=True)
    assert s1["candidates"] == s2["candidates"]
    assert s1["by_level"] == s2["by_level"]
