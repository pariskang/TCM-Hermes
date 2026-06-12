#!/usr/bin/env python3
"""A real MCP client (pure stdlib) that drives `python3 -m hermes mcp`.

Performs the full Model Context Protocol stdio handshake against the Hermes
server as a subprocess — initialize → notifications/initialized → tools/list →
tools/call — exactly as Claude Code / Codex would.  Run it to end-to-end
verify the integration without installing any MCP package:

    python3 scripts/mcp_client_demo.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


class MCPStdioClient:
    def __init__(self, command: list[str], env: dict | None = None):
        self.proc = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        self._id = 0

    def _send(self, obj: dict) -> None:
        self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _read(self) -> dict:
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed stdout: "
                               + self.proc.stderr.read())
        return json.loads(line)

    def request(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method,
                    "params": params or {}})
        while True:
            msg = self._read()
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(f"{method} error: {msg['error']}")
                return msg["result"]

    def notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def initialize(self) -> dict:
        result = self.request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "hermes-demo-client", "version": "1.0"}})
        self.notify("notifications/initialized")
        return result

    def list_tools(self) -> list[dict]:
        return self.request("tools/list")["tools"]

    def call_tool(self, name: str, arguments: dict) -> dict:
        res = self.request("tools/call", {"name": name, "arguments": arguments})
        text = res["content"][0]["text"] if res.get("content") else "{}"
        return {"isError": res.get("isError", False),
                "data": json.loads(text) if text.strip().startswith(("{", "["))
                else text}

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    client = MCPStdioClient([sys.executable, "-m", "hermes", "mcp"],
                            env={"HERMES_ROOT": str(root), "PATH": ""
                                 if False else __import__("os").environ.get("PATH", "")})
    try:
        info = client.initialize()
        print("✓ initialize →", info["serverInfo"], "| protocol",
              info["protocolVersion"])

        tools = client.list_tools()
        print(f"✓ tools/list → {len(tools)} tools:")
        for t in tools:
            print(f"    - {t['name']}")

        print("\n✓ tools/call hermes_list_diseases:")
        out = client.call_tool("hermes_list_diseases", {})
        for d in out["data"]["diseases"]:
            print(f"    {d['disease_id']:<22} {d['display_name']}")

        print("\n✓ tools/call hermes_match_prescription "
              "(桂枝,白芍,炙甘草,生姜,大枣):")
        out = client.call_tool("hermes_match_prescription",
                               {"herbs": "桂枝,白芍,炙甘草,生姜,大枣"})
        top = out["data"]["matches"][0]
        print(f"    → {top['formula']} (similarity {top['similarity']})")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
