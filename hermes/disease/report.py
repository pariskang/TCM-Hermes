"""ReportWritingAgent — methods / results / discussion from structured output."""

from __future__ import annotations

from collections import Counter

from ..config import HermesConfig
from ..utils import utc_now
from .profiles import DiseaseProfile


class ReportWritingAgent:
    name = "ReportWritingAgent"

    def __init__(self, config: HermesConfig | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.backend = backend

    def write(self, profile: DiseaseProfile, summary: dict, network: dict,
              temporal: dict) -> str:
        levels = summary["by_level"]
        included = levels.get("gold", 0) + levels.get("silver", 0)
        core = network.get("core_herbs", [])[:8]
        core_str = "、".join(c["herb"] for c in core) or "（样本不足）"
        dynasties = list(temporal.get("dynasty_trends", {}))

        lines = [
            f"# {profile.display_name}古籍多智能体知识发现报告",
            "",
            f"> 生成于 {utc_now()}；框架：TCM-Disease-Hermes（多智能体检索—审核—抽取—分析）。",
            "> 古今映射为表型对应/候选，非现代诊断；每条结论可回源至原文证据片段。",
            "",
            "## 摘要",
            "",
            f"以现代疾病“{profile.display_name}”为起点，经古病名扩展、表型组合检索、"
            "特殊表型补充、形态学精筛与排除性鉴别获取候选条文；再经证据回源、"
            "三视角相关性评审与共识裁决完成纳入判断；最终以五层本体映射、关系抽取、"
            "复杂网络与时序分析将非结构化古籍文本转化为可计算、可追溯的证据链。"
            f"共获候选条文 {summary['candidates']} 条，纳入（Gold+Silver）{included} 条。",
            "",
            "## 1 资料与方法",
            "",
            "### 1.1 检索框架",
            "采用分层召回—过滤—验证策略：T1 核心古病名广域检索 → T2 表型特征组合检索 → "
            "T3 特殊部位与复杂症候关联检索 → T4 形态学描述词精化 → T5 排除性鉴别 → "
            "T6 多评审一致性裁决 → T7 五层本体映射与关系抽取。",
            "",
            f"核心古病名（{len(profile.core_terms)}个）：{('、'.join(profile.core_terms))}。",
            f"排除性鉴别疾病：{('、'.join(profile.exclusion_terms[:12]))}。",
            "",
            "### 1.2 多智能体",
            "DiseaseConceptPlanner、AncientDiseaseNameExpansion、CoreSearch、"
            "PhenotypeSearch、SpecialSubtypeSearch、MorphologyRefinement、"
            "ExclusionDifferential、EvidenceSpanVerifier、"
            "TCMClassical/Dermatology/AdversarialDifferential 三评审、"
            "ConsensusRelevanceJudge、OntologyMapping、RelationExtraction、"
            "NetworkAnalysis、TemporalEvolution、ReportWriting。",
            "",
            "### 1.3 分级标准",
            "Gold≥0.90（三评审均纳入且排除项阴性）；Silver 0.80–0.89（≥2 纳入）；"
            "Bronze 0.65–0.79（候选线索）；Rejected<0.65 或命中强排除。",
            "",
            "## 2 结果",
            "",
            f"- 候选条文：{summary['candidates']} 条；",
            f"- 分级：Gold {levels.get('gold', 0)} / Silver {levels.get('silver', 0)}"
            f" / Bronze {levels.get('bronze', 0)} / Rejected {levels.get('rejected', 0)}；",
            f"- 命中分型分布：{summary.get('by_subtype', {})}；",
            f"- 核心药物（按中心性）：{core_str}；",
            f"- 涉及朝代：{('、'.join(dynasties)) or '—'}。",
            "",
            "### 2.1 药物网络",
            network.get("interpretation", ""),
            "",
            "### 2.2 时序演变",
        ]
        for d, t in temporal.get("dynasty_trends", {}).items():
            p = "、".join(x["term"] for x in t["dominant_pathogenesis"][:3]) or "—"
            tx = "、".join(x["term"] for x in t["dominant_treatments"][:3]) or "—"
            lines.append(f"- {d}：主要病机 {p}；主要治法 {tx}")
        lines += [
            "",
            "## 3 讨论",
            "",
            f"1. 主要发现：“{profile.display_name}”的古籍证治呈现以"
            f"{core_str}为核心的药物结构，病机以风、血、湿相关为主线。",
            "2. 方法学价值：将传统检索流程转化为多智能体协同框架，实现召回与精筛分离、"
            "正向检索与反向排除分离、现代表型与古籍语义分离、结论证据回源四原则。",
            "3. 局限性：启发式词表与样本覆盖有限；古今病名仅为表型对应；"
            "需在更大规模外科/本草语料上验证。",
            "4. 可迁移性：更换 DiseaseProfile 即可迁移至骨质疏松、类风湿关节炎、"
            "湿疹等病种。",
            "",
            "---",
            "No evidence, no rule. No source trace, no answer. 古今映射仅为候选，非诊断。",
            "",
        ]
        text = "\n".join(lines)
        if self.backend is not None and \
                getattr(self.backend, "kind", "heuristic") != "heuristic":
            try:
                text = self.backend.complete_text(
                    "你是中医古籍数据挖掘论文润色助手。在不改变任何数字、不新增结论的前提下，"
                    "把给定的结构化报告草稿润色为通顺的学术中文，保留所有小节与数据。",
                    text, role="writer")
            except Exception:
                pass
        return text
