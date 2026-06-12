"""ThemeRule — chapter / book / category level inductive summaries."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ThemeRule:
    theme_rule_id: str
    theme_level: str                     # chapter | book | category
    scope: dict[str, Any]                # ids/titles describing the scope
    category_path: list[str]
    title: str
    main_diseases: list[dict] = field(default_factory=list)       # {term, count, rule_ids}
    formula_spectrum: list[dict] = field(default_factory=list)
    contraindication_set: list[dict] = field(default_factory=list)
    mistreatment_logic: list[dict] = field(default_factory=list)
    transmission_paths: list[dict] = field(default_factory=list)
    pulse_profile: list[dict] = field(default_factory=list)
    supporting_initial_rules: list[str] = field(default_factory=list)
    supporting_rules_by_release_level: dict[str, list[str]] = field(default_factory=dict)
    source_level: str = "model_inductive_summary"
    autonomous_review: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ThemeRule":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})
