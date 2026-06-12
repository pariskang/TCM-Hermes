import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes.config import HermesConfig          # noqa: E402
from hermes.schemas import SourceUnit           # noqa: E402

GUIZHI_CLAUSE = ("太陽中風，陽浮而陰弱，陽浮者，熱自發，陰弱者，汗自出。"
                 "嗇嗇惡寒，淅淅惡風，翕翕發熱，鼻鳴乾嘔者，桂枝湯主之。")
TAIYANG_DEFINITION = "太陽之為病，脈浮，頭項強痛而惡寒。"
CONTRA_CLAUSE = "咽喉乾燥者，不可發汗。"
MISTREAT_CLAUSE = "太陽病，發熱惡寒者，若下之，必胸下結硬。"
FORMULA_BLOCK = ("桂枝湯方\n桂枝三兩（去皮） 芍藥三兩 甘草二兩（炙） 生薑三兩（切） "
                 "大棗十二枚（擘）\n右五味，㕮咀三味，以水七升，微火煮取三升，去滓。")
COMMENTARY_TEXT = ("成氏曰：營衛不和者，桂枝湯主之，所以調和營衛也。")


@pytest.fixture()
def cfg(tmp_path) -> HermesConfig:
    return HermesConfig(root=tmp_path)


def make_unit(raw_text: str, text_type: str = "original", seq: int = 0,
              book_type: str = "original", su_id: str = "SU_TEST_000001",
              subcategory: str = "傷寒") -> SourceUnit:
    from hermes.knowledge.entities import EntityExtractorAgent
    return SourceUnit(
        source_unit_id=su_id,
        category_path=["傷寒金匱類", subcategory],
        book_id="BOOK_TEST",
        book_title="傷寒論(宋本)",
        book_type=book_type,
        chapter_id="CH_TEST_001",
        chapter_title="辨太陽病脈證並治上",
        seq=seq,
        raw_text=raw_text,
        text_type=text_type,
        entities=EntityExtractorAgent().extract(raw_text),
    )


@pytest.fixture()
def guizhi_unit() -> SourceUnit:
    return make_unit(GUIZHI_CLAUSE)
