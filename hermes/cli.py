"""Hermes CLI — `python -m hermes <command>` / `hermes <command>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import HermesConfig


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_download(cfg: HermesConfig, args) -> None:
    from .corpus.downloader import DownloaderAgent
    agent = DownloaderAgent(cfg)
    path = agent.download(args.url) if args.url else agent.download()
    print(f"downloaded → {path}")
    if args.extract:
        agent.import_archive(path, categories=args.categories or None)
        print("extracted into", cfg.corpus_raw_dir)


def cmd_import(cfg: HermesConfig, args) -> None:
    from .corpus.downloader import DownloaderAgent
    agent = DownloaderAgent(cfg)
    for src in args.sources:
        p = Path(src)
        if p.is_dir():
            agent.import_tree(p)
        else:
            agent.import_archive(p, categories=args.categories or None)
        print(f"imported {src}")
    _print(agent.corpus_version())


def cmd_catalog(cfg: HermesConfig, args) -> None:
    from .corpus.catalog import CatalogAgent
    _print(CatalogAgent(cfg).build())


def cmd_segment(cfg: HermesConfig, args) -> None:
    from .corpus.segmenter import SegmenterAgent
    _print(SegmenterAgent(cfg).run(books=args.books or None,
                                   categories=args.categories or None))


def cmd_review(cfg: HermesConfig, args) -> None:
    from .agents.orchestrator import AutonomousReviewOrchestrator
    orch = AutonomousReviewOrchestrator(cfg)
    summary = orch.process_corpus(book_ids=args.books or None)
    summary.pop("per_book", None) if args.quiet else None
    _print(summary)


def cmd_themes(cfg: HermesConfig, args) -> None:
    from .agents.theme import ThemeInducerAgent
    _print(ThemeInducerAgent(cfg).run(book_ids=args.books or None))


def cmd_merge(cfg: HermesConfig, args) -> None:
    from .agents.merger import RuleMergerAgent
    _print(RuleMergerAgent(cfg).run(book_ids=args.books or None))


def cmd_skills(cfg: HermesConfig, args) -> None:
    from .agents.skills import SkillBuilderAgent
    _print(SkillBuilderAgent(cfg).run())


def cmd_report(cfg: HermesConfig, args) -> None:
    from .metrics.report import AutonomousReviewReporter
    path = AutonomousReviewReporter(cfg).generate(
        book_ids=args.books or None,
        scope_label=args.scope or "full corpus")
    print(f"report → {path}")


def cmd_metrics(cfg: HermesConfig, args) -> None:
    from .metrics.quality import QualityMetrics
    _print(QualityMetrics(cfg).compute(book_ids=args.books or None))


def cmd_pipeline(cfg: HermesConfig, args) -> None:
    """catalog → segment → review → themes → merge → skills → report."""
    from .corpus.catalog import CatalogAgent
    from .corpus.segmenter import SegmenterAgent
    from .agents.orchestrator import AutonomousReviewOrchestrator
    from .agents.theme import ThemeInducerAgent
    from .agents.merger import RuleMergerAgent
    from .agents.skills import SkillBuilderAgent
    from .metrics.report import AutonomousReviewReporter

    print("[1/7] catalog");  _print(CatalogAgent(cfg).build())
    print("[2/7] segment");  _print(SegmenterAgent(cfg).run(
        books=args.books or None, categories=args.categories or None))
    print("[3/7] autonomous review")
    summary = AutonomousReviewOrchestrator(cfg).process_corpus(
        book_ids=[f"BOOK_{b}" if not b.startswith("BOOK_") else b
                  for b in args.books] if args.books else None)
    summary.pop("per_book", None)
    _print(summary)
    print("[4/7] themes");   _print(ThemeInducerAgent(cfg).run())
    print("[5/7] merge");    _print(RuleMergerAgent(cfg).run())
    print("[6/7] skills");   _print(SkillBuilderAgent(cfg).run())
    print("[7/7] report")
    print("report →", AutonomousReviewReporter(cfg).generate(
        scope_label="pipeline run"))


def cmd_search(cfg: HermesConfig, args) -> None:
    from .rag.text_rag import ClassicalTextRAGAgent
    rag = ClassicalTextRAGAgent(cfg)
    filters = {}
    if args.subcategory:
        filters["subcategory"] = args.subcategory
    if args.book:
        filters["book"] = args.book
    if args.original_only:
        filters["exclude_text_types"] = ["commentary", "preface", "toc"]
    _print(rag.answer(args.query, limit=args.limit, **filters))


def cmd_ask(cfg: HermesConfig, args) -> None:
    from .rag.skill_rag import SkillRAGAgent
    _print(SkillRAGAgent(cfg).ask(args.query))


def cmd_lineage(cfg: HermesConfig, args) -> None:
    from .lineage.formula_lineage import FormulaLineageAgent
    report = FormulaLineageAgent(cfg).trace(args.formula)
    if args.brief:
        report["timeline"] = [
            {k: t[k] for k in ("book_title", "dynasty", "mentions")}
            for t in report["timeline"]]
    _print(report)


def cmd_match(cfg: HermesConfig, args) -> None:
    from .lineage.prescription import PrescriptionMatcherAgent
    herbs = [h.strip() for h in args.herbs.replace("，", ",").split(",") if h.strip()]
    _print(PrescriptionMatcherAgent(cfg).match(herbs))


def cmd_physician(cfg: HermesConfig, args) -> None:
    from .workbench.physician import DoctorAssistantAgent
    doc = DoctorAssistantAgent(cfg)
    if args.action == "match":
        _print(doc.match_pattern(
            symptoms=args.symptoms.split(",") if args.symptoms else None,
            pulse=args.pulse.split(",") if args.pulse else None,
            free_text=args.text or ""))
    elif args.action == "case":
        _print(doc.case_to_classics(args.text or ""))
    elif args.action == "differentiate":
        a, b = (args.formulas or "桂枝湯,麻黃湯").split(",")[:2]
        _print(doc.differentiate(a.strip(), b.strip()))


def cmd_research(cfg: HermesConfig, args) -> None:
    from .workbench.researcher import ResearchWorkbench
    wb = ResearchWorkbench(cfg)
    if args.action == "stats":
        _print(wb.corpus_statistics())
    elif args.action == "network":
        _print(wb.herb_cooccurrence())
        _print(wb.symptom_formula_graph())
    elif args.action == "map":
        _print(wb.disease_term_mapping())
    elif args.action == "mine":
        _print(wb.mine_topic(args.topic or "胸痹"))


def cmd_paper(cfg: HermesConfig, args) -> None:
    from .workbench.paper import PaperWriterAgent
    path = PaperWriterAgent(cfg).draft(args.topic, target=args.target)
    print(f"manuscript → {path}")


def cmd_patient(cfg: HermesConfig, args) -> None:
    from .workbench.patient import PatientEducationAgent
    pt = PatientEducationAgent(cfg)
    if args.action == "explain":
        _print(pt.explain(args.text or ""))
    elif args.action == "visit":
        _print(pt.visit_preparation(args.text or ""))
    elif args.action == "instruction":
        _print(pt.explain_instruction(args.text or ""))


def cmd_status(cfg: HermesConfig, args) -> None:
    from .utils import read_json
    from .memory.store import MemoryStore
    from . import protocol
    status = {
        "protocol": protocol.PROTOCOL_VERSION,
        "principles": protocol.CORE_PRINCIPLES,
        "corpus_version": (read_json(cfg.manifests_dir / "corpus_version.json", {})
                           or {}).get("corpus_version"),
        "books": len(read_json(cfg.manifests_dir / "book_manifest.json", []) or []),
        "source_unit_files": len(list(Path(cfg.source_units_dir).glob("*.jsonl"))),
        "initial_rule_files": len(list(Path(cfg.rules_initial_dir).glob("*.jsonl"))),
        "skills": len(read_json(cfg.skills_dir / "skill_index.json", []) or []),
    }
    store = MemoryStore(cfg)
    status["memory"] = {mt: store.count(mt) for mt in protocol.MEMORY_TYPES
                        if store.count(mt)}
    _print(status)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hermes",
        description="Hermes v5 — autonomous model-review rule mining OS for "
                    "classical TCM texts (no human review nodes; "
                    "no evidence, no rule)")
    p.add_argument("--root", default=".", help="project root (data/ lives here)")
    p.add_argument("--backend", choices=["heuristic", "anthropic"], default=None)
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("download", help="download the jicheng corpus archive")
    sp.add_argument("--url", default=None)
    sp.add_argument("--extract", action="store_true")
    sp.add_argument("--categories", nargs="*", default=None)
    sp.set_defaults(func=cmd_download)

    sp = sub.add_parser("import", help="import zip/7z archives or extracted trees")
    sp.add_argument("sources", nargs="+")
    sp.add_argument("--categories", nargs="*", default=None)
    sp.set_defaults(func=cmd_import)

    sp = sub.add_parser("catalog", help="rebuild catalog tree + manifests")
    sp.set_defaults(func=cmd_catalog)

    sp = sub.add_parser("segment", help="segment books into source units")
    sp.add_argument("--books", nargs="*", default=None)
    sp.add_argument("--categories", nargs="*", default=None)
    sp.set_defaults(func=cmd_segment)

    sp = sub.add_parser("review", help="run the autonomous review loop")
    sp.add_argument("--books", nargs="*", default=None)
    sp.add_argument("--quiet", action="store_true")
    sp.set_defaults(func=cmd_review)

    sp = sub.add_parser("themes", help="induce chapter/book/category themes")
    sp.add_argument("--books", nargs="*", default=None)
    sp.set_defaults(func=cmd_themes)

    sp = sub.add_parser("merge", help="build merged Hermes rules")
    sp.add_argument("--books", nargs="*", default=None)
    sp.set_defaults(func=cmd_merge)

    sp = sub.add_parser("skills", help="compile Hermes Skills")
    sp.set_defaults(func=cmd_skills)

    sp = sub.add_parser("report", help="generate the Autonomous Review Report")
    sp.add_argument("--books", nargs="*", default=None)
    sp.add_argument("--scope", default=None)
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("metrics", help="compute quality metrics")
    sp.add_argument("--books", nargs="*", default=None)
    sp.set_defaults(func=cmd_metrics)

    sp = sub.add_parser("pipeline", help="full pipeline: catalog→…→report")
    sp.add_argument("--books", nargs="*", default=None)
    sp.add_argument("--categories", nargs="*", default=None)
    sp.set_defaults(func=cmd_pipeline)

    sp = sub.add_parser("search", help="classical text RAG search")
    sp.add_argument("query")
    sp.add_argument("--subcategory", default=None, choices=["傷寒", "金匱", "綜合", "醫案"])
    sp.add_argument("--book", default=None)
    sp.add_argument("--original-only", action="store_true")
    sp.add_argument("--limit", type=int, default=8)
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("ask", help="Skill RAG question answering")
    sp.add_argument("query")
    sp.set_defaults(func=cmd_ask)

    sp = sub.add_parser("lineage", help="formula lineage report")
    sp.add_argument("formula")
    sp.add_argument("--brief", action="store_true")
    sp.set_defaults(func=cmd_lineage)

    sp = sub.add_parser("match-prescription", help="match herb list to formulas")
    sp.add_argument("herbs", help="comma separated herb list")
    sp.set_defaults(func=cmd_match)

    sp = sub.add_parser("physician", help="physician workbench")
    sp.add_argument("action", choices=["match", "case", "differentiate"])
    sp.add_argument("--symptoms", default=None)
    sp.add_argument("--pulse", default=None)
    sp.add_argument("--text", default=None)
    sp.add_argument("--formulas", default=None)
    sp.set_defaults(func=cmd_physician)

    sp = sub.add_parser("research", help="researcher workbench")
    sp.add_argument("action", choices=["stats", "network", "map", "mine"])
    sp.add_argument("--topic", default=None)
    sp.set_defaults(func=cmd_research)

    sp = sub.add_parser("paper", help="draft a mining paper")
    sp.add_argument("topic")
    sp.add_argument("--target", default="中文期刊")
    sp.set_defaults(func=cmd_paper)

    sp = sub.add_parser("patient", help="patient education (safety gated)")
    sp.add_argument("action", choices=["explain", "visit", "instruction"])
    sp.add_argument("--text", default=None)
    sp.set_defaults(func=cmd_patient)

    sp = sub.add_parser("status", help="system status")
    sp.set_defaults(func=cmd_status)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = HermesConfig(root=Path(args.root))
    if args.backend:
        cfg.backend = args.backend
    try:
        args.func(cfg, args)
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
