"""GoldBenchmark — extraction & gate quality against a hand-curated gold set.

The gold set (`data/eval/shanghan_gold.jsonl`) is a clause-level annotation of
representative 宋本《傷寒論》/《金匱》 passages: each record carries the exact
raw_text and the rules a human reader expects (rule_type + key conclusion +
salient conditions).  The benchmark runs the real extractor + the full
five-layer autonomous review on every clause and reports:

* detection precision / recall / F1 per rule type and micro-averaged;
* condition extraction quality on correctly detected formula rules;
* release-gate calibration — do correct rules score higher and land in
  better levels than spurious ones? (gold_precision is the fraction of
  gold-released extractions that are actually correct.)

This is the yardstick for every extractor / reviewer / gate change: run
`python3 -m hermes benchmark` before and after.
"""

from __future__ import annotations

from pathlib import Path

from ..config import HermesConfig
from ..knowledge.entities import EntityExtractorAgent
from ..schemas import SourceUnit
from ..utils import read_jsonl, utc_now, write_json

EVAL_TYPES = (
    "formula_indication_rule", "contraindication_rule", "mistreatment_rule",
    "prognosis_rule", "transmission_rule", "disease_definition_rule",
    "pulse_pattern_rule", "formula_composition_rule", "preparation_rule",
)


def _term_hit(a: str, b: str) -> bool:
    return bool(a) and bool(b) and (a in b or b in a)


class GoldBenchmark:
    name = "GoldBenchmark"

    def __init__(self, config: HermesConfig | None = None,
                 dataset: str | Path | None = None, backend=None) -> None:
        self.config = config or HermesConfig()
        self.dataset = Path(dataset) if dataset else \
            self.config.data_dir / "eval" / "shanghan_gold.jsonl"
        from ..agents.orchestrator import AutonomousReviewOrchestrator
        self.orch = AutonomousReviewOrchestrator(self.config, backend=backend)
        self.entities = EntityExtractorAgent()

    # ------------------------------------------------------------------
    def _unit(self, rec: dict, seq: int) -> SourceUnit:
        return SourceUnit(
            source_unit_id=f"SU_EVAL_{seq:06d}",
            category_path=["傷寒金匱類", rec.get("subcategory", "傷寒")],
            book_id="BOOK_EVAL",
            book_title=rec.get("book_title", "傷寒論(宋本)"),
            book_type="original",
            chapter_id="CH_EVAL_001",
            chapter_title="評測條文",
            seq=seq,
            raw_text=rec["raw_text"],
            text_type=rec.get("text_type", "original"),
            clause_no=rec.get("clause_no"),
            entities=self.entities.extract(rec["raw_text"]),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _matches(expected: dict, rule) -> bool:
        rt = expected["rule_type"]
        if rule.rule_type != rt:
            return False
        concl = rule.then_conclusions
        if rt in ("formula_indication_rule", "formula_composition_rule",
                  "preparation_rule"):
            return expected.get("formula") in concl.get("formula", [])
        if rt == "contraindication_rule":
            return any(_term_hit(expected.get("prohibition", ""), p)
                       for p in concl.get("prohibition", []))
        if rt == "mistreatment_rule":
            return any(_term_hit(expected.get("mistreatment", ""), m)
                       for m in concl.get("mistreatment", []))
        if rt == "prognosis_rule":
            return any(_term_hit(expected.get("prognosis", ""), p)
                       for p in concl.get("prognosis", []))
        if rt == "disease_definition_rule":
            exp = expected.get("disease", "").rstrip("病")
            return any(d.rstrip("病") == exp for d in concl.get("disease", []))
        if rt == "pulse_pattern_rule":
            return any(_term_hit(expected.get("pattern", ""), p)
                       for p in concl.get("pattern", []))
        if rt == "transmission_rule":
            exp = expected.get("transmission", "")
            return not exp or any(_term_hit(exp, t)
                                  for t in concl.get("transmission", []))
        return False

    # ------------------------------------------------------------------
    def run(self) -> dict:
        records = list(read_jsonl(self.dataset))
        by_type: dict[str, dict] = {
            t: {"expected": 0, "detected": 0, "extracted": 0, "correct": 0}
            for t in EVAL_TYPES}
        cond_hits = cond_expected = cond_extracted = cond_correct = 0
        correct_rules, spurious_rules = [], []
        misses: list[dict] = []

        for i, rec in enumerate(records):
            unit = self._unit(rec, i + 1)
            extracted = [r for r in self.orch.extractor.extract(unit)
                         if r.rule_type in EVAL_TYPES]
            for r in extracted:
                self.orch.review_rule(r, unit)

            expected = rec.get("expected_rules", [])
            matched_rule_ids: set[str] = set()
            for exp in expected:
                by_type[exp["rule_type"]]["expected"] += 1
                hits = [r for r in extracted if self._matches(exp, r)]
                if hits:
                    by_type[exp["rule_type"]]["detected"] += 1
                    matched_rule_ids.update(r.initial_rule_id for r in hits)
                    # condition quality on the best (first) hit of formula rules
                    exp_conds = exp.get("conditions", [])
                    if exp["rule_type"] == "formula_indication_rule" and exp_conds:
                        got = [t for t in hits[0].all_condition_terms() if t]
                        cond_expected += len(exp_conds)
                        cond_hits += sum(any(_term_hit(e, g) for g in got)
                                         for e in exp_conds)
                        cond_extracted += len(got)
                        cond_correct += sum(any(_term_hit(g, e) for e in exp_conds)
                                            for g in got)
                else:
                    misses.append({"clause_id": rec["clause_id"],
                                   "rule_type": exp["rule_type"],
                                   "key": exp.get("formula") or exp.get("disease")
                                   or exp.get("prohibition") or exp.get("prognosis")
                                   or exp.get("pattern") or exp.get("mistreatment")
                                   or exp.get("transmission", "")})
            for r in extracted:
                by_type[r.rule_type]["extracted"] += 1
                if r.initial_rule_id in matched_rule_ids or \
                        any(self._matches(exp, r) for exp in expected):
                    by_type[r.rule_type]["correct"] += 1
                    correct_rules.append(r)
                else:
                    spurious_rules.append(r)

        # ---- aggregate ------------------------------------------------
        def prf(d: dict) -> dict:
            p = d["correct"] / d["extracted"] if d["extracted"] else None
            r = d["detected"] / d["expected"] if d["expected"] else None
            f1 = (2 * p * r / (p + r)) if p and r and (p + r) else None
            rnd = lambda x: round(x, 3) if x is not None else None
            return {**d, "precision": rnd(p), "recall": rnd(r), "f1": rnd(f1)}

        micro = {k: sum(v[k] for v in by_type.values())
                 for k in ("expected", "detected", "extracted", "correct")}

        def calib(rules) -> dict:
            if not rules:
                return {"rules": 0, "mean_consensus": None, "levels": {}}
            levels: dict[str, int] = {}
            for r in rules:
                lv = r.autonomous_review.release_level or "none"
                levels[lv] = levels.get(lv, 0) + 1
            return {"rules": len(rules),
                    "mean_consensus": round(sum(
                        r.autonomous_review.consensus_score for r in rules)
                        / len(rules), 3),
                    "levels": levels}

        cal_correct, cal_spurious = calib(correct_rules), calib(spurious_rules)
        gold_total = cal_correct["levels"].get("gold", 0) \
            + cal_spurious["levels"].get("gold", 0)
        released = {"gold", "silver", "bronze"}
        rel_correct = sum(v for k, v in cal_correct["levels"].items()
                          if k in released)
        rel_total = rel_correct + sum(v for k, v in cal_spurious["levels"].items()
                                      if k in released)

        return {
            "generated_at": utc_now(),
            "dataset": str(self.dataset),
            "clauses": len(records),
            "backend": getattr(self.orch.backend, "kind", "heuristic"),
            "micro": prf(micro),
            "by_rule_type": {t: prf(d) for t, d in by_type.items()
                             if d["expected"] or d["extracted"]},
            "condition_quality": {
                "recall": round(cond_hits / cond_expected, 3)
                if cond_expected else None,
                "precision": round(cond_correct / cond_extracted, 3)
                if cond_extracted else None,
            },
            "gate_calibration": {
                "correct": cal_correct,
                "spurious": cal_spurious,
                # separation is only meaningful with samples on both sides
                "consensus_separation": round(
                    cal_correct["mean_consensus"]
                    - cal_spurious["mean_consensus"], 3)
                if cal_correct["rules"] and cal_spurious["rules"] else None,
                "gold_precision": round(
                    cal_correct["levels"].get("gold", 0) / gold_total, 3)
                if gold_total else None,
                "released_precision": round(rel_correct / rel_total, 3)
                if rel_total else None,
            },
            "misses": misses,
        }

    # ------------------------------------------------------------------
    def report(self, results: dict | None = None) -> Path:
        """Write a markdown report + raw JSON next to the governance reports."""
        res = results or self.run()
        out_dir = self.config.reports_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / "benchmark_results.json", res)
        lines = [
            "# Extraction Benchmark (Gold Set)", "",
            f"- Generated: {res['generated_at']}",
            f"- Dataset: {res['dataset']} ({res['clauses']} clauses)",
            f"- Backend: {res['backend']}", "",
            "## Detection (micro)", "",
            "| precision | recall | f1 |", "| --- | --- | --- |",
            f"| {res['micro']['precision']} | {res['micro']['recall']} "
            f"| {res['micro']['f1']} |", "",
            "## Per rule type", "",
            "| rule_type | expected | detected | extracted | correct "
            "| precision | recall | f1 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for t, d in res["by_rule_type"].items():
            lines.append(f"| {t} | {d['expected']} | {d['detected']} "
                         f"| {d['extracted']} | {d['correct']} "
                         f"| {d['precision']} | {d['recall']} | {d['f1']} |")
        cq, gc = res["condition_quality"], res["gate_calibration"]
        lines += [
            "", "## Condition quality (matched formula rules)", "",
            f"- recall {cq['recall']} / precision {cq['precision']}", "",
            "## Release-gate calibration", "",
            f"- correct rules: {gc['correct']['rules']}, mean consensus "
            f"{gc['correct']['mean_consensus']}, levels {gc['correct']['levels']}",
            f"- spurious rules: {gc['spurious']['rules']}, mean consensus "
            f"{gc['spurious']['mean_consensus']}, levels {gc['spurious']['levels']}",
            f"- consensus separation (correct − spurious): "
            f"{gc['consensus_separation']}",
            f"- gold precision: {gc['gold_precision']} / released precision: "
            f"{gc['released_precision']}", "",
            "## Missed expectations", "",
        ]
        lines += [f"- {m['clause_id']}: {m['rule_type']} ({m['key']})"
                  for m in res["misses"]] or ["- none"]
        path = out_dir / "benchmark_report_latest.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
