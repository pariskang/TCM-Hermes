"""ResearchWorkbench — 古籍主题挖掘 / 统计 / 图谱 / 假设生成.

Outputs are publication-grade data files (JSON + CSV + DOT) computed from
released rules and source units: term frequencies, herb co-occurrence
networks, symptom–formula bipartite graphs, 古今病名映射, dynasty evolution,
and rule-based research hypotheses.  Everything carries rule ids → original
evidence, so any figure can be traced back to the clauses behind it.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..knowledge.lexicon import LEXICON
from ..rag.text_rag import ClassicalTextRAGAgent
from ..schemas import InitialRule
from ..utils import ensure_dir, read_jsonl, write_json


class ResearchWorkbench:
    name = "ResearchWorkbench"

    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.rag = ClassicalTextRAGAgent(self.config)
        self.entities = EntityExtractorAgent()

    def _released_rules(self) -> list[InitialRule]:
        rules = []
        for level in ("gold", "silver", "bronze"):
            for path in sorted(Path(self.config.rules_released_dir / level)
                               .glob("BOOK_*.jsonl")):
                rules.extend(InitialRule.from_dict(d) for d in read_jsonl(path))
        return rules

    # ------------------------------------------------------------------
    def corpus_statistics(self) -> dict:
        """High-frequency terms with supporting rule ids, by category."""
        rules = self._released_rules()
        freq = {k: Counter() for k in
                ("formula", "disease", "symptoms", "pulse", "herbs")}
        support: dict[tuple, list[str]] = defaultdict(list)
        for r in rules:
            for f in r.then_conclusions.get("formula", []):
                freq["formula"][f] += 1
                support[("formula", f)].append(r.initial_rule_id)
            for k in ("disease", "symptoms", "pulse"):
                for t in r.if_conditions.get(k, []):
                    freq[k][t] += 1
                    support[(k, t)].append(r.initial_rule_id)
            for c in r.then_conclusions.get("composition", []):
                for h in LEXICON.find_terms(c, LEXICON.herbs)[:1]:
                    freq["herbs"][h] += 1

        out = {k: [{"term": t, "count": n,
                    "rule_ids": support[(k, t)][:10]}
                   for t, n in c.most_common(30)]
               for k, c in freq.items()}
        result = {"rules_analyzed": len(rules), "frequencies": out}
        rdir = ensure_dir(self.config.research_dir)
        write_json(rdir / "corpus_statistics.json", result)
        for k, items in out.items():
            with open(rdir / f"freq_{k}.csv", "w", newline="",
                      encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["term", "count"])
                for it in items:
                    w.writerow([it["term"], it["count"]])
        return result

    # ------------------------------------------------------------------
    def herb_cooccurrence(self, min_count: int = 2) -> dict:
        """藥對/方劑網絡 from composition rules; DOT + JSON export."""
        pair_counts: Counter = Counter()
        herb_counts: Counter = Counter()
        for r in self._released_rules():
            if r.rule_type != "formula_composition_rule":
                continue
            herbs = sorted({LEXICON.find_terms(c, LEXICON.herbs)[0]
                            for c in r.then_conclusions.get("composition", [])
                            if LEXICON.find_terms(c, LEXICON.herbs)})
            herb_counts.update(herbs)
            pair_counts.update(combinations(herbs, 2))
        edges = [{"source": a, "target": b, "weight": n}
                 for (a, b), n in pair_counts.most_common()
                 if n >= min_count]
        nodes = [{"id": h, "count": n} for h, n in herb_counts.most_common(60)]
        graph = {"nodes": nodes, "edges": edges[:300]}
        rdir = ensure_dir(self.config.research_dir)
        write_json(rdir / "herb_network.json", graph)
        with open(rdir / "herb_network.dot", "w", encoding="utf-8") as f:
            f.write("graph herbs {\n  node [shape=ellipse];\n")
            for e in edges[:120]:
                f.write(f'  "{e["source"]}" -- "{e["target"]}" '
                        f'[weight={e["weight"]}, penwidth={min(e["weight"], 6)}];\n')
            f.write("}\n")
        return {"nodes": len(nodes), "edges": len(edges)}

    # ------------------------------------------------------------------
    def symptom_formula_graph(self) -> dict:
        """症狀-方劑 bipartite network from indication rules."""
        edges: Counter = Counter()
        for r in self._released_rules():
            if r.rule_type != "formula_indication_rule":
                continue
            for f in r.then_conclusions.get("formula", []):
                for s in (r.if_conditions.get("symptoms", [])
                          + r.if_conditions.get("disease", [])):
                    edges[(s, f)] += 1
        graph = {"edges": [{"symptom": s, "formula": f, "weight": n}
                           for (s, f), n in edges.most_common(400)]}
        write_json(ensure_dir(self.config.research_dir) / "symptom_formula.json", graph)
        return {"edges": len(graph["edges"])}

    # ------------------------------------------------------------------
    def disease_term_mapping(self) -> list[dict]:
        """古今病名映射 with corpus evidence counts."""
        out = []
        for m in LEXICON.disease_modern_map:
            hits = self.rag.search_exact(m["classical"], limit=50)
            out.append({**m, "corpus_mentions": len(hits),
                        "example_books": sorted({h.source_unit.book_title
                                                 for h in hits})[:5]})
        write_json(ensure_dir(self.config.research_dir) / "disease_term_mapping.json",
                   out)
        return out

    # ------------------------------------------------------------------
    def mine_topic(self, topic: str, limit: int = 60) -> dict:
        """古籍主题自动挖掘: clauses, entities, formulas, hypotheses."""
        classical_terms = [topic]
        for m in LEXICON.disease_modern_map:
            if topic in (m["modern"], m["classical"]) or topic in m["modern"]:
                classical_terms.append(m["classical"])
        classical_terms = list(dict.fromkeys(classical_terms))

        hits = []
        for term in classical_terms:
            hits.extend(self.rag.search_exact(term, limit=limit))
        if not hits:
            hits = self.rag.search_semantic(topic, limit=limit)
        seen, uniq = set(), []
        for h in hits:
            if h.source_unit.source_unit_id not in seen:
                seen.add(h.source_unit.source_unit_id)
                uniq.append(h)

        ent_counter = {k: Counter() for k in
                       ("symptoms", "pulse", "formula", "herbs", "pathomechanism")}
        for h in uniq:
            for k in ent_counter:
                ent_counter[k].update(h.source_unit.entities.get(k, []))

        hypotheses = self._hypotheses(topic, classical_terms, ent_counter)
        result = {
            "topic": topic,
            "classical_terms": classical_terms,
            "clauses_found": len(uniq),
            "books": sorted({h.source_unit.book_title for h in uniq}),
            "top_entities": {k: c.most_common(12) for k, c in ent_counter.items()},
            "evidence_chain": [h.evidence() for h in uniq[:25]],
            "hypotheses": hypotheses,
        }
        slug = "".join(ch for ch in topic if ch.isalnum())[:20] or "topic"
        write_json(ensure_dir(self.config.research_dir) / f"topic_{slug}.json", result)
        return result

    def _hypotheses(self, topic: str, terms: list[str], ents: dict) -> list[dict]:
        hyps = []
        top_formulas = [f for f, _ in ents["formula"].most_common(3)]
        top_mech = [m for m, _ in ents["pathomechanism"].most_common(2)]
        top_sym = [s for s, _ in ents["symptoms"].most_common(4)]
        if top_formulas:
            hyps.append({
                "hypothesis": (f"古籍中「{terms[0]}」证治以{'、'.join(top_formulas)}为核心，"
                               f"提示可围绕该方药组合开展现代机制与临床研究。"),
                "supporting_pattern": {"formulas": top_formulas,
                                       "symptoms": top_sym},
                "suggested_methods": ["古籍证据系统梳理", "网络药理学", "回顾性病例分析"],
                "novelty_note": "需检索现代文献验证该组合是否已被系统研究。",
            })
        if top_mech:
            hyps.append({
                "hypothesis": (f"「{terms[0]}—{top_mech[0]}」病机链提示了可检验的"
                               f"生物学过程假说。"),
                "supporting_pattern": {"pathomechanism": top_mech},
                "suggested_methods": ["concept mapping", "动物模型验证"],
                "novelty_note": "病机术语到现代机制的映射需保守表述。",
            })
        if not hyps:
            hyps.append({"hypothesis": f"语料中「{topic}」证据较少，建议扩展类目后再挖掘。",
                         "supporting_pattern": {}, "suggested_methods": [],
                         "novelty_note": ""})
        return hyps
