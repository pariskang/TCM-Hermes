# TCM-Hermes v5 — 模型自主治理的古籍规则生成系统

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pariskang/TCM-Hermes/blob/claude/project-code-review-4jkbyh/notebooks/TCM_Hermes_Colab.ipynb)

> **Hermes 不再等待人工专家确认规则，而是通过「证据回源 + 对抗式质疑 + 一致性
> 裁决 + 自动修复 + 发布分级」实现模型自主审核；最终合并规则只使用
> Silver/Gold 初始规则，Rejected 规则永久保留但不得进入 Hermes Skill。**
>
> 自主审核 ≠ 无审核。自主审核 = 多模型、多轮、多证据、多门控的自动化审核。
>
> No evidence, no rule. No source trace, no answer. No human review.

> 🚀 **一键体验**：点上方 Colab 徽章打开
> [`notebooks/TCM_Hermes_Colab.ipynb`](notebooks/TCM_Hermes_Colab.ipynb)，全功能演示
> （检索 / 问答 / 溯源 / 安全筛查 / 工作台 / 评测 / 风险控制校准 / 疾病发现 +
> ECharts / MCP / 多厂商后端），大多数单元用仓库自带产物即可运行，无需下载语料。

Hermes 自动下载并解析伤寒金匮类古籍（[中醫笈成](https://jicheng.tw/)
book-20180111），按完整目录分类法逐书逐章抽取 InitialRules，经五重模型自主
审核（结构校验 → 证据回源 → 语义审核 → 对抗式质疑 → 一致性裁决）、自动修复
与发布门控，形成无需人工参与、全程可审计的规则资产，并编译为可检索的
Hermes Skills，支撑医师 / 科研 / 论文 / 患者教育 / 方药溯源等工作台。

## 本仓库已包含的真实产物（傷寒金匱類全量 66 部书）

| 产物 | 规模 | 仓库状态 |
| --- | --- | --- |
| SourceUnit（条文级证据单元） | 68,865 个 | 运行时重建 |
| InitialRule v5 | **28,421 条**，证据回源率 **100%** | 运行时重建（`data/rules/initial/` 不入库） |
| 发布分级 | Gold 1,434 / Silver 4,939 / Bronze 11,246 / Rejected 10,802（全部留档） | Gold 全量自带；Silver/Rejected 仅自带宋本/金匱样例，Bronze 及其余运行时重建 |
| 自动修复 | 14,754 条（解释级别校正 1.6 万次、证据裁剪、假支持剔除 93 处） | 记录于各规则 `audit_trail` |
| span↔claim 绑定 | 松散/多方并述规则被降级（silver→bronze），不得进入 Gold | 审核期门控行为 |
| 主题规则 | 1,325 章节 + 57 单书 + 4 类目 | 自带 |
| MergedHermesRule | 319 条（含证据链 / variant_set / conflict_set） | 自带 |
| Hermes Skills | 319 个（`data/skills/`） | 自带 |
| 治理报告 | `data/reports/autonomous_review_report_latest.md` | 自带 |

「运行时重建」产物由 `bash scripts/run_full_pipeline.sh` 从公开语料一键再生成
（公开压缩包按书内 `分類=` 元数据归类，范围略宽于原始整理树，各级数量会有小幅差异）。

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

# 方药溯源 与 处方→经典方匹配（支持简体输入；输出附十八反/十九畏/毒性/妊娠安全筛查）
python3 -m hermes lineage 桂枝湯 --brief
python3 -m hermes match-prescription "桂枝,白芍,炙甘草,生姜,大枣"

# 金标准评测基准（宋本伤寒论/金匮 55 条人工标注；抽取 P/R/F1 + 门控校准）
python3 -m hermes benchmark

# 风险控制门控校准（分布无关有限样本保证：RCPS + Clopper-Pearson + ECE）
python3 -m hermes calibrate

# 医师工作台：方证匹配 / 病案回源 / 经典方鉴别（附证据链、药物安全筛查与免责声明）
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

### 风险控制的分级门控（分布无关有限样本保证）

分级阈值 0.93/0.85/0.75 原为手工设定。`hermes calibrate` 把它升级为**统计可证的
决策**：在金标准校准集上，把「释放层错误率」（精度）与「漏放正确规则率」（召回）
各视为一个单调 0/1 损失，用**精确 Clopper-Pearson 二项上界**（Risk-Controlling
Prediction Sets, Bates et al. JACM 2021 / Learn-then-Test, Angelopoulos et al.
2021；Conformal Risk Control, Angelopoulos et al. ICLR 2024）在 1−δ 置信度下加以
控制。在可交换性假设下给出**有限样本保证**：*当 Hermes 释放一条规则时，其正确
率以 1−δ 置信度不低于目标精度*——把分级从启发式变成可审计的风险控制决策。

同一套机制还输出可信度校准诊断：**期望校准误差 ECE**（Guo et al. 2017）、
reliability 表、**选择性风险-覆盖曲线**（El-Yaniv & Wiener 2010）。在当前金标准上
它给出三个诚实且可复盘的发现：(1) 手工 Gold 阈值 0.93 只释放 8 条规则，样本过小
以致其精度**根本无法认证**（误差上界高达 0.31），却漏掉了 87% 的正确规则；风险
控制阈值 0.87 在同等经验精度（100%）下误差上界收紧到 0.07 且认证召回 ≥55%；
(2) 共识分**系统性欠自信**（ECE 0.18，每个分箱准确率均高于置信度）；(3) 约 8% 的
正确规则被硬门控误拒（置信度 0，MCE 1.0）——任何阈值都救不回，指明了下一步改进
方向。校准阈值经 `HERMES_CALIBRATED_GATE=1` 启用（默认关闭，行为不变）；保证仅对
与宋本《伤寒论》/《金匮》金标准可交换的条文严格成立，跨语料部署属分布漂移，校准
阈值是可审计的先验而非无条件承诺（此局限如实写入报告）。详见
`data/reports/calibration_report_latest.md`。

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

## 模型后端（litellm：一套接口接入几乎所有大模型）

默认 `heuristic` 后端：经典文法引擎（主之/宜/不可/誤下/之為病/脈X者…）+
受控词表，零依赖、确定性、66 书全管线约 3 分钟。

```bash
pip install -e ".[llm]"                         # litellm
export HERMES_BACKEND=litellm
export HERMES_LLM_MODEL=gpt-4o-mini             # 默认模型
export HERMES_LLM_MODEL_CRITIC=claude-opus-4-8  # 各角色可绑不同模型/厂商
export HERMES_LLM_MODEL_JUDGE=gemini/gemini-1.5-pro
python3 -m hermes review --books BOOK_SHL_SONGBEN

# Azure OpenAI
export HERMES_LLM_MODEL=azure/<部署名>
export HERMES_LLM_API_BASE=https://<resource>.openai.azure.com
export HERMES_LLM_API_KEY=<azure-key> HERMES_LLM_API_VERSION=2024-02-01

# MiniMax（原生；MINIMAX_API_KEY 自动识别）
export HERMES_LLM_MODEL=minimax/MiniMax-M2  MINIMAX_API_KEY=<minimax-key>
```

`LiteLLMBackend` 用 `litellm.completion` 统一调用 OpenAI / Anthropic / Gemini /
Mistral / Groq / DeepSeek / Ollama / vLLM / **Azure OpenAI** / **MiniMax** /
Bedrock 等；按 agent **角色**绑定不同模型，并可用 `HERMES_LLM_API_BASE[_ROLE]` /
`_API_KEY[_ROLE]` / `_API_VERSION[_ROLE]` 按角色绑定不同**端点/厂商**（如 Azure
裁决 + MiniMax 对抗 + OpenAI 抽取），使共识成为真正的多厂商投票。异常自动回落启
发式引擎，离线测试不变。详见 [docs/LLM_BACKENDS.md](docs/LLM_BACKENDS.md)。

### 针对三个已知问题的强化

| 问题 | 解决 |
| --- | --- |
| 默认是启发式、非真正多智能体 | **LiteLLMBackend** + 按角色多模型；extractor/reviewer/critic/judge 四核心 agent 与评审小组均走 LLM 路径（异常回落启发式）；`HERMES_CONSENSUS_MODE=panel` 启用辩论 |
| 证据存在 ≠ 语义正确 | **span↔claim 绑定校验**（`agents/binding.py`）：多方并述/跨句远距弱关联被量化降权，多方片段不得 Gold；分数入 `binding_score` |
| 共识是确定性评分、非辩论 | **多评审小组**（`agents/reviewer_profiles.py`）：保守派/训诂/方证/临床安全/现代转译/对抗六视角投票；分歧→`model_conflict`，多数否决→reject，记录于 `review_records.panel` |

## 疾病知识发现：TCM-Disease-Hermes（可迁移，内置 5 病种）

可迁移的疾病多智能体框架（15 个智能体，其中相关性评审小组含 3 个评审视角，
合计 17 路评审角色）：现代疾病 → 古籍多层检索（核心召回/表型/特殊型/形态/排除）
→ 候选自治审核（证据回源 + 三视角评审 + 共识分级）→ 五层本体 → 关系抽取 →
药物共现网络（PMI + 度/介数/特征向量/PageRank，纯 Python）→ 朝代时序 → 报告 → Skill → 可视化。

```bash
python3 -m hermes disease run --disease 银屑病                       # 示例语料
python3 -m hermes disease run --disease 骨质疏松
python3 -m hermes disease run --disease 类风湿 --use-corpus --no-sample --skills --viz  # 真实金匮语料+可视化
python3 -m hermes ask "白疕 鳞屑 血燥"                                # 疾病 Skill 经 Skill RAG 命中
```

内置 `psoriasis`/`osteoporosis`/`rheumatoid_arthritis`/`warm_disease`(温病)/`eczema`(湿疹) 五个 Profile。**类风湿直接命中
金匮「中风历节病」**，`--use-corpus` 得到真实条文与药物网络（核心：桂枝/甘草/附子/麻黄/
知母/芍药/白朮 = 桂枝芍药知母汤+乌头汤）。

**能否"完美迁移到所有疾病"**：框架零代码迁移（只需一个 `DiseaseProfile`），但**覆盖度
取决于语料**——伤寒/金匮底座下，痹证/历节类有真实数据，外科/骨伤/温病类需导入对应语料。
四原则落在代码：召回与精筛分离、正向与排除分离、现代表型与古籍语义分离、结论证据回源；
古今映射只为**候选/表型对应，非诊断**。候选可编译为 `hermes.disease.<病>.<分型>` Skill 并
接入现有 Skill RAG；可经 `hermes disease-corpus --category 外科|溫病` 接入**真实外科/温病语料**(隔离，不污染伤寒金匮底座；温病真实语料 2300 候选/16 silver)；候选一键导出 **9 种交互式 ECharts 图**(五层知识图谱/网络/桑基/旭日/雷达/热力/柱状/时序/PRISMA 漏斗，支持 **PNG·SVG·JSON 导出** + DIY 参数)：`hermes disease-viz --disease 温病`。详见 [docs/DISEASE_HERMES.md](docs/DISEASE_HERMES.md)。

## 接入 Claude Code / Codex / 任意 MCP·CLI Agent

```bash
python3 -m hermes mcp          # 零依赖 stdio MCP server，暴露 13 个 Hermes 工具（无需安装 mcp）
python3 scripts/mcp_client_demo.py     # 真实 MCP 客户端端到端联调（纯标准库）
```

Claude Code（`.mcp.json`）/ Codex（`~/.codex/config.toml`）注册 `python3 -m hermes mcp`
即可在对话中调用古籍检索、Skill 问答、方药溯源、处方匹配、疾病发现、可视化导出等工具；不支持 MCP 的
Agent 直接调 CLI（输出 JSON）。详见 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

## 文档与测试

- [docs/HERMES_V5_PROTOCOL.md](docs/HERMES_V5_PROTOCOL.md) — v5 协议全文（状态机/门控/记忆/指标）
- [docs/LLM_BACKENDS.md](docs/LLM_BACKENDS.md) — litellm 多模型后端、多评审共识、绑定校验
- [docs/DISEASE_HERMES.md](docs/DISEASE_HERMES.md) — 疾病多智能体框架（银屑病/骨质疏松/类风湿/温病/湿疹）、Disease-Skill、ECharts 可视化、迁移
- [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) — Claude Code / Codex / MCP·CLI 接入（零依赖 stdio 服务器 + 真实客户端联调）
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 架构与数据流
- [docs/SAFETY.md](docs/SAFETY.md) — 安全治理边界
- [docs/CALIBRATION.md](docs/CALIBRATION.md) — 风险控制门控（RCPS/Clopper-Pearson 有限样本保证、ECE、选择性风险）
- `prompts/` — 五个核心智能体的 v5 提示词；`examples/litellm_multi_model.py` — 多模型示例
- **评测基准**：`data/eval/shanghan_gold.jsonl` 为 55 条宋本伤寒论/金匮条文的
  人工金标准标注（62 条期望规则，含无规则误报探针）；`hermes benchmark` 输出
  分规则类型的抽取 P/R/F1、条件抽取质量与发布门控校准（正确规则 vs 误报规则的
  共识分差、gold 级精确率），报告落盘 `data/reports/benchmark_report_latest.md`
  ——任何抽取器/审核/门控改动前后都应跑一次作为回归判据。
- **风险控制校准**：`hermes calibrate` 用 RCPS + Clopper-Pearson 精确二项上界给
  分级门控加分布无关有限样本保证（精度 + 召回双向），并输出 ECE / reliability /
  选择性风险曲线；报告落盘 `data/reports/calibration_report_latest.md`，阈值落盘
  `data/eval/calibrated_gate.json`（`HERMES_CALIBRATED_GATE=1` 启用）。
- `pytest tests/`：139 项测试覆盖协议不变量（证据子串、门控阈值、修复上限、
  rejected 留档、合并仅用 silver/gold、Skill 输出契约、患者端安全拒绝、
  人审字段全仓扫描）+ litellm 后端/评审小组/绑定校验/四核心 agent LLM 接线与回落 + 疾病框架（乾癬→silver、
  圆癣→rejected、药物网络中心性、时序、断点续跑）+ 骨质疏松/类风湿 Profile、Disease-Skill 编译与 Skill RAG 接入、MCP 工具分发 + 温病/湿疹 Profile、ECharts 可视化导出、真实 MCP 客户端↔stdio 服务器端到端握手 + 外科/温病真实语料构建与隔离、五层知识图谱/旭日/雷达/PRISMA 可视化与 PNG/SVG 导出 + 扁平/嵌套语料布局编目、下载断点续传、陈旧中间态清理 + 金标准数据集完整性、基准检测/门控校准回归阈值、十八反/十九畏/毒性/妊娠筛查与工作台 MCP 工具 + 精确二项 CDF/Clopper-Pearson 上界/ECE/选择性风险的统计正确性、风险控制阈值阶梯单调性、校准门控 opt-in 接入与默认行为不变 + Azure/MiniMax 端点路由、按角色跨厂商绑定、端点变量缺省时不透传。

## 设计定位

| | |
| --- | --- |
| 旧 | 人机协同古籍规则系统（`human_review_required` / `expert_approved`） |
| **新** | **模型自主治理的古籍规则生成系统**（`autonomous_review_status` / `consensus_score` / `critic_result` / `auto_repair_applied` / `release_level` / `model_audit_trail`） |

古籍语料版权与使用规范请遵循中醫笈成的相关说明。本系统输出为古籍知识整理，
不构成诊疗建议。
