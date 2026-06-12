"""PatientEducationAgent — 患者教育与就诊辅助（绝不诊疗）.

Allowed: 中医概念通俗解释（附古籍文化背景）、症状日记结构化、就诊准备摘要、
医嘱理解辅导、风险信号提醒。Forbidden by SafetyGovernanceAgent: 诊断、处方、
剂量调整、停换药建议。Every output carries the patient disclaimer.
"""

from __future__ import annotations

from ..agents.safety import SafetyGovernanceAgent
from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..knowledge.lexicon import LEXICON
from ..rag.text_rag import ClassicalTextRAGAgent
from ..utils import utc_now


class PatientEducationAgent:
    name = "PatientEducationAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.safety = SafetyGovernanceAgent()
        self.entities = EntityExtractorAgent()
        self.rag = ClassicalTextRAGAgent(self.config)

    # ------------------------------------------------------------------
    def explain(self, query: str) -> dict:
        """中医概念通俗解释（教育性，非诊疗）."""
        verdict = self.safety.check_patient_query(query)
        if not verdict.allowed:
            return {"allowed": False, **verdict.to_dict()}

        from ..knowledge.s2t import to_traditional
        query_t = to_traditional(query)
        term = None
        for t in sorted(LEXICON.patient_glossary, key=len, reverse=True):
            if t in query_t:
                term = t
                break
        if term is None:
            ents = self.entities.extract(query)
            for k in ("disease", "formula", "pathomechanism"):
                if ents[k]:
                    term = ents[k][0]
                    break
        if term is None:
            return {"allowed": True, "term": None,
                    "answer": self.safety.wrap_patient_answer(
                        "我没有识别出明确的中医术语。您可以问我，比如：什么是太阳病？"
                        "医生说我营卫不和是什么意思？")}

        explanation = LEXICON.patient_glossary.get(
            term, f"「{term}」是中医古籍中的术语。下面给您看古籍原文片段帮助理解其语境。")
        quotes = []
        try:
            hits = self.rag.search_exact(term, limit=12,
                                         exclude_text_types=["commentary"])
            # 文化阅读引文优先出自原典而非注本
            hits.sort(key=lambda h: (h.source_unit.book_type != "original",
                                     -h.score))
            for h in hits[:2]:
                quotes.append({"book": h.source_unit.book_title,
                               "quote": h.source_unit.raw_text[:100]})
        except Exception:
            pass
        answer = f"**{term}**：{explanation}"
        if quotes:
            answer += "\n\n古籍原文（文化阅读）：\n" + "\n".join(
                f"> {q['quote']} ——《{q['book']}》" for q in quotes)
        answer += "\n\n建议：如这一术语来自您的诊疗过程，可以把疑问记下来，下次就诊时请医生结合您的情况解释。"
        return {"allowed": True, "term": term,
                "answer": self.safety.wrap_patient_answer(answer)}

    # ------------------------------------------------------------------
    def diary_summary(self, entries: list[dict]) -> dict:
        """症状日记 → 就诊摘要（entries: {date, symptoms, notes}）."""
        all_text = "；".join(f"{e.get('date', '')} {e.get('symptoms', '')} "
                            f"{e.get('notes', '')}" for e in entries)
        verdict = self.safety.check_patient_query(all_text)
        recognized = self.entities.extract(all_text)
        timeline = [{"date": e.get("date", f"第{i+1}条"),
                     "symptoms": e.get("symptoms", ""),
                     "notes": e.get("notes", "")} for i, e in enumerate(entries)]
        summary = {
            "generated_at": utc_now(),
            "entries": len(entries),
            "timeline": timeline,
            "recognized_symptoms": recognized["symptoms"],
            "questions_for_doctor": [
                "这些症状之间是否相关？最需要先处理哪一个？",
                "是否需要做进一步检查？",
                "目前的生活方式（饮食/睡眠/运动）需要怎样调整？",
            ],
            "urgent": verdict.urgent,
            "risk_notice": verdict.notice if verdict.urgent else "",
            "disclaimer": self.safety.wrap_patient_answer("").strip(),
        }
        return summary

    # ------------------------------------------------------------------
    def visit_preparation(self, chief_complaint: str, history: str = "",
                          medications: str = "") -> dict:
        verdict = self.safety.check_patient_query(chief_complaint + history)
        ents = self.entities.extract(chief_complaint + "；" + history)
        prep = {
            "主诉整理": chief_complaint.strip(),
            "现病史要点": history.strip() or "（请补充：起病时间、诱因、变化过程）",
            "用药史": medications.strip() or "（请列出正在使用的药物与保健品）",
            "可识别的中医相关描述": {k: v for k, v in ents.items() if v},
            "建议询问医生的问题": [
                "我的情况中医怎么看？大概属于什么证型？",
                "治疗预计多长时间？如何判断有效？",
                "饮食起居有哪些注意？",
                "出现什么情况需要立即复诊？",
            ],
            "urgent": verdict.urgent,
            "risk_notice": verdict.notice if verdict.urgent else "",
            "disclaimer": self.safety.wrap_patient_answer("").strip(),
        }
        return prep

    # ------------------------------------------------------------------
    def explain_instruction(self, instruction_text: str) -> dict:
        """医嘱/处方理解辅导：只解释传统用途语境，不评价、不调整。"""
        verdict = self.safety.check_patient_query(instruction_text)
        if not verdict.allowed and verdict.refusal_reason == "prescription_request":
            return {"allowed": False, **verdict.to_dict()}
        ents = self.entities.extract(instruction_text)
        herb_notes = []
        for h in ents["herbs"][:10]:
            ctx = []
            for f, info in LEXICON.canonical_formulas.items():
                if h in info["herbs"]:
                    ctx.append(f)
                if len(ctx) >= 2:
                    break
            herb_notes.append({
                "herb": h,
                "classical_context": (f"古籍经典方（如{'、'.join(ctx)}）中可见此药"
                                      if ctx else "古籍中常见药物"),
            })
        formula_notes = []
        for f in ents["formula"][:3]:
            info = LEXICON.canonical_formulas.get(f)
            formula_notes.append({
                "formula": f,
                "possible_source": "《伤寒论》/《金匮要略》经典方" if info else "需进一步溯源",
            })
        answer = {
            "allowed": True,
            "recognized": {"herbs": herb_notes, "formulas": formula_notes},
            "general_advice": [
                "请严格按医嘱的剂量与煎服方法使用，不要自行加减、停换。",
                "如服药后出现皮疹、心慌、腹泻加重等不适，停止服用并联系医生。",
                "把没听明白的地方记下来，复诊时询问医生。",
            ],
            "urgent": verdict.urgent,
            "risk_notice": verdict.notice if verdict.urgent else "",
            "disclaimer": self.safety.wrap_patient_answer("").strip(),
        }
        return answer
