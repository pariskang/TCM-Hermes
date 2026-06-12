"""InitialRuleExtractorAgent — mine IF/THEN rules from SourceUnits.

The heuristic engine recognises the canonical sentence grammars of 傷寒/金匱
clauses; every extracted rule carries an evidence_span that is an exact
substring of the source unit's raw_text (no evidence, no rule).  The optional
LLM backend follows the same contract via RULE_EXTRACTOR_PROMPT.
"""

from __future__ import annotations

import re

from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..knowledge.lexicon import (CONTRAINDICATION_PATTERN, LEXICON,
                                 MISTREATMENT_PATTERN, TRANSMISSION_PATTERN)
from ..schemas import InitialRule, SourceUnit
from ..utils import clamp, split_sentences
from . import prompts
from .backends import HeuristicBackend

_FORMULA_CONCLUSION = re.compile(
    rf"((?:[一-鿿]{{1,12}})[{ '湯散丸飲煎膏丹' }])(?:方)?主之")
_FORMULA_ADVISORY = re.compile(
    rf"(?:宜|可與|與|當與|屬|可服|急與)((?:[一-鿿]{{1,12}})[{ '湯散丸飲煎膏丹' }])")
_DISEASE_DEFINITION = re.compile(r"([一-鿿]{2,4})之為病[，,]?")
_PULSE_PATTERN_RULE = re.compile(
    r"(脈[一-鿿]{1,6}?)(?:者)?[，,]?(?:此)?(為|名曰|名為|是為)([一-鿿]{1,6})")
_FORMULA_BLOCK_HEAD = re.compile(r"^([一-鿿]{2,12}[湯散丸飲煎膏丹])方")
_PROGNOSIS_TAIL = re.compile(
    r"(必自愈|自愈|欲解|欲愈|必愈|不治|難治|必死|死|可治|為欲解)[。]?$")

_SPECIAL_PULSE_SPLITS = {
    "陽浮而陰弱": ["陽浮", "陰弱"],
    "脈陰陽俱緊": ["脈陰陽俱緊"],
}

CONF = {
    "formula_zhuzhi": 0.90, "formula_advisory": 0.80, "contraindication": 0.88,
    "mistreatment": 0.80, "prognosis": 0.75, "transmission": 0.78,
    "disease_definition": 0.92, "pulse_pattern": 0.80,
    "composition": 0.95, "preparation": 0.95,
}


class InitialRuleExtractorAgent:
    name = "InitialRuleExtractorAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend or HeuristicBackend()
        self.entities = EntityExtractorAgent()
        self._seq: dict[str, int] = {}

    # ------------------------------------------------------------------
    def extract(self, unit: SourceUnit) -> list[InitialRule]:
        if unit.text_type in ("preface", "toc"):
            return []
        if getattr(self.backend, "kind", "heuristic") == "anthropic":
            try:
                return self._extract_llm(unit)
            except Exception:
                pass  # deterministic fallback keeps the pipeline running
        return self._extract_heuristic(unit)

    # ------------------------------------------------------------------
    def _next_id(self, unit: SourceUnit) -> str:
        short = unit.book_id.removeprefix("BOOK_")
        self._seq[short] = self._seq.get(short, 0) + 1
        return f"IR_{short}_{self._seq[short]:06d}"

    def _evidence_type(self, unit: SourceUnit) -> str:
        return {"original": "original_text", "commentary": "commentary",
                "formula": "formula_block", "variant": "variant",
                "case": "case_record"}.get(unit.text_type, "original_text")

    def _base_rule(self, unit: SourceUnit, rule_type: str, span: str,
                   if_cond: dict, then_con: dict, conf: float,
                   pattern: str, interpretation: str) -> InitialRule:
        rule = InitialRule(
            initial_rule_id=self._next_id(unit),
            category_path=list(unit.category_path),
            book_id=unit.book_id,
            book_title=unit.book_title,
            book_type=unit.book_type,
            chapter_id=unit.chapter_id,
            chapter_title=unit.chapter_title,
            source_unit_id=unit.source_unit_id,
            rule_type=rule_type,
            if_conditions=if_cond,
            then_conclusions=then_con,
            evidence_span=span,
            # the extractor is optimistic about provenance; the adversarial
            # critic + repair loop is responsible for catching contamination
            evidence_type=self._evidence_type(unit),
            interpretation=interpretation,
            interpretation_level="original_text",
            model_confidence=clamp(conf),
            clause_no=unit.clause_no,
            status="extracted",
            extraction_pattern=pattern,
        )
        rule.log(self.name, "created", pattern=pattern)
        return rule

    # ------------------------------------------------------------------
    def _conditions_from(self, text: str) -> dict[str, list[str]]:
        pulses_raw = LEXICON.find_terms(text, LEXICON.pulses)
        pulses: list[str] = []
        for p in pulses_raw:
            pulses.extend(_SPECIAL_PULSE_SPLITS.get(p, [p]))
        for special, parts in _SPECIAL_PULSE_SPLITS.items():
            if special in text:
                for part in parts:
                    if part not in pulses:
                        pulses.append(part)
        diseases = LEXICON.find_terms(text, LEXICON.diseases)
        symptoms = [s for s in LEXICON.find_terms(text, LEXICON.symptoms)
                    if s not in diseases]
        return {
            "disease": diseases,
            "symptoms": symptoms,
            "pulse": pulses,
            "pathomechanism": LEXICON.find_terms(text, LEXICON.pathomechanisms),
        }

    @staticmethod
    def _span_until(sentences: list[str], idx: int, max_sents: int = 4) -> str:
        start = max(0, idx - (max_sents - 1))
        return "".join(sentences[start:idx + 1])

    # ------------------------------------------------------------------
    def _extract_heuristic(self, unit: SourceUnit) -> list[InitialRule]:
        text = unit.raw_text
        rules: list[InitialRule] = []

        if unit.text_type == "formula":
            rules.extend(self._extract_formula_block(unit))
            return rules

        sentences = split_sentences(text)
        consumed_formulas: set[str] = set()

        for i, sent in enumerate(sentences):
            # 1) 方證: …，X湯主之
            for m in _FORMULA_CONCLUSION.finditer(sent):
                formula = LEXICON._trim_formula(m.group(1))
                if len(formula) < 3:
                    continue
                span = self._span_until(sentences, i)
                cond_text = span[:span.rfind(formula)] if formula in span else span
                if_cond = self._conditions_from(cond_text)
                principles = LEXICON.formula_principles(formula)
                conf = CONF["formula_zhuzhi"]
                if not any(if_cond.values()):
                    conf -= 0.07
                if unit.text_type == "commentary":
                    conf -= 0.10
                rules.append(self._base_rule(
                    unit, "formula_indication_rule", span, if_cond,
                    {"formula": [formula], "treatment_principle": principles},
                    conf, "X主之",
                    f"見{ '、'.join((if_cond['disease'] or if_cond['symptoms'] or ['本條所述'])[:4]) }等，"
                    f"可歸入{formula}方證。"))
                consumed_formulas.add(formula)

            # 2) 方證(建議式): 宜X湯 / 可與X湯
            for m in _FORMULA_ADVISORY.finditer(sent):
                formula = LEXICON._trim_formula(m.group(1))
                if len(formula) < 3 or formula in consumed_formulas:
                    continue
                span = self._span_until(sentences, i)
                cond_text = span[:span.rfind(formula)] if formula in span else span
                if_cond = self._conditions_from(cond_text)
                conf = CONF["formula_advisory"]
                if unit.text_type == "commentary":
                    conf -= 0.10
                rules.append(self._base_rule(
                    unit, "formula_indication_rule", span, if_cond,
                    {"formula": [formula],
                     "treatment_principle": LEXICON.formula_principles(formula)},
                    conf, "宜/與X", f"本條建議使用{formula}。"))
                consumed_formulas.add(formula)

            # 3) 禁忌: 不可發汗/下/吐…
            m = CONTRAINDICATION_PATTERN.search(sent)
            if m:
                span = self._span_until(sentences, i, max_sents=2)
                if_cond = self._conditions_from(span[:m.start(0) + 1])
                rules.append(self._base_rule(
                    unit, "contraindication_rule", span, if_cond,
                    {"prohibition": [m.group(0)]},
                    CONF["contraindication"], "不可X",
                    f"本條明示禁忌：{m.group(0)}。"))

            # 4) 誤治: 若下之/反汗之 + 變證
            m = MISTREATMENT_PATTERN.search(sent)
            if m and not CONTRAINDICATION_PATTERN.search(sent[:m.start()] or ""):
                consequence = sent[m.end():].strip("，,。 ")
                if consequence:
                    span = self._span_until(sentences, i, max_sents=2)
                    if_cond = self._conditions_from(span[:span.find(m.group(0))]
                                                    if m.group(0) in span else span)
                    rules.append(self._base_rule(
                        unit, "mistreatment_rule", span, if_cond,
                        {"mistreatment": [m.group(0)],
                         "consequence": [consequence[:30]]},
                        CONF["mistreatment"], "誤治→變證",
                        f"誤行「{m.group(0)}」可致{consequence[:20]}。"))

            # 5) 預後: …必自愈/不治/死
            m = _PROGNOSIS_TAIL.search(sent.rstrip())
            if m:
                span = self._span_until(sentences, i, max_sents=2)
                if_cond = self._conditions_from(span[:span.rfind(m.group(1))])
                if any(if_cond.values()):
                    rules.append(self._base_rule(
                        unit, "prognosis_rule", span, if_cond,
                        {"prognosis": [m.group(1)]},
                        CONF["prognosis"], "預後判斷",
                        f"本條預後判斷：{m.group(1)}。"))

            # 6) 傳變
            m = TRANSMISSION_PATTERN.search(sent)
            if m:
                span = self._span_until(sentences, i, max_sents=2)
                if_cond = self._conditions_from(span[:span.find(m.group(0))]
                                                if m.group(0) in span else span)
                if any(if_cond.values()):
                    rules.append(self._base_rule(
                        unit, "transmission_rule", span, if_cond,
                        {"transmission": [m.group(0)]},
                        CONF["transmission"], "傳變",
                        f"本條提示傳變：{m.group(0)}。"))

            # 7) 病證定義: X之為病
            m = _DISEASE_DEFINITION.search(sent)
            if m:
                span = sent
                defining = sent[m.end():]
                if_cond = self._conditions_from(defining)
                if any(if_cond.values()):
                    rules.append(self._base_rule(
                        unit, "disease_definition_rule", span, if_cond,
                        {"disease": [m.group(1) + ("病" if not m.group(1).endswith("病")
                                                   and len(m.group(1)) <= 2 else "")]},
                        CONF["disease_definition"], "X之為病",
                        f"本條為{m.group(1)}的定義條文。"))

            # 8) 脈證: 脈X者，為Y
            m = _PULSE_PATTERN_RULE.search(sent)
            if m and "之為病" not in sent:
                pulse_term, label = m.group(1), m.group(3)
                span = sent
                rules.append(self._base_rule(
                    unit, "pulse_pattern_rule", span,
                    {"disease": [], "symptoms": [], "pulse": [pulse_term],
                     "pathomechanism": []},
                    {"pattern": [label]},
                    CONF["pulse_pattern"], "脈X為Y",
                    f"{pulse_term}提示{label}。"))

        return rules

    # ------------------------------------------------------------------
    def _extract_formula_block(self, unit: SourceUnit) -> list[InitialRule]:
        text = unit.raw_text
        rules: list[InitialRule] = []
        m = _FORMULA_BLOCK_HEAD.match(text)
        formula = LEXICON._trim_formula(m.group(1)) if m else ""
        if not formula:
            hits = LEXICON.find_formulas(text[:20])
            formula = hits[0] if hits else ""

        comp = self.entities.extract_composition(text)
        if comp and formula:
            prep_m = re.search(r"右[一二三四五六七八九十]+味", text)
            span_end = prep_m.start() if prep_m else len(text)
            span = text[:span_end].rstrip()
            if not span:        # composition listing absent → no evidence, no rule
                comp = []
        if comp and formula:
            rules.append(self._base_rule(
                unit, "formula_composition_rule", span, {},
                {"formula": [formula],
                 "composition": [f"{c['herb']}{c['dose']}" for c in comp]},
                CONF["composition"], "方劑組成",
                f"{formula}組成：{'、'.join(c['herb'] for c in comp)}。"))

        prep = self.entities.extract_preparation(text)
        if prep and formula and prep in text:
            rules.append(self._base_rule(
                unit, "preparation_rule", prep, {},
                {"formula": [formula], "preparation": [prep[:80]]},
                CONF["preparation"], "煎服法",
                f"{formula}煎服法見原文。"))
        return rules

    # ------------------------------------------------------------------
    def _extract_llm(self, unit: SourceUnit) -> list[InitialRule]:
        import json
        payload = json.dumps(unit.to_dict(), ensure_ascii=False)
        from .. import protocol
        out = self.backend.complete_json(
            prompts.RULE_EXTRACTOR_PROMPT +
            "\nControlled rule types: " + ", ".join(protocol.RULE_TYPES),
            payload, role="extractor")
        rules = []
        for rd in out.get("rules", []):
            span = rd.get("evidence_span", "")
            if not span or span not in unit.raw_text:
                continue  # no evidence, no rule
            rule = self._base_rule(
                unit, rd.get("rule_type", "formula_indication_rule"), span,
                rd.get("if_conditions", {}) or {},
                rd.get("then_conclusions", {}) or {},
                float(rd.get("model_confidence", 0.7)),
                "llm", rd.get("interpretation", ""))
            rule.interpretation_level = rd.get("interpretation_level", "original_text")
            rules.append(rule)
        return rules
