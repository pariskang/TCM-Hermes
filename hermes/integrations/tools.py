"""Provider-agnostic Hermes capability tools.

Pure functions: JSON-serialisable args in, dict out, no MCP/agent dependency —
so they're unit-testable and reusable by any harness (MCP server, HTTP shim,
a coding agent calling them over a thin bridge, etc.).  Each tool is described
declaratively in HERMES_TOOLS (name / description / JSON schema) so an MCP
server or function-calling client can register them mechanically.
"""

from __future__ import annotations

from typing import Any, Callable

from ..config import HermesConfig


def _cfg(config: HermesConfig | None) -> HermesConfig:
    return config or HermesConfig()


# ---------------------------------------------------------------------------
# capability functions
# ---------------------------------------------------------------------------

def search_classics(query: str, subcategory: str | None = None,
                    book: str | None = None, original_only: bool = False,
                    limit: int = 8, config: HermesConfig | None = None) -> dict:
    """Classical text RAG — exact/semantic search with evidence chain."""
    from ..rag.text_rag import ClassicalTextRAGAgent
    rag = ClassicalTextRAGAgent(_cfg(config))
    filters: dict[str, Any] = {}
    if subcategory:
        filters["subcategory"] = subcategory
    if book:
        filters["book"] = book
    if original_only:
        filters["exclude_text_types"] = ["commentary", "preface", "toc"]
    return rag.answer(query, limit=limit, **filters)


def ask_skill(query: str, config: HermesConfig | None = None) -> dict:
    """Skill RAG — answer from compiled Hermes Skills (formula + disease)."""
    from ..rag.skill_rag import SkillRAGAgent
    return SkillRAGAgent(_cfg(config)).ask(query)


def formula_lineage(formula: str, brief: bool = True,
                    config: HermesConfig | None = None) -> dict:
    """Trace a formula across the corpus (earliest source, timeline, variants)."""
    from ..lineage.formula_lineage import FormulaLineageAgent
    report = FormulaLineageAgent(_cfg(config)).trace(formula)
    if brief:
        report["timeline"] = [{k: t[k] for k in ("book_title", "dynasty", "mentions")}
                              for t in report["timeline"]]
    return report


def match_prescription(herbs: list[str] | str, top: int = 8,
                       config: HermesConfig | None = None) -> dict:
    """Match an herb list to classical formulas (Jaccard + containment)."""
    from ..lineage.prescription import PrescriptionMatcherAgent
    if isinstance(herbs, str):
        herbs = [h.strip() for h in herbs.replace("，", ",").split(",") if h.strip()]
    return PrescriptionMatcherAgent(_cfg(config)).match(herbs, top=top)


def disease_run(disease: str, use_corpus: bool = False, use_sample: bool = True,
                include_bronze: bool = False, compile_skills: bool = False,
                limit: int | None = None, config: HermesConfig | None = None) -> dict:
    """Run the TCM-Disease-Hermes multi-agent pipeline for a disease."""
    cfg = _cfg(config)
    from ..disease.pipeline import DiseaseHermesPipeline
    backend = None
    if cfg.backend != "heuristic":
        from ..agents.backends import get_backend
        backend = get_backend(cfg)
    summary = DiseaseHermesPipeline(cfg, backend=backend,
                                    include_bronze=include_bronze).run(
        disease, use_corpus=use_corpus, use_sample=use_sample, limit=limit)
    if compile_skills:
        from ..disease.skills import DiseaseSkillBuilder
        summary["disease_skills"] = DiseaseSkillBuilder(
            cfg, include_bronze=include_bronze).run(disease)
    return summary


def disease_candidates(disease: str, level: str | None = None, limit: int = 20,
                       config: HermesConfig | None = None) -> dict:
    """Read a disease's candidate records (optionally filtered by release level)."""
    cfg = _cfg(config)
    from ..disease.profiles import get_profile
    from ..utils import read_jsonl
    profile = get_profile(disease)
    path = cfg.data_dir / "disease" / profile.disease_id / "candidates.jsonl"
    if not path.exists():
        return {"disease": profile.disease_id, "candidates": [],
                "message": "no candidates; run disease_run first"}
    out = []
    for c in read_jsonl(path):
        if level and c["review"]["release_level"] != level:
            continue
        out.append({"entry_id": c["entry_id"], "book": c["source"]["book"],
                    "chapter": c["source"].get("chapter", ""),
                    "release_level": c["review"]["release_level"],
                    "consensus_score": c["review"]["consensus_score"],
                    "candidate_modern_type":
                        c["phenotype_evidence"]["candidate_modern_type"],
                    "evidence": c["phenotype_evidence"]["supporting_features"],
                    "raw_text": c["raw_text"]})
        if len(out) >= limit:
            break
    return {"disease": profile.disease_id, "count": len(out), "candidates": out,
            "caveat": "古今映射为候选/表型对应，非诊断。"}


def disease_viz(disease: str, min_edge_count: int = 1, top_n: int = 25,
                size_metric: str = "pagerank", theme: str = "light",
                config: HermesConfig | None = None) -> dict:
    """Export an interactive ECharts HTML dashboard for a disease workspace."""
    from ..viz import VisualizationExporter, VizParams
    params = VizParams(min_edge_count=min_edge_count, top_n=top_n,
                       size_metric=size_metric, theme=theme)
    return VisualizationExporter(_cfg(config)).export(disease, params)


def list_diseases(config: HermesConfig | None = None) -> dict:
    """List available disease profiles."""
    from ..disease.profiles import DISEASE_PROFILES
    seen = {}
    for p in DISEASE_PROFILES.values():
        seen[p.disease_id] = {"disease_id": p.disease_id,
                              "display_name": p.display_name,
                              "modern_subtypes": p.modern_subtypes,
                              "core_terms": p.core_terms[:8]}
    return {"diseases": list(seen.values())}


# ---------------------------------------------------------------------------
# declarative registry (name → handler + JSON schema)
# ---------------------------------------------------------------------------

HERMES_TOOLS: list[dict] = [
    {"name": "hermes_search_classics",
     "handler": search_classics,
     "description": "搜索伤寒/金匮等古籍原文（精确+语义），返回带书名/章节/条文的证据链。"
                    "Search classical TCM source texts; returns an evidence chain.",
     "schema": {"type": "object", "properties": {
         "query": {"type": "string"},
         "subcategory": {"type": "string", "enum": ["傷寒", "金匱", "綜合", "醫案"]},
         "book": {"type": "string"},
         "original_only": {"type": "boolean"},
         "limit": {"type": "integer"}}, "required": ["query"]}},
    {"name": "hermes_ask_skill",
     "handler": ask_skill,
     "description": "用已编译的 Hermes Skills（方剂/疾病）回答问题，含发布级别、一致性分、"
                    "支持规则、原文证据与安全声明。",
     "schema": {"type": "object", "properties": {"query": {"type": "string"}},
                "required": ["query"]}},
    {"name": "hermes_formula_lineage",
     "handler": formula_lineage,
     "description": "方药溯源：某方剂的最早出处、历代时间线、加减方与证据。",
     "schema": {"type": "object", "properties": {
         "formula": {"type": "string"}, "brief": {"type": "boolean"}},
         "required": ["formula"]}},
    {"name": "hermes_match_prescription",
     "handler": match_prescription,
     "description": "处方（药物列表）→ 经典方匹配（相似度/共有药/加减方），附书名证据。",
     "schema": {"type": "object", "properties": {
         "herbs": {"type": "array", "items": {"type": "string"}},
         "top": {"type": "integer"}}, "required": ["herbs"]}},
    {"name": "hermes_list_diseases",
     "handler": list_diseases,
     "description": "列出可用的疾病 Profile（银屑病/骨质疏松/类风湿…）。",
     "schema": {"type": "object", "properties": {}}},
    {"name": "hermes_disease_run",
     "handler": disease_run,
     "description": "运行 TCM-Disease-Hermes 多智能体疾病发现流程，可选编译 Disease-Skills。",
     "schema": {"type": "object", "properties": {
         "disease": {"type": "string"},
         "use_corpus": {"type": "boolean"},
         "use_sample": {"type": "boolean"},
         "include_bronze": {"type": "boolean"},
         "compile_skills": {"type": "boolean"},
         "limit": {"type": "integer"}}, "required": ["disease"]}},
    {"name": "hermes_disease_candidates",
     "handler": disease_candidates,
     "description": "读取某疾病的候选条文（可按 gold/silver/bronze/rejected 过滤）。",
     "schema": {"type": "object", "properties": {
         "disease": {"type": "string"},
         "level": {"type": "string",
                   "enum": ["gold", "silver", "bronze", "rejected"]},
         "limit": {"type": "integer"}}, "required": ["disease"]}},
    {"name": "hermes_disease_viz",
     "handler": disease_viz,
     "description": "导出疾病知识的交互式 ECharts HTML 仪表盘（网络/桑基/热力/柱状/"
                    "时序，含 DIY 参数面板）。",
     "schema": {"type": "object", "properties": {
         "disease": {"type": "string"},
         "min_edge_count": {"type": "integer"},
         "top_n": {"type": "integer"},
         "size_metric": {"type": "string",
                         "enum": ["pagerank", "degree", "betweenness", "eigenvector"]},
         "theme": {"type": "string", "enum": ["light", "dark"]}},
         "required": ["disease"]}},
]

_HANDLERS: dict[str, Callable] = {t["name"]: t["handler"] for t in HERMES_TOOLS}


def run_tool(name: str, arguments: dict | None = None,
             config: HermesConfig | None = None) -> dict:
    """Dispatch a tool by name with keyword arguments (config injected)."""
    if name not in _HANDLERS:
        raise KeyError(f"unknown tool: {name}; available: {sorted(_HANDLERS)}")
    return _HANDLERS[name](**(arguments or {}), config=config)
