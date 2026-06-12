"""SkillRAGAgent — retrieve and execute Hermes Skills.

Flow: user question → skill retrieval (keyword/entity match over the skill
index) → expand merged rule → trace supporting InitialRules → original
evidence → answer object.  Output always reports: selected skill, merged
rule, release level, consensus score, supporting initial rules, original
evidence, variant set, conflict set, safety notice.
"""

from __future__ import annotations

from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..memory.store import MemoryCuratorAgent
from ..utils import read_json


class SkillRAGAgent:
    name = "SkillRAGAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.entities = EntityExtractorAgent()
        self.memory = MemoryCuratorAgent(self.config)

    def index(self) -> list[dict]:
        # merge formula/disease-pattern skills (skill_index.json) with the
        # TCM-Disease-Hermes skills (disease_skill_index.json); re-running the
        # main pipeline rewrites only the former, never clobbering disease skills
        main = read_json(self.config.skills_dir / "skill_index.json", []) or []
        disease = read_json(self.config.skills_dir / "disease_skill_index.json", []) or []
        return main + disease

    def load_skill(self, skill_id: str) -> dict | None:
        return read_json(self.config.skills_dir / f"{skill_id}.json")

    # ------------------------------------------------------------------
    def retrieve(self, query: str, limit: int = 3) -> list[dict]:
        ents = self.entities.extract(query)
        q_terms = set(t for vals in ents.values() for t in vals)
        scored = []
        for entry in self.index():
            kw = set(entry.get("keywords", []))
            subject = entry.get("subject", "")
            score = 0.0
            if subject and subject in query:
                score += 2.0
            score += len(q_terms & kw) * 0.5
            score += sum(0.25 for k in kw if k and k in query)
            if entry.get("release_level") == "gold":
                score += 0.25
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:limit]]

    # ------------------------------------------------------------------
    def ask(self, query: str) -> dict:
        candidates = self.retrieve(query)
        if not candidates:
            return {"query": query, "selected_skill": None,
                    "message": "未检索到匹配的 Hermes Skill；可尝试原文 RAG（hermes search）。"}
        top = self.load_skill(candidates[0]["skill_id"]) or candidates[0]
        answer = {
            "query": query,
            "selected_skill": top.get("skill_id"),
            "skill_kind": top.get("kind"),
            "skill_title": top.get("title"),
            "merged_rule": top.get("merged_rule_id"),
            "release_level": top.get("release_level"),
            "consensus_score": top.get("consensus_score"),
            "abstracted_claim": top.get("abstracted_claim"),
            "supporting_initial_rules": top.get("supporting_initial_rules", []),
            "original_evidence": top.get("original_evidence", [])[:8],
            "variant_set": top.get("variant_set", []),
            "conflict_set": top.get("conflict_set", []),
            "other_candidate_skills": [c["skill_id"] for c in candidates[1:]],
            "safety_notice": top.get("safety_notice"),
        }
        if top.get("kind") == "disease":
            # disease skills carry phenotype-mapping extras
            answer["disease_id"] = top.get("disease_id")
            answer["ancient_disease_names"] = top.get("ancient_disease_names", [])
            answer["ontology_summary"] = top.get("ontology_summary", {})
            answer["mapping_caveat"] = "古今映射为候选/表型对应，非诊断。"
        self.memory.record_skill(top.get("skill_id", "?"),
                                 {"event": "skill_invoked", "query": query})
        return answer
