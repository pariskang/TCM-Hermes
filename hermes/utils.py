"""Shared helpers: deterministic IDs, JSONL stores, hashing, timestamps."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def short_hash(text: str, n: int = 8) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n].upper()


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: str | Path, obj: Any) -> Path:
    p = Path(path)
    ensure_dir(p.parent)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False),
                 encoding="utf-8")
    return p


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def append_jsonl(path: str | Path, records: Iterable[dict] | dict) -> int:
    p = Path(path)
    ensure_dir(p.parent)
    if isinstance(records, dict):
        records = [records]
    n = 0
    with open(p, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def write_jsonl(path: str | Path, records: Iterable[dict]) -> int:
    p = Path(path)
    ensure_dir(p.parent)
    n = 0
    with open(p, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_jsonl(path: str | Path) -> Iterator[dict]:
    p = Path(path)
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def normalize_text(text: str) -> str:
    """NFC-normalize and unify whitespace without altering CJK content."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t　]+", lambda m: " " if " " in m.group() else m.group(), text)
    return text


_SENT_SPLIT = re.compile(r"(?<=[。！？；])")


def split_sentences(text: str) -> list[str]:
    """Split classical Chinese text into sentence units (keeps terminators)."""
    parts = [s for s in _SENT_SPLIT.split(text) if s.strip()]
    return parts


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def env_flag(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")
