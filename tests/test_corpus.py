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
