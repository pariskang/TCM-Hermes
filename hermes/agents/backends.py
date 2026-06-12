"""Model backends.

Hermes agents speak to a `ModelBackend` exposing `complete_json(system, user,
role)` (and `complete_text` for free-form generation).  Four implementations:

* HeuristicBackend — deterministic, lexicon/pattern-driven.  Runs the whole
  pipeline offline and reproducibly; the default and what the test suite
  exercises.  Agents implement their own deterministic logic and never call
  the backend.

* LiteLLMBackend — **the recommended LLM backend**.  Wraps `litellm.completion`
  so any provider (OpenAI, Anthropic, Gemini, Mistral, Groq, Ollama, vLLM,
  Bedrock, Azure, …) is reachable through one interface.  Each agent role may
  bind a *different* model, which makes the multi-reviewer panel and the
  consensus layer a genuine multi-model vote rather than one model talking to
  itself.  Set `HERMES_BACKEND=litellm` and per-role `HERMES_LLM_MODEL[_ROLE]`.

* AnthropicBackend — direct Anthropic SDK backend (kept for parity).

All LLM backends import their SDK lazily, so `import hermes` works with none of
them installed; the heuristic pipeline never touches them.
"""

from __future__ import annotations

import json
import os
import re
import time
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

    def complete_text(self, system: str, user: str, role: str = "") -> str:
        raise BackendError("HeuristicBackend has no generative model.")


# ---------------------------------------------------------------------------
# LiteLLM — one interface to (almost) every model
# ---------------------------------------------------------------------------

class LiteLLMBackend:
    """Provider-agnostic LLM backend via litellm.

    Role → model resolution (first hit wins):
      1. explicit `role_models[role]`
      2. env `HERMES_LLM_MODEL_<ROLE>` (e.g. HERMES_LLM_MODEL_CRITIC)
      3. config.litellm_model / env HERMES_LLM_MODEL
      4. "gpt-4o-mini"

    Assigning different models per role (e.g. an OpenAI extractor, a Claude
    critic, a Gemini judge) is exactly how the consensus layer becomes a real
    multi-model vote.  Any model litellm supports works — see docs/LLM_BACKENDS.md.
    """
    kind = "litellm"

    DEFAULT_ROLE_MODELS = {
        "extractor": "gpt-4o-mini",
        "reviewer": "gpt-4o-mini",
        "critic": "gpt-4o-mini",
        "judge": "gpt-4o-mini",
        "repair": "gpt-4o-mini",
        "writer": "gpt-4o-mini",
        # disease multi-agent roles
        "planner": "gpt-4o-mini",
        "relevance_classical": "gpt-4o-mini",
        "relevance_dermatology": "gpt-4o-mini",
        "relevance_adversarial": "gpt-4o-mini",
        "ontology": "gpt-4o-mini",
        "relation": "gpt-4o-mini",
    }

    def __init__(self, config: HermesConfig | None = None,
                 role_models: dict[str, str] | None = None,
                 max_retries: int = 3) -> None:
        try:
            import litellm  # noqa: F401
        except Exception as exc:  # pragma: no cover - optional dependency
            raise BackendError(
                "pip install litellm to use the litellm backend") from exc
        self._litellm = litellm
        # be quiet and resilient by default
        try:
            litellm.drop_params = True            # ignore unsupported kwargs per provider
            litellm.suppress_debug_info = True
        except Exception:
            pass
        self.config = config or HermesConfig()
        self.max_retries = max_retries
        default = (self.config.litellm_model
                   or os.environ.get("HERMES_LLM_MODEL")
                   or "gpt-4o-mini")
        self.role_models = {k: default for k in self.DEFAULT_ROLE_MODELS}
        for role in self.role_models:
            env = os.environ.get(f"HERMES_LLM_MODEL_{role.upper()}")
            if env:
                self.role_models[role] = env
        if role_models:
            self.role_models.update(role_models)

    def model_for(self, role: str) -> str:
        return self.role_models.get(role) or self.role_models.get("judge") \
            or "gpt-4o-mini"

    # ------------------------------------------------------------------
    def _complete(self, system: str, user: str, role: str,
                  json_mode: bool, temperature: float) -> str:
        model = self.model_for(role)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": int(os.environ.get("HERMES_LLM_MAX_TOKENS", "4096")),
        }
        if json_mode:
            # litellm normalizes this across providers that support it; with
            # drop_params=True it is silently ignored where unsupported.
            kwargs["response_format"] = {"type": "json_object"}
        last: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self._litellm.completion(**kwargs)
                return resp["choices"][0]["message"]["content"] or ""
            except Exception as exc:  # network / rate-limit / provider error
                last = exc
                time.sleep(min(2 ** attempt, 8))
        raise BackendError(f"litellm completion failed for {model}: {last}")

    def complete_json(self, system: str, user: str, role: str = "") -> dict[str, Any]:
        text = self._complete(system, user, role, json_mode=True,
                              temperature=float(os.environ.get(
                                  "HERMES_LLM_TEMPERATURE", "0.0")))
        return _parse_json(text)

    def complete_text(self, system: str, user: str, role: str = "") -> str:
        return self._complete(system, user, role, json_mode=False,
                              temperature=float(os.environ.get(
                                  "HERMES_LLM_TEMPERATURE", "0.3")))


# ---------------------------------------------------------------------------
# Direct Anthropic SDK backend
# ---------------------------------------------------------------------------

class AnthropicBackend:
    kind = "anthropic"

    DEFAULT_ROLE_MODELS = {
        "extractor": "claude-opus-4-8",
        "reviewer": "claude-opus-4-8",
        "critic": "claude-sonnet-4-6",
        "judge": "claude-opus-4-8",
        "repair": "claude-sonnet-4-6",
        "writer": "claude-opus-4-8",
        "planner": "claude-opus-4-8",
        "relevance_classical": "claude-opus-4-8",
        "relevance_dermatology": "claude-sonnet-4-6",
        "relevance_adversarial": "claude-sonnet-4-6",
        "ontology": "claude-opus-4-8",
        "relation": "claude-opus-4-8",
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

    def model_for(self, role: str) -> str:
        return self.role_models.get(role, self.role_models.get("judge"))

    def _complete(self, system: str, user: str, role: str) -> str:
        resp = self._client.messages.create(
            model=self.model_for(role),
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if resp.stop_reason == "refusal":  # pragma: no cover
            raise BackendError("model refused the request")
        return next((b.text for b in resp.content if b.type == "text"), "")

    def complete_json(self, system: str, user: str, role: str = "") -> dict[str, Any]:
        return _parse_json(self._complete(system, user, role))

    def complete_text(self, system: str, user: str, role: str = "") -> str:
        return self._complete(system, user, role)


def _parse_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
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
    if config.backend == "litellm":
        return LiteLLMBackend(config)
    if config.backend == "anthropic":
        return AnthropicBackend(config)
    return HeuristicBackend()
