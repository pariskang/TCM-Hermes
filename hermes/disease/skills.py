"""DiseaseSkillBuilder — compile disease candidates into Hermes Skills.

Included (silver/gold; bronze opt-in) candidates of a disease are grouped by
modern subtype and compiled into Skills in the *same* shape the existing
SkillRAGAgent consumes, so disease knowledge is queryable through the one Skill
RAG surface alongside the formula/disease-pattern skills mined from the corpus.

Disease skills are namespaced `hermes.disease.<disease_id>.<subtype>` and
indexed in a separate `disease_skill_index.json`, which SkillRAGAgent merges
with the main index — so re-running the main pipeline never clobbers them.

Every skill answer keeps the mandated surface (release level, consensus score,
supporting candidates, original evidence, variant/conflict sets, safety notice)
and the disease-specific safety framing: 古今映射为候选/表型对应，非诊断。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from ..config import HermesConfig
from ..memory.store import MemoryCuratorAgent
from ..utils import read_json, read_jsonl, utc_now, write_json
from .profiles import DiseaseProfile, get_profile

_SUBTYPE_DISPLAY = {
    "vulgaris": "寻常型", "pustular": "脓疱型", "erythrodermic": "红皮病型",
    "arthropathic": "关节型", "nail": "甲型", "scalp": "头皮型",
    "bone_loss": "骨量减少(骨痿)", "pain": "骨痛/腰背痛", "deformity": "畸形/屈伸不利",
    "frailty": "虚劳/衰弱", "spine": "脊柱", "limb": "四肢",
    "joint_pain": "关节疼痛", "swelling": "关节肿胀", "systemic": "全身症候",
    "hand_foot": "手足关节", "knee": "膝/鹤膝",
}

SAFETY_NOTICE = (
    "本 Disease-Skill 为古籍证候知识整理，古今病名仅建立表型对应/候选映射，"
    "不构成现代诊断或处方建议；每条证据可回源至原文，临床决策须由执业医师判断。")


class DiseaseSkillBuilder:
    name = "DiseaseSkillBuilder"

    def __init__(self, config: HermesConfig | None = None,
                 include_bronze: bool = False) -> None:
        self.config = config or HermesConfig()
        self.include_bronze = include_bronze
        self.memory = MemoryCuratorAgent(self.config)

    # ------------------------------------------------------------------
    def run(self, disease: str) -> dict:
        profile = get_profile(disease)
        ws = self.config.data_dir / "disease" / profile.disease_id
        cand_path = ws / "candidates.jsonl"
        if not cand_path.exists():
            raise FileNotFoundError(
                f"no candidates for {profile.disease_id}; run `hermes disease run "
                f"--disease {disease}` first")
        cands = list(read_jsonl(cand_path))

        levels = ("gold", "silver", "bronze") if self.include_bronze \
            else ("gold", "silver")
        included = [c for c in cands if c["review"]["release_level"] in levels]

        by_subtype: dict[str, list] = defaultdict(list)
        for c in included:
            st = c["phenotype_evidence"].get("candidate_modern_type") or "general"
            by_subtype[st].append(c)

        skills = []
        for subtype, group in sorted(by_subtype.items()):
            skills.append(self._build_skill(profile, subtype, group))
        if len(by_subtype) > 1 and included:
            skills.append(self._build_overview(profile, included, by_subtype))

        # merge into the disease skill index (replace this disease's entries)
        idx_path = self.config.skills_dir / "disease_skill_index.json"
        index = [e for e in (read_json(idx_path, []) or [])
                 if not e["skill_id"].startswith(f"hermes.disease.{profile.disease_id}")]
        for s in skills:
            index.append({"skill_id": s["skill_id"], "title": s["title"],
                          "kind": "disease", "subject": s["subject"],
                          "disease_id": profile.disease_id,
                          "release_level": s["release_level"],
                          "consensus_score": s["consensus_score"],
                          "keywords": s["keywords"]})
        write_json(idx_path, index)
        return {"disease": profile.disease_id, "skills_compiled": len(skills),
                "included_candidates": len(included),
                "by_subtype": {k: len(v) for k, v in by_subtype.items()},
                "skill_ids": [s["skill_id"] for s in skills]}

    # ------------------------------------------------------------------
    def _release_level(self, group: list) -> tuple[str, float]:
        scores = [c["review"]["consensus_score"] for c in group]
        mean = round(sum(scores) / len(scores), 3) if scores else 0.0
        has_gold = any(c["review"]["release_level"] == "gold" for c in group)
        has_silver = any(c["review"]["release_level"] in ("gold", "silver")
                         for c in group)
        if has_gold and len(group) >= 2 and mean >= 0.90:
            return "gold", mean
        if has_silver and mean >= 0.80:
            return "silver", mean
        return "bronze", mean

    def _evidence(self, group: list) -> list[dict]:
        out = []
        for c in sorted(group, key=lambda c: -c["review"]["consensus_score"]):
            pe = c["phenotype_evidence"]
            span = (pe.get("evidence_clauses") or [c["raw_text"][:160]])[0]
            out.append({
                "book_title": c["source"]["book"],
                "chapter_title": c["source"].get("chapter", ""),
                "dynasty": c["source"].get("dynasty", ""),
                "source_unit_id": c["source"].get("source_unit_id"),
                "entry_id": c["entry_id"],
                "evidence_span": span,
                "release_level": c["review"]["release_level"],
            })
        return out[:30]

    def _ontology_summary(self, group: list) -> dict:
        layers = {"symptoms": Counter(), "pathogenesis": Counter(),
                  "treatment_method": Counter(), "herbs": Counter(),
                  "ancient_disease_name": Counter()}
        for c in group:
            ont = c.get("ontology") or {}
            for k in layers:
                layers[k].update(ont.get(k, []))
        return {k: [{"term": t, "count": n} for t, n in c.most_common(15)]
                for k, c in layers.items()}

    def _relations(self, group: list) -> list[list[str]]:
        seen, out = set(), []
        for c in group:
            for tr in c.get("extracted_relations", []):
                key = tuple(tr)
                if key not in seen:
                    seen.add(key)
                    out.append(tr)
        return out[:60]

    def _variants(self, group: list) -> list[dict]:
        by_book = defaultdict(list)
        for c in group:
            by_book[c["source"]["book"]].append(c)
        if len(by_book) < 2:
            return []
        variants = []
        for book, cs in sorted(by_book.items()):
            names = sorted({n for c in cs
                            for n in (c.get("ontology") or {}).get(
                                "ancient_disease_name", [])})
            variants.append({"kind": "book_variant", "book_title": book,
                             "ancient_names": names,
                             "entry_ids": [c["entry_id"] for c in cs][:8]})
        return variants

    def _conflicts(self, group: list) -> list[dict]:
        out = []
        for c in group:
            if c["exclusion"].get("soft_exclude"):
                out.append({"kind": "differential_ambiguity",
                            "entry_id": c["entry_id"],
                            "matched_terms": c["exclusion"]["matched_exclusion_terms"],
                            "message": "提及鉴别病但保留为候选，需进一步区分"})
        return out

    # ------------------------------------------------------------------
    def _build_skill(self, profile: DiseaseProfile, subtype: str,
                     group: list) -> dict:
        level, mean = self._release_level(group)
        by_level = defaultdict(list)
        for c in group:
            by_level[c["review"]["release_level"]].append(c["entry_id"])
        ont = self._ontology_summary(group)
        subtype_disp = _SUBTYPE_DISPLAY.get(subtype, subtype)
        subject = f"{profile.display_name}·{subtype_disp}"
        names = [e["term"] for e in ont["ancient_disease_name"][:5]]
        symps = [e["term"] for e in ont["symptoms"][:6]]
        herbs = [e["term"] for e in ont["herbs"][:8]]
        patho = [e["term"] for e in ont["pathogenesis"][:4]]
        claim = (f"古籍中与{subject}表型相似的条文，核心古病名 "
                 f"{'、'.join(names) or '（未明确命名）'}；常见症候 "
                 f"{'、'.join(symps) or '—'}；病机多属 {'、'.join(patho) or '—'}"
                 + (f"；高频药物 {'、'.join(herbs)}" if herbs else "")
                 + "。（候选/表型对应，非诊断）")
        keywords = list(dict.fromkeys(
            [profile.display_name, subtype_disp, profile.disease_id]
            + names + symps + herbs))

        skill_id = f"hermes.disease.{profile.disease_id}.{subtype}"
        skill = {
            "skill_id": skill_id, "kind": "disease",
            "disease_id": profile.disease_id, "subtype": subtype,
            "title": f"{subject} 古籍证候 Skill",
            "subject": subject,
            "abstracted_claim": claim,
            "merged_rule_id": skill_id,
            "release_level": level, "consensus_score": mean,
            "supporting_initial_rules": [c["entry_id"] for c in group],
            "supporting_rules_by_release_level": dict(by_level),
            "original_evidence": self._evidence(group),
            "ancient_disease_names": names,
            "ontology_summary": ont,
            "relation_triples": self._relations(group),
            "if_profile": {"symptoms": ont["symptoms"][:10],
                           "pathogenesis": ont["pathogenesis"][:6]},
            "then_profile": {"treatment_method": ont["treatment_method"][:8],
                             "herbs": ont["herbs"][:10]},
            "variant_set": self._variants(group),
            "conflict_set": self._conflicts(group),
            "keywords": keywords,
            "safety_notice": SAFETY_NOTICE,
            "compiled_at": utc_now(), "protocol": "hermes-v5",
        }
        self._write(skill)
        self.memory.record_skill(skill_id, {
            "event": "disease_skill_compiled", "disease": profile.disease_id,
            "subtype": subtype, "release_level": level,
            "supporting": len(group)})
        return skill

    def _build_overview(self, profile: DiseaseProfile, included: list,
                        by_subtype: dict) -> dict:
        level, mean = self._release_level(included)
        ont = self._ontology_summary(included)
        names = [e["term"] for e in ont["ancient_disease_name"][:8]]
        subtypes = "、".join(_SUBTYPE_DISPLAY.get(s, s) for s in by_subtype)
        skill_id = f"hermes.disease.{profile.disease_id}"
        skill = {
            "skill_id": skill_id, "kind": "disease",
            "disease_id": profile.disease_id, "subtype": "overview",
            "title": f"{profile.display_name} 古籍证候总览 Skill",
            "subject": profile.display_name,
            "abstracted_claim": (
                f"{profile.display_name}古籍证候总览：核心古病名 "
                f"{'、'.join(names)}；覆盖分型 {subtypes}；"
                f"纳入条文 {len(included)} 条。（候选/表型对应，非诊断）"),
            "merged_rule_id": skill_id,
            "release_level": level, "consensus_score": mean,
            "supporting_initial_rules": [c["entry_id"] for c in included],
            "supporting_rules_by_release_level": {},
            "original_evidence": self._evidence(included),
            "ancient_disease_names": names,
            "ontology_summary": ont,
            "relation_triples": self._relations(included),
            "if_profile": {"symptoms": ont["symptoms"][:12]},
            "then_profile": {"herbs": ont["herbs"][:12]},
            "variant_set": self._variants(included),
            "conflict_set": self._conflicts(included),
            "keywords": list(dict.fromkeys(
                [profile.display_name, profile.disease_id] + names
                + [e["term"] for e in ont["symptoms"][:8]])),
            "safety_notice": SAFETY_NOTICE,
            "compiled_at": utc_now(), "protocol": "hermes-v5",
        }
        self._write(skill)
        return skill

    def _write(self, skill: dict) -> None:
        out = self.config.skills_dir
        write_json(out / f"{skill['skill_id']}.json", skill)
        (Path(out) / f"{skill['skill_id']}.md").write_text(
            self._render_md(skill), encoding="utf-8")

    @staticmethod
    def _render_md(s: dict) -> str:
        lines = [f"# {s['title']}", "",
                 f"- **Skill**: `{s['skill_id']}`",
                 f"- **Release level**: {s['release_level']}",
                 f"- **Consensus score**: {s['consensus_score']}",
                 f"- **Supporting candidates**: {len(s['supporting_initial_rules'])}",
                 f"- **Ancient names**: {'、'.join(s['ancient_disease_names']) or '—'}",
                 "", "## 归纳主张（候选/表型对应，非诊断）", s["abstracted_claim"],
                 "", "## 原文证据（节选）"]
        for e in s["original_evidence"][:8]:
            lines.append(f"> {e['evidence_span']}")
            lines.append(f"> ——《{e['book_title']}》"
                         + (f"·{e['chapter_title']}" if e.get("chapter_title") else "")
                         + f"（{e.get('dynasty','')}，{e['source_unit_id']}，"
                         f"{e['release_level']}）")
            lines.append("")
        herbs = s["then_profile"].get("herbs", [])
        if herbs:
            lines += ["## 高频药物", "、".join(f"{h['term']}({h['count']})"
                                            for h in herbs), ""]
        if s["conflict_set"]:
            lines += ["## 鉴别冲突 conflict_set"]
            lines += [f"- {c.get('message','')}（{c.get('matched_terms')}）"
                      for c in s["conflict_set"][:6]] + [""]
        lines += ["## 安全声明", s["safety_notice"], ""]
        return "\n".join(lines)
