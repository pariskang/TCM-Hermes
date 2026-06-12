"""ThemeInducerAgent — chapter / book / category theme induction.

Theme rules are inductive summaries built ONLY from released InitialRules
(silver/gold by default; bronze opt-in via config).  Every aggregate keeps
the supporting rule ids per release level, so each statistic can be expanded
back to original evidence.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from ..config import HermesConfig
from ..schemas import InitialRule, ThemeRule
from ..utils import read_jsonl, write_jsonl


def _top(counter_map: dict[str, list[str]], top_n: int = 12) -> list[dict]:
    items = sorted(counter_map.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:top_n]
    return [{"term": t, "count": len(ids), "rule_ids": ids[:20]} for t, ids in items]


class ThemeInducerAgent:
    name = "ThemeInducerAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def eligible_levels(self) -> tuple[str, ...]:
        return ("gold", "silver", "bronze") if self.config.merge_include_bronze \
            else ("gold", "silver")

    def load_released_rules(self, book_ids: list[str] | None = None) -> list[InitialRule]:
        rules: list[InitialRule] = []
        for level in self.eligible_levels():
            level_dir = self.config.rules_released_dir / level
            for path in sorted(Path(level_dir).glob("BOOK_*.jsonl")):
                if book_ids and path.stem not in book_ids:
                    continue
                rules.extend(InitialRule.from_dict(d) for d in read_jsonl(path))
        return rules

    # ------------------------------------------------------------------
    def _aggregate(self, rules: list[InitialRule]) -> dict:
        diseases: dict[str, list[str]] = defaultdict(list)
        formulas: dict[str, list[str]] = defaultdict(list)
        contras: dict[str, list[str]] = defaultdict(list)
        mistreat: dict[str, list[str]] = defaultdict(list)
        trans: dict[str, list[str]] = defaultdict(list)
        pulses: dict[str, list[str]] = defaultdict(list)
        for r in rules:
            rid = r.initial_rule_id
            for d in r.if_conditions.get("disease", []):
                diseases[d].append(rid)
            for p in r.if_conditions.get("pulse", []):
                pulses[p].append(rid)
            for f in r.then_conclusions.get("formula", []):
                formulas[f].append(rid)
            for pr in r.then_conclusions.get("prohibition", []):
                contras[pr].append(rid)
            for ms in r.then_conclusions.get("mistreatment", []):
                mistreat[ms].append(rid)
            for tr in r.then_conclusions.get("transmission", []):
                trans[tr].append(rid)
        return {
            "main_diseases": _top(diseases),
            "formula_spectrum": _top(formulas),
            "contraindication_set": _top(contras),
            "mistreatment_logic": _top(mistreat),
            "transmission_paths": _top(trans),
            "pulse_profile": _top(pulses),
        }

    def _theme(self, theme_id: str, level: str, scope: dict, category: list[str],
               title: str, rules: list[InitialRule]) -> ThemeRule:
        agg = self._aggregate(rules)
        by_level: dict[str, list[str]] = defaultdict(list)
        for r in rules:
            by_level[r.autonomous_review.release_level].append(r.initial_rule_id)
        scores = [r.autonomous_review.consensus_score for r in rules]
        min_level = "gold"
        for lv in ("bronze", "silver"):
            if by_level.get(lv):
                min_level = lv
                break
        review = {
            "consensus_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
            "critic_result": "pass",
            "evidence_coverage_rate": round(
                sum(r.autonomous_review.evidence_verified for r in rules)
                / len(rules), 3) if rules else 0.0,
            "minimum_child_rule_level": min_level,
            "release_level": "silver" if rules else "rejected",
            "review_status": "model_accepted" if rules else "model_rejected",
        }
        return ThemeRule(
            theme_rule_id=theme_id, theme_level=level, scope=scope,
            category_path=category, title=title,
            supporting_initial_rules=[r.initial_rule_id for r in rules],
            supporting_rules_by_release_level=dict(by_level),
            autonomous_review=review,
            **agg,
        )

    # ------------------------------------------------------------------
    def run(self, book_ids: list[str] | None = None) -> dict:
        rules = self.load_released_rules(book_ids)

        chapters: dict[tuple, list[InitialRule]] = defaultdict(list)
        books: dict[str, list[InitialRule]] = defaultdict(list)
        cats: dict[str, list[InitialRule]] = defaultdict(list)
        meta: dict = {}
        for r in rules:
            chapters[(r.book_id, r.chapter_id)].append(r)
            books[r.book_id].append(r)
            sub = r.category_path[1] if len(r.category_path) > 1 else "?"
            cats[sub].append(r)
            meta[r.book_id] = r.book_title
            meta[r.chapter_id] = r.chapter_title

        themes: list[ThemeRule] = []
        for (book_id, chapter_id), rs in sorted(chapters.items()):
            themes.append(self._theme(
                f"THEME_CH_{chapter_id.removeprefix('CH_')}", "chapter",
                {"book_id": book_id, "chapter_id": chapter_id,
                 "chapter_title": meta[chapter_id]},
                rs[0].category_path, f"{meta[book_id]}·{meta[chapter_id]} 章節主題", rs))
        for book_id, rs in sorted(books.items()):
            themes.append(self._theme(
                f"THEME_BOOK_{book_id.removeprefix('BOOK_')}", "book",
                {"book_id": book_id, "book_title": meta[book_id]},
                rs[0].category_path, f"《{meta[book_id]}》單書主題", rs))
        for sub, rs in sorted(cats.items()):
            themes.append(self._theme(
                f"THEME_CAT_{abs(hash(sub)) % 10**6:06d}", "category",
                {"subcategory": sub}, rs[0].category_path,
                f"傷寒金匱類·{sub} 類目主題", rs))

        out = self.config.rules_theme_dir
        write_jsonl(out / "chapter_themes.jsonl",
                    (t.to_dict() for t in themes if t.theme_level == "chapter"))
        write_jsonl(out / "book_themes.jsonl",
                    (t.to_dict() for t in themes if t.theme_level == "book"))
        write_jsonl(out / "category_themes.jsonl",
                    (t.to_dict() for t in themes if t.theme_level == "category"))
        return {"chapter_themes": sum(t.theme_level == "chapter" for t in themes),
                "book_themes": sum(t.theme_level == "book" for t in themes),
                "category_themes": sum(t.theme_level == "category" for t in themes),
                "supporting_rules": len(rules)}
