# 湿疹古籍多智能体知识发现报告

> 生成于 2026-06-12T12:38:48Z；框架：TCM-Disease-Hermes（多智能体检索—审核—抽取—分析）。
> 古今映射为表型对应/候选，非现代诊断；每条结论可回源至原文证据片段。

## 摘要

以现代疾病“湿疹”为起点，经古病名扩展、表型组合检索、特殊表型补充、形态学精筛与排除性鉴别获取候选条文；再经证据回源、三视角相关性评审与共识裁决完成纳入判断；最终以五层本体映射、关系抽取、复杂网络与时序分析将非结构化古籍文本转化为可计算、可追溯的证据链。共获候选条文 346 条，纳入（Gold+Silver）0 条。

## 1 资料与方法

### 1.1 检索框架
采用分层召回—过滤—验证策略：T1 核心古病名广域检索 → T2 表型特征组合检索 → T3 特殊部位与复杂症候关联检索 → T4 形态学描述词精化 → T5 排除性鉴别 → T6 多评审一致性裁决 → T7 五层本体映射与关系抽取。

核心古病名（11个）：濕瘡、浸淫瘡、旋耳瘡、四彎風、奶癬、胎斂瘡、血風瘡、黃水瘡、繡球風、濕癬、風濕瘍。
排除性鉴别疾病：白疕、牛皮癬、疥瘡、圓癬、金錢癬、丹毒、天皰瘡、麻風。

### 1.2 多智能体
DiseaseConceptPlanner、AncientDiseaseNameExpansion、CoreSearch、PhenotypeSearch、SpecialSubtypeSearch、MorphologyRefinement、ExclusionDifferential、EvidenceSpanVerifier、TCMClassical/Dermatology/AdversarialDifferential 三评审、ConsensusRelevanceJudge、OntologyMapping、RelationExtraction、NetworkAnalysis、TemporalEvolution、ReportWriting。

### 1.3 分级标准
Gold≥0.90（三评审均纳入且排除项阴性）；Silver 0.80–0.89（≥2 纳入）；Bronze 0.65–0.79（候选线索）；Rejected<0.65 或命中强排除。

## 2 结果

- 候选条文：346 条；
- 分级：Gold 0 / Silver 0 / Bronze 9 / Rejected 337；
- 命中分型分布：{'site': 2, 'acute': 6, 'infant': 1}；
- 核心药物（按中心性）：大麥、黃柏；
- 涉及朝代：明、清。

### 2.1 药物网络
核心药物（按 PageRank/度中心性）：大麥、黃柏。

### 2.2 时序演变
- 明：主要病机 風熱、濕熱；主要治法 —
- 清：主要病机 濕熱、胎毒；主要治法 涼血

## 3 讨论

1. 主要发现：“湿疹”的古籍证治呈现以大麥、黃柏为核心的药物结构，病机以风、血、湿相关为主线。
2. 方法学价值：将传统检索流程转化为多智能体协同框架，实现召回与精筛分离、正向检索与反向排除分离、现代表型与古籍语义分离、结论证据回源四原则。
3. 局限性：启发式词表与样本覆盖有限；古今病名仅为表型对应；需在更大规模外科/本草语料上验证。
4. 可迁移性：更换 DiseaseProfile 即可迁移至骨质疏松、类风湿关节炎、湿疹等病种。

---
No evidence, no rule. No source trace, no answer. 古今映射仅为候选，非诊断。
