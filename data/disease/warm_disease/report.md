# 温病古籍多智能体知识发现报告

> 生成于 2026-06-12T12:38:49Z；框架：TCM-Disease-Hermes（多智能体检索—审核—抽取—分析）。
> 古今映射为表型对应/候选，非现代诊断；每条结论可回源至原文证据片段。

## 摘要

以现代疾病“温病”为起点，经古病名扩展、表型组合检索、特殊表型补充、形态学精筛与排除性鉴别获取候选条文；再经证据回源、三视角相关性评审与共识裁决完成纳入判断；最终以五层本体映射、关系抽取、复杂网络与时序分析将非结构化古籍文本转化为可计算、可追溯的证据链。共获候选条文 2300 条，纳入（Gold+Silver）16 条。

## 1 资料与方法

### 1.1 检索框架
采用分层召回—过滤—验证策略：T1 核心古病名广域检索 → T2 表型特征组合检索 → T3 特殊部位与复杂症候关联检索 → T4 形态学描述词精化 → T5 排除性鉴别 → T6 多评审一致性裁决 → T7 五层本体映射与关系抽取。

核心古病名（12个）：溫病、風溫、春溫、暑溫、濕溫、秋燥、冬溫、溫熱、溫疫、溫毒、伏暑、溫邪。
排除性鉴别疾病：太陽伤寒、伤寒表實、中風、風寒、直中、陰寒、内伤發熱、虛劳。

### 1.2 多智能体
DiseaseConceptPlanner、AncientDiseaseNameExpansion、CoreSearch、PhenotypeSearch、SpecialSubtypeSearch、MorphologyRefinement、ExclusionDifferential、EvidenceSpanVerifier、TCMClassical/Dermatology/AdversarialDifferential 三评审、ConsensusRelevanceJudge、OntologyMapping、RelationExtraction、NetworkAnalysis、TemporalEvolution、ReportWriting。

### 1.3 分级标准
Gold≥0.90（三评审均纳入且排除项阴性）；Silver 0.80–0.89（≥2 纳入）；Bronze 0.65–0.79（候选线索）；Rejected<0.65 或命中强排除。

## 2 结果

- 候选条文：2300 条；
- 分级：Gold 0 / Silver 16 / Bronze 145 / Rejected 2139；
- 命中分型分布：{'wei': 75, 'qi': 24, 'ying': 7, 'xue': 43, 'shiwen': 4, 'shuwen': 8}；
- 核心药物（按中心性）：連翹、石膏、知母、黃芩、甘草、杏仁、丹皮、竹葉；
- 涉及朝代：明、清、未知。

### 2.1 药物网络
核心药物（按 PageRank/度中心性）：連翹、石膏、知母、黃芩、甘草。

### 2.2 时序演变
- 明：主要病机 濕熱、燥熱；主要治法 —
- 清：主要病机 溫邪、氣分、血分；主要治法 辛涼解表、清熱解毒、滋陰
- 未知：主要病机 溫邪、氣分、營分；主要治法 辛涼解表、清熱解毒、息風

## 3 讨论

1. 主要发现：“温病”的古籍证治呈现以連翹、石膏、知母、黃芩、甘草、杏仁、丹皮、竹葉为核心的药物结构，病机以风、血、湿相关为主线。
2. 方法学价值：将传统检索流程转化为多智能体协同框架，实现召回与精筛分离、正向检索与反向排除分离、现代表型与古籍语义分离、结论证据回源四原则。
3. 局限性：启发式词表与样本覆盖有限；古今病名仅为表型对应；需在更大规模外科/本草语料上验证。
4. 可迁移性：更换 DiseaseProfile 即可迁移至骨质疏松、类风湿关节炎、湿疹等病种。

---
No evidence, no rule. No source trace, no answer. 古今映射仅为候选，非诊断。
