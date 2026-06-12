"""Illustrative psoriasis (白疕/癬) sample corpus.

The bundled 傷寒/金匱 corpus contains almost no dermatology, so this small set
of well-known classical excerpts lets the psoriasis pipeline run end-to-end as
a demonstration.  Each unit is flagged `sample: true` with explicit
provenance — in production point the pipeline at a vetted 外科/本草 corpus
(`hermes import <外科 corpus>` then `hermes disease run --use-corpus`) rather
than relying on these excerpts.  Evidence-span substring guarantees hold
against these raw_texts exactly as they do for any corpus.
"""

from __future__ import annotations

from ..protocol import ROOT_CATEGORY
from ..schemas import SourceUnit

# (book, chapter, dynasty, author, year, raw_text, text_type)
_SAMPLES = [
    ("諸病源候論", "瘡病諸候·乾癬候", "隋", "巢元方", 610,
     "乾癬，但有匡郭，皮枯索，痒，搔之白屑出是也。皆是風濕邪氣，客於腠理，"
     "復值寒濕，與血氣相搏所生。", "original"),
    ("諸病源候論", "瘡病諸候·濕癬候", "隋", "巢元方", 610,
     "濕癬者，亦有匡郭，如蟲行，浸淫，赤濕，痒，搔之多汁成瘡，是其風毒氣淺，"
     "濕氣多故也。", "original"),
    ("諸病源候論", "瘡病諸候·白癬候", "隋", "巢元方", 610,
     "白癬之狀，白色，硿硿然而癢。此由風邪折於肌膚，血氣不潤所生也。", "original"),
    ("醫宗金鑒", "外科心法要訣·白疕", "清", "吳謙等", 1742,
     "白疕，俗名蛇虱，生於皮膚，形如疹疥，色白而癢，搔起白皮。由風邪客於皮膚，"
     "血燥不能榮養所致。", "original"),
    ("外科大成", "松皮癬", "清", "祁坤", 1665,
     "松皮癬，狀如蒼松之皮，紅白斑點相連，時時作癢。", "original"),
    ("外科證治全書", "白疕", "清", "許克昌", 1831,
     "白疕，皮膚燥癢，起如疹疥而色白，搔之屑起，漸至成片，由血虛風燥所致，"
     "治宜養血潤燥祛風。", "original"),
    ("瘍醫大全", "牛皮癬門", "清", "顧世澄", 1760,
     "牛皮癬，狀如牛項之皮，厚而且堅，頑癬之類也，搔之不知痛癢，宜外用殺蟲潤燥之藥。",
     "original"),
    ("外科正宗", "頑癬", "明", "陳實功", 1617,
     "頑癬者，抓之全然不痛，此因風濕凝聚生蟲，故頑麻木而難愈，宜以殺蟲之藥外擦。",
     "original"),
    # a deliberate differential (should be excluded): 圆癣/金钱癣 = 真菌感染
    ("外科證治全書", "圓癬", "清", "許克昌", 1831,
     "圓癬者，狀如錢文，圓而有匡郭，多由濕熱生蟲所致，俗名金錢癬，與白疕不同。",
     "original"),
    # arthropathic-flavoured note
    ("醫宗金鑒", "外科心法要訣·白疕附", "清", "吳謙等", 1742,
     "白疕日久，風毒入於筋骨，四肢骨節疼痛，屈伸不利者，乃血燥兼風濕入絡所致。",
     "original"),
]


def load_sample_units() -> list[SourceUnit]:
    from ..knowledge.entities import EntityExtractorAgent
    ent = EntityExtractorAgent()
    units: list[SourceUnit] = []
    for i, (book, chapter, dynasty, author, year, raw, ttype) in enumerate(_SAMPLES, 1):
        bid = f"BOOK_PSO_SAMPLE_{abs(hash(book)) % 1000:03d}"
        units.append(SourceUnit(
            source_unit_id=f"SU_PSO_SAMPLE_{i:04d}",
            category_path=[ROOT_CATEGORY, "外科"],
            book_id=bid,
            book_title=book,
            book_type="original",
            chapter_id=f"CH_PSO_SAMPLE_{i:04d}",
            chapter_title=chapter,
            seq=0,
            raw_text=raw,
            text_type=ttype,
            entities=ent.extract(raw),
            meta={"sample": True, "dynasty": dynasty, "author": author,
                  "year": year, "provenance": f"{book}·{chapter}"},
        ))
    return units
