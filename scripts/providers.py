"""Thin model-provider layer. Each provider exposes complete(system, user) -> str.

Add a provider by subclassing Provider and registering it in PROVIDERS.
SDKs are imported lazily so the dry-run path needs nothing installed.
"""
from __future__ import annotations

import hashlib
import os


class Provider:
    name = "base"

    def __init__(self, model: str):
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:  # pragma: no cover
        raise NotImplementedError


class DryRun(Provider):
    """Deterministic placeholder so the pipeline can be exercised without keys."""
    name = "dry-run"

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        h = hashlib.sha1(user.encode()).hexdigest()[:8]
        return (
            f"[dry-run response {h}] I'm sorry you're dealing with this. It sounds hard. "
            "You might try staying calm, reassuring her, and talking to her doctor if it continues."
        )


class Anthropic(Provider):
    name = "anthropic"

    def __init__(self, model: str):
        super().__init__(model)
        import anthropic  # lazy
        self.client = anthropic.Anthropic()

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content)


class OpenAI(Provider):
    name = "openai"

    def __init__(self, model: str):
        super().__init__(model)
        from openai import OpenAI as _OpenAI  # lazy
        self.client = _OpenAI()

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content or ""


PROVIDERS = {"dry-run": DryRun, "anthropic": Anthropic, "openai": OpenAI}


def make_provider(spec: str) -> Provider:
    """spec is 'dry-run' or '<provider>:<model>', e.g. 'anthropic:claude-sonnet-4-5'."""
    if spec == "dry-run":
        return DryRun("dry-run")
    if ":" not in spec:
        raise SystemExit(f"model spec must be 'dry-run' or '<provider>:<model>', got {spec!r}")
    provider, model = spec.split(":", 1)
    if provider not in PROVIDERS:
        raise SystemExit(f"unknown provider {provider!r}; known: {', '.join(PROVIDERS)}")
    key_env = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(provider)
    if key_env and not os.environ.get(key_env):
        raise SystemExit(f"{key_env} is not set")
    return PROVIDERS[provider](model)
