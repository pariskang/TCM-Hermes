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
