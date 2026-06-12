# Hermes 架构

## 数据流

```text
jicheng.tw 7z / 本地 zip / 目录树
  │ DownloaderAgent（hash 校验、版本登记、重复检测）
  ▼
data/corpus/raw/<分類>/書籍/<書名>/*.txt
  │ CatalogAgent（<book> 元数据优先 → 目录树/书目/章节清单）
  ▼
data/corpus/manifests/{catalog_tree, book_manifest, chapter_manifest,
                       corpus_version, file_hash_report}
  │ SegmenterAgent（书→卷/篇→章→条文；文本类型 original/commentary/
  │                 formula/variant/case/preface；实体标注）
  ▼
data/corpus/source_units/BOOK_*.jsonl          ← 证据底座（raw_text）
  │ AutonomousReviewOrchestrator
  │   InitialRuleExtractorAgent → 五重审核 → 修复循环 → 发布门控
  ▼
data/rules/initial/BOOK_*.jsonl                ← 全部初始规则（含审计轨迹）
data/rules/released/{gold,silver,bronze}/      ← 分级发布
data/rules_rejected/                           ← 永久留档
data/memory/*.jsonl                            ← 10+ 类记忆流
  │ ThemeInducerAgent / RuleMergerAgent（仅 silver/gold）
  ▼
data/rules/theme/{chapter,book,category}_themes.jsonl
data/rules/merged/merged_rules.jsonl           ← 证据链/变体/冲突全保留
  │ SkillBuilderAgent（仅 silver/gold 合并规则）
  ▼
data/skills/hermes.formula.*.{json,md} + skill_index.json
  │
  ├─ SkillRAGAgent / ClassicalTextRAGAgent     ← 问答与检索
  ├─ DoctorAssistantAgent                      ← 方证匹配/病案回源/鉴别
  ├─ FormulaLineageAgent / PrescriptionMatcher ← 溯源与处方匹配
  ├─ ResearchWorkbench / PaperWriterAgent      ← 统计/图谱/假设/论文
  └─ PatientEducationAgent + SafetyGovernance  ← 患者教育（安全门控）
  ▼
data/reports/autonomous_review_report_*.md     ← 每轮治理报告
```

## 包结构

```text
hermes/
├─ protocol.py        # v5 协议常量（状态/门槛/词表/记忆类型/禁用字段）
├─ config.py          # HermesConfig：数据布局 + 门槛 + 后端选择
├─ utils.py           # JSONL/hash/时间戳/分句
├─ schemas/           # SourceUnit / InitialRule / ThemeRule / MergedHermesRule
│                     # + SchemaValidator（第 1 层审核）
├─ knowledge/         # 词表（病/证/脉/治法/药/名方）、实体抽取、简繁转换
├─ corpus/            # downloader / parser（wiki 标记）/ catalog / segmenter
├─ agents/            # extractor + 5 层审核 + repair + gate + orchestrator
│                     # + theme + merger + skills + safety + prompts + backends
├─ memory/            # MemoryStore + MemoryCuratorAgent
├─ rag/               # ClassicalTextRAGAgent + SkillRAGAgent
├─ metrics/           # QualityMetrics + AutonomousReviewReporter
├─ lineage/           # FormulaLineageAgent + PrescriptionMatcherAgent
├─ workbench/         # physician / researcher / paper / patient
└─ cli.py             # hermes 命令行
```

## 关键不变量

1. `evidence_span in source_unit.raw_text`（严格子串）— 由 EvidenceVerifier
   强制执行，verifier 失败的规则永远无法越过发布门控；
2. 合并规则/主题/Skill 仅由 silver/gold 初始规则支撑；
3. rejected 规则只进 `data/rules_rejected/`，不删除、不参与推理；
4. 每条规则携带完整 `audit_trail`（agent/action/timestamp）与
   `review_records`（五层原始输出），任何结论可复盘；
5. 患者端输出永不包含诊断/处方/剂量，红旗症状直接转急诊提示；
6. 任何产物中不得出现 `protocol.BANNED_FIELDS` 中的人审字段。

## 后端与扩展

- 默认 heuristic 后端：经典文法模式（主之/宜/不可/誤下/之為病/脈X者…）+
  受控词表，0 依赖离线运行，66 书 ~7 万条文全管线分钟级完成；
- `HERMES_BACKEND=anthropic`：抽取/语义审核/质疑/裁决/修复各角色可配不同
  Claude 模型（见 `agents/backends.py` 的 role_models），prompts 见
  `agents/prompts.py` 与 `prompts/`；
- 新增类目（温病/本草/针灸…）：将分类树落入 `corpus_raw` 后全管线自动适配，
  `protocol.SUBCATEGORY_MAP` 增加映射即可。
