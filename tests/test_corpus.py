"""Parser / catalog / segmenter behaviour on the jicheng format."""

from hermes.corpus.parser import parse_book_text, strip_markup, book_short_id

SAMPLE = """======傷寒論(宋本)======

<book>
書名=傷寒論(宋本)
作者=張仲景
朝代=東漢
分類=傷寒
品質=90%
</book>

=====卷第二=====

====辨太陽病脈證並治上第五====

太陽之為病，脈浮，頭項強痛而惡寒。

太陽病，發熱，汗出，惡風，脈緩者，名為中風。

<#/>太陽中風，陽浮而陰弱，嗇嗇惡寒，淅淅惡風，翕翕發熱，鼻鳴乾嘔者，桂枝湯主之。
"""


def test_book_metadata():
    book = parse_book_text(SAMPLE)
    assert book.title == "傷寒論(宋本)"
    assert book.author == "張仲景"
    assert book.dynasty == "東漢"
    assert book.raw_category == "傷寒"
    assert book.book_type() == "original"


def test_sections_and_paragraphs():
    book = parse_book_text(SAMPLE)
    ch = [s for s in book.sections if s.level == 3]
    assert ch and ch[0].title == "辨太陽病脈證並治上第五"
    assert len(ch[0].paragraphs) == 3
    # clause markers stripped, text preserved verbatim
    assert ch[0].paragraphs[2]["text"].startswith("太陽中風")
    assert "<#" not in ch[0].paragraphs[2]["text"]


def test_strip_markup():
    assert strip_markup("葛<j>弘</j>景") == "葛弘景"
    assert strip_markup("參見[[book:傷寒論_條文版:]]") == "參見傷寒論_條文版"
    assert strip_markup("<#12/>太陽病") == "太陽病"


def test_commentary_book_detection():
    text = SAMPLE.replace("傷寒論(宋本)", "註解傷寒論").replace("分類=傷寒",
                                                          "分類=傷寒")
    book = parse_book_text(text)
    assert book.book_type() == "commentary"


def test_book_short_id_aliases():
    assert book_short_id("傷寒論_宋本", "傷寒論(宋本)") == "SHL_SONGBEN"
    assert book_short_id("金匱要略方論", "金匱要略方論") == "JGYL_FANGLUN"
    generated = book_short_id("某某不知名醫書", "某某不知名醫書")
    assert generated.startswith("B") and len(generated) == 9


def test_segmenter_types(cfg):
    import conftest as fx
    from hermes.corpus.segmenter import SegmenterAgent
    seg = SegmenterAgent(cfg)
    assert seg.classify_paragraph(fx.FORMULA_BLOCK, "original", "X") == "formula"
    assert seg.classify_paragraph(fx.GUIZHI_CLAUSE, "original", "X") == "original"
    assert seg.classify_paragraph("成氏曰：此乃營衛不和之故。", "original", "X") \
        == "commentary"
    assert seg.classify_paragraph("一本作「脈浮緊」。校勘記。", "original", "X") \
        == "variant"
    assert seg.classify_paragraph("自序云云", "original", "自序") == "preface"


# ---------------------------------------------------------------------------
# public-archive flat layout (raw/<書名>/*.txt) — classified via 分類= metadata

WAIKE_SAMPLE = """======外科發揮======

<book>
書名=外科發揮
作者=薛己
朝代=明
分類=外科
</book>

=====卷一=====

====腫瘍====

瘡瘍腫痛，此毒氣凝滯也。
"""


def _write_flat_book(raw_dir, dir_name, text):
    book_dir = raw_dir / dir_name
    book_dir.mkdir(parents=True)
    (book_dir / "index.txt").write_text(text, encoding="utf-8")


def test_catalog_flat_layout_uses_metadata(cfg):
    import json
    from hermes.corpus.catalog import CatalogAgent
    _write_flat_book(cfg.corpus_raw_dir, "傷寒論_宋本", SAMPLE)
    result = CatalogAgent(cfg).build()
    assert result["books"] == 1
    assert result["subcategories"] == ["傷寒"]
    books = json.loads((cfg.manifests_dir / "book_manifest.json")
                       .read_text(encoding="utf-8"))
    assert books[0]["category_path"] == ["傷寒金匱類", "傷寒"]
    assert books[0]["book_title"] == "傷寒論(宋本)"


def test_catalog_nested_layout_unchanged(cfg):
    import json
    from hermes.corpus.catalog import CatalogAgent
    book_dir = cfg.corpus_raw_dir / "傷寒" / "書籍" / "傷寒論_宋本"
    book_dir.mkdir(parents=True)
    (book_dir / "index.txt").write_text(SAMPLE, encoding="utf-8")
    result = CatalogAgent(cfg).build()
    assert result["books"] == 1
    books = json.loads((cfg.manifests_dir / "book_manifest.json")
                       .read_text(encoding="utf-8"))
    assert books[0]["category_path"] == ["傷寒金匱類", "傷寒"]


def test_segmenter_flat_layout_and_category_filter(cfg):
    import json
    from hermes.corpus.segmenter import SegmenterAgent
    _write_flat_book(cfg.corpus_raw_dir, "傷寒論_宋本", SAMPLE)
    _write_flat_book(cfg.corpus_raw_dir, "外科發揮", WAIKE_SAMPLE)
    stats = SegmenterAgent(cfg).run(
        categories=["傷寒", "金匱", "傷寒 金匱", "醫案 傷寒 金匱"])
    # the 外科 book is filtered out by its 分類= metadata
    assert stats["books"] == 1
    files = list(cfg.source_units_dir.glob("BOOK_*.jsonl"))
    assert len(files) == 1
    unit = json.loads(files[0].read_text(encoding="utf-8").splitlines()[0])
    assert unit["category_path"] == ["傷寒金匱類", "傷寒"]


def test_segmenter_full_run_drops_stale_source_units(cfg):
    from hermes.corpus.segmenter import SegmenterAgent
    _write_flat_book(cfg.corpus_raw_dir, "傷寒論_宋本", SAMPLE)
    stale = cfg.source_units_dir / "BOOK_STALE.jsonl"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("{}\n", encoding="utf-8")
    SegmenterAgent(cfg).run()
    assert not stale.exists()          # full run reconciles the store
    assert list(cfg.source_units_dir.glob("BOOK_*.jsonl"))

    stale.write_text("{}\n", encoding="utf-8")
    SegmenterAgent(cfg).run(books=["傷寒論_宋本"])
    assert stale.exists()              # partial (--books) run keeps others


def test_download_416_means_already_complete(cfg, monkeypatch):
    import urllib.error
    import urllib.request
    from hermes.corpus.downloader import DownloaderAgent
    dest = cfg.data_dir / "downloads" / "book.7z"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"x" * 16)

    def raise_416(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 416,
                                     "Requested Range Not Satisfiable", None, None)

    monkeypatch.setattr(urllib.request, "urlopen", raise_416)
    out = DownloaderAgent(cfg).download(url="https://example.invalid/book.7z",
                                        dest=dest)
    assert out == dest
    assert dest.read_bytes() == b"x" * 16
