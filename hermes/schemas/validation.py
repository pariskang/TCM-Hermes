"""SchemaValidator — layer 1 of the five-layer autonomous review.

Pure-program structural checks (no model involved):
  * JSON-representability and required fields
  * rule_type within the controlled vocabulary
  * confidence within [0, 1]
  * category_path / book_id / chapter_id / source_unit_id present
  * no banned human-review fields anywhere in the record
Failure ⇒ auto_repair_required (the orchestrator routes to RuleRepairAgent).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .. import protocol
from .initial_rule import InitialRule

REQUIRED_FIELDS = (
    "initial_rule_id", "category_path", "book_id", "book_title", "chapter_id",
    "chapter_title", "source_unit_id", "rule_type",
    "then_conclusions", "evidence_span", "evidence_type", "interpretation_level",
    "model_confidence",
)

# structural rule types whose IF side is legitimately empty (a composition
# listing has no clinical conditions)
_NO_CONDITION_RULE_TYPES = ("formula_composition_rule", "preparation_rule",
                            "dosage_rule")


@dataclass
class SchemaValidationResult:
    schema_valid: bool
    problems: list[str] = field(default_factory=list)
    auto_repair_required: bool = False
    repair_hints: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema_valid": self.schema_valid,
            "problems": self.problems,
            "auto_repair_required": self.auto_repair_required,
            "repair_hints": self.repair_hints,
        }


class SchemaValidator:
    name = "SchemaValidator"

    def validate(self, rule: InitialRule) -> SchemaValidationResult:
        problems: list[str] = []
        hints: list[dict] = []
        d = rule.to_dict()

        # JSON validity (catches non-serialisable payloads)
        try:
            json.dumps(d, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            problems.append(f"not JSON-serialisable: {exc}")

        for f in REQUIRED_FIELDS:
            v = d.get(f)
            if v in (None, "", [], {}):
                problems.append(f"missing or empty field: {f}")

        if d.get("rule_type") not in protocol.RULE_TYPES:
            problems.append(f"rule_type not in controlled vocabulary: {d.get('rule_type')}")
            hints.append({"type": "rule_type_error", "field": "rule_type"})

        conf = d.get("model_confidence")
        if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
            problems.append(f"confidence outside [0,1]: {conf}")
            hints.append({"type": "confidence_out_of_range", "field": "model_confidence"})

        if d.get("interpretation_level") not in protocol.INTERPRETATION_LEVELS:
            problems.append(
                f"interpretation_level invalid: {d.get('interpretation_level')}")
            hints.append({"type": "interpretation_level_error",
                          "field": "interpretation_level"})

        if d.get("evidence_type") not in protocol.EVIDENCE_TYPES:
            problems.append(f"evidence_type invalid: {d.get('evidence_type')}")
            hints.append({"type": "evidence_type_error", "field": "evidence_type"})

        cp = d.get("category_path")
        if not isinstance(cp, list) or not cp or cp[0] != protocol.ROOT_CATEGORY:
            problems.append(f"category_path missing or not rooted at "
                            f"{protocol.ROOT_CATEGORY}: {cp}")

        if not isinstance(d.get("if_conditions"), dict) or \
           not isinstance(d.get("then_conclusions"), dict):
            problems.append("if_conditions/then_conclusions must be objects")
        else:
            if not any(d["then_conclusions"].values()):
                problems.append("then_conclusions has no content")
            if not any(d["if_conditions"].values()) and \
                    d.get("rule_type") not in _NO_CONDITION_RULE_TYPES:
                problems.append("if_conditions has no content for a "
                                "condition-bearing rule_type")

        # the human-review protocol is retired — its fields are forbidden
        flat = json.dumps(d, ensure_ascii=False)
        for banned in protocol.BANNED_FIELDS:
            if f'"{banned}"' in flat:
                problems.append(f"banned human-review field present: {banned}")

        ok = not problems
        return SchemaValidationResult(
            schema_valid=ok,
            problems=problems,
            auto_repair_required=bool(problems) and bool(hints),
            repair_hints=hints,
        )
