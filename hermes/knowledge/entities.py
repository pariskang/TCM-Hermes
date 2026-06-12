"""EntityExtractorAgent — lexicon-driven entity recognition for source units."""

from __future__ import annotations

import re

from .lexicon import LEXICON, CN_NUMS, DOSE_UNITS
from .s2t import to_traditional

# herb + dosage, e.g. 桂枝三兩（去皮） / 半夏半升，洗
_HERB_DOSE = re.compile(
    rf"([一-鿿]{{1,6}}?)([{CN_NUMS}十]+)({'|'.join(DOSE_UNITS)})")


class EntityExtractorAgent:
    name = "EntityExtractorAgent"

    def extract(self, text: str) -> dict[str, list[str]]:
        text = to_traditional(text)
        return {
            "disease": LEXICON.find_terms(text, LEXICON.diseases),
            "symptoms": LEXICON.find_terms(text, LEXICON.symptoms),
            "pulse": LEXICON.find_terms(text, LEXICON.pulses),
            "pathomechanism": LEXICON.find_terms(text, LEXICON.pathomechanisms),
            "treatment_principle": LEXICON.find_terms(text, LEXICON.principles),
            "formula": LEXICON.find_formulas(text),
            "herbs": LEXICON.find_terms(text, LEXICON.herbs),
        }

    def extract_composition(self, text: str) -> list[dict]:
        """Parse a formula block into herb/dose pairs."""
        out: list[dict] = []
        seen: set[str] = set()
        for m in _HERB_DOSE.finditer(text):
            cand, num, unit = m.group(1), m.group(2), m.group(3)
            herb = None
            for h in LEXICON.herbs:
                if cand.endswith(h):
                    herb = h
                    break
            if herb and herb not in seen:
                seen.add(herb)
                out.append({"herb": herb, "dose": f"{num}{unit}"})
        if not out:
            for h in LEXICON.find_terms(text, LEXICON.herbs):
                if h not in seen:
                    seen.add(h)
                    out.append({"herb": h, "dose": ""})
        return out

    def extract_preparation(self, text: str) -> str | None:
        """煎服法 sentence, e.g. 右五味，㕮咀，以水七升，微火煮取三升…"""
        m = re.search(r"(右[一二三四五六七八九十]+味[^。]*。?[^。]*。?)", text)
        if m:
            return m.group(1)
        m = re.search(r"(以水[一二三四五六七八九十百]+升[^。]*。)", text)
        return m.group(1) if m else None
