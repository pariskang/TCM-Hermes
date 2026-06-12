"""Task-planning layer: disease decomposition + ancient-name expansion."""

from __future__ import annotations

from ..config import HermesConfig
from .profiles import DiseaseProfile


class DiseaseConceptPlannerAgent:
    """Decompose a modern disease into subtypes, phenotype schema and
    differential diseases (the retrieval plan)."""
    name = "DiseaseConceptPlannerAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend

    def plan(self, profile: DiseaseProfile) -> dict:
        return {
            "target_disease": profile.disease_id,
            "display_name": profile.display_name,
            "modern_subtypes": profile.modern_subtypes,
            "phenotype_schema": profile.phenotype_schema,
            "special_subtypes": list(profile.special_subtypes),
            "differential_diseases": profile.exclusion_terms,
            "search_strategy": ["T1_core_recall", "T2_phenotype",
                                "T3_special_subtype", "T4_morphology",
                                "T5_exclusion", "T6_consensus", "T7_ontology"],
        }


class AncientDiseaseNameExpansionAgent:
    """Produce the core ancient-name vocabulary and a boolean recall query."""
    name = "AncientDiseaseNameExpansionAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend

    def expand(self, profile: DiseaseProfile) -> dict:
        return {
            "core_terms": profile.core_terms,
            "query": profile.core_query(),
            "search_goal": "high_recall",
            "note": "广域召回，允许较高噪声；后续层负责精筛与排除。",
        }
