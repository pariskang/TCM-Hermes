"""Agent/editor integration layer: provider-agnostic tools + MCP wiring.

The `mcp` package is not importable in this sandbox, so the MCP server is
verified to (a) lazy-import cleanly and (b) raise a helpful error when mcp is
absent; the underlying tool dispatch is tested directly."""

import sys
import types

import conftest as fx
import pytest

from hermes.integrations.tools import HERMES_TOOLS, run_tool
from hermes.disease.pipeline import DiseaseHermesPipeline


def test_tool_registry_shape():
    names = {t["name"] for t in HERMES_TOOLS}
    assert {"hermes_search_classics", "hermes_ask_skill", "hermes_formula_lineage",
            "hermes_match_prescription", "hermes_list_diseases",
            "hermes_disease_run", "hermes_disease_candidates"} <= names
    for t in HERMES_TOOLS:
        assert callable(t["handler"])
        assert t["schema"]["type"] == "object"
        assert t["description"]


def test_run_tool_unknown(cfg):
    with pytest.raises(KeyError):
        run_tool("hermes_nope", {}, cfg)


def test_list_diseases_tool(cfg):
    out = run_tool("hermes_list_diseases", {}, cfg)
    ids = {d["disease_id"] for d in out["diseases"]}
    assert {"psoriasis", "osteoporosis", "rheumatoid_arthritis"} <= ids


def test_match_prescription_tool_accepts_string_and_list(cfg):
    a = run_tool("hermes_match_prescription",
                 {"herbs": "桂枝,白芍,炙甘草,生姜,大枣"}, cfg)
    b = run_tool("hermes_match_prescription",
                 {"herbs": ["桂枝", "白芍", "炙甘草", "生姜", "大枣"]}, cfg)
    assert a["matches"][0]["formula"] == "桂枝湯"
    assert b["matches"][0]["formula"] == "桂枝湯"


def test_disease_run_and_candidates_tools(cfg):
    r = run_tool("hermes_disease_run",
                 {"disease": "银屑病", "include_bronze": True,
                  "compile_skills": True}, cfg)
    assert r["candidates"] == 10
    assert "disease_skills" in r
    c = run_tool("hermes_disease_candidates",
                 {"disease": "银屑病", "limit": 3}, cfg)
    assert c["count"] >= 1
    assert "非诊断" in c["caveat"]


def test_search_classics_tool(cfg):
    from hermes.utils import write_jsonl
    write_jsonl(cfg.source_units_dir / "BOOK_TEST.jsonl",
                [fx.make_unit(fx.GUIZHI_CLAUSE).to_dict()])
    out = run_tool("hermes_search_classics", {"query": "陽浮而陰弱"}, cfg)
    assert out["evidence_chain"]
    assert out["evidence_chain"][0]["source_unit_id"]


def test_mcp_server_lazy_import_error(cfg, monkeypatch):
    # simulate mcp not installed → helpful RuntimeError, no import-time crash
    monkeypatch.setitem(sys.modules, "mcp", None)
    monkeypatch.setitem(sys.modules, "mcp.server", None)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", None)
    from hermes.integrations.mcp_server import build_server
    with pytest.raises(RuntimeError) as exc:
        build_server(cfg)
    assert "mcp" in str(exc.value).lower()


def test_mcp_server_builds_with_fake_mcp(cfg, monkeypatch):
    # inject a minimal fake FastMCP to verify every tool registers + dispatches
    registered = {}

    class _FakeMCP:
        def __init__(self, name): self.name = name

        def add_tool(self, fn, name=None, description=None):
            registered[name] = fn

        def run(self):  # pragma: no cover
            pass

    fake_pkg = types.ModuleType("mcp")
    fake_server = types.ModuleType("mcp.server")
    fake_fastmcp = types.ModuleType("mcp.server.fastmcp")
    fake_fastmcp.FastMCP = _FakeMCP
    monkeypatch.setitem(sys.modules, "mcp", fake_pkg)
    monkeypatch.setitem(sys.modules, "mcp.server", fake_server)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fake_fastmcp)

    from hermes.integrations.mcp_server import build_server
    build_server(cfg)
    assert "hermes_list_diseases" in registered
    # the registered callable dispatches and returns JSON text
    out = registered["hermes_list_diseases"]({})
    assert "银屑病" in out
