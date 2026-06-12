"""SkillBuilderAgent — compile Hermes Skills from merged rules.

Skills are the deployable knowledge assets.  Only silver/gold merged rules
compile to skills; every skill answer must surface: selected skill, merged
rule, release level, consensus score, supporting initial rules, original
evidence, variant set, conflict set, and a safety notice.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import HermesConfig
from ..knowledge.lexicon import LEXICON
from ..memory.store import MemoryCuratorAgent
from ..schemas import MergedHermesRule
from ..utils import read_jsonl, utc_now, write_json

SAFETY_NOTICE = (
    "本 Skill 输出为古籍知识整理，供学习与研究参考；不构成诊断或处方建议，"
    "临床使用须由执业中医师结合患者具体情况判断。")


class SkillBuilderAgent:
    name = "SkillBuilderAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.memory = MemoryCuratorAgent(self.config)

    def run(self) -> dict:
        merged_path = self.config.rules_merged_dir / "merged_rules.jsonl"
        skills = []
        for d in read_jsonl(merged_path):
            rule = MergedHermesRule.from_dict(d)
            level = rule.autonomous_review.get("release_level")
            if level not in ("silver", "gold"):
                continue        # bronze/rejected merged rules never become skills
            skills.append(self._build_skill(rule))
        index = [{"skill_id": s["skill_id"], "title": s["title"],
                  "kind": s["kind"], "subject": s["subject"],
                  "release_level": s["release_level"],
                  "consensus_score": s["consensus_score"],
                  "keywords": s["keywords"]} for s in skills]
        write_json(self.config.skills_dir / "skill_index.json", index)
        return {"skills": len(skills),
                "gold": sum(s["release_level"] == "gold" for s in skills),
                "silver": sum(s["release_level"] == "silver" for s in skills)}

    # ------------------------------------------------------------------
    def _build_skill(self, rule: MergedHermesRule) -> dict:
        if rule.merged_rule_type == "formula_pattern":
            slug = LEXICON.formula_slug(rule.subject)
            skill_id = f"hermes.formula.{slug}"
            kind = "formula"
        else:
            skill_id = f"hermes.disease.{rule.merged_rule_id.split('_')[-1].lower()}"
            kind = "disease"

        keywords = [rule.subject]
        for key in ("disease", "symptoms", "pulse"):
            keywords += [e["term"] for e in rule.if_profile.get(key, [])[:5]]
        keywords = list(dict.fromkeys(k for k in keywords if k))

        skill = {
            "skill_id": skill_id,
            "kind": kind,
            "title": rule.title,
            "subject": rule.subject,
            "abstracted_claim": rule.abstracted_claim,
            "merged_rule_id": rule.merged_rule_id,
            "release_level": rule.autonomous_review.get("release_level"),
            "consensus_score": rule.autonomous_review.get("consensus_score"),
            "supporting_initial_rules": rule.supporting_initial_rules,
            "supporting_rules_by_release_level": rule.supporting_rules_by_release_level,
            # concise canonical clauses first — long compiled passages last
            "original_evidence": [
                {"book_title": e.get("book_title"),
                 "chapter_title": e.get("chapter_title", ""),
                 "source_unit_id": e.get("source_unit_id"),
                 "evidence_span": e.get("evidence_span"),
                 "release_level": e.get("release_level")}
                for e in sorted(rule.evidence_chain,
                                key=lambda e: ({"gold": 0, "silver": 1}.get(
                                    e.get("release_level"), 2),
                                    len(e.get("evidence_span") or "")))[:30]],
            "variant_set": rule.variant_set,
            "conflict_set": rule.conflict_set,
            "if_profile": rule.if_profile,
            "then_profile": rule.then_profile,
            "keywords": keywords,
            "safety_notice": SAFETY_NOTICE,
            "compiled_at": utc_now(),
            "protocol": "hermes-v5",
        }
        out_dir = self.config.skills_dir
        write_json(out_dir / f"{skill_id}.json", skill)
        (Path(out_dir) / f"{skill_id}.md").write_text(
            self._render_md(skill), encoding="utf-8")
        self.memory.record_skill(skill_id, {
            "merged_rule_id": rule.merged_rule_id,
            "release_level": skill["release_level"],
            "supporting_rules": len(rule.supporting_initial_rules)})
        return skill

    @staticmethod
    def _render_md(s: dict) -> str:
        lines = [
            f"# {s['title']}",
            "",
            f"- **Skill**: `{s['skill_id']}`",
            f"- **Merged rule**: `{s['merged_rule_id']}`",
            f"- **Release level**: {s['release_level']}",
            f"- **Consensus score**: {s['consensus_score']}",
            f"- **Supporting initial rules**: {len(s['supporting_initial_rules'])}",
            "",
            "## 归纳主张",
            s["abstracted_claim"],
            "",
            "## 原文证据（节选）",
        ]
        for e in s["original_evidence"][:8]:
            lines.append(f"> {e['evidence_span']}")
            lines.append(f"> ——《{e['book_title']}》"
                         + (f"·{e['chapter_title']}" if e.get("chapter_title") else "")
                         + f"（{e['source_unit_id']}，{e['release_level']}）")
            lines.append("")
        if s["variant_set"]:
            lines.append("## 版本差异 variant_set")
            for v in s["variant_set"][:6]:
                lines.append(f"- {json.dumps(v, ensure_ascii=False)}")
            lines.append("")
        if s["conflict_set"]:
            lines.append("## 冲突记录 conflict_set")
            for c in s["conflict_set"][:6]:
                lines.append(f"- {c.get('message', json.dumps(c, ensure_ascii=False))}")
            lines.append("")
        lines += ["## 安全声明", s["safety_notice"], ""]
        return "\n".join(lines)
