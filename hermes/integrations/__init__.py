"""Agent / editor integrations.

`tools` holds provider-agnostic capability functions (pure dict in/out) that
any harness can call.  `mcp_server` exposes them over the Model Context
Protocol (stdio) for Claude Code, Codex, and other MCP-capable agents.
"""

from .tools import HERMES_TOOLS, run_tool

__all__ = ["HERMES_TOOLS", "run_tool"]
