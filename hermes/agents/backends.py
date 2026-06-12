"""Model backends.

Hermes agents speak to a `ModelBackend`.  Two implementations:

* HeuristicBackend — deterministic, lexicon/pattern-driven.  Runs the whole
  pipeline offline and reproducibly; this is the default and what the test
  suite exercises.  Each agent implements its heuristic logic itself; the
  backend only records that the heuristic engine answered.

* AnthropicBackend — optional Claude-powered backend (multi-model: a
  different model can be assigned per role, which gives the consensus layer
  genuinely independent judgements).  Requires `pip install anthropic` and
  ANTHROPIC_API_KEY.  JSON responses are requested via output_config and
  parsed defensively.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from ..config import HermesConfig


class BackendError(RuntimeError):
    pass


class HeuristicBackend:
    """Marker backend: agents use their built-in deterministic logic."""
    kind = "heuristic"

    def complete_json(self, system: str, user: str, role: str = "") -> dict[str, Any]:
        raise BackendError(
            "HeuristicBackend has no generative model; agents must implement "
            "their deterministic logic and not call the backend.")


class AnthropicBackend:
    kind = "anthropic"

    # role → model; reviewer/critic/judge intentionally use distinct models so
    # the consensus is a real multi-model vote.
    DEFAULT_ROLE_MODELS = {
        "extractor": "claude-opus-4-8",
        "reviewer": "claude-opus-4-8",
        "critic": "claude-sonnet-4-6",
        "judge": "claude-opus-4-8",
        "repair": "claude-sonnet-4-6",
        "writer": "claude-opus-4-8",
    }

    def __init__(self, config: HermesConfig | None = None,
                 role_models: dict[str, str] | None = None) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise BackendError("pip install anthropic to use the LLM backend") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise BackendError("ANTHROPIC_API_KEY not set")
        self._client = anthropic.Anthropic()
        self.config = config or HermesConfig()
        self.role_models = dict(self.DEFAULT_ROLE_MODELS)
        if self.config.anthropic_model:
            self.role_models = {k: self.config.anthropic_model for k in self.role_models}
        if role_models:
            self.role_models.update(role_models)

    def complete_json(self, system: str, user: str, role: str = "") -> dict[str, Any]:
        model = self.role_models.get(role, self.role_models.get("judge"))
        resp = self._client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if resp.stop_reason == "refusal":  # pragma: no cover
            raise BackendError("model refused the request")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        return _parse_json(text)


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def get_backend(config: HermesConfig | None = None):
    config = config or HermesConfig()
    if config.backend == "anthropic":
        return AnthropicBackend(config)
    return HeuristicBackend()
