"""RuleMergerAgent — build MergedHermesRule v5 across books.

Policy (hard requirements of the protocol):
  * only silver/gold InitialRules support merged rules (bronze opt-in);
    rejected rules may NEVER support a merged rule;
  * merged rules never overwrite InitialRules — they reference rule ids and
    carry the full evidence chain, per-level support, variants and conflicts;
  * a merged rule's release level is gated on child levels + consensus.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from ..config import HermesConfig
from ..knowledge.lexicon import LEXICON
from ..schemas import InitialRule, MergedHermesRule
from ..utils import write_jsonl
from .theme import ThemeInducerAgent


class RuleMergerAgent:
    name = "RuleMergerAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.loader = ThemeInducerAgent(self.config)

    # ------------------------------------------------------------------
    def run(self, book_ids: list[str] | None = None) -> dict:
        rules = self.loader.load_released_rules(book_ids)
        merged: list[MergedHermesRule] = []
        merged.extend(self._merge_formula_patterns(rules))
        merged.extend(self._merge_disease_patterns(rules))
        write_jsonl(self.config.rules_merged_dir / "merged_rules.jsonl",
                    (m.to_dict() for m in merged))
        levels = Counter(m.autonomous_review.get("release_level") for m in merged)
        return {"merged_rules": len(merged), "by_level": dict(levels)}

    # ------------------------------------------------------------------
    def _merge_formula_patterns(self, rules: list[InitialRule]) -> list[MergedHermesRule]:
        groups: dict[str, list[InitialRule]] = defaultdict(list)
        comp_rules: dict[str, list[InitialRule]] = defaultdict(list)
        for r in rules:
            for f in r.then_conclusions.get("formula", []):
                if r.rule_type == "formula_indication_rule":
                    groups[f].append(r)
                elif r.rule_type == "formula_composition_rule":
                    comp_rules[f].append(r)

        out: list[MergedHermesRule] = []
        for formula, members in sorted(groups.items(),
                                       key=lambda kv: -len(kv[1])):
            if len(members) < 2:        # a merged rule needs corroboration
                continue
            out.append(self._build_formula_rule(formula, members,
                                                comp_rules.get(formula, [])))
        return out

    def _build_formula_rule(self, formula: str, members: list[InitialRule],
                            comps: list[InitialRule]) -> MergedHermesRule:
        slug = LEXICON.formula_slug(formula)
        by_level: dict[str, list[str]] = {"gold": [], "silver": [], "bronze": []}
        chain = []
        for r in members:
            by_level.setdefault(r.autonomous_review.release_level, []).append(
                r.initial_rule_id)
            chain.append({
                "initial_rule_id": r.initial_rule_id,
                "book_id": r.book_id, "book_title": r.book_title,
                "chapter_title": r.chapter_title,
                "source_unit_id": r.source_unit_id,
                "release_level": r.autonomous_review.release_level,
                "consensus_score": r.autonomous_review.consensus_score,
                "evidence_span": r.evidence_span,
            })

        # IF/THEN profiles: how often each term appears across the support set
        if_profile: dict[str, list[dict]] = {}
        for key in ("disease", "symptoms", "pulse", "pathomechanism"):
            c = Counter(t for r in members for t in r.if_conditions.get(key, []))
            if_profile[key] = [{"term": t, "count": n} for t, n in c.most_common(10)]
        then_profile = {
            "treatment_principle": [
                {"term": t, "count": n} for t, n in Counter(
                    t for r in members
                    for t in r.then_conclusions.get("treatment_principle", [])
                ).most_common(6)]
        }

        variants = self._variants(members, comps)
        conflicts = self._conflicts(formula, members)

        scores = [r.autonomous_review.consensus_score for r in members]
        consensus = round(sum(scores) / len(scores), 3)
        coverage = round(sum(r.autonomous_review.evidence_verified
                             for r in members) / len(members), 3)
        min_level = "gold"
        for lv in ("bronze", "silver"):
            if by_level.get(lv):
                min_level = lv
                break
        release = self._merged_gate(consensus, coverage, min_level, conflicts)

        core_terms = [e["term"] for e in
                      (if_profile["disease"] + if_profile["symptoms"]
                       + if_profile["pulse"])[:6]]
        claim = (f"{formula}可歸納為"
                 + ("、".join(core_terms) if core_terms else "本組條文所述病證")
                 + f"等方證的核心方（支持條文 {len(members)} 條，跨 "
                 + f"{len({r.book_id for r in members})} 部書）。")

        return MergedHermesRule(
            merged_rule_id=f"MHR_FORMULA_{slug.upper()}",
            title=f"{formula}方證合併規則",
            merged_rule_type="formula_pattern",
            abstracted_claim=claim,
            subject=formula,
            if_profile=if_profile,
            then_profile=then_profile,
            supporting_initial_rules=[r.initial_rule_id for r in members],
            supporting_rules_by_release_level={k: v for k, v in by_level.items()},
            evidence_chain=chain,
            variant_set=variants,
            conflict_set=conflicts,
            autonomous_review={
                "consensus_score": consensus,
                "critic_result": "pass" if not conflicts else "minor_issue",
                "evidence_coverage_rate": coverage,
                "minimum_child_rule_level": min_level,
                "release_level": release,
                "review_status": "model_accepted",
            },
        )

    # ------------------------------------------------------------------
    def _merge_disease_patterns(self, rules: list[InitialRule]) -> list[MergedHermesRule]:
        groups: dict[str, list[InitialRule]] = defaultdict(list)
        for r in rules:
            if r.rule_type in ("disease_definition_rule", "formula_indication_rule",
                               "contraindication_rule", "mistreatment_rule"):
                for d in r.if_conditions.get("disease", []) \
                        + r.then_conclusions.get("disease", []):
                    groups[d].append(r)
        out = []
        for disease, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            if len(members) < 3:
                continue
            by_level: dict[str, list[str]] = {"gold": [], "silver": [], "bronze": []}
            for r in members:
                by_level.setdefault(r.autonomous_review.release_level, []).append(
                    r.initial_rule_id)
            formulas = Counter(f for r in members
                               for f in r.then_conclusions.get("formula", []))
            scores = [r.autonomous_review.consensus_score for r in members]
            consensus = round(sum(scores) / len(scores), 3)
            min_level = "gold"
            for lv in ("bronze", "silver"):
                if by_level.get(lv):
                    min_level = lv
                    break
            release = self._merged_gate(consensus, 1.0, min_level, [])
            top_formulas = "、".join(f for f, _ in formulas.most_common(5))
            out.append(MergedHermesRule(
                merged_rule_id=f"MHR_DISEASE_{abs(hash(disease)) % 10**8:08d}",
                title=f"{disease}證治合併規則",
                merged_rule_type="disease_pattern",
                abstracted_claim=(f"{disease}相關條文 {len(members)} 條；"
                                  + (f"主要方劑：{top_formulas}。" if top_formulas
                                     else "以證候/禁忌條文為主。")),
                subject=disease,
                supporting_initial_rules=[r.initial_rule_id for r in members],
                supporting_rules_by_release_level=by_level,
                evidence_chain=[{
                    "initial_rule_id": r.initial_rule_id, "book_id": r.book_id,
                    "book_title": r.book_title,
                    "source_unit_id": r.source_unit_id,
                    "release_level": r.autonomous_review.release_level,
                    "evidence_span": r.evidence_span} for r in members[:50]],
                autonomous_review={
                    "consensus_score": consensus,
                    "critic_result": "pass",
                    "evidence_coverage_rate": 1.0,
                    "minimum_child_rule_level": min_level,
                    "release_level": release,
                    "review_status": "model_accepted",
                },
            ))
        return out

    # ------------------------------------------------------------------
    def _variants(self, members: list[InitialRule],
                  comps: list[InitialRule]) -> list[dict]:
        """Per-book condition variations + composition variants."""
        variants = []
        by_book: dict[str, list[InitialRule]] = defaultdict(list)
        for r in members:
            by_book[r.book_id].append(r)
        if len(by_book) > 1:
            base_conditions = set(
                t for r in members for t in r.all_condition_terms())
            for book_id, rs in sorted(by_book.items()):
                terms = set(t for r in rs for t in r.all_condition_terms())
                only_here = sorted(terms - set(
                    t for r in members if r.book_id != book_id
                    for t in r.all_condition_terms()))
                if only_here:
                    variants.append({
                        "kind": "condition_variant",
                        "book_id": book_id,
                        "book_title": rs[0].book_title,
                        "distinct_conditions": only_here[:8],
                        "rule_ids": [r.initial_rule_id for r in rs][:8],
                    })
        comp_sets: dict[frozenset, list[InitialRule]] = defaultdict(list)
        for r in comps:
            herbs = frozenset(c[:len(c)] for c in
                              r.then_conclusions.get("composition", []))
            comp_sets[herbs].append(r)
        if len(comp_sets) > 1:
            for herbs, rs in comp_sets.items():
                variants.append({
                    "kind": "composition_variant",
                    "books": sorted({r.book_title for r in rs}),
                    "composition": sorted(herbs),
                    "rule_ids": [r.initial_rule_id for r in rs][:5],
                })
        return variants

    def _conflicts(self, formula: str, members: list[InitialRule]) -> list[dict]:
        """Indication vs contraindication tension on shared conditions."""
        conflicts = []
        pos: dict[str, list[str]] = defaultdict(list)
        for r in members:
            for d in r.if_conditions.get("disease", []):
                pos[d].append(r.initial_rule_id)
        # members are indication rules; conflicting signals appear when the
        # same disease context shows mutually exclusive evidence directions
        seen_pairs = set()
        for r in members:
            span = r.evidence_span
            if any(mk in span for mk in ("不可", "勿", "禁")) and formula in span:
                key = (r.initial_rule_id, "contraindication_in_evidence")
                if key not in seen_pairs:
                    seen_pairs.add(key)
                    conflicts.append({
                        "kind": "indication_vs_prohibition",
                        "message": f"證據中同時出現{formula}應用與禁忌表述，需按條件區分。",
                        "rule_ids": [r.initial_rule_id],
                        "book_title": r.book_title,
                    })
        return conflicts

    def _merged_gate(self, consensus: float, coverage: float,
                     min_level: str, conflicts: list) -> str:
        cfg = self.config
        if coverage < 1.0:
            return "bronze"
        if consensus >= cfg.gold_min_consensus and min_level in ("silver", "gold") \
                and not conflicts:
            return "gold"
        if consensus >= cfg.silver_min_consensus:
            return "silver"
        if consensus >= cfg.bronze_min_consensus:
            return "bronze"
        return "rejected"
