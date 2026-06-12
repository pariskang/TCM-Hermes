"""SafetyGovernanceAgent — safety boundary for every user-facing surface.

Hard rules:
  * patient-facing outputs never contain diagnosis, prescriptions, dosage
    advice or treatment replacement;
  * red-flag symptoms trigger an immediate seek-care notice;
  * physician-facing outputs are decision *support* and carry an explicit
    practitioner-judgement disclaimer;
  * every answer that cites rules also surfaces release level + evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..knowledge.lexicon import LEXICON

PATIENT_DISCLAIMER = (
    "以上内容为中医古籍知识科普，不能替代医生的诊断和治疗。"
    "如有不适，请及时就医，用药请遵执业医师医嘱。")

PHYSICIAN_DISCLAIMER = (
    "本结果为古籍证据检索与匹配，仅供具备执业资质的中医师参考，"
    "不构成对具体患者的诊疗方案；处方决策须由医师结合四诊合参自行判断。")

URGENT_NOTICE = "您描述的情况可能属于急症：{signals}。请立即就医或拨打当地急救电话。"

# intents a patient-facing surface must refuse
_PRESCRIPTION_INTENT = re.compile(
    r"(给我开|帮我开|开个方|开点药|吃什么药|用什么方|怎么治|如何治疗|"
    r"剂量|用量|吃多少|怎么吃|要不要停药|换个方子|自己抓药|帮我配)")


@dataclass
class SafetyVerdict:
    allowed: bool
    refusal_reason: str = ""
    urgent: bool = False
    risk_signals: list[str] = field(default_factory=list)
    notice: str = ""

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "refusal_reason": self.refusal_reason,
                "urgent": self.urgent, "risk_signals": self.risk_signals,
                "notice": self.notice}


class SafetyGovernanceAgent:
    name = "SafetyGovernanceAgent"

    # ------------------------------------------------------------------
    def check_patient_query(self, query: str) -> SafetyVerdict:
        signals = [rs["pattern"] for rs in LEXICON.risk_signals
                   if rs["pattern"] in query]
        if signals:
            return SafetyVerdict(
                allowed=False, urgent=True, risk_signals=signals,
                refusal_reason="risk_signal",
                notice=URGENT_NOTICE.format(signals="、".join(signals)))
        if _PRESCRIPTION_INTENT.search(query):
            return SafetyVerdict(
                allowed=False, refusal_reason="prescription_request",
                notice=("抱歉，我不能提供诊断、处方或剂量建议。"
                        "我可以帮您：理解中医术语、整理症状日记、准备就诊问题。"
                        "具体治疗请咨询执业中医师。"))
        return SafetyVerdict(allowed=True)

    def wrap_patient_answer(self, text: str) -> str:
        return text.rstrip() + "\n\n" + PATIENT_DISCLAIMER

    def wrap_physician_answer(self, text: str) -> str:
        return text.rstrip() + "\n\n" + PHYSICIAN_DISCLAIMER

    # compliance guard for industry-facing copy ------------------------
    _OVERCLAIM = ("根治", "治愈率", "包治", "无效退款", "替代药物", "抗癌神药")

    def check_marketing_copy(self, text: str) -> list[str]:
        return [w for w in self._OVERCLAIM if w in text]
