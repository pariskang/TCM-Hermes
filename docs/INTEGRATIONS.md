# 接入编辑器 / Agent：Claude Code、Codex、以及任意 MCP/CLI 客户端

Hermes 提供两条通用接入通道,覆盖几乎所有 AI 编程/Agent 工具:

1. **MCP 服务器**(推荐)——`python3 -m hermes mcp`,通过 Model Context Protocol
   暴露 Hermes 能力为工具。Claude Code、Codex 等原生支持 MCP 的客户端都可注册。
2. **CLI**——任何能跑 shell 的 Agent(含 `codex exec`、脚本化 harness)都可直接调
   `python3 -m hermes <command>`,输出为 JSON,易于解析。

> 关于 "openclaw":Hermes 不绑定任何特定客户端。只要该工具**支持 MCP**(stdio)
> 或**能执行 shell 命令**,就能用下面任一通道接入;若它支持 MCP,用第 1 种,
> 否则用第 2 种(CLI)。下面给出 Claude Code 与 Codex 的确切配置,其余 MCP 客户端
> 用同一条 `python3 -m hermes mcp` 命令即可。

## 暴露的 MCP 工具

| 工具 | 说明 |
| --- | --- |
| `hermes_search_classics` | 古籍原文 RAG(精确+语义),返回证据链 |
| `hermes_ask_skill` | Skill RAG 问答(方剂 + 疾病 Skill),含级别/一致性分/原文/安全声明 |
| `hermes_formula_lineage` | 方药溯源(最早出处/历代时间线/加减方) |
| `hermes_match_prescription` | 处方→经典方匹配 |
| `hermes_list_diseases` | 列出疾病 Profile(银屑病/骨质疏松/类风湿…) |
| `hermes_disease_run` | 运行疾病多智能体流程,可选编译 Disease-Skill |
| `hermes_disease_candidates` | 读取某疾病候选条文(按级别过滤) |

工具定义集中在 `hermes/integrations/tools.py`(纯函数,JSON 入/出),MCP 服务器
`hermes/integrations/mcp_server.py` 仅做协议封装。

## 安装

```bash
pip install -e ".[mcp]"          # 安装 mcp
# 可叠加 .[llm] 让工具内部用大模型做多评审：pip install -e ".[mcp,llm]"
```

## Claude Code

项目根放 `.mcp.json`(或 `claude mcp add hermes -- python3 -m hermes mcp`):

```json
{
  "mcpServers": {
    "hermes": {
      "command": "python3",
      "args": ["-m", "hermes", "mcp"],
      "env": { "HERMES_ROOT": "/path/to/TCM-Hermes" }
    }
  }
}
```

随后在 Claude Code 里直接说"用 hermes 查桂枝汤的方药溯源 / 跑一遍银屑病疾病发现"
即可触发对应工具。要让工具内部走大模型多评审,再加
`"env": { "HERMES_ROOT": "...", "HERMES_BACKEND": "litellm", "HERMES_LLM_MODEL": "..." }`。

## Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.hermes]
command = "python3"
args = ["-m", "hermes", "mcp"]
env = { HERMES_ROOT = "/path/to/TCM-Hermes" }
```

或不走 MCP,直接让 Codex 用 shell 调 CLI(见下)。

## 任意 MCP 客户端 / openclaw 类 Agent

同一条命令即可:

```bash
HERMES_ROOT=/path/to/TCM-Hermes python3 -m hermes mcp     # stdio MCP server
```

把它注册为该客户端的 stdio MCP server(command=`python3`, args=`["-m","hermes","mcp"]`)。

## CLI 通道(任何能跑 shell 的 Agent)

所有命令输出 JSON,可直接解析:

```bash
python3 -m hermes ask "汗出恶风脉浮缓有哪些方证依据"
python3 -m hermes lineage 桂枝湯 --brief
python3 -m hermes match-prescription "桂枝,白芍,炙甘草,生姜,大枣"
python3 -m hermes disease run --disease 类风湿 --use-corpus --skills
python3 -m hermes disease-skills --disease 银屑病 --include-bronze
```

例如 Codex 的非交互模式:`codex exec "运行 python3 -m hermes disease run --disease 骨质疏松 并总结结果"`。

## 自己的代码里调用

```python
from hermes.config import HermesConfig
from hermes.integrations.tools import run_tool

cfg = HermesConfig(root="/path/to/TCM-Hermes")
print(run_tool("hermes_ask_skill", {"query": "白疕 鳞屑 血燥"}, cfg))
print(run_tool("hermes_disease_run",
               {"disease": "类风湿", "use_corpus": True, "compile_skills": True}, cfg))
```

## 安全

所有面向用户的输出保留安全声明:疾病映射为**候选/表型对应,非诊断**,患者向
能力不提供处方/剂量(见 docs/SAFETY.md)。MCP 服务器只读本地语料与产物,
不访问网络(除非显式启用 litellm 后端);LLM 后端只读取标准 provider 环境密钥。
