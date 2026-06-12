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
            "kg": self._kg_data(relations),
            "network": self._network_data(network),
            "sankey": self._sankey_data(relations),
            "sunburst": self._sunburst_data(relations),
            "radar": self._radar_data(candidates),
            "heatmap": self._heatmap_data(network),
            "bars": self._bar_data(candidates),
            "timeline": self._timeline_data(temporal),
            "prisma": self._prisma_data(candidates, summary),
            "params": params.to_dict(),
        }

        out = ensure_dir(ws / "viz")
        html = self._dashboard(data, params)
        (out / "dashboard.html").write_text(html, encoding="utf-8")
        (out / "viz_data.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"disease": profile.disease_id, "workspace": str(ws),
                "files": [str(out / "dashboard.html"), str(out / "viz_data.json")],
                "charts": ["kg", "network", "sankey", "sunburst", "radar",
                           "heatmap", "bars", "timeline", "prisma"],
                "export_formats": ["png", "svg", "json"],
                "kg_nodes": len(data["kg"]["nodes"]),
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

    # ---- five-layer knowledge graph 古病名↔症状↔病机↔治法↔药物 -------------
    _LAYERS = ["古病名", "症状", "病机", "治法", "药物"]

    def _kg_data(self, triples: list, per_layer: int = 12) -> dict:
        layer_terms = {l: Counter() for l in self._LAYERS}
        raw_links: Counter = Counter()
        for s, rel, o in triples:
            if rel == "has_symptom":
                a, b = ("古病名", s), ("症状", o)
            elif rel == "associated_with":          # 病机 → 古病名
                a, b = ("病机", s), ("古病名", o)
            elif rel == "treated_by":               # 病机 → 治法
                a, b = ("病机", s), ("治法", o)
            elif rel == "uses_herb":                # 治法 → 药物
                a, b = ("治法", s), ("药物", o)
            else:
                continue
            layer_terms[a[0]][a[1]] += 1
            layer_terms[b[0]][b[1]] += 1
            raw_links[(a, b)] += 1
        # keep the top terms per layer for readability
        keep = {l: dict(c.most_common(per_layer)) for l, c in layer_terms.items()}
        nodes, idx = [], {}
        for li, layer in enumerate(self._LAYERS):
            for term, cnt in keep[layer].items():
                idx[(layer, term)] = len(nodes)
                nodes.append({"name": f"{layer}:{term}", "label": term,
                              "category": li, "layer": layer, "value": cnt})
        links = []
        for (a, b), w in raw_links.items():
            if a in idx and b in idx:
                links.append({"source": nodes[idx[a]]["name"],
                              "target": nodes[idx[b]]["name"], "value": w})
        return {"nodes": nodes, "links": links, "layers": self._LAYERS}

    def _sunburst_data(self, triples: list, breadth: int = 6) -> dict:
        # 病机 → 治法 → 药物 hierarchy
        p2t: dict = defaultdict(Counter)
        t2h: dict = defaultdict(Counter)
        for s, rel, o in triples:
            if rel == "treated_by":
                p2t[s][o] += 1
            elif rel == "uses_herb":
                t2h[s][o] += 1
        roots = []
        for patho, treats in sorted(p2t.items(),
                                    key=lambda kv: -sum(kv[1].values()))[:breadth]:
            tchildren = []
            for treat, _ in treats.most_common(breadth):
                hchildren = [{"name": h, "value": c}
                             for h, c in t2h.get(treat, Counter()).most_common(breadth)]
                tchildren.append({"name": treat,
                                  "value": sum(treats.values()) if not hchildren else None,
                                  "children": hchildren or None})
            roots.append({"name": patho, "children": tchildren})
        return {"roots": roots}

    def _radar_data(self, candidates: list, dims: int = 6) -> dict:
        by_sub: dict = defaultdict(Counter)
        overall: Counter = Counter()
        for c in candidates:
            if c["review"]["release_level"] == "rejected":
                continue
            sub = c["phenotype_evidence"].get("candidate_modern_type") or "general"
            for p in (c.get("ontology") or {}).get("pathogenesis", []):
                by_sub[sub][p] += 1
                overall[p] += 1
        indicators = [p for p, _ in overall.most_common(dims)]
        maxv = max((overall[i] for i in indicators), default=1)
        series = []
        for sub, c in sorted(by_sub.items()):
            vals = [c.get(i, 0) for i in indicators]
            if any(vals):
                series.append({"name": sub, "value": vals})
        return {"indicators": [{"name": i, "max": maxv} for i in indicators],
                "series": series}

    def _prisma_data(self, candidates: list, summary: dict) -> dict:
        levels = summary.get("by_level", {})
        excluded = (Counter(t for c in candidates
                            for t in c["exclusion"]["matched_exclusion_terms"]
                            if c["review"]["release_level"] == "rejected"))
        return {"recalled": len(candidates),
                "by_level": levels,
                "top_exclusions": excluded.most_common(8)}

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
 :root{--bg:#f6f4ee;--fg:#2a2a2a;--card:#fff;--accent:#b4532a;--muted:#777;--bd:#0001;}
 body.dark{--bg:#16181c;--fg:#e6e6e6;--card:#22252b;--accent:#e0925f;--muted:#9aa;--bd:#fff1;}
 *{box-sizing:border-box} body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg)}
 header{padding:14px 20px;border-bottom:1px solid var(--bd);display:flex;align-items:center;gap:14px;flex-wrap:wrap}
 h1{font-size:18px;margin:0} .tag{font-size:12px;color:var(--muted)}
 .tabs{display:flex;gap:6px;padding:10px 20px;flex-wrap:wrap}
 .tab{padding:6px 13px;border-radius:16px;border:1px solid var(--bd);cursor:pointer;font-size:13px;background:var(--card)}
 .tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
 .panel{display:none;padding:0 20px 24px} .panel.active{display:block}
 .toolbar{display:flex;gap:18px;flex-wrap:wrap;align-items:center;padding:10px 0;font-size:13px}
 .toolbar label{display:flex;gap:6px;align-items:center}
 .chart{height:600px;background:var(--card);border-radius:10px;border:1px solid var(--bd)}
 select,input[type=number]{padding:3px 6px;border-radius:6px;border:1px solid var(--bd);background:var(--card);color:var(--fg)}
 .caveat{font-size:12px;color:var(--muted);padding:6px 20px}
 button{padding:5px 10px;border-radius:8px;border:1px solid var(--bd);background:var(--card);color:var(--fg);cursor:pointer;font-size:12px}
 button:hover{border-color:var(--accent)} .exp{margin-left:auto;display:flex;gap:6px}
</style></head>
<body class="__THEME__">
<header>
 <h1>__DISEASE__ · 古籍知识可视化</h1>
 <span class="tag" id="meta"></span>
 <button onclick="document.body.classList.toggle('dark');render()">明/暗</button>
</header>
<div class="tabs" id="tabs"></div>
<div class="caveat">古今映射为候选/表型对应，非诊断；所有结论可回源至原文。No evidence, no rule. 每张图可导出 PNG / SVG / JSON。</div>
<div id="panels"></div>
<script>
const DATA = __DATA__;
const P = Object.assign({}, DATA.params);
const TABS = [
 {id:"kg",      name:"五层知识图谱"},
 {id:"network", name:"药物共现网络"},
 {id:"sankey",  name:"病机→治法→药物桑基"},
 {id:"sunburst",name:"病机治法旭日图"},
 {id:"radar",   name:"分型病机雷达"},
 {id:"heatmap", name:"药物共现热力"},
 {id:"bars",    name:"高频词柱状"},
 {id:"timeline",name:"朝代时序演变"},
 {id:"prisma",  name:"召回→纳入流程"},
];
let active = "kg";
let barCat = null;
const charts = {};
function el(t,a,h){const e=document.createElement(t);Object.assign(e,a||{});if(h!=null)e.innerHTML=h;return e;}
function dark(){return document.body.classList.contains('dark');}
function ctl(lbl,node){const l=el('label',{},lbl+' ');l.appendChild(node);return l;}

function buildUI(){
 const tabs=document.getElementById('tabs'),panels=document.getElementById('panels');
 document.getElementById('meta').textContent=`条文 ${DATA.summary.candidates||0}｜分级 `+JSON.stringify(DATA.summary.by_level||{});
 TABS.forEach(t=>{
   tabs.appendChild(el('div',{className:'tab'+(t.id===active?' active':''),onclick:()=>{active=t.id;sync();render();}},t.name));
   const p=el('div',{className:'panel'+(t.id===active?' active':''),id:'panel-'+t.id});
   p.appendChild(toolbarFor(t.id));
   p.appendChild(el('div',{className:'chart',id:'chart-'+t.id}));
   panels.appendChild(p);
 });
}
function sync(){
 document.querySelectorAll('.tab').forEach((b,i)=>b.classList.toggle('active',TABS[i].id===active));
 document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id==='panel-'+active));
}
function num(v,mn,mx,on){const e=el('input',{type:'number',min:mn,max:mx,value:v,style:'width:60px'});e.onchange=ev=>{on(+ev.target.value);render();};return e;}
function rng(v,mn,mx,on){const e=el('input',{type:'range',min:mn,max:mx,value:v});e.oninput=ev=>{on(+ev.target.value);render();};return e;}
function sel(opts,cur,on){const s=el('select');opts.forEach(o=>s.appendChild(el('option',{value:o,selected:o===cur},o)));s.onchange=e=>{on(e.target.value);render();};return s;}
function toolbarFor(id){
 const c=el('div',{className:'toolbar'});
 if(id==='kg'){c.append(ctl('每层Top-N',num(P.top_n,4,20,v=>P.top_n=v)),el('span',{className:'tag'},'古病名→症状→病机→治法→药物，可拖拽缩放'));}
 else if(id==='network'){c.append(ctl('最小共现≥',rng(P.min_edge_count,1,8,v=>P.min_edge_count=v)),ctl('节点大小=',sel(['pagerank','degree','betweenness','eigenvector'],P.size_metric,v=>P.size_metric=v)),ctl('斥力',rng(P.repulsion,60,600,v=>P.repulsion=v)),ctl('Top-N',num(P.top_n,5,60,v=>P.top_n=v)));}
 else if(id==='sankey'){c.append(ctl('最小流量≥',rng(P.sankey_min_weight,1,6,v=>P.sankey_min_weight=v)));}
 else if(id==='heatmap'){c.append(ctl('Top-N',num(P.top_n,5,18,v=>P.top_n=v)));}
 else if(id==='bars'){const cats=Object.keys(DATA.bars);barCat=barCat||cats[0];c.append(ctl('维度',sel(cats,barCat,v=>barCat=v)),ctl('Top-N',num(P.top_n,5,30,v=>P.top_n=v)));}
 else if(id==='radar'){c.append(el('span',{className:'tag'},'各现代分型的病机谱（计数）'));}
 else if(id==='sunburst'){c.append(el('span',{className:'tag'},'点击下钻：病机→治法→药物'));}
 else if(id==='timeline'){c.append(el('span',{className:'tag'},'按朝代展示病机/治法相对频率'));}
 else {c.append(el('span',{className:'tag'},'高召回→排除→证据回源→共识分级'));}
 const exp=el('div',{className:'exp'});
 exp.append(el('button',{onclick:exportPNG},'导出 PNG'),el('button',{onclick:exportSVG},'导出 SVG'),el('button',{onclick:exportJSON},'导出数据'));
 c.append(exp); return c;
}

function opt(){return {kg:kgOpt,network:netOpt,sankey:sankeyOpt,sunburst:sunOpt,radar:radarOpt,heatmap:heatOpt,bars:barOpt,timeline:timeOpt,prisma:prismaOpt}[active]();}

function kgOpt(){
 const L=DATA.kg.layers,N=P.top_n,by={};L.forEach(l=>by[l]=[]);
 DATA.kg.nodes.forEach(n=>by[n.layer].push(n));
 const keep=new Set();L.forEach(l=>by[l].sort((a,b)=>b.value-a.value).slice(0,N).forEach(n=>keep.add(n.name)));
 const nodes=DATA.kg.nodes.filter(n=>keep.has(n.name));
 const cnt={},cw=1000/Math.max(1,L.length-1);
 const per={};L.forEach(l=>per[l]=nodes.filter(n=>n.layer===l).length);
 nodes.forEach(n=>{cnt[n.layer]=(cnt[n.layer]||0)+1;n.x=n.category*cw;n.y=620*(cnt[n.layer]/(per[n.layer]+1));});
 const links=DATA.kg.links.filter(l=>keep.has(l.source)&&keep.has(l.target));
 return {tooltip:{},legend:[{data:L,top:6}],series:[{type:'graph',layout:'none',roam:true,draggable:true,
   categories:L.map(l=>({name:l})),label:{show:true,formatter:p=>p.data.label,fontSize:11,color:dark()?'#ddd':'#333'},
   edgeSymbol:['none','arrow'],edgeSymbolSize:6,
   data:nodes.map(n=>({name:n.name,label:n.label,category:n.category,x:n.x,y:n.y,fixed:false,
     symbolSize:12+Math.min(30,n.value*2),value:n.value,
     tooltip:{formatter:`${n.layer}：${n.label}（${n.value}）`}})),
   links:links.map(l=>({source:l.source,target:l.target,value:l.value,
     lineStyle:{width:Math.min(5,l.value),opacity:.35,curveness:.05},
     tooltip:{formatter:`${l.source} → ${l.target}（${l.value}）`}}))}]};
}
function netOpt(){
 const nodes=DATA.network.nodes.slice().sort((a,b)=>b[P.size_metric]-a[P.size_metric]).slice(0,P.top_n);
 const keep=new Set(nodes.map(n=>n.name));
 const links=DATA.network.links.filter(l=>l.count>=P.min_edge_count&&keep.has(l.source)&&keep.has(l.target));
 const mv=Math.max(1e-9,...nodes.map(n=>n[P.size_metric]));
 return {tooltip:{},legend:[{data:DATA.network.categories,top:8}],series:[{type:'graph',layout:'force',roam:true,draggable:true,
   categories:DATA.network.categories.map(c=>({name:c})),force:{repulsion:P.repulsion,edgeLength:[40,120],gravity:.08},
   label:{show:true,fontSize:11},
   data:nodes.map(n=>({name:n.name,category:DATA.network.categories.indexOf(n.category),
     symbolSize:10+38*(n[P.size_metric]/mv),value:n[P.size_metric],
     tooltip:{formatter:`${n.name}<br>count ${n.count}<br>degree ${n.degree}<br>betweenness ${n.betweenness}<br>eigenvector ${n.eigenvector}<br>pagerank ${n.pagerank}`}})),
   links:links.map(l=>({source:l.source,target:l.target,value:l.count,
     lineStyle:{width:Math.min(6,l.count),opacity:.5,curveness:.1},
     tooltip:{formatter:`${l.source}–${l.target}<br>共现 ${l.count}<br>PMI ${l.pmi}`}}))}]};
}
function sankeyOpt(){
 const links=DATA.sankey.links.filter(l=>l.value>=P.sankey_min_weight);
 const used=new Set();links.forEach(l=>{used.add(l.source);used.add(l.target);});
 if(!links.length)return{title:{text:'暂无足够关系数据',left:'center',top:'center',textStyle:{color:'#999'}}};
 return {tooltip:{trigger:'item',triggerOn:'mousemove'},series:[{type:'sankey',data:DATA.sankey.nodes.filter(n=>used.has(n.name)),links,emphasis:{focus:'adjacency'},nodeAlign:'left',lineStyle:{color:'gradient',opacity:.45},label:{fontSize:11}}]};
}
function sunOpt(){
 if(!DATA.sunburst.roots.length)return{title:{text:'暂无足够病机-治法-药物数据',left:'center',top:'center',textStyle:{color:'#999'}}};
 return {tooltip:{},series:[{type:'sunburst',radius:[0,'92%'],data:DATA.sunburst.roots,label:{minAngle:8,rotate:'radial'},emphasis:{focus:'ancestor'},
   levels:[{},{r0:'12%',r:'45%',label:{rotate:'tangential'}},{r0:'45%',r:'72%'},{r0:'72%',r:'90%',label:{align:'right'}}]}]};
}
function radarOpt(){
 if(!DATA.radar.indicators.length)return{title:{text:'样本不足',left:'center',top:'center',textStyle:{color:'#999'}}};
 return {tooltip:{},legend:{top:6,type:'scroll'},radar:{indicator:DATA.radar.indicators,radius:'62%'},
   series:[{type:'radar',areaStyle:{opacity:.12},data:DATA.radar.series.map(s=>({name:s.name,value:s.value}))}]};
}
function heatOpt(){
 const herbs=DATA.heatmap.herbs.slice(0,P.top_n);
 const cells=DATA.heatmap.cells.filter(c=>c[0]<herbs.length&&c[1]<herbs.length);
 if(!cells.length)return{title:{text:'共现数据不足',left:'center',top:'center',textStyle:{color:'#999'}}};
 return {tooltip:{position:'top',formatter:p=>`${herbs[p.value[1]]}–${herbs[p.value[0]]}: ${p.value[2]}`},
   grid:{height:'70%',top:'8%'},xAxis:{type:'category',data:herbs,axisLabel:{rotate:60,fontSize:10}},
   yAxis:{type:'category',data:herbs,axisLabel:{fontSize:10}},
   visualMap:{min:0,max:DATA.heatmap.max,calculable:true,orient:'horizontal',left:'center',bottom:'2%'},
   series:[{type:'heatmap',data:cells}]};
}
function barOpt(){
 const items=(DATA.bars[barCat]||[]).slice(0,P.top_n).reverse();
 return {title:{text:'高频'+barCat,left:'center',textStyle:{fontSize:13}},tooltip:{},
   grid:{left:100,right:40},xAxis:{type:'value'},yAxis:{type:'category',data:items.map(i=>i[0]),axisLabel:{fontSize:11}},
   series:[{type:'bar',data:items.map(i=>i[1]),itemStyle:{color:'#b4532a'},label:{show:true,position:'right'}}]};
}
function timeOpt(){
 const dyn=DATA.timeline.dynasties,terms=[...new Set(DATA.timeline.rows.map(r=>r[1]))];
 if(!dyn.length)return{title:{text:'暂无朝代信息',left:'center',top:'center',textStyle:{color:'#999'}}};
 const series=terms.map(t=>({name:t,type:'line',smooth:true,data:dyn.map(d=>{const r=DATA.timeline.rows.find(x=>x[0]===d&&x[1]===t);return r?r[2]:0;})}));
 return {tooltip:{trigger:'axis'},legend:{type:'scroll',top:6,textStyle:{fontSize:10}},grid:{top:60},xAxis:{type:'category',data:dyn},yAxis:{type:'value',name:'相对频率'},series};
}
function prismaOpt(){
 const lv=DATA.prisma.by_level||{},inc=(lv.gold||0)+(lv.silver||0)+(lv.bronze||0);
 const data=[{name:'召回候选 '+DATA.prisma.recalled,value:DATA.prisma.recalled},
  {name:'非排除',value:DATA.prisma.recalled-(lv.rejected||0)},
  {name:'纳入(Bronze+) '+inc,value:inc},{name:'Silver+',value:(lv.gold||0)+(lv.silver||0)},{name:'Gold '+(lv.gold||0),value:lv.gold||0}];
 const ex=(DATA.prisma.top_exclusions||[]).map(e=>e[0]+'('+e[1]+')').join('、');
 return {title:{text:'高召回 → 排除鉴别 → 证据回源 → 共识分级',left:'center',textStyle:{fontSize:13},
   subtext:ex?('主要排除：'+ex):'',subtextStyle:{fontSize:11}},tooltip:{trigger:'item'},
   series:[{type:'funnel',left:'12%',width:'76%',top:70,sort:'descending',gap:2,minSize:'14%',
     label:{formatter:'{b}: {c}',fontSize:12},data}]};
}

function render(){
 const dom=document.getElementById('chart-'+active);
 if(charts[active])charts[active].dispose();
 charts[active]=echarts.init(dom,dark()?'dark':null);
 try{charts[active].setOption(opt(),true);}catch(e){dom.innerHTML='<p style="padding:20px">渲染失败：'+e+'</p>';}
}
function dl(name,url){const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();}
function exportPNG(){const c=charts[active];if(!c)return;dl(DATA.disease_id+'_'+active+'.png',c.getDataURL({type:'png',pixelRatio:2,backgroundColor:dark()?'#16181c':'#fff'}));}
function exportSVG(){const d=el('div',{style:'width:1280px;height:760px;position:absolute;left:-99999px;top:0'});document.body.appendChild(d);
 const t=echarts.init(d,dark()?'dark':null,{renderer:'svg'});t.setOption(opt(),true);
 let svg;try{svg=t.renderToSVGString();}catch(e){svg=null;}
 t.dispose();d.remove();
 if(svg)dl(DATA.disease_id+'_'+active+'.svg','data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg));}
function exportJSON(){const key={kg:'kg',network:'network',sankey:'sankey',sunburst:'sunburst',radar:'radar',heatmap:'heatmap',bars:'bars',timeline:'timeline',prisma:'prisma'}[active];
 dl(DATA.disease_id+'_'+active+'.json','data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(DATA[key],null,2)));}
window.addEventListener('resize',()=>{if(charts[active])charts[active].resize();});
buildUI();
if(typeof echarts==='undefined'){document.getElementById('panels').innerHTML='<p style="padding:20px">ECharts 未能加载（离线？）。数据已内嵌于本文件及 viz_data.json，可用 --echarts-url 指向本地副本，或直接复用 JSON。</p>';}
else{render();}
</script></body></html>
"""
