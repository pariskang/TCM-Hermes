"""Analytics layer: herb co-occurrence network (PMI + centralities) and
dynasty-wise temporal evolution.  Pure Python — no numpy/networkx dependency."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from itertools import combinations

from ..config import HermesConfig


# ---------------------------------------------------------------------------
# graph centralities (pure python)
# ---------------------------------------------------------------------------

def _degree_centrality(nodes, adj):
    n = len(nodes)
    if n <= 1:
        return {v: 0.0 for v in nodes}
    return {v: len(adj[v]) / (n - 1) for v in nodes}


def _eigenvector_centrality(nodes, adj, weight, iters=100, tol=1e-6):
    x = {v: 1.0 for v in nodes}
    for _ in range(iters):
        nx = {v: sum(weight.get(_edge(v, u), 0.0) * x[u] for u in adj[v])
              for v in nodes}
        norm = math.sqrt(sum(val * val for val in nx.values())) or 1.0
        nx = {v: val / norm for v, val in nx.items()}
        if sum(abs(nx[v] - x[v]) for v in nodes) < tol:
            x = nx
            break
        x = nx
    return {v: round(val, 4) for v, val in x.items()}


def _pagerank(nodes, adj, weight, damping=0.85, iters=100, tol=1e-6):
    n = len(nodes)
    if n == 0:
        return {}
    pr = {v: 1.0 / n for v in nodes}
    wdeg = {v: sum(weight.get(_edge(v, u), 0.0) for u in adj[v]) or 1.0
            for v in nodes}
    for _ in range(iters):
        npr = {}
        for v in nodes:
            s = sum(pr[u] * weight.get(_edge(v, u), 0.0) / wdeg[u] for u in adj[v])
            npr[v] = (1 - damping) / n + damping * s
        if sum(abs(npr[v] - pr[v]) for v in nodes) < tol:
            pr = npr
            break
        pr = npr
    return {v: round(val, 4) for v, val in pr.items()}


def _betweenness(nodes, adj):
    """Brandes' algorithm (unweighted), normalized."""
    bet = {v: 0.0 for v in nodes}
    for s in nodes:
        stack, pred = [], {v: [] for v in nodes}
        sigma = {v: 0.0 for v in nodes}
        sigma[s] = 1.0
        dist = {v: -1 for v in nodes}
        dist[s] = 0
        queue = [s]
        while queue:
            v = queue.pop(0)
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = {v: 0.0 for v in nodes}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bet[w] += delta[w]
    n = len(nodes)
    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    return {v: round(bet[v] * scale, 4) for v in nodes}


def _edge(a, b):
    return (a, b) if a <= b else (b, a)


class NetworkAnalysisAgent:
    name = "NetworkAnalysisAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def analyze(self, herb_lists: list[list[str]], min_count: int = 2,
                top: int = 25) -> dict:
        """herb_lists: one herb list per included candidate."""
        total = len(herb_lists)
        herb_freq: Counter = Counter()
        pair_freq: Counter = Counter()
        for herbs in herb_lists:
            hs = sorted(set(herbs))
            herb_freq.update(hs)
            for a, b in combinations(hs, 2):
                pair_freq[_edge(a, b)] += 1

        nodes = [h for h, c in herb_freq.items() if c >= 1]
        adj = defaultdict(set)
        weight: dict[tuple, float] = {}
        edges = []
        for (a, b), c in pair_freq.items():
            if c < min_count:
                continue
            adj[a].add(b)
            adj[b].add(a)
            weight[_edge(a, b)] = float(c)
            # PMI
            pa = herb_freq[a] / total
            pb = herb_freq[b] / total
            pab = c / total
            pmi = math.log(pab / (pa * pb)) if pa and pb and pab else 0.0
            edges.append({"source": a, "target": b, "count": c,
                          "pmi": round(pmi, 3)})
        nodes = [v for v in nodes if v in adj] or nodes
        adj = {v: adj[v] for v in nodes}

        degree = _degree_centrality(nodes, adj)
        between = _betweenness(nodes, adj)
        eigen = _eigenvector_centrality(nodes, adj, weight)
        pr = _pagerank(nodes, adj, weight)

        core = sorted(
            ({"herb": v, "count": herb_freq[v], "degree": degree.get(v, 0.0),
              "betweenness": between.get(v, 0.0), "eigenvector": eigen.get(v, 0.0),
              "pagerank": pr.get(v, 0.0)} for v in nodes),
            key=lambda d: (-d["pagerank"], -d["degree"]))[:top]
        edges.sort(key=lambda e: -e["count"])
        return {
            "candidates_analyzed": total,
            "n_nodes": len(nodes),
            "n_edges": len(edges),
            "core_herbs": core,
            "edges": edges[:200],
            "interpretation": self._interpret(core),
        }

    @staticmethod
    def _interpret(core: list[dict]) -> str:
        if not core:
            return "样本不足，未形成稳定药物网络。"
        names = "、".join(c["herb"] for c in core[:5])
        return f"核心药物（按 PageRank/度中心性）：{names}。"


class TemporalEvolutionAgent:
    name = "TemporalEvolutionAgent"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()

    def analyze(self, records: list[dict]) -> dict:
        """records: included candidate ontologies carrying dynasty."""
        by_dynasty_p: dict[str, Counter] = defaultdict(Counter)
        by_dynasty_t: dict[str, Counter] = defaultdict(Counter)
        for r in records:
            d = r.get("dynasty") or "未知"
            by_dynasty_p[d].update(r.get("pathogenesis", []))
            by_dynasty_t[d].update(r.get("treatment_method", []))
        order = ["隋", "唐", "宋", "金", "元", "明", "清", "民國", "未知"]
        trends = {}
        for d in sorted(by_dynasty_p, key=lambda x: order.index(x)
                        if x in order else len(order)):
            pc, tc = by_dynasty_p[d], by_dynasty_t[d]
            ptot, ttot = sum(pc.values()) or 1, sum(tc.values()) or 1
            trends[d] = {
                "dominant_pathogenesis": [
                    {"term": k, "rel_freq": round(v / ptot, 3)}
                    for k, v in pc.most_common(5)],
                "dominant_treatments": [
                    {"term": k, "rel_freq": round(v / ttot, 3)}
                    for k, v in tc.most_common(5)],
            }
        return {"dynasty_trends": trends}
