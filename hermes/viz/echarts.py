"""ECharts HTML exporter for TCM-Disease-Hermes workspaces.

Reads a disease workspace (network.json / temporal.json / relations.jsonl /
candidates.jsonl / summary.json) and emits interactive, self-contained HTML.
Pure stdlib + string templating; no Python plotting deps.  Data is embedded as
JSON; ECharts is loaded from a configurable CDN.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..config import HermesConfig
from ..utils import ensure_dir, read_json, read_jsonl, utc_now

ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"


@dataclass
class VizParams:
    """DIY-adjustable defaults (also exposed as in-page controls)."""
    min_edge_count: int = 1            # network/heatmap edge threshold
    top_n: int = 25                    # nodes / bars
    size_metric: str = "pagerank"      # degree|betweenness|eigenvector|pagerank
    repulsion: int = 220               # network force layout repulsion
    sankey_min_weight: int = 1
    echarts_url: str = ECHARTS_CDN
    theme: str = "light"               # light|dark

    def to_dict(self) -> dict:
        return {"min_edge_count": self.min_edge_count, "top_n": self.top_n,
                "size_metric": self.size_metric, "repulsion": self.repulsion,
                "sankey_min_weight": self.sankey_min_weight,
                "theme": self.theme}


# herb category coloring (coarse) for nicer networks
_HERB_CATEGORY = {
    "祛风": ["防風", "羌活", "獨活", "白芷", "荊芥", "防风", "蝉蜕", "蟬蛻",
            "威靈仙", "秦艽", "細辛", "桑寄生", "海風藤", "絡石藤"],
    "清热": ["石膏", "知母", "黃連", "黃柏", "黃芩", "梔子", "連翹", "金銀花",
            "銀花", "板藍根", "苦參", "龍膽草", "牡丹皮", "赤芍", "生地黃", "玄參"],
    "活血": ["當歸", "川芎", "桃仁", "牡丹皮", "赤芍", "水蛭"],
    "补益": ["熟地黃", "杜仲", "續斷", "骨碎補", "淫羊藿", "巴戟天", "肉蓯蓉",
            "枸杞子", "山茱萸", "菟絲子", "黃耆", "人參", "鹿茸", "龜板"],
    "解表": ["桂枝", "麻黃", "葛根", "薄荷", "牛蒡子", "桑葉", "菊花", "淡豆豉"],
    "温阳": ["附子", "烏頭", "乾薑", "肉桂"],
    "化湿": ["茯苓", "白朮", "蒼朮", "薏苡仁", "澤瀉", "萆薢", "土茯苓",
            "地膚子", "蛇床子", "白鮮皮", "車前子"],
}
_CAT_OF = {h: cat for cat, hs in _HERB_CATEGORY.items() for h in hs}


class VisualizationExporter:
    name = "VisualizationExporter"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def workspace(self, disease_id: str) -> Path:
        return self.config.data_dir / "disease" / disease_id

    # ------------------------------------------------------------------
    def export(self, disease_id: str, params: VizParams | None = None) -> dict:
        from ..disease.profiles import get_profile
        profile = get_profile(disease_id)
        ws = self.workspace(profile.disease_id)
        if not (ws / "summary.json").exists():
            raise FileNotFoundError(
                f"no workspace for {profile.disease_id}; run `hermes disease run "
                f"--disease {disease_id}` first")
        params = params or VizParams()

        network = read_json(ws / "network.json", {}) or {}
        temporal = read_json(ws / "temporal.json", {}) or {}
        summary = read_json(ws / "summary.json", {}) or {}
        relations = [r["triple"] for r in read_jsonl(ws / "relations.jsonl")]
        candidates = list(read_jsonl(ws / "candidates.jsonl"))

        data = {
            "disease": profile.display_name,
            "disease_id": profile.disease_id,
            "generated_at": utc_now(),
            "summary": summary,
            "network": self._network_data(network),
            "sankey": self._sankey_data(relations),
            "heatmap": self._heatmap_data(network),
            "bars": self._bar_data(candidates),
            "timeline": self._timeline_data(temporal),
            "params": params.to_dict(),
        }

        out = ensure_dir(ws / "viz")
        written = []
        for name, builder in (("dashboard", self._dashboard),):
            html = builder(data, params)
            path = out / f"{name}.html"
            path.write_text(html, encoding="utf-8")
            written.append(str(path))
        # also drop the data json for reuse / external tools
        (out / "viz_data.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"disease": profile.disease_id, "workspace": str(ws),
                "files": written + [str(out / "viz_data.json")],
                "charts": ["network", "sankey", "heatmap", "bars", "timeline"],
                "network_nodes": len(data["network"]["nodes"]),
                "sankey_links": len(data["sankey"]["links"])}

    # ---- data shaping -------------------------------------------------
    def _network_data(self, network: dict) -> dict:
        core = {c["herb"]: c for c in network.get("core_herbs", [])}
        nodes = [{"name": h, "category": _CAT_OF.get(h, "其他"),
                  "count": c.get("count", 1),
                  "degree": c.get("degree", 0), "betweenness": c.get("betweenness", 0),
                  "eigenvector": c.get("eigenvector", 0), "pagerank": c.get("pagerank", 0)}
                 for h, c in core.items()]
        names = set(core)
        links = [{"source": e["source"], "target": e["target"],
                  "count": e["count"], "pmi": e.get("pmi", 0)}
                 for e in network.get("edges", [])
                 if e["source"] in names and e["target"] in names]
        cats = sorted({n["category"] for n in nodes})
        return {"nodes": nodes, "links": links, "categories": cats}

    def _sankey_data(self, triples: list) -> dict:
        # 病机 → 治法 → 药物  (associated_with via disease omitted to keep flow clean)
        patho_treat: Counter = Counter()
        treat_herb: Counter = Counter()
        dis_symptom: Counter = Counter()
        for s, rel, o in triples:
            if rel == "treated_by":
                patho_treat[(f"病机·{s}", f"治法·{o}")] += 1
            elif rel == "uses_herb":
                treat_herb[(f"治法·{s}", f"药·{o}")] += 1
            elif rel == "has_symptom":
                dis_symptom[(f"病名·{s}", f"症·{o}")] += 1
        links, names = [], set()
        for counter in (dis_symptom, patho_treat, treat_herb):
            for (a, b), w in counter.most_common():
                links.append({"source": a, "target": b, "value": w})
                names.add(a)
                names.add(b)
        return {"nodes": [{"name": n} for n in sorted(names)], "links": links}

    def _heatmap_data(self, network: dict) -> dict:
        herbs = [c["herb"] for c in network.get("core_herbs", [])][:18]
        idx = {h: i for i, h in enumerate(herbs)}
        cells = []
        emap = {(e["source"], e["target"]): e["count"]
                for e in network.get("edges", [])}
        for a in herbs:
            for b in herbs:
                if a == b:
                    continue
                v = emap.get((a, b)) or emap.get((b, a)) or 0
                if v:
                    cells.append([idx[b], idx[a], v])
        return {"herbs": herbs, "cells": cells,
                "max": max((c[2] for c in cells), default=1)}

    def _bar_data(self, candidates: list) -> dict:
        layers = {"症状": Counter(), "病机": Counter(), "治法": Counter(),
                  "药物": Counter()}
        keymap = {"症状": "symptoms", "病机": "pathogenesis",
                  "治法": "treatment_method", "药物": "herbs"}
        for c in candidates:
            if c["review"]["release_level"] == "rejected":
                continue
            ont = c.get("ontology") or {}
            for label, k in keymap.items():
                layers[label].update(ont.get(k, []))
        return {label: c.most_common(20) for label, c in layers.items()}

    def _timeline_data(self, temporal: dict) -> dict:
        trends = temporal.get("dynasty_trends", {})
        rows = []
        for dyn, t in trends.items():
            for kind, key in (("病机", "dominant_pathogenesis"),
                              ("治法", "dominant_treatments")):
                for item in t.get(key, []):
                    rows.append([dyn, f"{kind}·{item['term']}", item["rel_freq"]])
        return {"dynasties": list(trends), "rows": rows}

    # ---- HTML ---------------------------------------------------------
    def _dashboard(self, data: dict, params: VizParams) -> str:
        payload = json.dumps(data, ensure_ascii=False)
        return _DASHBOARD_HTML.replace("__ECHARTS_URL__", params.echarts_url) \
            .replace("__DATA__", payload) \
            .replace("__DISEASE__", data["disease"]) \
            .replace("__THEME__", params.theme)


# ---------------------------------------------------------------------------
# self-contained dashboard template (ECharts + DIY controls, client-side)
# ---------------------------------------------------------------------------

_DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__DISEASE__ · TCM-Disease-Hermes 可视化</title>
<script src="__ECHARTS_URL__"></script>
<style>
 :root{--bg:#f6f4ee;--fg:#2a2a2a;--card:#fff;--accent:#b4532a;--muted:#777;}
 body.dark{--bg:#16181c;--fg:#e6e6e6;--card:#22252b;--accent:#e0925f;--muted:#9aa;}
 *{box-sizing:border-box} body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg)}
 header{padding:14px 20px;border-bottom:1px solid #0001;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
 h1{font-size:18px;margin:0} .tag{font-size:12px;color:var(--muted)}
 .tabs{display:flex;gap:6px;padding:10px 20px;flex-wrap:wrap}
 .tab{padding:6px 14px;border-radius:16px;border:1px solid #0002;cursor:pointer;font-size:13px;background:var(--card)}
 .tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
 .panel{display:none;padding:0 20px 24px} .panel.active{display:block}
 .chart{height:560px;background:var(--card);border-radius:10px;border:1px solid #0001}
 .controls{display:flex;gap:18px;flex-wrap:wrap;align-items:center;padding:12px 0;font-size:13px}
 .controls label{display:flex;gap:6px;align-items:center}
 .controls input[type=range]{vertical-align:middle}
 select,input[type=number]{padding:3px 6px;border-radius:6px;border:1px solid #0003;background:var(--card);color:var(--fg)}
 .caveat{font-size:12px;color:var(--muted);padding:6px 20px}
 button.toggle{margin-left:auto;padding:5px 10px;border-radius:8px;border:1px solid #0002;background:var(--card);color:var(--fg);cursor:pointer}
</style></head>
<body class="__THEME__">
<header>
 <h1>__DISEASE__ · 古籍知识可视化</h1>
 <span class="tag" id="meta"></span>
 <button class="toggle" onclick="document.body.classList.toggle('dark');render()">明/暗</button>
</header>
<div class="tabs" id="tabs"></div>
<div class="caveat">古今映射为候选/表型对应，非诊断；所有结论可回源至原文。No evidence, no rule.</div>
<div id="panels"></div>
<script>
const DATA = __DATA__;
const P = Object.assign({}, DATA.params);
const TABS = [
 {id:"network", name:"药物共现网络"},
 {id:"sankey",  name:"病机→治法→药物 桑基图"},
 {id:"heatmap", name:"药物共现热力图"},
 {id:"bars",    name:"高频词柱状图"},
 {id:"timeline",name:"朝代时序演变"},
];
let active = "network";
const charts = {};

function el(tag, attrs, html){const e=document.createElement(tag);Object.assign(e,attrs||{});if(html!=null)e.innerHTML=html;return e;}
function dark(){return document.body.classList.contains('dark');}

function buildUI(){
 const tabs=document.getElementById('tabs'); const panels=document.getElementById('panels');
 document.getElementById('meta').textContent =
   `条文 ${DATA.summary.candidates||0}｜分级 `+JSON.stringify(DATA.summary.by_level||{});
 TABS.forEach(t=>{
   const b=el('div',{className:'tab'+(t.id===active?' active':''),onclick:()=>{active=t.id;syncTabs();render();}},t.name);
   tabs.appendChild(b);
   const p=el('div',{className:'panel'+(t.id===active?' active':''),id:'panel-'+t.id});
   p.appendChild(controlsFor(t.id));
   const c=el('div',{className:'chart',id:'chart-'+t.id});
   p.appendChild(c); panels.appendChild(p);
 });
}
function syncTabs(){
 document.querySelectorAll('.tab').forEach((b,i)=>b.classList.toggle('active',TABS[i].id===active));
 document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='panel-'+active));
}
function ctl(label, node){const l=el('label',{},label+' ');l.appendChild(node);return l;}
function controlsFor(id){
 const c=el('div',{className:'controls'});
 if(id==='network'){
   const me=el('input',{type:'range',min:1,max:8,value:P.min_edge_count});
   me.oninput=e=>{P.min_edge_count=+e.target.value;render();};
   const sm=el('select'); ['pagerank','degree','betweenness','eigenvector'].forEach(o=>sm.appendChild(el('option',{value:o,selected:o===P.size_metric},o)));
   sm.onchange=e=>{P.size_metric=e.target.value;render();};
   const rp=el('input',{type:'range',min:60,max:600,value:P.repulsion});
   rp.oninput=e=>{P.repulsion=+e.target.value;render();};
   const tn=el('input',{type:'number',min:5,max:60,value:P.top_n,style:'width:60px'});
   tn.onchange=e=>{P.top_n=+e.target.value;render();};
   c.append(ctl('最小共现≥',me),ctl('节点大小=',sm),ctl('斥力',rp),ctl('Top-N',tn));
 } else if(id==='sankey'){
   const mw=el('input',{type:'range',min:1,max:6,value:P.sankey_min_weight});
   mw.oninput=e=>{P.sankey_min_weight=+e.target.value;render();};
   c.append(ctl('最小流量≥',mw));
 } else if(id==='heatmap'||id==='bars'){
   const tn=el('input',{type:'number',min:5,max:30,value:P.top_n,style:'width:60px'});
   tn.onchange=e=>{P.top_n=+e.target.value;render();};
   c.append(ctl('Top-N',tn));
 } else { c.append(el('span',{className:'tag'},'按朝代展示病机/治法相对频率')); }
 return c;
}

function opt(){return {network:netOpt,sankey:sankeyOpt,heatmap:heatOpt,bars:barOpt,timeline:timeOpt}[active]();}
function netOpt(){
 const nodes=DATA.network.nodes.slice().sort((a,b)=>b[P.size_metric]-a[P.size_metric]).slice(0,P.top_n);
 const keep=new Set(nodes.map(n=>n.name));
 const links=DATA.network.links.filter(l=>l.count>=P.min_edge_count&&keep.has(l.source)&&keep.has(l.target));
 const maxv=Math.max(1,...nodes.map(n=>n[P.size_metric]));
 return {tooltip:{},legend:[{data:DATA.network.categories,top:8}],series:[{
   type:'graph',layout:'force',roam:true,draggable:true,
   categories:DATA.network.categories.map(c=>({name:c})),
   force:{repulsion:P.repulsion,edgeLength:[40,120],gravity:0.08},
   label:{show:true,fontSize:11},
   data:nodes.map(n=>({name:n.name,category:DATA.network.categories.indexOf(n.category),
     symbolSize:10+38*(n[P.size_metric]/maxv),
     value:n[P.size_metric],
     tooltip:{formatter:`${n.name}<br>count ${n.count}<br>degree ${n.degree}<br>betweenness ${n.betweenness}<br>eigenvector ${n.eigenvector}<br>pagerank ${n.pagerank}`}})),
   links:links.map(l=>({source:l.source,target:l.target,value:l.count,
     lineStyle:{width:Math.min(6,l.count),opacity:.5,curveness:.1},
     tooltip:{formatter:`${l.source}–${l.target}<br>共现 ${l.count}<br>PMI ${l.pmi}`}}))}]};
}
function sankeyOpt(){
 const links=DATA.sankey.links.filter(l=>l.value>=P.sankey_min_weight);
 const used=new Set();links.forEach(l=>{used.add(l.source);used.add(l.target);});
 return {tooltip:{trigger:'item',triggerOn:'mousemove'},series:[{type:'sankey',
   data:DATA.sankey.nodes.filter(n=>used.has(n.name)),links,
   emphasis:{focus:'adjacency'},nodeAlign:'left',
   lineStyle:{color:'gradient',opacity:.45},label:{fontSize:11}}]};
}
function heatOpt(){
 const herbs=DATA.heatmap.herbs.slice(0,P.top_n);
 const keep=new Set(herbs.map((h,i)=>i));
 const cells=DATA.heatmap.cells.filter(c=>c[0]<herbs.length&&c[1]<herbs.length);
 return {tooltip:{position:'top',formatter:p=>`${herbs[p.value[1]]}–${herbs[p.value[0]]}: ${p.value[2]}`},
   grid:{height:'70%',top:'8%'},xAxis:{type:'category',data:herbs,axisLabel:{rotate:60,fontSize:10}},
   yAxis:{type:'category',data:herbs,axisLabel:{fontSize:10}},
   visualMap:{min:0,max:DATA.heatmap.max,calculable:true,orient:'horizontal',left:'center',bottom:'2%'},
   series:[{type:'heatmap',data:cells,label:{show:false}}]};
}
function barOpt(){
 const cats=Object.keys(DATA.bars);
 const sel=cats[0];
 const items=(DATA.bars[sel]||[]).slice(0,P.top_n).reverse();
 return {title:{text:'高频'+sel,left:'center',textStyle:{fontSize:13}},tooltip:{},
   grid:{left:90,right:30},xAxis:{type:'value'},
   yAxis:{type:'category',data:items.map(i=>i[0]),axisLabel:{fontSize:11}},
   series:[{type:'bar',data:items.map(i=>i[1]),itemStyle:{color:'#b4532a'},
     label:{show:true,position:'right'}}],
   graphic: cats.length>1 ? [] : []};
}
function timeOpt(){
 const dyn=DATA.timeline.dynasties;
 const terms=[...new Set(DATA.timeline.rows.map(r=>r[1]))];
 const series=terms.map(t=>({name:t,type:'line',smooth:true,
   data:dyn.map(d=>{const r=DATA.timeline.rows.find(x=>x[0]===d&&x[1]===t);return r?r[2]:0;})}));
 return {tooltip:{trigger:'axis'},legend:{type:'scroll',top:6,textStyle:{fontSize:10}},
   grid:{top:60},xAxis:{type:'category',data:dyn},yAxis:{type:'value',name:'相对频率'},
   series};
}

function render(){
 const id='chart-'+active; const dom=document.getElementById(id);
 if(charts[active]){charts[active].dispose();}
 charts[active]=echarts.init(dom, dark()?'dark':null);
 try{charts[active].setOption(opt(),true);}catch(e){dom.innerHTML='<p style="padding:20px">渲染失败：'+e+'</p>';}
}
window.addEventListener('resize',()=>{if(charts[active])charts[active].resize();});
buildUI();
if(typeof echarts==='undefined'){document.getElementById('panels').innerHTML=
 '<p style="padding:20px">ECharts 未能加载（离线？）。数据已内嵌于本文件 viz_data.json，可改用本地 echarts 或 --echarts-url 指向本地副本。</p>';}
else{render();}
</script></body></html>
"""
