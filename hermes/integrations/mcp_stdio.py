"""Dependency-free MCP server over stdio (JSON-RPC 2.0, newline-delimited).

This implements the Model Context Protocol stdio transport directly with the
standard library, so `python3 -m hermes mcp` runs anywhere — no `mcp` package
needed — and still speaks the real wire protocol that Claude Code, Codex, and
any other MCP client expect (initialize → tools/list → tools/call).

stdout is the protocol channel — only JSON-RPC frames go there; logs go to
stderr.  Tool execution errors are returned as a result with `isError: true`
(MCP convention), not as JSON-RPC errors.

A FastMCP-based server is also available (mcp_server.build_server) for users
who prefer the official SDK; this stdlib server is the default.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from ..config import HermesConfig
from ..version import __version__
from .tools import HERMES_TOOLS, run_tool

PROTOCOL_VERSION = "2025-06-18"
_SUPPORTED = {"2025-06-18", "2025-03-26", "2024-11-05"}


def _log(msg: str) -> None:
    print(f"[hermes-mcp] {msg}", file=sys.stderr, flush=True)


def _tools_payload() -> list[dict]:
    return [{"name": t["name"], "description": t["description"],
             "inputSchema": t["schema"]} for t in HERMES_TOOLS]


class StdioMCPServer:
    def __init__(self, config: HermesConfig | None = None,
                 stdin=None, stdout=None) -> None:
        self.config = config or HermesConfig()
        self._in = stdin or sys.stdin
        self._out = stdout or sys.stdout

    # ------------------------------------------------------------------
    def _send(self, obj: dict) -> None:
        self._out.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self._out.flush()

    def _result(self, mid: Any, result: dict) -> None:
        self._send({"jsonrpc": "2.0", "id": mid, "result": result})

    def _error(self, mid: Any, code: int, message: str) -> None:
        self._send({"jsonrpc": "2.0", "id": mid,
                    "error": {"code": code, "message": message}})

    # ------------------------------------------------------------------
    def handle(self, msg: dict) -> None:
        method = msg.get("method")
        mid = msg.get("id")
        is_request = "id" in msg

        if method == "initialize":
            client_ver = (msg.get("params") or {}).get("protocolVersion")
            version = client_ver if client_ver in _SUPPORTED else PROTOCOL_VERSION
            self._result(mid, {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "hermes", "version": __version__},
                "instructions": "Hermes 古籍规则与疾病知识发现工具。古今映射为候选/"
                                "表型对应，非诊断。"})
            return
        if method in ("notifications/initialized", "initialized"):
            return  # notification, no response
        if method == "ping":
            self._result(mid, {})
            return
        if method == "tools/list":
            self._result(mid, {"tools": _tools_payload()})
            return
        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            try:
                result = run_tool(name, arguments, config=self.config)
                text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
                self._result(mid, {"content": [{"type": "text", "text": text}],
                                   "isError": False})
            except Exception as exc:  # tool error → result with isError
                self._result(mid, {
                    "content": [{"type": "text", "text": f"tool error: {exc}"}],
                    "isError": True})
            return

        if is_request:
            self._error(mid, -32601, f"method not found: {method}")

    # ------------------------------------------------------------------
    def serve(self) -> None:
        _log(f"serving {len(HERMES_TOOLS)} tools (stdio, protocol {PROTOCOL_VERSION})")
        for line in self._in:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(msg, list):       # batch
                for m in msg:
                    self.handle(m)
            else:
                self.handle(msg)


def run_stdio_server(config: HermesConfig | None = None) -> None:
    StdioMCPServer(config).serve()
