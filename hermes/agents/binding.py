"""Span ↔ claim binding — Problem 2: evidence present ≠ association correct.

A single long span may legitimately contain its evidence substring yet bundle
several symptoms, several conditions and several formulas, so "X主之" might be
mis-associated with conditions that actually belong to a neighbouring clause.

This checker quantifies how tightly a rule's conclusion is *bound* to its
conditions inside the span:

  * multi_formula      — the span asserts more than one distinct 方劑主之 /
                         宜X湯, so a single-formula rule is ambiguous;
  * proximity          — distance (in chars) between the conclusion anchor and
                         each condition term; conditions far from the anchor, or
                         separated from it by a sentence terminator, are weakly
                         bound;
  * binding_score      — 0..1, lower = looser association.

The score feeds the consensus layer and the release gate; it does not replace
the substring guarantee, it sharpens what that guarantee is allowed to claim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..schemas import InitialRule

_FORMULA_ASSERTION = re.compile(
    r"[一-鿿]{2,12}[湯散丸飲煎膏丹](?:方)?(?:主之|主治)|(?:宜|可與|與|當與)[一-鿿]{2,12}[湯散丸飲煎膏丹]")
_TERMINATOR = "。！？；"


@dataclass
class BindingReport:
    binding_score: float
    multi_formula: bool = False
    distinct_formula_assertions: int = 0
    weakly_bound_terms: list[str] = field(default_factory=list)
    anchor: str = ""

    def to_dict(self) -> dict:
        return {"binding_score": round(self.binding_score, 3),
                "multi_formula": self.multi_formula,
                "distinct_formula_assertions": self.distinct_formula_assertions,
                "weakly_bound_terms": self.weakly_bound_terms,
                "anchor": self.anchor}


def _anchor_for(rule: InitialRule) -> str:
    for key in ("formula", "prohibition", "mistreatment", "prognosis",
                "transmission", "pattern"):
        vals = rule.then_conclusions.get(key, [])
        if vals:
            return vals[0]
    return ""


def _clause_window(span: str, idx: int) -> tuple[int, int]:
    """Bounds of the sentence (between terminators) containing position idx."""
    lo = idx
    while lo > 0 and span[lo - 1] not in _TERMINATOR:
        lo -= 1
    hi = idx
    while hi < len(span) and span[hi] not in _TERMINATOR:
        hi += 1
    return lo, hi


def check_binding(rule: InitialRule, max_window: int = 60) -> BindingReport:
    span = rule.evidence_span or ""
    anchor = _anchor_for(rule)
    if not span or not anchor:
        # composition/preparation rules carry no clinical conditions to bind
        return BindingReport(binding_score=1.0, anchor=anchor)

    assertions = {m.group(0) for m in _FORMULA_ASSERTION.finditer(span)}
    n_assert = len(assertions)
    multi = (rule.rule_type == "formula_indication_rule" and n_assert >= 2)

    a_idx = span.rfind(anchor)
    if a_idx < 0:
        a_idx = span.find(anchor)
    score = 1.0
    weak: list[str] = []
    if a_idx >= 0:
        c_lo, c_hi = _clause_window(span, a_idx)
        terms = [t for t in rule.all_condition_terms() if t]
        for t in terms:
            t_idx = span.find(t)
            if t_idx < 0:
                weak.append(t)
                score -= 0.6 / max(len(terms), 1)
                continue
            # same sentence as the anchor → tightly bound
            if c_lo <= t_idx <= c_hi:
                continue
            dist = abs(t_idx - a_idx)
            terminators_between = sum(
                span[i] in _TERMINATOR for i in range(min(t_idx, a_idx),
                                                       max(t_idx, a_idx)))
            penalty = 0.0
            if dist > max_window:
                penalty += 0.25
            penalty += 0.2 * terminators_between
            if penalty > 0:
                weak.append(t)
                score -= penalty / max(len(terms), 1)

    # each extra competing formula assertion loosens a single-formula claim
    if multi:
        score -= 0.2 * (n_assert - 1)

    score = max(0.0, min(1.0, score))
    return BindingReport(binding_score=round(score, 3), multi_formula=multi,
                         distinct_formula_assertions=n_assert,
                         weakly_bound_terms=weak[:8], anchor=anchor)
