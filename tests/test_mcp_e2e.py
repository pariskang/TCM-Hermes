"""End-to-end MCP stdio test: drive the real server over JSON-RPC.

Spawns `python3 -m hermes mcp` (the dependency-free stdio server) as a
subprocess and performs the full MCP handshake exactly as Claude Code / Codex
would — initialize → notifications/initialized → tools/list → tools/call —
verifying the actual wire protocol, not a mock."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class _Client:
    def __init__(self, env):
        self.p = subprocess.Popen(
            [sys.executable, "-m", "hermes", "mcp"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1, cwd=str(ROOT), env=env)
        self._id = 0

    def req(self, method, params=None):
        self._id += 1
        self.p.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "id": self._id, "method": method,
             "params": params or {}}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server closed: " + self.p.stderr.read())
            msg = json.loads(line)
            if msg.get("id") == self._id:
                return msg

    def notify(self, method, params=None):
        self.p.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params or {}}) + "\n")
        self.p.stdin.flush()

    def close(self):
        try:
            self.p.stdin.close(); self.p.terminate(); self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


@pytest.fixture()
def client(tmp_path):
    env = dict(os.environ)
    env["HERMES_ROOT"] = str(tmp_path)
    c = _Client(env)
    yield c
    c.close()


def test_mcp_handshake_and_tool_call(client):
    init = client.req("initialize", {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"}})
    assert init["result"]["serverInfo"]["name"] == "hermes"
    assert "tools" in init["result"]["capabilities"]
    client.notify("notifications/initialized")

    tools = client.req("tools/list")["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "hermes_list_diseases" in names
    assert "hermes_disease_viz" in names
    # every tool advertises an inputSchema (MCP contract)
    assert all("inputSchema" in t for t in tools)

    call = client.req("tools/call", {"name": "hermes_list_diseases",
                                     "arguments": {}})
    assert call["result"]["isError"] is False
    payload = json.loads(call["result"]["content"][0]["text"])
    ids = {d["disease_id"] for d in payload["diseases"]}
    assert {"psoriasis", "warm_disease", "eczema"} <= ids


def test_mcp_tool_error_is_result_not_protocol_error(client):
    client.req("initialize", {"protocolVersion": "2025-06-18",
                              "capabilities": {}})
    client.notify("notifications/initialized")
    # missing required arg → tool raises → MCP result with isError, not -32xxx
    call = client.req("tools/call",
                      {"name": "hermes_formula_lineage", "arguments": {}})
    assert "error" not in call
    assert call["result"]["isError"] is True


def test_mcp_unknown_method(client):
    client.req("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
    resp = client.req("nonexistent/method")
    assert resp["error"]["code"] == -32601


def test_mcp_ping(client):
    client.req("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
    assert client.req("ping")["result"] == {}
