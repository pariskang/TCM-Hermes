"""Multi-channel retrieval layer: core recall → phenotype → special → morphology
→ exclusion.  Recall and precision stay in separate agents by design."""

from __future__ import annotations

from ..config import HermesConfig
from ..schemas import SourceUnit
from .profiles import DiseaseProfile


def _hits(text: str, terms: list[str]) -> list[str]:
    return [t for t in terms if t and t in text]


def _near(text: str, anchors: list[str], qualifiers: list[str],
          window: int) -> tuple[bool, list[str]]:
    """True if any anchor and qualifier co-occur within `window` chars."""
    a_pos = [(i, a) for a in anchors for i in _all_idx(text, a)]
    q_pos = [(i, q) for q in qualifiers for i in _all_idx(text, q)]
    pairs: list[str] = []
    for ai, a in a_pos:
        for qi, q in q_pos:
            if abs(ai - qi) <= window:
                pairs.append(f"{a}~{q}")
    return bool(pairs), sorted(set(pairs))[:6]


def _all_idx(text: str, term: str) -> list[int]:
    out, start = [], 0
    while True:
        i = text.find(term, start)
        if i < 0:
            break
        out.append(i)
        start = i + 1
    return out


class CoreSearchAgent:
    """T1 — broad recall over core ancient names (high recall, noisy)."""
    name = "CoreSearchAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def search(self, units: list[SourceUnit], profile: DiseaseProfile) -> list[dict]:
        out = []
        for u in units:
            hit = _hits(u.raw_text, profile.core_terms)
            if hit:
                out.append({"unit": u, "hit_terms": hit,
                            "retrieval_layer": "T1_core_recall"})
        return out


class PhenotypeSearchAgent:
    """T2 — phenotype-combination retrieval per modern subtype."""
    name = "PhenotypeSearchAgent"

    def annotate(self, text: str, profile: DiseaseProfile) -> dict:
        support: dict[str, dict] = {}
        for subtype, feats in profile.phenotype_schema.items():
            hit = _hits(text, feats)
            if hit:
                # saturating: 1 hit → 0.5, 2 → 0.8, ≥3 → 1.0 (a long feature
                # list must not dilute a strong, specific match)
                strength = min(1.0, 0.3 + 0.3 * len(hit))
                support[subtype] = {"hits": hit, "support": round(strength, 3)}
        best = max(support.items(), key=lambda kv: kv[1]["support"], default=None)
        return {"phenotype_support": support,
                "candidate_modern_type": best[0] if best else None,
                "best_support": best[1]["support"] if best else 0.0}


class SpecialSubtypeSearchAgent:
    """T3 — arthropathic / nail / scalp recall via anchor~qualifier proximity."""
    name = "SpecialSubtypeSearchAgent"

    def annotate(self, text: str, profile: DiseaseProfile) -> dict:
        hits = {}
        for subtype, spec in profile.special_subtypes.items():
            ok, pairs = _near(text, spec["anchors"], spec["qualifiers"],
                              spec["window"])
            if ok:
                hits[subtype] = pairs
        return {"special_subtype_hits": hits,
                "special_subtypes": sorted(hits)}


class MorphologyRefinementAgent:
    """T4 — morphology vocabulary boosts phenotype precision."""
    name = "MorphologyRefinementAgent"

    def refine(self, text: str, profile: DiseaseProfile) -> dict:
        hit = _hits(text, profile.morphology_terms)
        score = min(1.0, 0.3 * len(hit))
        support = "vulgaris_like" if any(
            t in hit for t in ("如錢文", "匡郭", "白皮", "皮枯索", "隱胗",
                               "脫屑", "白屑")) else None
        return {"morphology_hits": hit, "morphology_score": round(score, 3),
                "phenotype_support": support}


class ExclusionDifferentialAgent:
    """T5 — flag candidates that look like differential (non-target) diseases."""
    name = "ExclusionDifferentialAgent"

    def screen(self, text: str, profile: DiseaseProfile) -> dict:
        # longest-first so 金錢癬/圓癬 win over the bare 癬 core term
        matched = []
        for term in sorted(set(profile.exclusion_terms), key=len, reverse=True):
            if term in text:
                matched.append(term)
        # a differential term in the leading clause is the passage's *subject*
        # (e.g. 「圓癬者，狀如錢文…」) — a hard exclude regardless of phrasing
        headword = any(text.find(m) >= 0 and text.find(m) <= 6 for m in matched)
        # "與白疕不同 / 非…" contrastive context only softens a non-subject mention
        contrastive = any(p in text for p in ("不同", "非", "別於", "异于", "異於"))
        strong = bool(matched) and (headword or not contrastive)
        reasons = [{"term": m, "note": profile.differential_notes.get(m, "")}
                   for m in matched]
        return {"exclude_flag": strong,
                "soft_exclude": bool(matched) and not strong,
                "matched_exclusion_terms": matched,
                "exclusion_reasons": reasons}
