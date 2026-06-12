# Hermes v5 自主审核型规则生成协议（Autonomous Model-Review Protocol）

> 自主审核 ≠ 无审核。自主审核 = 多模型、多轮、多证据、多门控的自动化审核。
>
> **No evidence, no rule. No source trace, no answer. No human review.**

本协议将古籍规则挖掘的审核机制完全模型化、程序化、可追踪化：不再设置任何
人类专家审核节点，由「证据回源 + 对抗式质疑 + 一致性裁决 + 自动修复 + 发布
分级」实现规则质量治理。

## 一、总体原则

| 原则 | 含义 |
| --- | --- |
| `autonomous_model_review_required` | 每条规则必须通过五重自主审核 |
| `model_consensus_required` | 发布以一致性裁决为前提 |
| `evidence_trace_required` | evidence_span 必须是原文严格子串 |
| `release_gate_required` | 未过门控的规则不进入任何下游 |

已废除的人审字段（`human_review_required` / `expert_approved` /
`expert_approved_required` / `needs_human` / `human_review_queue` /
`reviewer_memory` / `expert_feedback_memory` / `human_review_resolution_rate` /
`expert_approval_rate`）被列入 `protocol.BANNED_FIELDS`：SchemaValidator 拒绝
含有这些字段的规则，测试套件扫描全部源代码与产物确保其不复存在。

## 二、智能体矩阵

```text
Hermes Autonomous Agent OS
├─ DownloaderAgent                  # 自动下载/导入中醫笈成古籍（URL/7z/zip/目录树）
├─ CatalogAgent                     # 重建完整目录分类法（傷寒金匱類→傷寒/金匱/綜合/醫案）
├─ SegmenterAgent                   # 按书/章/条文切分 SourceUnit + 文本类型标注
├─ EntityExtractorAgent             # 病/证/脉/方/药/治法实体识别
├─ ClassicalTextRAGAgent            # 古籍原文 RAG（精确/语义/结构过滤）
├─ InitialRuleExtractorAgent        # 初始规则抽取（IF/THEN/BECAUSE）
├─ SchemaValidator                  # 第 1 层：结构审核
├─ EvidenceVerifierAgent            # 第 2 层：证据回源验证
├─ RuleReviewerAgent                # 第 3 层：模型正向语义审核
├─ AdversarialCriticAgent           # 第 4 层：对抗式质疑（专职找错）
├─ ConsensusJudgeAgent              # 第 5 层：多路一致性裁决
├─ RuleRepairAgent                  # 自动修复（最小编辑，绝不伪造证据）
├─ ReleaseGateAgent                 # 自动发布门控（gold/silver/bronze/rejected）
├─ AutonomousReviewOrchestrator     # 自主审核循环编排
├─ ThemeInducerAgent                # 章节/单书/类目主题归纳
├─ RuleMergerAgent                  # 跨书合并规则（保留全部证据链/变体/冲突）
├─ SkillBuilderAgent                # 编译 Hermes Skills（仅 silver/gold）
├─ SkillRAGAgent                    # Skill RAG 检索调用
├─ FormulaLineageAgent              # 方药溯源
├─ PrescriptionMatcherAgent         # 处方→经典方匹配
├─ DoctorAssistantAgent             # 医师工作台
├─ ResearchWorkbench                # 科研工作台
├─ PaperWriterAgent                 # 论文自动撰写
├─ PatientEducationAgent            # 患者教育（安全门控）
├─ MemoryCuratorAgent               # 记忆管理
└─ SafetyGovernanceAgent            # 安全边界控制
```

## 三、五重模型自主审核

每条 InitialRule 必须顺序通过：

1. **Schema Review（结构审核，程序化）** — JSON 合法性、必填字段、
   `rule_type` 受控词表、`confidence∈[0,1]`、`category_path`/`book_id`/
   `chapter_id`/`source_unit_id` 存在、禁用字段扫描。失败 → 进入
   `auto_repair_required`；不可修复（如条件型规则 IF 为空）→ 拒绝。
2. **Evidence Review（证据回源，程序化）** — 核心规则：**evidence_span 必须
   是 raw_text 的严格子串**，否则该规则不得进入后续合并。同时校验来源单元
   匹配与 evidence_type 与文本类型的一致性。输出
   `{evidence_valid, evidence_span_found, source_unit_match, evidence_type, problems}`。
3. **Semantic Review（语义审核，模型层）** — 条件/结论是否来自原文、
   证据使用是否正确、原文/注文/异文/现代解释是否混杂、治法是直述还是归纳、
   是否过度抽取，并给出建议置信度。输出
   `{semantic_review_result, unsupported_inference_detected,
   commentary_contamination_detected, over_modernized_interpretation,
   suggested_confidence, review_notes}`。
4. **Adversarial Review（对抗式质疑，模型层）** — 任务是反驳规则：过度概括、
   症状虚增（假支持检测）、注文冒充原文、方剂主治扩大、「若/不可/反/誤下/誤汗」
   等限制条件遗漏、异文误作正文、伤寒/金匮语境混淆、证据片段过长。输出
   `{critic_result: pass|minor_issue|major_issue|fatal, challenge_points,
   must_repair, recommended_repair}`。
5. **Consensus Review（一致性裁决）** — 整合至少三路独立信号：抽取自信度、
   审核建议置信度、critic 严重度、证据验证结果。硬性规则：证据失败 ⇒ 拒绝；
   critic fatal ⇒ 拒绝；两路置信分歧 > 0.35 ⇒ `model_conflict`；
   `consensus_score < 0.75` ⇒ 拒绝。裁决状态：`model_accepted` /
   `model_repaired_accepted` / `model_low_confidence` / `model_conflict` /
   `model_rejected`。

### 自主审核循环

```text
SourceUnit → InitialRuleExtractorAgent → SchemaValidator
  → EvidenceVerifierAgent → RuleReviewerAgent → AdversarialCriticAgent
  → ConsensusJudgeAgent → (RuleRepairAgent → 全层复审, 若需要)
  → ReleaseGateAgent → RuleMemory + ModelAuditMemory
```

终止条件：`schema_valid ∧ evidence_verified ∧ consensus ≥ 0.75 ∧
critic ≠ fatal ∧ repair_round ≤ 2`。

失败处理：`consensus < 0.75 → model_rejected`；`critic = fatal →
model_rejected`；`evidence_verified = false → model_rejected`；
`repair_round > 2 → model_low_confidence`。

**Rejected 规则不删除**：写入 `data/rules_rejected/`，用于审计记忆与错误分析，
永不进入合并规则与 Skill。

## 四、规则状态系统

```text
extracted → schema_validated → evidence_verified → model_reviewed
→ critic_reviewed → [auto_repaired →] model_accepted | model_repaired_accepted
| model_low_confidence | model_conflict | model_rejected
→ released_bronze | released_silver | released_gold
```

## 五、发布门控（ReleaseGateAgent）

| 级别 | 条件 | 用途 |
| --- | --- | --- |
| **Gold** | 证据有效 ∧ consensus ≥ 0.93 ∧ critic = pass ∧ 无未支持推理 ∧ 无注文污染 | Hermes 默认输出、合并规则核心依据、正式规则资产 |
| **Silver** | 证据有效 ∧ consensus ≥ 0.85 ∧ critic ∈ {pass, minor_issue} ∧ minor 已修复或已标记 | 主题归纳、Skill RAG、一般研究问答 |
| **Bronze** | 证据有效 ∧ consensus ≥ 0.75 ∧ critic ≠ fatal ∧ 解释性归纳已明确标记 | 内部检索、候选规则、章节归纳参考 |
| **Rejected** | 证据失败 / 方证严重错配 / 结构不可修复 / consensus < 0.75 | 留档 `data/rules_rejected/`，仅供误差分析 |

合并规则（MergedHermesRule）与主题规则（ThemeRule）默认**只使用 silver/gold**
初始规则（bronze 须显式配置 `merge_include_bronze`），rejected 永不支持合并。
合并规则保留：全部支持规则 ID、按级别分组、逐条证据链、variant_set（跨书
条件/组成差异）、conflict_set（应用与禁忌张力）、autonomous_review。

## 六、记忆体系（去人审化）

`corpus_memory` / `terminology_memory` / `rule_memory` / `model_audit_memory`
/ `critic_memory` / `repair_memory` / `consensus_memory` / `release_memory`
/ `skill_memory` / `evaluation_memory` / `user_workflow_memory`。

ModelAuditMemory 示例：

```json
{
  "memory_type": "model_audit_memory",
  "rule_id": "IR_SHL_SONGBEN_000123",
  "audit_summary": "證據有效，對抗審核 minor_issue，問題已自動修復。",
  "agents_involved": ["RuleReviewerAgent", "AdversarialCriticAgent",
                       "RuleRepairAgent", "ConsensusJudgeAgent"],
  "final_status": "model_repaired_accepted",
  "release_level": "silver"
}
```

## 七、质量指标

`autonomous_acceptance_rate` / `model_repair_rate` / `critic_rejection_rate`
/ `evidence_verification_rate` / `consensus_score_mean` / `gold_rule_rate`
/ `silver_rule_rate` / `bronze_rule_rate` / `model_conflict_rate`
/ `false_support_detection_rate`。

每轮自动生成 `Autonomous Review Report`（Corpus Scope / Extraction
Statistics / Release Levels / Main Critic Findings / Auto Repair Summary /
Residual Risks / Rules Ready for Skill Compilation）。

## 八、Skill 输出契约

每次 Skill 调用必须报告：selected skill、merged rule、release level、
consensus score、supporting initial rules、original evidence、variant set、
conflict set、safety notice。

## 九、模型后端

- `heuristic`（默认）：确定性词法/文法引擎，离线可复现，测试套件全覆盖；
- `anthropic`（可选）：`HERMES_BACKEND=anthropic` + `ANTHROPIC_API_KEY`，
  抽取/审核/质疑/裁决可指派不同 Claude 模型，使一致性投票成为真正的
  多模型裁决；LLM 异常时自动回落启发式引擎，保证管线不中断。

两种后端遵守同一契约：证据子串硬约束、受控词表、JSON 审核记录。
