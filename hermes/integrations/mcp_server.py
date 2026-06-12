"""Hermes MCP server — exposes Hermes tools over the Model Context Protocol.

This is the universal integration point: any MCP-capable agent (Claude Code,
Codex, and other MCP clients) can register this stdio server and call the
Hermes tools defined in `tools.py`.  The `mcp` package is imported lazily, so
`import hermes` works without it; install with `pip install "mcp"` (or
`pip install -e ".[mcp]"`).

Register in Claude Code (.mcp.json or `claude mcp add`):

    {
      "mcpServers": {
        "hermes": {"command": "python3", "args": ["-m", "hermes", "mcp"],
                   "env": {"HERMES_ROOT": "/path/to/TCM-Hermes"}}
      }
    }

Register in Codex (~/.codex/config.toml):

    [mcp_servers.hermes]
    command = "python3"
    args = ["-m", "hermes", "mcp"]
    env = { HERMES_ROOT = "/path/to/TCM-Hermes" }

Any other MCP/stdio client uses the same `python3 -m hermes mcp` command.
Agents that only run shell can call the CLI directly (see docs/INTEGRATIONS.md).
"""

from __future__ import annotations

import json

from ..config import HermesConfig
from .tools import HERMES_TOOLS, run_tool


def build_server(config: HermesConfig | None = None):
    """Build a FastMCP server registering every Hermes tool. Lazy-imports mcp."""
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            'pip install "mcp" to run the Hermes MCP server '
            "(python3 -m hermes mcp)") from exc

    cfg = config or HermesConfig()
    server = FastMCP("hermes")

    def _make(tool: dict):
        def _call(arguments: dict | None = None) -> str:
            result = run_tool(tool["name"], arguments or {}, config=cfg)
            return json.dumps(result, ensure_ascii=False, indent=2, default=str)
        _call.__name__ = tool["name"]
        _call.__doc__ = tool["description"]
        return _call

    for tool in HERMES_TOOLS:
        # register a single-arg tool taking the JSON-schema `arguments` object;
        # FastMCP exposes name + docstring, the dispatch validates internally
        server.add_tool(_make(tool), name=tool["name"],
                        description=tool["description"])
    return server


def run_server(config: HermesConfig | None = None) -> None:
    build_server(config).run()


if __name__ == "__main__":  # pragma: no cover
    run_server()
