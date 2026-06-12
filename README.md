# TCM-Hermes v5 — 模型自主治理的古籍规则生成系统

> **Hermes 不再等待人工专家确认规则，而是通过「证据回源 + 对抗式质疑 + 一致性
> 裁决 + 自动修复 + 发布分级」实现模型自主审核；最终合并规则只使用
> Silver/Gold 初始规则，Rejected 规则永久保留但不得进入 Hermes Skill。**
>
> 自主审核 ≠ 无审核。自主审核 = 多模型、多轮、多证据、多门控的自动化审核。
>
> No evidence, no rule. No source trace, no answer. No human review.

Hermes 自动下载并解析伤寒金匮类古籍（[中醫笈成](https://jicheng.tw/)
book-20180111），按完整目录分类法逐书逐章抽取 InitialRules，经五重模型自主
审核（结构校验 → 证据回源 → 语义审核 → 对抗式质疑 → 一致性裁决）、自动修复
与发布门控，形成无需人工参与、全程可审计的规则资产，并编译为可检索的
Hermes Skills，支撑医师 / 科研 / 论文 / 患者教育 / 方药溯源等工作台。

## 本仓库已包含的真实产物（傷寒金匱類全量 66 部书）

| 产物 | 规模 |
| --- | --- |
| SourceUnit（条文级证据单元） | 68,865 个（运行时重建） |
| InitialRule v5 | **28,475 条**，证据回源率 **100%** |
| 发布分级 | Gold 1,441 / Silver 5,789 / Bronze 10,418 / Rejected 10,827（全部留档） |
| 自动修复 | 14,692 条（解释级别校正 1.6 万次、证据裁剪、假支持剔除 93 处） |
| 主题规则 | 1,438 章节 + 57 单书 + 4 类目 |
| MergedHermesRule | 331 条（含证据链 / variant_set / conflict_set） |
| Hermes Skills | 331 个（`data/skills/`，7 gold） |
| 治理报告 | `data/reports/autonomous_review_report_latest.md` |

```text
模型抽取 → 多模型自主复核 → 对抗式质疑 → 证据回源校验 → 一致性投票
        → 自动修复 → 自动分级发布
```

## 快速开始

```bash
pip install -e ".[dev]"        # 零强制依赖；py7zr 仅用于 7z 下载解压

# 一键复现（下载语料 → 全管线 → 报告）
bash scripts/run_full_pipeline.sh

# 或分步
python3 -m hermes download --extract        # 或: hermes import <zip/目录>
python3 -m hermes pipeline                  # catalog→segment→审核→主题→合并→Skill→报告
```

### 旗舰功能速览

```bash
# 古籍原文 RAG（精确/语义/结构过滤；输出强制证据链）
python3 -m hermes search "陽浮而陰弱" --subcategory 傷寒 --original-only
python3 -m hermes search "怕冷 无汗 身疼痛 脉浮紧"

# Skill RAG 问答（输出：skill/合并规则/级别/一致性分/支持规则/原文/变体/冲突/安全声明）
python3 -m hermes ask "汗出惡風，脈浮緩，古籍中有哪些方證依據？"

# 方药溯源 与 处方→经典方匹配（支持简体输入）
python3 -m hermes lineage 桂枝湯 --brief
python3 -m hermes match-prescription "桂枝,白芍,炙甘草,生姜,大枣"

# 医师工作台：方证匹配 / 病案回源 / 经典方鉴别（附证据链与免责声明）
python3 -m hermes physician match --text "恶寒发热，无汗，身疼痛，脉浮紧"
python3 -m hermes physician differentiate --formulas "桂枝湯,麻黃湯"

# 科研工作台：统计 / 共现网络 / 古今病名映射 / 主题挖掘（输出 JSON+CSV+DOT）
python3 -m hermes research stats
python3 -m hermes research mine --topic 胸痹

# 论文自动撰写（Methods/Results 注入真实管线数字）
python3 -m hermes paper 胸痹

# 患者教育（安全门控：拒绝处方/剂量请求；红旗症状直接转急诊提示）
python3 -m hermes patient explain --text "医生说我营卫不和是什么意思？"

# 治理
python3 -m hermes metrics && python3 -m hermes report && python3 -m hermes status
```

## 五重模型自主审核

每条 InitialRule 必须通过：

1. **SchemaValidator** — 结构合法性 + 受控词表 + 禁用人审字段扫描；
2. **EvidenceVerifierAgent** — **evidence_span 必须是原文严格子串**，否则永不进入合并；
3. **RuleReviewerAgent** — 语义审核（条件/结论是否来自原文、原文注文是否混杂、治法直述还是归纳）；
4. **AdversarialCriticAgent** — 专职找错（过度概括、症状虚增、注文冒充原文、限制条件「若/不可/反/誤」遗漏、伤寒金匮语境混淆）；
5. **ConsensusJudgeAgent** — 多路置信融合裁决（分歧 >0.35 判 model_conflict）。

需修复者由 **RuleRepairAgent** 以最小编辑修复后**全层复审**（≤2 轮），再经
**ReleaseGateAgent** 分级：Gold(≥0.93) / Silver(≥0.85) / Bronze(≥0.75) /
Rejected（留档 `data/rules_rejected/`）。每条规则携带完整 `audit_trail` 与
五层 `review_records`，任何结论可复盘到智能体级动作。

真实样例（宋本桂枝汤条文的审计轨迹）：

```text
InitialRuleExtractorAgent: created (X主之)
RuleReviewerAgent:         semantic_review (治法「解肌發表」未见于原文)
AdversarialCriticAgent:    flagged interpretation_level_issue
RuleRepairAgent:           changed interpretation_level original_text → normalized
RuleReviewerAgent:         semantic_review (复审通过)
ConsensusJudgeAgent:       model_repaired_accepted, score 0.92
ReleaseGateAgent:          released_silver
```

## 模型后端

默认 `heuristic` 后端：经典文法引擎（主之/宜/不可/誤下/之為病/脈X者…）+
受控词表，零依赖、确定性、66 书全管线约 3 分钟。设
`HERMES_BACKEND=anthropic`（需 `pip install anthropic` 与
`ANTHROPIC_API_KEY`）可启用 Claude 多模型后端：抽取 / 审核 / 质疑 / 裁决
分派不同模型，一致性投票成为真正的多模型裁决；异常自动回落启发式引擎。

## 文档与测试

- [docs/HERMES_V5_PROTOCOL.md](docs/HERMES_V5_PROTOCOL.md) — v5 协议全文（状态机/门控/记忆/指标）
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 架构与数据流
- [docs/SAFETY.md](docs/SAFETY.md) — 安全治理边界
- `prompts/` — 五个核心智能体的 v5 提示词
- `pytest tests/`：53 项测试覆盖协议不变量（证据子串、门控阈值、修复上限、
  rejected 留档、合并仅用 silver/gold、Skill 输出契约、患者端安全拒绝、
  人审字段全仓扫描）。

## 设计定位

| | |
| --- | --- |
| 旧 | 人机协同古籍规则系统（`human_review_required` / `expert_approved`） |
| **新** | **模型自主治理的古籍规则生成系统**（`autonomous_review_status` / `consensus_score` / `critic_result` / `auto_repair_applied` / `release_level` / `model_audit_trail`） |

古籍语料版权与使用规范请遵循中醫笈成的相关说明。本系统输出为古籍知识整理，
不构成诊疗建议。
