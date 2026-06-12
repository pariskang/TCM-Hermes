"""DownloaderAgent — acquire and version the 中醫笈成 corpus.

Sources supported:
  * remote 7z archive (https://jicheng.tw/files/jcw/book-20180111.7z)
  * local .7z / .zip archives
  * already-extracted directory trees (category/書籍/book/*.txt)

Every import produces a corpus_version record and a file-hash report so the
provenance of every byte of evidence is auditable.
"""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

from ..config import HermesConfig
from ..protocol import JICHENG_CORPUS_URL, SUBCATEGORY_MAP
from ..utils import ensure_dir, read_json, sha256_file, utc_now, write_json


class DownloaderAgent:
    name = "DownloaderAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    # ------------------------------------------------------------------
    def download(self, url: str = JICHENG_CORPUS_URL, dest: str | Path | None = None,
                 max_retries: int = 3) -> Path:
        """Download a corpus archive with resume support."""
        dest = Path(dest) if dest else self.config.data_dir / "downloads" / Path(url).name
        ensure_dir(dest.parent)
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "TCM-Hermes/5.0"})
                existing = dest.stat().st_size if dest.exists() else 0
                if existing:
                    req.add_header("Range", f"bytes={existing}-")
                with urllib.request.urlopen(req, timeout=120) as resp:
                    total = resp.headers.get("Content-Length")
                    mode = "ab" if existing and resp.status == 206 else "wb"
                    with open(dest, mode) as f:
                        shutil.copyfileobj(resp, f)
                return dest
            except Exception:
                if attempt == max_retries - 1:
                    raise
        return dest

    # ------------------------------------------------------------------
    def import_archive(self, archive: str | Path, categories: list[str] | None = None) -> Path:
        """Extract a zip/7z archive into corpus_raw and register the version."""
        archive = Path(archive)
        raw = ensure_dir(self.config.corpus_raw_dir)
        if archive.suffix == ".zip":
            with zipfile.ZipFile(archive) as z:
                z.extractall(raw)
        elif archive.suffix == ".7z":
            import py7zr  # optional dependency
            with py7zr.SevenZipFile(archive) as z:
                if categories:
                    names = z.getnames()
                    targets = [n for n in names
                               if any(n == c or n.startswith(c + "/") for c in categories)]
                    z.extract(path=raw, targets=targets)
                else:
                    z.extractall(raw)
        else:
            raise ValueError(f"unsupported archive type: {archive}")
        self._register_version(source=str(archive))
        return raw

    def import_tree(self, tree: str | Path) -> Path:
        """Copy an extracted category tree (分類/書籍/書名/*.txt) into corpus_raw."""
        tree = Path(tree)
        raw = ensure_dir(self.config.corpus_raw_dir)
        for child in sorted(tree.iterdir()):
            if not child.is_dir():
                continue
            dest = raw / child.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(child, dest)
        self._register_version(source=str(tree))
        return raw

    # ------------------------------------------------------------------
    def _register_version(self, source: str) -> dict:
        raw = self.config.corpus_raw_dir
        files = sorted(p for p in raw.rglob("*.txt"))
        hash_report = []
        seen_hashes: dict[str, str] = {}
        duplicates = []
        for p in files:
            digest = sha256_file(p)
            rel = str(p.relative_to(raw))
            hash_report.append({"path": rel, "sha256": digest, "bytes": p.stat().st_size})
            if digest in seen_hashes:
                duplicates.append({"path": rel, "duplicate_of": seen_hashes[digest]})
            else:
                seen_hashes[digest] = rel
        version = {
            "corpus_version": f"jicheng-{utc_now()[:10]}",
            "imported_at": utc_now(),
            "source": source,
            "file_count": len(files),
            "total_bytes": sum(r["bytes"] for r in hash_report),
            "duplicate_files": duplicates,
            "categories": sorted({p.parts[0] for p in
                                  (f.relative_to(raw) for f in files)}),
        }
        write_json(self.config.manifests_dir / "corpus_version.json", version)
        write_json(self.config.manifests_dir / "file_hash_report.json", hash_report)
        return version

    def corpus_version(self) -> dict | None:
        return read_json(self.config.manifests_dir / "corpus_version.json")

    def known_subcategories(self) -> list[str]:
        raw = self.config.corpus_raw_dir
        if not raw.exists():
            return []
        return [d.name for d in sorted(raw.iterdir())
                if d.is_dir() and (d.name in SUBCATEGORY_MAP or (d / "書籍").exists())]
