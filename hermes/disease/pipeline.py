"""DiseaseHermesPipeline — the multi-agent state machine.

    disease → plan → ancient-name expansion → core recall → phenotype /
    special / morphology / exclusion annotation → evidence verify →
    3-reviewer relevance + consensus → ontology + relations →
    network + temporal analytics → report

Every candidate is one JSONL record carrying the unified schema (source,
retrieval, phenotype_evidence, exclusion, review, ontology, relations).  The
run is resumable: candidate records are streamed to disk and re-load on
`--resume`; analytics/report recompute from them.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import HermesConfig
from ..schemas import SourceUnit
from ..utils import (ensure_dir, read_json, read_jsonl, utc_now, write_json,
                     write_jsonl)
from .analytics import NetworkAnalysisAgent, TemporalEvolutionAgent
from .ontology import OntologyMappingAgent, RelationExtractionAgent
from .planner import (AncientDiseaseNameExpansionAgent,
                      DiseaseConceptPlannerAgent)
from .profiles import DiseaseProfile, get_profile
from .relevance import (ConsensusRelevanceJudgeAgent, EvidenceSpanVerifierAgent,
                        RelevanceReviewPanel)
from .report import ReportWritingAgent
from .retrieval import (CoreSearchAgent, ExclusionDifferentialAgent,
                        MorphologyRefinementAgent, PhenotypeSearchAgent,
                        SpecialSubtypeSearchAgent)


@dataclass
class CandidateRecord:
    entry_id: str
    source: dict
    raw_text: str
    retrieval: dict
    phenotype_evidence: dict
    exclusion: dict
    review: dict
    ontology: dict = field(default_factory=dict)
    extracted_relations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id, "source": self.source,
            "raw_text": self.raw_text, "retrieval": self.retrieval,
            "phenotype_evidence": self.phenotype_evidence,
            "exclusion": self.exclusion, "review": self.review,
            "ontology": self.ontology, "extracted_relations": self.extracted_relations,
        }


class DiseaseHermesPipeline:
    name = "DiseaseHermesPipeline"

    def __init__(self, config: HermesConfig | None = None, backend=None,
                 include_bronze: bool = False) -> None:
        self.config = config or HermesConfig()
        self.backend = backend
        self.include_bronze = include_bronze
        self.planner = DiseaseConceptPlannerAgent(self.config, backend)
        self.expander = AncientDiseaseNameExpansionAgent(self.config, backend)
        self.core = CoreSearchAgent(self.config)
        self.phenotype = PhenotypeSearchAgent()
        self.special = SpecialSubtypeSearchAgent()
        self.morphology = MorphologyRefinementAgent()
        self.exclusion = ExclusionDifferentialAgent()
        self.evidence = EvidenceSpanVerifierAgent()
        self.panel = RelevanceReviewPanel(self.config, backend)
        self.judge = ConsensusRelevanceJudgeAgent(self.config)
        self.ontology = OntologyMappingAgent(self.config)
        self.relation = RelationExtractionAgent(self.config)
        self.network = NetworkAnalysisAgent(self.config)
        self.temporal = TemporalEvolutionAgent(self.config)
        self.reporter = ReportWritingAgent(self.config, backend)
        self._dynasty_map: dict[str, str] | None = None

    # ------------------------------------------------------------------
    def workspace(self, disease_id: str) -> Path:
        return ensure_dir(self.config.data_dir / "disease" / disease_id)

    def _load_units(self, disease_id: str, use_corpus: bool,
                    use_sample: bool) -> list[SourceUnit]:
        units: list[SourceUnit] = []
        if use_corpus:
            for path in sorted(Path(self.config.source_units_dir).glob("BOOK_*.jsonl")):
                units.extend(SourceUnit.from_dict(d) for d in read_jsonl(path))
        if use_sample or not units:
            from .sample_corpus import load_sample_units
            units.extend(load_sample_units(disease_id))
        return units

    # ------------------------------------------------------------------
    def annotate(self, unit: SourceUnit, profile: DiseaseProfile,
                 core_hits: list[str]) -> dict:
        return {
            "core": {"hit_terms": core_hits},
            "phenotype": self.phenotype.annotate(unit.raw_text, profile),
            "special": self.special.annotate(unit.raw_text, profile),
            "morphology": self.morphology.refine(unit.raw_text, profile),
            "exclusion": self.exclusion.screen(unit.raw_text, profile),
        }

    def _book_dynasty(self) -> dict[str, str]:
        if getattr(self, "_dynasty_map", None) is None:
            books = read_json(self.config.manifests_dir / "book_manifest.json", []) or []
            self._dynasty_map = {b["book_id"]: b.get("dynasty", "") for b in books}
        return self._dynasty_map

    def build_candidate(self, unit: SourceUnit, profile: DiseaseProfile,
                        core_hits: list[str], idx: int) -> CandidateRecord:
        annot = self.annotate(unit, profile, core_hits)
        supporting = (core_hits
                      + annot["morphology"]["morphology_hits"]
                      + [w for sub in annot["phenotype"]["phenotype_support"].values()
                         for w in sub["hits"]])
        ev = self.evidence.verify(unit, supporting)
        votes = self.panel.review(unit, profile, annot)
        review = self.judge.judge(unit, profile, annot, votes)

        meta = unit.meta if isinstance(unit.meta, dict) else {}
        dynasty = meta.get("dynasty") or self._book_dynasty().get(unit.book_id, "")
        rec = CandidateRecord(
            entry_id=f"{profile.disease_id.upper()}_{idx:06d}",
            source={"database": "hermes_corpus", "book": unit.book_title,
                    "chapter": unit.chapter_title, "book_id": unit.book_id,
                    "dynasty": dynasty,
                    "author": meta.get("author", ""), "year": meta.get("year", ""),
                    "source_unit_id": unit.source_unit_id,
                    "sample": meta.get("sample", False)},
            raw_text=unit.raw_text,
            retrieval={"hit_terms": core_hits,
                       "retrieval_layers": self._layers(annot),
                       "query_string": profile.core_query()},
            phenotype_evidence={
                "candidate_modern_type": annot["phenotype"]["candidate_modern_type"],
                "phenotype_support": annot["phenotype"]["phenotype_support"],
                "special_subtypes": annot["special"]["special_subtypes"],
                "supporting_features": ev["evidence_spans"],
                "evidence_clauses": ev["evidence_clauses"],
                "morphology_score": annot["morphology"]["morphology_score"],
                "warning": ev["warning"]},
            exclusion={"exclude_flag": annot["exclusion"]["exclude_flag"],
                       "soft_exclude": annot["exclusion"]["soft_exclude"],
                       "matched_exclusion_terms":
                           annot["exclusion"]["matched_exclusion_terms"],
                       "exclusion_reasons": annot["exclusion"]["exclusion_reasons"]},
            review=review,
        )
        # ontology + relations for everything that isn't rejected
        if review["release_level"] != "rejected":
            rec.ontology = self.ontology.map(unit, profile, annot)
            rec.extracted_relations = self.relation.extract(unit, rec.ontology)
        return rec

    @staticmethod
    def _layers(annot: dict) -> list[str]:
        layers = ["T1_core"]
        if annot["phenotype"]["candidate_modern_type"]:
            layers.append("T2_" + annot["phenotype"]["candidate_modern_type"])
        if annot["special"]["special_subtypes"]:
            layers.append("T3_special")
        if annot["morphology"]["morphology_hits"]:
            layers.append("T4_morphology")
        if annot["exclusion"]["matched_exclusion_terms"]:
            layers.append("T5_exclusion")
        return layers

    def _recall(self, units, profile) -> list[dict]:
        """T1 core-name recall ∪ T2 phenotype recall (≥2 phenotype features or
        a special-subtype near-hit), so phenotype-rich passages surface even
        without a named ancient disease term."""
        recalled = self.core.search(units, profile)
        seen = {r["unit"].source_unit_id for r in recalled}
        for u in units:
            if u.source_unit_id in seen:
                continue
            ph = self.phenotype.annotate(u.raw_text, profile)
            sp = self.special.annotate(u.raw_text, profile)
            n_ph = sum(len(v["hits"]) for v in ph["phenotype_support"].values())
            if n_ph >= 2 or sp["special_subtypes"]:
                recalled.append({"unit": u, "hit_terms": [],
                                 "retrieval_layer": "T2_phenotype"})
                seen.add(u.source_unit_id)
        return recalled

    # ------------------------------------------------------------------
    def run(self, disease: str = "psoriasis", use_corpus: bool = False,
            use_sample: bool = True, resume: bool = False,
            limit: int | None = None) -> dict:
        profile = get_profile(disease)
        ws = self.workspace(profile.disease_id)
        cand_path = ws / "candidates.jsonl"

        write_json(ws / "plan.json", self.planner.plan(profile))
        write_json(ws / "ancient_names.json", self.expander.expand(profile))

        if resume and cand_path.exists():
            records = [CandidateRecord(**{k: d.get(k) for k in
                                          CandidateRecord.__dataclass_fields__})
                       for d in read_jsonl(cand_path)]
        else:
            units = self._load_units(profile.disease_id, use_corpus, use_sample)
            recalled = self._recall(units, profile)
            if limit:
                recalled = recalled[:limit]
            records = []
            for i, hit in enumerate(recalled, 1):
                records.append(self.build_candidate(
                    hit["unit"], profile, hit["hit_terms"], i))
            write_jsonl(cand_path, (r.to_dict() for r in records))

        return self._finalize(profile, ws, records)

    # ------------------------------------------------------------------
    def _finalize(self, profile: DiseaseProfile, ws: Path,
                  records: list[CandidateRecord]) -> dict:
        levels = Counter(r.review["release_level"] for r in records)
        subtypes = Counter(r.phenotype_evidence["candidate_modern_type"]
                           for r in records
                           if r.phenotype_evidence["candidate_modern_type"]
                           and r.review["release_level"] != "rejected")

        eligible = ("gold", "silver", "bronze") if self.include_bronze \
            else ("gold", "silver")
        included = [r for r in records if r.review["release_level"] in eligible]

        # relations + network + temporal from included candidates
        all_relations = []
        for r in included:
            for tr in r.extracted_relations:
                all_relations.append({"entry_id": r.entry_id, "triple": tr})
        write_jsonl(ws / "relations.jsonl", all_relations)

        herb_lists = [r.ontology.get("herbs", []) for r in included
                      if r.ontology.get("herbs")]
        network = self.network.analyze(herb_lists)
        write_json(ws / "network.json", network)
        _write_dot(ws / "network.dot", network)

        temporal = self.temporal.analyze([
            {"dynasty": r.source.get("dynasty"),
             "pathogenesis": r.ontology.get("pathogenesis", []),
             "treatment_method": r.ontology.get("treatment_method", [])}
            for r in included])
        write_json(ws / "temporal.json", temporal)

        summary = {
            "disease": profile.disease_id,
            "display_name": profile.display_name,
            "generated_at": utc_now(),
            "candidates": len(records),
            "by_level": dict(levels),
            "by_subtype": dict(subtypes),
            "included_for_analytics": len(included),
            "network_nodes": network["n_nodes"],
            "network_edges": network["n_edges"],
            "core_herbs": [c["herb"] for c in network["core_herbs"][:8]],
            "principle": ("古今映射为候选/表型对应，非诊断；结论可回源至原文。"
                          "召回与精筛分离、正向与排除分离。"),
        }
        write_json(ws / "summary.json", summary)
        report = self.reporter.write(profile, summary, network, temporal)
        (ws / "report.md").write_text(report, encoding="utf-8")
        summary["workspace"] = str(ws)
        return summary


def _write_dot(path: Path, network: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("graph herbs {\n  node [shape=ellipse];\n")
        core = {c["herb"] for c in network.get("core_herbs", [])}
        for e in network.get("edges", [])[:120]:
            style = ' color="firebrick"' if e["source"] in core or e["target"] in core \
                else ""
            f.write(f'  "{e["source"]}" -- "{e["target"]}" '
                    f'[penwidth={min(e["count"], 6)}{style}];\n')
        f.write("}\n")
