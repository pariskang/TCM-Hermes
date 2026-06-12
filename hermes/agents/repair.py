"""RuleRepairAgent — smallest-edit automatic repair.

Repair strategies (section D2): trim/extend evidence span to clause
boundaries, relabel interpretation_level / evidence_type, drop unsupported
conditions (moved into the interpretation note — never silently deleted),
fix rule_type, clamp confidence.  Repairs never fabricate evidence and never
delete the rule; everything is logged to the audit trail.
"""

from __future__ import annotations

from ..config import HermesConfig
from ..schemas import InitialRule, SourceUnit
from ..schemas.validation import SchemaValidationResult
from ..utils import clamp, split_sentences
from .backends import HeuristicBackend
from .critic import CriticReview
from .evidence import EvidenceReview
from .reviewer import SemanticReview

_EXPECTED_EVIDENCE = {"original": "original_text", "commentary": "commentary",
                      "formula": "formula_block", "variant": "variant",
                      "case": "case_record"}


class RuleRepairAgent:
    name = "RuleRepairAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend or HeuristicBackend()

    # ------------------------------------------------------------------
    def repair(self, rule: InitialRule, unit: SourceUnit | None,
               schema: SchemaValidationResult | None,
               evidence: EvidenceReview | None,
               semantic: SemanticReview | None,
               critic: CriticReview | None) -> list[dict]:
        """Apply applicable repairs in place; return the list of repairs."""
        repairs: list[dict] = []

        def did(rtype: str, **detail):
            repairs.append({"type": rtype, **detail})
            rule.log(self.name, rtype, **detail)

        # ---- schema-level fixes ------------------------------------------
        if schema and not schema.schema_valid:
            from .. import protocol
            if rule.rule_type not in protocol.RULE_TYPES:
                old = rule.rule_type
                rule.rule_type = self._guess_rule_type(rule)
                did("rule_type_corrected", from_=old, to=rule.rule_type)
            if not isinstance(rule.model_confidence, (int, float)) or \
                    not (0.0 <= float(rule.model_confidence) <= 1.0):
                old = rule.model_confidence
                rule.model_confidence = clamp(float(rule.model_confidence)
                                              if isinstance(rule.model_confidence,
                                                            (int, float)) else 0.5)
                did("confidence_clamped", from_=old, to=rule.model_confidence)
            if rule.interpretation_level not in protocol.INTERPRETATION_LEVELS:
                did("interpretation_level_corrected",
                    from_=rule.interpretation_level, to="normalized")
                rule.interpretation_level = "normalized"
            if rule.evidence_type not in protocol.EVIDENCE_TYPES:
                expected = _EXPECTED_EVIDENCE.get(unit.text_type, "original_text") \
                    if unit else "original_text"
                did("evidence_type_corrected", from_=rule.evidence_type, to=expected)
                rule.evidence_type = expected

        # ---- evidence-level fixes ----------------------------------------
        if evidence is not None and unit is not None and not evidence.evidence_span_found:
            fixed = self._relocate_span(rule.evidence_span, unit.raw_text)
            if fixed:
                did("evidence_span_relocated",
                    detail="snapped span to clause boundary inside raw_text")
                rule.evidence_span = fixed

        if evidence is not None and evidence.problems and unit is not None:
            expected = _EXPECTED_EVIDENCE.get(unit.text_type, "original_text")
            if rule.evidence_type != expected and evidence.evidence_span_found:
                did("evidence_type_relabelled", from_=rule.evidence_type, to=expected)
                rule.evidence_type = expected
                if expected == "commentary":
                    rule.interpretation_level = "later_commentary"

        # ---- critic-directed fixes ---------------------------------------
        for rec in (critic.recommended_repair if critic else []):
            rtype = rec.get("type")
            if rtype == "relabel_interpretation_level":
                to = rec.get("to", "normalized")
                upgrade = (rule.interpretation_level == "original_text"
                           or (to == "later_commentary"
                               and rule.interpretation_level == "normalized"))
                if upgrade:
                    did(f"changed interpretation_level from "
                        f"{rule.interpretation_level} to {to}",
                        terms=rec.get("terms", []))
                    rule.interpretation_level = to
            elif rtype == "relabel_evidence_type":
                did("evidence_type_relabelled", from_=rule.evidence_type,
                    to=rec.get("to"))
                rule.evidence_type = rec.get("to", rule.evidence_type)
                if rec.get("to") == "commentary":
                    rule.interpretation_level = "later_commentary"
            elif rtype == "drop_unsupported_conditions":
                dropped = self._drop_conditions(rule, rec.get("terms", []))
                if dropped:
                    rule.interpretation += (
                        f"（自動修復：刪去證據未支持的條件 {'、'.join(dropped)}）")
                    did("dropped_unsupported_conditions", terms=dropped)
            elif rtype == "trim_evidence_span" and unit is not None:
                trimmed = self._trim_span(rule, unit)
                if trimmed:
                    did("evidence_span_trimmed", new_length=len(rule.evidence_span))
            elif rtype == "soften_claim":
                for mk in ("凡", "皆", "一切", "無不"):
                    if mk in rule.interpretation:
                        rule.interpretation = rule.interpretation.replace(mk, "")
                did("claim_softened")

        # ---- reviewer-directed confidence adjustment ---------------------
        if semantic is not None and \
                abs(semantic.suggested_confidence - rule.model_confidence) > 0.15:
            old = rule.model_confidence
            rule.model_confidence = round(
                (rule.model_confidence + semantic.suggested_confidence) / 2, 3)
            did("confidence_adjusted", from_=old, to=rule.model_confidence)

        if repairs:
            rule.autonomous_review.auto_repair_applied = True
            rule.status = "auto_repaired"
        return repairs

    # ------------------------------------------------------------------
    def _guess_rule_type(self, rule: InitialRule) -> str:
        t = rule.then_conclusions
        if t.get("composition"):
            return "formula_composition_rule"
        if t.get("preparation"):
            return "preparation_rule"
        if t.get("prohibition"):
            return "contraindication_rule"
        if t.get("mistreatment"):
            return "mistreatment_rule"
        if t.get("prognosis"):
            return "prognosis_rule"
        if t.get("transmission"):
            return "transmission_rule"
        if t.get("formula"):
            return "formula_indication_rule"
        if t.get("pattern"):
            return "pulse_pattern_rule"
        if t.get("treatment_principle"):
            return "treatment_principle_rule"
        return "symptom_rule"

    def _relocate_span(self, span: str, raw: str) -> str | None:
        """Try to re-anchor a broken span on the real text (whitespace drift,
        truncated copy).  Returns a corrected exact substring or None."""
        if not span:
            return None
        compact = span.replace(" ", "").replace("\n", "")
        if compact and compact in raw:
            return compact
        for cut in (len(span) * 3 // 4, len(span) // 2, 12):
            head = span[:cut]
            if len(head) >= 6 and head in raw:
                start = raw.find(head)
                end = raw.find("。", start + len(head))
                return raw[start:end + 1] if end > 0 else raw[start:start + len(head)]
        return None

    def _trim_span(self, rule: InitialRule, unit: SourceUnit) -> bool:
        sents = split_sentences(rule.evidence_span)
        if len(sents) <= 1:
            return False
        anchor = None
        for key in ("formula", "prohibition", "mistreatment", "prognosis",
                    "transmission", "pattern"):
            vals = rule.then_conclusions.get(key, [])
            if vals:
                anchor = vals[0][:8]
                break
        if anchor:
            for i, s in enumerate(sents):
                if anchor in s:
                    new_span = "".join(sents[max(0, i - 2):i + 1])
                    if new_span in unit.raw_text and len(new_span) < len(rule.evidence_span):
                        rule.evidence_span = new_span
                        return True
        new_span = "".join(sents[-3:])
        if new_span in unit.raw_text and len(new_span) < len(rule.evidence_span):
            rule.evidence_span = new_span
            return True
        return False

    def _drop_conditions(self, rule: InitialRule, terms: list[str]) -> list[str]:
        dropped = []
        for key, vals in rule.if_conditions.items():
            keep = []
            for v in vals:
                if v in terms and v not in rule.evidence_span:
                    dropped.append(v)
                else:
                    keep.append(v)
            rule.if_conditions[key] = keep
        return dropped
