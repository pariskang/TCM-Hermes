"""Knowledge-extraction layer: 5-layer ontology mapping + relation extraction."""

from __future__ import annotations

from ..config import HermesConfig
from ..knowledge.lexicon import LEXICON
from ..schemas import SourceUnit
from .profiles import DiseaseProfile

_SUBTYPE_DISPLAY = {
    "vulgaris": "寻常型", "pustular": "脓疱型", "erythrodermic": "红皮病型",
    "arthropathic": "关节型", "nail": "甲型", "scalp": "头皮型",
}


class OntologyMappingAgent:
    """古病名 — 症状 — 病机 — 治法 — 药物 (5-layer)."""
    name = "OntologyMappingAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def map(self, unit: SourceUnit, profile: DiseaseProfile, annot: dict) -> dict:
        text = unit.raw_text
        herbs = sorted(set(LEXICON.find_terms(text, LEXICON.herbs)
                           + [h for h in profile.extra_herbs if h in text]),
                       key=len, reverse=True)
        symptoms = sorted(set(
            LEXICON.find_terms(text, LEXICON.symptoms)
            + [w for w in profile.all_phenotype_terms() if w in text]
            + [m for m in profile.morphology_terms if m in text]),
            key=len, reverse=True)
        cand = annot["phenotype"]["candidate_modern_type"]
        modern = []
        if cand:
            modern.append(f"{profile.display_name}·{_SUBTYPE_DISPLAY.get(cand, cand)}")
        modern += [f"{profile.display_name}·{_SUBTYPE_DISPLAY.get(s, s)}"
                   for s in annot["special"]["special_subtypes"]]
        return {
            "ancient_disease_name": annot["core"]["hit_terms"],
            "modern_phenotype_candidate": sorted(set(modern)),
            "symptoms": symptoms,
            "pathogenesis": [p for p in profile.pathogenesis_terms if p in text],
            "treatment_method": [t for t in profile.treatment_terms if t in text],
            "herbs": herbs,
            "evidence_text": text,
        }


class RelationExtractionAgent:
    """Binary / chained relations for graph + sankey + analytics."""
    name = "RelationExtractionAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def extract(self, unit: SourceUnit, ontology: dict) -> list[list[str]]:
        triples: list[list[str]] = []
        names = ontology["ancient_disease_name"] or ["(unnamed)"]
        dynasty = unit.meta.get("dynasty", "") if isinstance(unit.meta, dict) else ""

        for name in names:
            for s in ontology["symptoms"]:
                triples.append([name, "has_symptom", s])
            for m in ontology["modern_phenotype_candidate"]:
                triples.append([name, "maps_to_candidate", m])
            for p in ontology["pathogenesis"]:
                triples.append([p, "associated_with", name])
        for p in ontology["pathogenesis"]:
            for t in ontology["treatment_method"]:
                triples.append([p, "treated_by", t])
        for t in ontology["treatment_method"]:
            for h in ontology["herbs"]:
                triples.append([t, "uses_herb", h])
        herbs = ontology["herbs"]
        for i in range(len(herbs)):
            for j in range(i + 1, len(herbs)):
                triples.append([herbs[i], "co_occurs_with", herbs[j]])
        if dynasty:
            for p in ontology["pathogenesis"]:
                triples.append([dynasty, "dynasty_pathogenesis", p])
            for t in ontology["treatment_method"]:
                triples.append([dynasty, "dynasty_treatment", t])
        # de-dup, preserve order
        seen, out = set(), []
        for tr in triples:
            key = tuple(tr)
            if key not in seen:
                seen.add(key)
                out.append(tr)
        return out
