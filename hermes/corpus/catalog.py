"""CatalogAgent — rebuild the 中醫笈成 classification tree and book manifests.

Catalog priority follows the corpus packaging convention: the `分類=` field
inside each book's <book> block wins; the directory name supplies the
fallback.  Output:
    catalog_tree.json    傷寒金匱類 → 傷寒/金匱/綜合/醫案 → books
    book_manifest.csv / .json
    chapter_manifest.csv / .json
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..config import HermesConfig
from ..protocol import ROOT_CATEGORY, SUBCATEGORY_MAP, category_path
from ..utils import ensure_dir, write_json
from .parser import ParsedBook, book_short_id, parse_book_text


def _read_book_dir(book_dir: Path) -> str:
    """Concatenate a book's txt files in natural reading order."""
    files = sorted(book_dir.glob("*.txt"), key=_natural_key)
    return "\n\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files)


def _natural_key(p: Path):
    import re
    parts = re.split(r"(\d+)", p.stem)
    return [int(x) if x.isdigit() else x for x in parts]


class CatalogAgent:
    name = "CatalogAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def iter_book_dirs(self):
        raw = self.config.corpus_raw_dir
        for cat_dir in sorted(raw.iterdir() if raw.exists() else []):
            if not cat_dir.is_dir():
                continue
            books_root = cat_dir / "書籍" if (cat_dir / "書籍").exists() else cat_dir
            for book_dir in sorted(books_root.iterdir()):
                if book_dir.is_dir() and any(book_dir.glob("*.txt")):
                    yield cat_dir.name, book_dir

    def parse_book(self, raw_category: str, book_dir: Path) -> tuple[dict, ParsedBook]:
        text = _read_book_dir(book_dir)
        parsed = parse_book_text(text, fallback_title=book_dir.name)
        meta_cat = parsed.raw_category or raw_category
        sub = SUBCATEGORY_MAP.get(raw_category, SUBCATEGORY_MAP.get(meta_cat, raw_category))
        short = book_short_id(book_dir.name, parsed.title)
        record = {
            "book_id": f"BOOK_{short}",
            "book_short": short,
            "book_title": parsed.title or book_dir.name,
            "dir_name": book_dir.name,
            "author": parsed.author,
            "dynasty": parsed.dynasty,
            "raw_category": raw_category,
            "meta_category": meta_cat,
            "subcategory": sub,
            "category_path": category_path(raw_category),
            "book_type": parsed.book_type(),
            "quality": parsed.meta.get("品質", ""),
            "edition": parsed.meta.get("版本", ""),
            "file_count": len(list(book_dir.glob("*.txt"))),
            "path": str(book_dir),
        }
        return record, parsed

    # ------------------------------------------------------------------
    def build(self) -> dict:
        books: list[dict] = []
        chapters: list[dict] = []
        tree: dict = {ROOT_CATEGORY: {}}

        for raw_category, book_dir in self.iter_book_dirs():
            record, parsed = self.parse_book(raw_category, book_dir)
            books.append(record)
            sub = record["subcategory"]
            tree[ROOT_CATEGORY].setdefault(sub, []).append(
                {"book_id": record["book_id"], "book_title": record["book_title"],
                 "author": record["author"], "dynasty": record["dynasty"],
                 "book_type": record["book_type"]})
            ch_idx = 0
            for sec in parsed.sections:
                if sec.level < 2 or not sec.paragraphs:
                    continue
                ch_idx += 1
                chapters.append({
                    "chapter_id": f"CH_{record['book_short']}_{ch_idx:03d}",
                    "book_id": record["book_id"],
                    "book_title": record["book_title"],
                    "chapter_title": sec.title,
                    "level": sec.level,
                    "paragraphs": len(sec.paragraphs),
                    "subcategory": sub,
                })

        mdir = ensure_dir(self.config.manifests_dir)
        write_json(mdir / "catalog_tree.json", tree)
        write_json(mdir / "book_manifest.json", books)
        write_json(mdir / "chapter_manifest.json", chapters)
        _write_csv(mdir / "book_manifest.csv", books)
        _write_csv(mdir / "chapter_manifest.csv", chapters)
        return {"books": len(books), "chapters": len(chapters),
                "subcategories": sorted(tree[ROOT_CATEGORY].keys())}


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    keys = [k for k in rows[0] if not isinstance(rows[0][k], (list, dict))]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
