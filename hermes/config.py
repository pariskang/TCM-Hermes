"""Runtime configuration: data layout and gate thresholds."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from . import protocol


@dataclass
class HermesConfig:
    root: Path = field(default_factory=lambda: Path(os.environ.get("HERMES_ROOT", ".")))
    data_dir: Path | None = None

    # gates (defaults come from the protocol; overridable for experiments)
    gold_min_consensus: float = protocol.GOLD_MIN_CONSENSUS
    silver_min_consensus: float = protocol.SILVER_MIN_CONSENSUS
    bronze_min_consensus: float = protocol.BRONZE_MIN_CONSENSUS
    loop_min_consensus: float = protocol.LOOP_MIN_CONSENSUS
    max_repair_rounds: int = protocol.MAX_REPAIR_ROUNDS
    conflict_delta: float = protocol.CONFLICT_DELTA

    # merging policy: ThemeRule/MergedHermesRule use silver+gold by default
    merge_include_bronze: bool = False

    # model backend: "heuristic" (offline, deterministic), "litellm"
    # (any provider via litellm) or "anthropic" (direct SDK)
    backend: str = field(default_factory=lambda: os.environ.get("HERMES_BACKEND", "heuristic"))
    anthropic_model: str = field(
        default_factory=lambda: os.environ.get("HERMES_MODEL", "claude-opus-4-8"))
    litellm_model: str = field(
        default_factory=lambda: os.environ.get("HERMES_LLM_MODEL", "gpt-4o-mini"))
    # consensus mode: "deterministic" (formula scoring) or "panel"
    # (multi-reviewer debate; auto-enabled when an LLM backend is active)
    consensus_mode: str = field(
        default_factory=lambda: os.environ.get("HERMES_CONSENSUS_MODE", "auto"))

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.data_dir is None:
            self.data_dir = self.root / "data"
        self.data_dir = Path(self.data_dir)

    # ---- data layout -----------------------------------------------------
    @property
    def corpus_raw_dir(self) -> Path: return self.data_dir / "corpus" / "raw"

    @property
    def manifests_dir(self) -> Path: return self.data_dir / "corpus" / "manifests"

    @property
    def source_units_dir(self) -> Path: return self.data_dir / "corpus" / "source_units"

    @property
    def rules_initial_dir(self) -> Path: return self.data_dir / "rules" / "initial"

    @property
    def rules_released_dir(self) -> Path: return self.data_dir / "rules" / "released"

    @property
    def rules_rejected_dir(self) -> Path:
        # rejected rules are preserved forever for audit + error analysis
        return self.data_dir / "rules_rejected"

    @property
    def rules_theme_dir(self) -> Path: return self.data_dir / "rules" / "theme"

    @property
    def rules_merged_dir(self) -> Path: return self.data_dir / "rules" / "merged"

    @property
    def memory_dir(self) -> Path: return self.data_dir / "memory"

    @property
    def skills_dir(self) -> Path: return self.data_dir / "skills"

    @property
    def reports_dir(self) -> Path: return self.data_dir / "reports"

    @property
    def lineage_dir(self) -> Path: return self.data_dir / "lineage"

    @property
    def research_dir(self) -> Path: return self.data_dir / "research"

    @property
    def papers_dir(self) -> Path: return self.data_dir / "papers"


DEFAULT_CONFIG = HermesConfig()
