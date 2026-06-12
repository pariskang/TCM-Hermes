"""AutonomousReviewReporter — the per-run governance report (section 九)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..config import HermesConfig
from ..memory.store import MemoryCuratorAgent
from ..schemas import InitialRule
from ..utils import read_json, utc_now
from .quality import QualityMetrics


class AutonomousReviewReporter:
    def __init__(self, config: HermesConfig | None = None) -> None:
        self.config = config or HermesConfig()
        self.metrics = QualityMetrics(self.config)
        self.memory = MemoryCuratorAgent(self.config)

    # ------------------------------------------------------------------
    def generate(self, book_ids: list[str] | None = None,
                 scope_label: str = "full corpus") -> Path:
        rules = self.metrics.load_all_rules(book_ids)
        m = self.metrics.compute(rules)
        self.memory.record_evaluation({"scope": scope_label, **m})

        books = sorted({(r.book_id, r.book_title) for r in rules})
        chapters = sorted({(r.book_id, r.chapter_title) for r in rules})
        sus = {r.source_unit_id for r in rules}
        cats = sorted({tuple(r.category_path) for r in rules})
        statuses = Counter(r.autonomous_review.review_status for r in rules)
        levels = Counter(r.autonomous_review.release_level for r in rules)
        critic_digest = self.memory.critic_pattern_digest(8)
        repair_digest = self.memory.repair_pattern_digest(8)
        ready = [r for r in rules
                 if r.autonomous_review.release_level in ("gold", "silver")]
        version = read_json(self.config.manifests_dir / "corpus_version.json", {})

        lines = [
            "# Autonomous Review Report",
            "",
            f"- Generated: {utc_now()}",
            f"- Protocol: hermes-v5 (autonomous model review — no human review nodes)",
            f"- Corpus version: {version.get('corpus_version', 'n/a')}",
            "",
            "## Corpus Scope",
            "",
            f"- Category: {'; '.join(' / '.join(c) for c in cats) or 'n/a'}",
            f"- Scope label: {scope_label}",
            f"- Books: {len(books)}",
            f"- Chapters: {len(chapters)}",
            f"- SourceUnits with rules: {len(sus)}",
            "",
            "## Extraction Statistics",
            "",
            f"- InitialRules extracted: {m.get('rules_total', 0)}",
            f"- Schema valid: {sum(r.autonomous_review.schema_valid for r in rules)}",
            f"- Evidence verified: {sum(r.autonomous_review.evidence_verified for r in rules)}",
            f"- Model accepted: {statuses.get('model_accepted', 0)}",
            f"- Model repaired accepted: {statuses.get('model_repaired_accepted', 0)}",
            f"- Model low confidence: {statuses.get('model_low_confidence', 0)}",
            f"- Model conflict: {statuses.get('model_conflict', 0)}",
            f"- Model rejected: {statuses.get('model_rejected', 0)}",
            "",
            "## Release Levels",
            "",
            f"- Gold: {levels.get('gold', 0)}",
            f"- Silver: {levels.get('silver', 0)}",
            f"- Bronze: {levels.get('bronze', 0)}",
            f"- Rejected: {levels.get('rejected', 0)} (preserved in data/rules_rejected/)",
            "",
            "## Quality Metrics",
            "",
        ]
        for key in ("autonomous_acceptance_rate", "model_repair_rate",
                    "critic_rejection_rate", "evidence_verification_rate",
                    "consensus_score_mean", "gold_rule_rate", "silver_rule_rate",
                    "bronze_rule_rate", "model_conflict_rate",
                    "false_support_detection_rate"):
            lines.append(f"- {key}: {m.get(key, 0)}")
        lines += [
            "",
            "## Main Critic Findings",
            "",
        ]
        if critic_digest:
            for i, c in enumerate(critic_digest, 1):
                lines.append(f"{i}. {c['pattern']} × {c['count']}")
        else:
            lines.append("(none recorded)")
        lines += [
            "",
            "## Auto Repair Summary",
            "",
        ]
        if repair_digest:
            for r in repair_digest:
                lines.append(f"- {r['problem_type']} × {r['count']}")
        else:
            lines.append("(no repairs)")

        residual = []
        if m.get("model_conflict_rate", 0) > 0.02:
            residual.append("模型分歧率偏高：抽取与审核置信差异需要更强的多模型投票。")
        if m.get("bronze_rule_rate", 0) > 0.4:
            residual.append("Bronze 占比偏高：归纳性解释较多，建议仅内部检索使用。")
        if m.get("false_support_detection_rate", 0) > 0.15:
            residual.append("假支持检出率较高：建议复查抽取条件窗口与词表边界。")
        if not residual:
            residual.append("当前轮次无显著残余风险；持续监控 critic_memory 模式漂移。")
        lines += ["", "## Residual Risks", ""] + [f"- {r}" for r in residual]
        lines += [
            "",
            "## Rules Ready for Skill Compilation",
            "",
            f"- Silver/Gold InitialRules: {len(ready)}",
            f"- Coverage: {len({r.book_id for r in ready})} books, "
            f"{len({(r.book_id, r.chapter_id) for r in ready})} chapters",
            "",
            "---",
            "原则：自主审核 ≠ 无审核；自主审核 = 多模型、多轮、多证据、多门控的自动化审核。",
            "No evidence, no rule. No source trace, no answer.",
            "",
        ]
        out = self.config.reports_dir / f"autonomous_review_report_{utc_now()[:10]}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")
        latest = self.config.reports_dir / "autonomous_review_report_latest.md"
        latest.write_text("\n".join(lines), encoding="utf-8")
        return out
