"""TCM-Disease-Hermes — multi-agent classical-TCM disease knowledge discovery.

A migratable framework that maps a modern disease (psoriasis as the worked
example) onto classical sources through a layered recall → refine → exclude →
verify → consensus → ontology → relation → analytics → report pipeline.

Design principles (the load-bearing ones):
  1. recall and precision are separate agents (broad search ≠ strict judging);
  2. positive retrieval and negative exclusion are separate agents;
  3. modern phenotype and classical semantics are kept apart — a classical
     disease name is only ever a *candidate / phenotype correspondence*, never
     a modern diagnosis;
  4. every conclusion is traceable to an evidence span in raw_text.
"""

from .profiles import DiseaseProfile, PSORIASIS, DISEASE_PROFILES, get_profile
from .pipeline import DiseaseHermesPipeline, CandidateRecord

__all__ = [
    "DiseaseProfile", "PSORIASIS", "DISEASE_PROFILES", "get_profile",
    "DiseaseHermesPipeline", "CandidateRecord",
]
