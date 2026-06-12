"""Isolated 外科/溫病 disease corpus builder + running diseases on it."""

from pathlib import Path

import pytest

from hermes.disease.corpus import DiseaseCorpusBuilder
from hermes.disease.pipeline import DiseaseHermesPipeline


def _make_tree(root: Path):
    """A tiny extracted-tree fixture: book_name/index.txt with <book> blocks."""
    books = {
        "外科正宗": ("外科", "明", "陳實功",
                   "白疕風熱血燥，搔起白皮，色白而癢，宜養血潤燥祛風，"
                   "當歸、生地黃、防風、白芷、苦參。"),
        "外科證治全書": ("外科", "清", "許克昌",
                     "浸淫瘡，遍身起疹，搔癢流水，浸淫成片，由濕熱內蘊外受風邪，"
                     "宜清熱利濕祛風，苦參、白鮮皮、地膚子、黃柏。"),
    }
    for name, (cat, dyn, author, body) in books.items():
        d = root / name
        d.mkdir(parents=True)
        (d / "index.txt").write_text(
            f"======{name}======\n\n<book>\n書名={name}\n作者={author}\n"
            f"朝代={dyn}\n分類={cat}\n</book>\n\n=====正文=====\n\n{body}\n",
            encoding="utf-8")
    return root


def test_build_from_tree_isolated(cfg, tmp_path):
    tree = _make_tree(tmp_path / "src")
    out = DiseaseCorpusBuilder(cfg).build_from_tree(
        tree, "外科", books=["外科正宗", "外科證治全書"])
    assert out["book_count"] == 2
    assert out["source_units"] >= 2
    # isolated under data/disease_corpus/外科 — base 伤寒金匮 corpus untouched
    units_dir = Path(out["source_units_dir"])
    assert "disease_corpus" in str(units_dir) and units_dir.exists()
    assert not (cfg.source_units_dir).exists() or \
        not list(cfg.source_units_dir.glob("BOOK_*.jsonl"))


def test_run_disease_on_built_corpus(cfg, tmp_path):
    tree = _make_tree(tmp_path / "src")
    builder = DiseaseCorpusBuilder(cfg)
    builder.build_from_tree(tree, "外科")
    units_dir = builder.source_units_dir("外科")

    summary = DiseaseHermesPipeline(cfg, include_bronze=True).run(
        "银屑病", use_sample=False, units_dir=units_dir)
    # 白疕 passage with 当归/生地/防风/苦参 → candidate + herb ontology
    assert summary["candidates"] >= 1
    ws = cfg.data_dir / "disease" / "psoriasis"
    from hermes.utils import read_jsonl
    cands = list(read_jsonl(ws / "candidates.jsonl"))
    assert any("白疕" in c["raw_text"] for c in cands)
    # dynasty carried through from the <book> block via segmenter meta
    assert any(c["source"]["dynasty"] in ("明", "清") for c in cands)


def test_eczema_on_built_corpus(cfg, tmp_path):
    tree = _make_tree(tmp_path / "src")
    builder = DiseaseCorpusBuilder(cfg)
    builder.build_from_tree(tree, "外科")
    summary = DiseaseHermesPipeline(cfg, include_bronze=True).run(
        "湿疹", use_sample=False, units_dir=builder.source_units_dir("外科"))
    ws = cfg.data_dir / "disease" / "eczema"
    from hermes.utils import read_jsonl
    cands = list(read_jsonl(ws / "candidates.jsonl"))
    assert any("浸淫瘡" in c["raw_text"] for c in cands)


def test_category_path_generalizes():
    from hermes.protocol import category_path
    assert category_path("傷寒")[0] == "傷寒金匱類"
    assert category_path("外科") == ["典籍", "外科"]      # non-伤寒金匮 → 典籍
    assert category_path("溫病") == ["典籍", "溫病"]
