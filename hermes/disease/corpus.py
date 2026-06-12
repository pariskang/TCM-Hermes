"""DiseaseCorpusBuilder — build a separate 外科/溫病 corpus for disease mining.

The 伤寒/金匮 rule-mining corpus stays untouched; this extracts the relevant
外科/溫病 books from the 中醫笈成 7z (or an extracted tree) into an isolated
workspace under data/disease_corpus/<category>/ and segments them into their
own source-unit store, which `hermes disease run --corpus <category>` reads.

Curated book lists cover the bundled diseases (白疕/湿疮 → 外科; 温病 → 溫病);
pass explicit --books to override.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from ..config import HermesConfig
from ..corpus.catalog import CatalogAgent
from ..corpus.segmenter import SegmenterAgent
from ..protocol import JICHENG_CORPUS_URL

# canonical 外科/皮肤 sources containing 白疕/疥/癬/浸淫瘡/旋耳瘡/四彎風…
EXTERNAL_BOOKS = [
    "外科正宗", "外科大成", "外科證治全書", "醫宗金鑑", "瘍科心得集", "瘍醫大全",
    "外科啟玄", "外科理例", "外科精義", "外科精要", "外科樞要", "外科全生集",
    "外科十法", "立齋外科發揮", "萬氏秘傳外科心法", "外科醫鏡", "外科選要",
    "外科方外奇方", "外科集驗方",
]
# canonical 溫病 sources (叶天士/吴鞠通/薛雪/王孟英…)
WARM_BOOKS = [
    "溫病條辨", "溫熱論", "溫熱經緯", "溫疫論", "時病論", "濕熱病篇",
    "溫熱暑疫全書", "外感溫熱篇", "溫熱逢源", "六因條辨", "廣溫疫論",
    "溫病指南", "溫病正宗", "廣瘟疫論", "增訂葉評傷暑全書", "松峰說疫",
]

CATEGORY_BOOKS = {
    "外科": EXTERNAL_BOOKS,
    "溫病": WARM_BOOKS, "温病": WARM_BOOKS,
}


class DiseaseCorpusBuilder:
    name = "DiseaseCorpusBuilder"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    # ------------------------------------------------------------------
    def _sub_config(self, category: str) -> HermesConfig:
        # isolated data dir so the 伤寒金匮 corpus and rules are never touched
        cat = {"温病": "溫病"}.get(category, category)
        return replace(self.config,
                       data_dir=self.config.data_dir / "disease_corpus" / cat)

    def source_units_dir(self, category: str) -> Path:
        return self._sub_config(category).source_units_dir

    # ------------------------------------------------------------------
    def build_from_tree(self, tree: str | Path, category: str,
                        books: list[str] | None = None) -> dict:
        """Import already-extracted book dirs (book_name/*.txt) under category."""
        cat = {"温病": "溫病"}.get(category, category)
        sub = self._sub_config(cat)
        raw_cat = sub.corpus_raw_dir / cat / "書籍"
        raw_cat.mkdir(parents=True, exist_ok=True)
        wanted = books or CATEGORY_BOOKS.get(cat, [])
        tree = Path(tree)
        copied = []
        for child in sorted(tree.iterdir()):
            if not child.is_dir():
                continue
            if wanted and child.name not in wanted:
                continue
            dest = raw_cat / child.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(child, dest)
            copied.append(child.name)
        return self._finalize(sub, cat, copied)

    def build_from_7z(self, archive: str | Path | None, category: str,
                      books: list[str] | None = None,
                      download: bool = False) -> dict:
        """Extract selected books from the jicheng 7z into the category corpus."""
        import py7zr  # optional dependency

        cat = {"温病": "溫病"}.get(category, category)
        sub = self._sub_config(cat)
        raw_cat = sub.corpus_raw_dir / cat / "書籍"
        raw_cat.mkdir(parents=True, exist_ok=True)
        wanted = books or CATEGORY_BOOKS.get(cat, [])

        archive = Path(archive) if archive else \
            self.config.data_dir / "downloads" / Path(JICHENG_CORPUS_URL).name
        if not archive.exists() and download:
            from ..corpus.downloader import DownloaderAgent
            archive = DownloaderAgent(self.config).download(dest=archive)
        if not archive.exists():
            raise FileNotFoundError(
                f"corpus archive not found: {archive}; pass --from-7z PATH or "
                f"--download, or use --from-tree DIR")

        staging = sub.data_dir / "_staging"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True, exist_ok=True)
        with py7zr.SevenZipFile(archive) as z:
            names = z.getnames()
            targets = [n for n in names
                       if any(n == b or n.startswith(b + "/") for b in wanted)]
            z.extract(path=staging, targets=targets)

        copied = []
        for b in wanted:
            src = staging / b
            if src.is_dir() and any(src.glob("*.txt")):
                dest = raw_cat / b
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
                copied.append(b)
        shutil.rmtree(staging, ignore_errors=True)
        return self._finalize(sub, cat, copied)

    # ------------------------------------------------------------------
    def _finalize(self, sub: HermesConfig, category: str,
                  books: list[str]) -> dict:
        catalog = CatalogAgent(sub).build()
        seg = SegmenterAgent(sub).run()
        return {
            "category": category,
            "books_imported": books,
            "book_count": len(books),
            "source_units": seg["source_units"],
            "source_units_dir": str(sub.source_units_dir),
            "by_type": seg["by_type"],
            "catalog": catalog,
        }
