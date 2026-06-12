# LLM 后端与多智能体共识（litellm 集成）

本页解决三件事，对应你提出的三个问题：

| 问题 | 解决 |
| --- | --- |
| 1. 默认是启发式系统，不是真正多智能体 LLM | 加入 **LiteLLMBackend**，一套接口接入几乎所有大模型；各 agent 角色可绑不同模型 |
| 2. 证据片段存在 ≠ 语义一定正确 | 新增 **span↔claim 绑定校验**（`binding.py`），长片段多方多症的弱关联会被量化、降权、并阻止进入 Gold |
| 3. 共识裁判是确定性评分，不是模型辩论共识 | 新增 **多评审小组 ReviewerPanel**（保守派/训诂/方证/临床安全/现代转译/对抗），共识由多模型投票 + 分歧检测产生 |

## 一、为什么用 litellm

`litellm.completion()` 用统一的 OpenAI 风格接口调用 OpenAI、Anthropic、Gemini、
Mistral、Groq、Together、DeepSeek、Ollama、vLLM、Azure、Bedrock 等几乎所有模型。
Hermes 的 `LiteLLMBackend` 封装了它，并支持**按 agent 角色绑定不同模型**——这正是
让「共识」从「一个模型自说自话」变成「多模型投票」的关键。

```bash
pip install -e ".[llm]"        # 安装 litellm
```

## 二、最小调用示例

```bash
# 1) 选 litellm 后端
export HERMES_BACKEND=litellm

# 2) 配置默认模型与各角色模型（任选其一或全配）
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...

export HERMES_LLM_MODEL=gpt-4o-mini                       # 默认模型
export HERMES_LLM_MODEL_EXTRACTOR=gpt-4o                   # 抽取
export HERMES_LLM_MODEL_REVIEWER=claude-sonnet-4-6         # 正向审核
export HERMES_LLM_MODEL_CRITIC=claude-opus-4-8             # 对抗式质疑
export HERMES_LLM_MODEL_JUDGE=gemini/gemini-1.5-pro        # 一致性裁决
export HERMES_LLM_MODEL_RELEVANCE_CLASSICAL=claude-opus-4-8
export HERMES_LLM_MODEL_RELEVANCE_DERMATOLOGY=gpt-4o
export HERMES_LLM_MODEL_RELEVANCE_ADVERSARIAL=claude-sonnet-4-6

# 3) 正常运行——共识自动切换为多模型辩论
python3 -m hermes review --books BOOK_SHL_SONGBEN
python3 -m hermes disease run --disease 银屑病
```

本地模型（无需联网/密钥）：

```bash
export HERMES_BACKEND=litellm
export HERMES_LLM_MODEL=ollama/qwen2.5:14b          # 或 ollama/llama3.1
export OLLAMA_API_BASE=http://localhost:11434
python3 -m hermes disease run --disease 银屑病
```

## 三、代码内调用

```python
from hermes.config import HermesConfig
from hermes.agents.backends import LiteLLMBackend
from hermes.agents.orchestrator import AutonomousReviewOrchestrator

cfg = HermesConfig(root=".", backend="litellm")
# 角色→模型可在代码里直接指定（覆盖环境变量）
backend = LiteLLMBackend(cfg, role_models={
    "extractor": "gpt-4o",
    "reviewer":  "claude-sonnet-4-6",
    "critic":    "claude-opus-4-8",
    "judge":     "gemini/gemini-1.5-pro",
})
orch = AutonomousReviewOrchestrator(cfg, backend=backend)
orch.process_book("BOOK_SHL_SONGBEN")     # 五重审核 + 多评审小组辩论
```

直接调用后端（任意角色，返回解析后的 JSON）：

```python
out = backend.complete_json(
    system="只输出 JSON：{\"verdict\":\"support|warn|reject\",\"confidence\":0-1}",
    user="…规则与原文…", role="critic")          # role 决定用哪个模型
print(out["verdict"], out["confidence"])
```

## 四、共识模式

`HERMES_CONSENSUS_MODE`：

- `auto`（默认）：LLM 后端下自动启用多评审小组辩论；启发式后端下保持原确定性评分（离线可复现，测试不变）。
- `panel`：强制启用评审小组（即使离线，小组由确定性的正向审核 + 对抗审核两路声音组成）。
- `deterministic`：始终用公式评分。

辩论如何变成共识（`consensus.py`）：

1. 硬门控不可推翻：结构无效 / 证据非子串 / critic fatal / **评审小组多数否决** → 直接 reject；
2. 评审小组分数（按各评审置信加权的 support 比例）与确定性分数按 0.6/0.4 融合；
3. 小组无多数一致（support 与 reject 并存、agreement < 0.5）→ 判 `model_conflict`；
4. 绑定松散（多方并述 / 条件与结论跨句远距）→ 扣分并封顶（多方片段不得 Gold）。

每条规则的 `review_records.panel` 保存全部评审的 verdict/confidence/所用模型，
`audit_trail` 记录一次 `ReviewerPanel.panel_debate`——多智能体共识可完整复盘。

## 五、进一步实质化（推荐做法）

- 给五个 reviewer 角色分配**不同厂商**的模型（如 OpenAI 抽取 + Anthropic 对抗 + Gemini 裁决），
  让分歧来自真正独立的模型，而非同一模型的不同提示；
- 对抗 critic 用最强模型（找错收益最高）；
- 对成本敏感的批量抽取用小模型，对裁决/对抗用大模型；
- `HERMES_LLM_TEMPERATURE=0` 保证审核可复现，写作类（report）默认 0.3。
