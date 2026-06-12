"""SourceUnit — the smallest evidence-bearing unit of the corpus (条文/段落)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SourceUnit:
    source_unit_id: str
    category_path: list[str]
    book_id: str
    book_title: str
    book_type: str                  # original | commentary | compilation | case_collection
    chapter_id: str
    chapter_title: str
    seq: int                        # order within chapter
    raw_text: str                   # exact text — evidence_span must be a substring
    text_type: str                  # original | commentary | formula | variant | case | preface | toc
    clause_no: str | None = None    # modern clause number when the edition provides one (條文版)
    entities: dict[str, list[str]] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SourceUnit":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})
