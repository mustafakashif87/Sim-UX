"""Several API keys, switched automatically when one runs out.

`.env` (or the shell) lists keys as numbered sets; the plain names are the
first:

    LLM_PROVIDER=groq        LLM_API_KEY=...   LLM_MODEL=...      # 1st
    LLM_PROVIDER_2=gemini    LLM_API_KEY_2=... LLM_MODEL_2=...    # 2nd
    LLM_PROVIDER_3=groq      LLM_API_KEY_3=...                    # 3rd ...

When a run ends because the provider's quota is spent, `evaluate` asks the
pool for the next key and reruns that job.

One rule keeps results valid: an evaluation folder never mixes models. Its
model is pinned by the first run that counts (or by the runs already in its
runs.csv), and from then on only keys for that same model are used. A second
key for the same model is a free switch; a key for another model is used
only by an evaluation that has not started, so P2 can run on Gemini while P1
stays on Groq.
"""

import os
from pathlib import Path

from agent.llm import ENV_FILE, LLMClient, load_env_file

MAX_KEYS = 9


def clients_from_env(env_file: Path = ENV_FILE, **kwargs) -> list[LLMClient]:
    """Every key set in the environment, in order: LLM_* then LLM_*_2 to _9."""
    load_env_file(env_file)
    out = []
    for n in range(1, MAX_KEYS + 1):
        suffix = "" if n == 1 else f"_{n}"
        provider = os.environ.get(f"LLM_PROVIDER{suffix}") or ("groq" if n == 1 else None)
        key = os.environ.get(f"LLM_API_KEY{suffix}")
        if provider is None or (not key and provider != "ollama" and not kwargs.get("replay")):
            continue
        out.append(
            LLMClient(
                provider=provider,
                api_key=key,
                model=os.environ.get(f"LLM_MODEL{suffix}"),
                base_url=os.environ.get(f"LLM_BASE_URL{suffix}"),
                **kwargs,
            )
        )
    return out


def is_quota_error(error: str) -> bool:
    return "quota spent" in error or "HTTP 429" in error


class KeyPool:
    def __init__(self, clients: list, pinned_model: str | None = None):
        if not clients:
            raise SystemExit("no API key set: add LLM_PROVIDER and LLM_API_KEY to .env")
        self.clients = clients
        self.pinned = pinned_model
        self._spent: set[int] = set()
        if pinned_model and not self._usable():
            have = ", ".join(sorted({c.model_id for c in clients}))
            raise SystemExit(
                f"this evaluation uses {pinned_model}, but no key for it is set (have: {have})"
            )

    def _usable(self) -> list[int]:
        return [
            i
            for i, c in enumerate(self.clients)
            if i not in self._spent and (self.pinned is None or c.model_id == self.pinned)
        ]

    def current(self):
        usable = self._usable()
        return self.clients[usable[0]] if usable else None

    def spent(self) -> bool:
        """The current key ran out. True if another usable key is left."""
        usable = self._usable()
        if usable:
            self._spent.add(usable[0])
        return bool(self._usable())

    def pin(self, model_id: str) -> None:
        """A run with this model counted: keep this evaluation on it."""
        if model_id and self.pinned is None:
            self.pinned = model_id
