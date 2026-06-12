# TCM-Disease-Hermes：银屑病古籍知识发现多智能体框架

> Psoriasis-Hermes — a Multi-Agent Classical TCM Retrieval and Knowledge
> Discovery Framework. 以现代疾病为起点 → 古籍多层检索 → 候选条文自治审核 →
> 五层本体映射 → 证法方药链条抽取 → 网络与时序分析 → 报告/Skill/RAG。
>
> 古今映射只建立**表型对应 / 候选**，绝不等同现代诊断；每个结论可回源至原文。

## 四层 / 17 智能体架构

```text
用户输入现代疾病：银屑病
  ↓ 任务规划层
DiseaseConceptPlannerAgent           现代分型/症状域/鉴别病
AncientDiseaseNameExpansionAgent     古病名词表 + 布尔检索式（高召回）
  ↓ 多路召回层
CoreSearchAgent                      T1 核心古病名广域召回
PhenotypeSearchAgent                 T2 寻常/脓疱/红皮病型 表型组合检索
SpecialSubtypeSearchAgent            T3 关节/甲/头皮型 anchor~qualifier 近邻
MorphologyRefinementAgent            T4 形态学精筛（如钱文/匡郭/成片…）
ExclusionDifferentialAgent           T5 排除真菌癣/疥疮/麻风/丹毒…
  ↓ 证据审核层
EvidenceSpanVerifierAgent            每个判断回源到 raw_text 子串
TCMClassicalReviewerAgent            中医古籍/训诂视角
DermatologyReviewerAgent             现代皮肤病学表型视角
AdversarialDifferentialAgent         反证视角（越像鉴别病分越高）
ConsensusRelevanceJudgeAgent         三评审 + 组件评分 → gold/silver/bronze/rejected
  ↓ 知识抽取与分析层
OntologyMappingAgent                 古病名/症状/病机/治法/药物 五层本体
RelationExtractionAgent              二元组/三元组/链式关系
NetworkAnalysisAgent                 药物共现 + PMI + 度/介数/特征向量/PageRank
TemporalEvolutionAgent               朝代×病机/治法 相对频率
ReportWritingAgent                   方法/结果/讨论草稿
```

四条核心设计原则（落在代码里，不只是口号）：

1. **召回与精筛分离** — CoreSearch 只召回（高噪声），判断在审核层；
2. **正向检索与反向排除分离** — ExclusionDifferential 专找“不是银屑病”的证据；
3. **现代表型与古籍语义分离** — 输出永远是 `candidate_modern_type` / 表型对应，不是诊断；
4. **每个结论证据回源** — `EvidenceSpanVerifier` 保证 evidence_spans ⊆ raw_text。

## 运行

```bash
# 计划（看分型/古病名/检索式）
python3 -m hermes disease plan --disease 银屑病

# 在内置示例语料上跑全流程（默认）
python3 -m hermes disease run --disease 银屑病

# 在已导入的语料 source units 上检索（外科/本草语料更合适）
python3 -m hermes import <外科语料.zip 或目录>
python3 -m hermes segment
python3 -m hermes disease run --disease 银屑病 --use-corpus --no-sample

# 接入大模型让三评审成为真正多模型判断
export HERMES_BACKEND=litellm HERMES_LLM_MODEL=gpt-4o-mini
python3 -m hermes disease run --disease 银屑病
```

产物（`data/disease/<disease_id>/`）：`plan.json`、`ancient_names.json`、
`candidates.jsonl`（统一候选结构）、`relations.jsonl`、`network.json/.dot`、
`temporal.json`、`summary.json`、`report.md`。`--resume` 复用 candidates 重算分析。

## 统一候选结构（candidates.jsonl）

```json
{
  "entry_id": "PSORIASIS_000001",
  "source": {"book": "諸病源候論", "chapter": "瘡病諸候·乾癬候",
             "dynasty": "隋", "author": "巢元方", "year": 610,
             "source_unit_id": "SU_PSO_SAMPLE_0001", "sample": true},
  "raw_text": "乾癬，但有匡郭，皮枯索，痒，搔之白屑出是也。皆是風濕邪氣……",
  "retrieval": {"hit_terms": ["乾癬", "癬"],
                "retrieval_layers": ["T1_core", "T2_vulgaris", "T4_morphology"],
                "query_string": "(癬 OR 疕 OR …)"},
  "phenotype_evidence": {"candidate_modern_type": "vulgaris",
                         "supporting_features": ["匡郭", "皮枯索", "白屑"],
                         "morphology_score": 0.6,
                         "warning": "phenomenological correspondence only; not modern diagnosis"},
  "exclusion": {"exclude_flag": false, "matched_exclusion_terms": []},
  "review": {"tcm_reviewer_score": 0.9, "dermatology_reviewer_score": 0.8,
             "adversarial_score": 0.15, "consensus_score": 0.87,
             "label": "include", "release_level": "silver",
             "reviewer_votes": {"TCMClassicalReviewer": "include", ...}},
  "ontology": {"ancient_disease_name": ["乾癬"], "symptoms": ["匡郭","皮枯索","痒"],
               "pathogenesis": ["風濕","寒濕","血氣相搏"], "treatment_method": [],
               "herbs": []},
  "extracted_relations": [["乾癬","has_symptom","白屑"],
                          ["乾癬","maps_to_candidate","银屑病·寻常型"],
                          ["風濕","associated_with","乾癬"]]
}
```

## 综合相关性评分与分级

```
final = 0.20·古病名命中 + 0.25·表型支持 + 0.20·形态学支持
      + 0.15·上下文一致 + 0.10·来源可信 + 0.10·基础
      − 排除惩罚(强0.6/软0.1) − 证据不足惩罚(0.25)
```

| 级别 | 阈值 + 投票 | 用途 |
| --- | --- | --- |
| Gold | ≥0.90 且三评审全纳入且排除阴性 | 核心分析集 |
| Silver | 0.80–0.89 且 ≥2 纳入 | 主分析（保留不确定性） |
| Bronze | 0.65–0.79 | 候选线索，不进入主结论 |
| Rejected | <0.65 或命中强排除 / 对抗判排除 | 排除（留档） |

## 内置疾病 Profile（开箱即用，5 个）

| 疾病 | 古病名映射 | 数据来源 |
| --- | --- | --- |
| 银屑病 `psoriasis` | 白疕 / 干癣 / 松皮癣 / 牛皮癣 / 蛇虱 | 示例外科语料（伤寒金匮无） |
| 骨质疏松 `osteoporosis` / 骨痿 | 骨痿 / 骨枯 / 骨极 / 虚劳腰痛 | 示例（内经/本草色彩浓）+ 金匮「八味肾气丸」 |
| 类风湿 `rheumatoid_arthritis` / 历节 | 历节 / 痹证 / 尪痹 / 鹤膝风 / 白虎历节 | **直接命中金匮「中风历节病」**，`--use-corpus` 即得真实条文与方药网络 |
| 温病 `warm_disease` / 温病 | 温病 / 风温 / 春温 / 暑温 / 湿温 / 卫气营血 | 示例（叶天士《温热论》、吴鞠通《温病条辨》银翘散/桑菊饮） |
| 湿疹 `eczema` / 湿疮 | 浸淫疮 / 旋耳疮 / 四弯风 / 奶癣 / 血风疮 | 示例外科语料（诸病源候论/医宗金鉴外科） |

```bash
python3 -m hermes disease run --disease 骨质疏松
python3 -m hermes disease run --disease 类风湿 --use-corpus --no-sample --skills
```

类风湿在真实金匮语料上能召回桂枝芍药知母汤、乌头汤等条文，药物共现网络核心为
桂枝/甘草/附子/麻黄/知母/芍药/白朮——与原方完全吻合，是"框架在真实语料上跑通"的
最佳示例。骨质疏松/银屑病的外科·骨伤内容在伤寒金匮中稀少，故以示例语料演示，
正式研究需导入对应语料。

> **能否"完美迁移到所有疾病"？** 框架（17 个 agent）零代码迁移——只需一个
> `DiseaseProfile`；但**覆盖度取决于语料**：底座是伤寒/金匮时，痹证/历节类疾病
> 有真实数据，外科/骨伤/温病类需导入相应语料。这是数据问题，不是框架问题。

## Disease-Skill：编译为 Skill 并接入 Skill RAG

候选条文（默认 silver/gold，可含 bronze）按现代分型编译为 Hermes Skill，
命名 `hermes.disease.<disease>.<subtype>`，写入独立的 `disease_skill_index.json`，
被 `SkillRAGAgent` 与方剂 Skill **统一检索**（重跑主管线不会覆盖疾病 Skill）。

```bash
python3 -m hermes disease run --disease 银屑病 --skills           # 跑流程并编译 Skill
python3 -m hermes disease-skills --disease 类风湿 --include-bronze # 单独编译
python3 -m hermes ask "白疕 鳞屑 血燥"                             # 经 Skill RAG 命中疾病 Skill
```

疾病 Skill 答复保留统一契约（发布级别 / 一致性分 / 支持候选 / 原文证据 / variant /
conflict / 安全声明），并附疾病专属字段：`ancient_disease_names`、`ontology_summary`、
`mapping_caveat`（古今映射为候选/表型对应，非诊断）。

## 可视化导出（交互式 ECharts HTML，含 DIY 参数）

把疾病知识导出为自包含的 HTML 仪表盘（数据内嵌，ECharts 走 CDN），五种图表：
药物共现**网络**、病机→治法→药物**桑基图**、共现**热力图**、高频词**柱状图**、
朝代**时序**。dashboard 顶部标签切换，每图都带**实时 DIY 控件**（最小共现阈值、
节点大小指标 degree/betweenness/eigenvector/pagerank、力导向斥力、Top-N、明暗主题），
浏览器内即时重绘。

```bash
python3 -m hermes disease run --disease 类风湿 --use-corpus --no-sample --viz   # 跑流程并出图
python3 -m hermes disease-viz --disease 类风湿 --size-metric pagerank --min-edge 2 --theme dark
```

产物在 `data/disease/<病>/viz/`：`dashboard.html`（打开即用）+ `viz_data.json`
（数据，供外部工具复用）。类风湿在真实金匮语料上的 dashboard 含 23 节点/88 边药物
网络、漢/宋/明/清多朝代时序、373 条桑基流，核心药物为桂枝/甘草/附子/芍药/麻黄/白朮/
乌头/知母/防风（= 桂枝芍药知母汤+乌头汤）。离线无网时 ECharts 加载失败会提示改用
`--echarts-url` 指向本地副本，数据仍在 `viz_data.json` 中可用。

## 迁移到其他疾病

只需新增一个 `DiseaseProfile` 并在 `DISEASE_PROFILES` 注册——agent 代码零改动：

```python
from hermes.disease.profiles import DiseaseProfile, DISEASE_PROFILES

OSTEOPOROSIS = DiseaseProfile(
    disease_id="osteoporosis", display_name="骨质疏松",
    modern_subtypes=["原发性", "继发性"],
    phenotype_schema={"bone_loss": ["骨痿", "骨枯", "腰背痛", "骨痛"],
                      "fracture": ["折", "骨折", "伛偻"]},
    core_terms=["骨痿", "骨枯", "骨极", "腰痛", "痿"],
    morphology_terms=["伛偻", "驼背", "腰脊不举"],
    special_subtypes={},
    exclusion_terms=["骨疽", "骨痈", "附骨疽", "历节"],
    differential_notes={"附骨疽": "化脓性骨感染，非骨质疏松"},
    pathogenesis_terms=["肾虚", "精亏", "髓减", "脾虚", "血瘀"],
    treatment_terms=["补肾", "填精", "强骨", "健脾", "活血"],
    extra_herbs=["熟地黄", "杜仲", "续断", "骨碎补", "淫羊藿", "枸杞子"])
DISEASE_PROFILES[OSTEOPOROSIS.disease_id] = OSTEOPOROSIS
```

随后 `hermes disease run --disease osteoporosis --use-corpus` 即可。

## 说明

内置 `sample_corpus.py` 为少量**示例性**经典条文（傷寒/金匮语料几乎无外科内容），
带 provenance 与 `sample: true` 标记；正式研究请指向经过校勘的外科/本草语料，
本框架对任意语料的 source units 同样适用。
