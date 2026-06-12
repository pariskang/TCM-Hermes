"""Illustrative per-disease sample corpora.

The bundled 傷寒/金匱 corpus is thin on 外科/骨傷, so each disease ships a small
set of well-known classical excerpts so its pipeline runs end-to-end as a
demonstration.  Every unit is flagged `sample: true` with explicit provenance —
in production point the pipeline at a vetted 外科/本草/骨傷 corpus
(`hermes import <corpus>` → `hermes segment` → `hermes disease run --use-corpus
--no-sample`).  Evidence-span substring guarantees hold against these raw_texts
exactly as for any corpus.

Note on 类风湿: 金匮「中風歷節病脈證並治」is already in the main corpus, so
`hermes disease run --disease 类风湿 --use-corpus` surfaces *real* 歷節 条文 in
addition to (or instead of) these samples.
"""

from __future__ import annotations

from ..protocol import ROOT_CATEGORY
from ..schemas import SourceUnit

# disease_id -> [(book, chapter, dynasty, author, year, raw_text, text_type)]
_SAMPLES: dict[str, list] = {
    "psoriasis": [
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
        ("外科證治全書", "圓癬", "清", "許克昌", 1831,
         "圓癬者，狀如錢文，圓而有匡郭，多由濕熱生蟲所致，俗名金錢癬，與白疕不同。",
         "original"),
        ("醫宗金鑒", "外科心法要訣·白疕附", "清", "吳謙等", 1742,
         "白疕日久，風毒入於筋骨，四肢骨節疼痛，屈伸不利者，乃血燥兼風濕入絡所致。",
         "original"),
    ],
    "osteoporosis": [
        ("黃帝內經素問", "痿論", "戰國", "佚名", -200,
         "腎氣熱，則腰脊不舉，骨枯而髓減，發為骨痿。", "original"),
        ("黃帝內經素問", "脈要精微論", "戰國", "佚名", -200,
         "腰者腎之府，轉搖不能，腎將憊矣；膝者筋之府，屈伸不能，行則僂附，筋將憊矣；"
         "骨者髓之府，不能久立，行則振掉，骨將憊矣。", "original"),
        ("黃帝內經素問", "上古天真論", "戰國", "佚名", -200,
         "女子七七，任脈虛，太衝脈衰少，天癸竭……丈夫八八，則齒髮去，腎臟衰，"
         "形體皆極，則齒髮去。", "original"),
        ("金匱要略方論", "血痹虛勞病脈證並治", "漢", "張仲景", 219,
         "虛勞腰痛，少腹拘急，小便不利者，八味腎氣丸主之。", "formula"),
        ("諸病源候論", "虛勞病諸候·骨極候", "隋", "巢元方", 610,
         "骨極，令人痠削，齒苦痛，手足煩疼，不可以立，不欲行動。", "original"),
        ("景岳全書", "非風·論治", "明", "張介賓", 1624,
         "腰痛之虛者，十居八九，蓋腰為腎之府，腎虛則精髓不足，骨痿而腰脊不舉，"
         "治宜補腎填精壯骨，左歸右歸之屬。", "original"),
        ("醫宗金鑒", "雜病心法·腰痛", "清", "吳謙等", 1742,
         "腰痛拘急，痠軟無力，遇勞則甚，臥則減者，腎虛也，宜補腎益精，杜仲、續斷、"
         "牛膝、熟地黃之類。", "original"),
        ("丹溪心法", "痿", "元", "朱震亨", 1481,
         "骨痿者，腎水不能勝心火，足不任身，腰脊不舉，宜補腎益陰，虎潛丸主之。",
         "original"),
    ],
    "rheumatoid_arthritis": [
        ("金匱要略方論", "中風歷節病脈證並治", "漢", "張仲景", 219,
         "諸肢節疼痛，身體尪羸，腳腫如脫，頭眩短氣，溫溫欲吐，桂枝芍藥知母湯主之。",
         "formula"),
        ("金匱要略方論", "中風歷節病脈證並治", "漢", "張仲景", 219,
         "病歷節不可屈伸，疼痛，烏頭湯主之。", "formula"),
        ("金匱要略方論", "中風歷節病脈證並治", "漢", "張仲景", 219,
         "寸口脈沉而弱，沉即主骨，弱即主筋，沉即為腎，弱即為肝。汗出入水中，"
         "如水傷心，歷節黃汗出，故曰歷節。", "original"),
        ("諸病源候論", "風病諸候·歷節風候", "隋", "巢元方", 610,
         "歷節風之狀，短氣，自汗出，歷節疼痛不可忍，屈伸不得是也。由飲酒腠理開，"
         "汗出當風所致，亦有血氣虛，受風邪而得之者。", "original"),
        ("濟生方", "痹", "宋", "嚴用和", 1253,
         "痹者，風寒濕三氣雜至，合而為痹。其風氣勝者為行痹，寒氣勝者為痛痹，"
         "濕氣勝者為著痹。", "original"),
        ("醫宗金鑒", "雜病心法·痹病", "清", "吳謙等", 1742,
         "鶴膝風者，膝腫粗大而股脛枯細，狀如鶴膝，痛不可屈伸，乃風寒濕邪深入"
         "筋骨所致，宜大防風湯溫散補益。", "original"),
        ("類證治裁", "痹證論治", "清", "林珮琴", 1839,
         "久痹不已，肢節腫大，屈伸不利，痰瘀互結，肝腎虧虛，治宜益肝腎、養氣血、"
         "祛風除濕、活血通絡。", "original"),
        ("外科正宗", "鶴膝風", "明", "陳實功", 1617,
         "鶴膝風者，胻細而膝腫是也，初起寒熱交作，膝痛如虎咬，不能屈伸。", "original"),
    ],
}


def load_sample_units(disease_id: str = "psoriasis") -> list[SourceUnit]:
    from ..knowledge.entities import EntityExtractorAgent
    ent = EntityExtractorAgent()
    samples = _SAMPLES.get(disease_id, [])
    units: list[SourceUnit] = []
    for i, (book, chapter, dynasty, author, year, raw, ttype) in enumerate(samples, 1):
        bid = f"BOOK_{disease_id.upper()}_SAMPLE_{abs(hash(book)) % 1000:03d}"
        units.append(SourceUnit(
            source_unit_id=f"SU_{disease_id.upper()}_SAMPLE_{i:04d}",
            category_path=[ROOT_CATEGORY, "外科" if disease_id == "psoriasis"
                           else "骨傷" if disease_id == "osteoporosis" else "痹病"],
            book_id=bid,
            book_title=book,
            book_type="original",
            chapter_id=f"CH_{disease_id.upper()}_SAMPLE_{i:04d}",
            chapter_title=chapter,
            seq=0,
            raw_text=raw,
            text_type=ttype,
            entities=ent.extract(raw),
            meta={"sample": True, "dynasty": dynasty, "author": author,
                  "year": year, "provenance": f"{book}·{chapter}"},
        ))
    return units
