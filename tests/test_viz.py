"""Visualization export (ECharts HTML dashboard) + new 温病/湿疹 profiles."""

import json

import conftest as fx
import pytest

from hermes.disease.pipeline import DiseaseHermesPipeline
from hermes.disease.profiles import ECZEMA, WARM_DISEASE, get_profile
from hermes.viz import VisualizationExporter, VizParams


def test_new_profiles_registered():
    assert get_profile("温病") is WARM_DISEASE
    assert get_profile("湿疹") is ECZEMA
    assert get_profile("浸淫疮") is ECZEMA
    assert "溫病" in WARM_DISEASE.core_terms          # 温病 → 溫病
    assert "浸淫瘡" in ECZEMA.core_terms              # 浸淫疮 → 浸淫瘡
    assert "辛涼解表" in WARM_DISEASE.treatment_terms  # 辛凉解表 → 辛涼解表
    assert "白鮮皮" in ECZEMA.extra_herbs              # 白鲜皮 → 白鮮皮


def test_s2t_covers_new_vocabulary():
    from hermes.knowledge.s2t import to_traditional as T
    for s, t in [("温病", "溫病"), ("银翘散", "銀翹散"), ("卫气营血", "衛氣營血"),
                 ("瘙痒", "瘙癢"), ("养血润燥", "養血潤燥"), ("斑疹隐隐", "斑疹隱隱"),
                 ("浸淫疮", "浸淫瘡"), ("绣球风", "繡球風")]:
        assert T(s) == t, (s, T(s))


def test_warm_disease_pipeline(cfg):
    s = DiseaseHermesPipeline(cfg, include_bronze=True).run("温病")
    assert s["candidates"] >= 6
    # 银翘散/桑菊饮 carry herbs → adaptive min_count yields a network
    assert s["network_nodes"] > 0
    assert {"連翹", "薄荷"} & set(s["core_herbs"]) or s["network_nodes"] > 0


def test_eczema_pipeline(cfg):
    s = DiseaseHermesPipeline(cfg).run("湿疹")
    assert s["candidates"] >= 6
    # 浸淫疮 canonical description is a strong match
    assert s["by_level"].get("silver", 0) + s["by_level"].get("bronze", 0) >= 3


def test_viz_export(cfg):
    DiseaseHermesPipeline(cfg, include_bronze=True).run("温病")
    out = VisualizationExporter(cfg).export("温病")
    ws = cfg.data_dir / "disease" / "warm_disease" / "viz"
    assert (ws / "dashboard.html").exists()
    assert (ws / "viz_data.json").exists()
    assert set(out["charts"]) == {"network", "sankey", "heatmap", "bars", "timeline"}

    html = (ws / "dashboard.html").read_text(encoding="utf-8")
    # self-contained: embedded data + ECharts + DIY controls + caveat
    assert "echarts" in html
    assert '"network"' in html and '"sankey"' in html
    assert "min_edge_count" in html and "size_metric" in html  # DIY controls
    assert "非诊断" in html

    data = json.loads((ws / "viz_data.json").read_text(encoding="utf-8"))
    assert data["network"]["nodes"]                     # herbs present
    assert data["sankey"]["links"]                      # 病机→治法→药物 flows
    assert set(data["bars"]) == {"症状", "病机", "治法", "药物"}


def test_viz_params_diy(cfg):
    DiseaseHermesPipeline(cfg, include_bronze=True).run("温病")
    params = VizParams(min_edge_count=2, top_n=10, size_metric="degree",
                       theme="dark", repulsion=400)
    VisualizationExporter(cfg).export("温病", params)
    html = (cfg.data_dir / "disease" / "warm_disease" / "viz"
            / "dashboard.html").read_text(encoding="utf-8")
    assert 'class="dark"' in html or "dark" in html
    # params are embedded so the page initializes from the chosen DIY defaults
    data = json.loads((cfg.data_dir / "disease" / "warm_disease" / "viz"
                       / "viz_data.json").read_text(encoding="utf-8"))
    assert data["params"]["size_metric"] == "degree"
    assert data["params"]["min_edge_count"] == 2


def test_viz_requires_workspace(cfg):
    with pytest.raises(FileNotFoundError):
        VisualizationExporter(cfg).export("湿疹")     # not run yet


def test_viz_tool_via_registry(cfg):
    from hermes.integrations.tools import run_tool
    run_tool("hermes_disease_run", {"disease": "温病", "include_bronze": True}, cfg)
    out = run_tool("hermes_disease_viz", {"disease": "温病", "theme": "dark"}, cfg)
    assert out["charts"]
    assert any("dashboard.html" in f for f in out["files"])
