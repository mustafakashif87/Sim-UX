"""LLM client: the real model behind the loop's Model protocol.

One OpenAI-compatible chat client for every provider; `LLM_PROVIDER` picks
the endpoint and default model, `LLM_API_KEY` holds the key and `LLM_MODEL`
overrides the model; each may be set in the git-ignored `.env` instead.
The prompt template is shared by every persona and holds no persona limit:
those are enforced by the harness (spec: Persona framework). The model
only ever sees the Observation and its own history.

    model = LLMClient.from_env(cache_dir=Path("logs/llm-cache"))
    run(page, task, persona, model, log_root)

Free tiers fail in two ways, and neither may count against a page: a rate
limit (HTTP 429) is retried with backoff, honouring `Retry-After`; anything
that cannot be retried raises `ProviderError`, which the loop records as
`aborted_provider`. With `cache_dir` every live reply is recorded by request
hash, and `replay=True` serves a recorded run with no network call.
"""

import functools
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from agent.contracts import Action, Observation

SYSTEM_PROMPT = """\
You are a person using a web page to complete a task. Each turn you see the \
page as an accessibility tree. Every element you can act on has a reference \
such as [ref=e12].

Reply with exactly one JSON object and nothing else:
{"thought": "<one short sentence>", "action": "<kind>", "ref": "<ref or null>", \
"text": "<text or null>", "key": "<key or null>"}

Kinds:
- click: needs ref.
- type: needs ref and text. Replaces what is in the field.
- press: needs key, e.g. "Tab", "Enter" or "Escape". Add a ref to press it on \
that element.
- scroll: optional ref to scroll it into view; without one, scrolls down.
- back: the browser's back button. No ref, text or key.
- give_up: you cannot complete the task. No ref, text or key.

You cannot declare the task done; keep going until it is, or give up."""

TURN_TEMPLATE = """\
Step {step}. Page: {url}
Focused: {focused}
{notes}Accessibility tree:
{tree}"""

# The prompt hash in run.json identifies the template, so a run can be
# matched to the exact wording it was given.
PROMPT_HASH = hashlib.sha256(f"{SYSTEM_PROMPT}\n{TURN_TEMPLATE}".encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Provider:
    base_url: str
    model: str
    needs_key: bool = True


PROVIDERS = {
    "groq": Provider("https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
    "openrouter": Provider("https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct"),
    "gemini": Provider(
        "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash"
    ),
    "ollama": Provider("http://localhost:11434/v1", "llama3.1", needs_key=False),
}

# (status, headers, body). Tests pass their own; the default uses urllib.
Response = tuple[int, dict[str, str], bytes]
Post = Callable[[str, dict[str, str], bytes], Response]

RETRY_STATUS = {429, 500, 502, 503, 504}

# Git-ignored; holds the key so it need not be exported in every terminal.
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class ProviderError(Exception):
    """The provider could not give a usable reply: quota spent, a bad key, no
    recorded reply in replay mode, or invalid output after every retry. The
    run is aborted and rerun later; it is not a finding about the page."""


def load_env_file(path: Path) -> None:
    """Sets each `NAME=value` line of a .env file as an environment variable,
    unless the environment already sets it. Blank lines and `#` comments are
    skipped, and one pair of surrounding quotes is removed. A missing file is
    fine: CI and the API take the key from the environment."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip().removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name, value)


def _urllib_post(url: str, headers: dict[str, str], body: bytes, timeout: float = 60) -> Response:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            return reply.status, dict(reply.headers), reply.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


def render_turn(obs: Observation) -> str:
    f = obs.focused
    notes = "".join(f"Note: {n}\n" for n in obs.persona_notes)
    return TURN_TEMPLATE.format(
        step=obs.step,
        url=obs.url_path,
        focused=f'{f.role} "{f.name}" [ref={f.ref}]' if f else "nothing",
        notes=notes,
        tree=obs.tree,
    )


def build_messages(task: str, observation: Observation, history: list) -> list[dict]:
    """The chat for one step: the task, each remembered turn, then the current
    page. `history` is already cut to the persona's window by the loop;
    nothing outside it is sent. Whether an action worked reaches the model
    only as the harness's notes on the next observation."""
    turns = [*history, None]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for i, turn in enumerate(turns):
        page = render_turn(turn.observation if turn else observation)
        messages.append({"role": "user", "content": f"Task: {task}\n\n{page}" if i == 0 else page})
        if turn:
            messages.append({"role": "assistant", "content": turn.action.model_dump_json()})
    return messages


def parse_action(content: str) -> Action:
    """The reply as an Action. Tolerates a ```json fence around the object;
    anything else invalid raises ValidationError."""
    fenced = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", content, re.DOTALL)
    return Action.model_validate_json(fenced[1] if fenced else content)


class LLMClient:
    """Implements the loop's Model protocol over an OpenAI-compatible API.

    Temperature 0 and JSON output. A reply that is not a valid Action is sent
    back with the validation error, up to `max_invalid` times, then the run is
    aborted: a model that cannot follow the format says nothing about the page.
    """

    prompt_hash = PROMPT_HASH

    def __init__(
        self,
        provider: str = "groq",
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        cache_dir: Path | None = None,
        replay: bool = False,
        max_attempts: int = 5,
        max_invalid: int = 2,
        max_wait_s: float = 60.0,
        timeout_s: float = 60.0,
        post: Post | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if provider not in PROVIDERS:
            raise ValueError(f"unknown provider {provider!r}; choose from {sorted(PROVIDERS)}")
        spec = PROVIDERS[provider]
        if spec.needs_key and not api_key and not replay:
            raise ValueError(f"{provider} needs an API key (set LLM_API_KEY)")
        if replay and cache_dir is None:
            raise ValueError("replay needs cache_dir")
        self.provider = provider
        self.model = model or spec.model
        self.model_id = f"{provider}/{self.model}"
        self._url = (base_url or spec.base_url).rstrip("/") + "/chat/completions"
        self._key = api_key
        self._cache = cache_dir
        self.replay = replay  # logged in run.json, so a replay never passes as live
        self._max_attempts = max_attempts
        self._max_invalid = max_invalid
        self._max_wait_s = max_wait_s
        self._post = post or functools.partial(_urllib_post, timeout=timeout_s)
        self._sleep = sleep

    @classmethod
    def from_env(cls, env_file: Path = ENV_FILE, **kwargs) -> "LLMClient":
        """Reads LLM_PROVIDER (default groq), LLM_API_KEY, LLM_MODEL and LLM_BASE_URL,
        first filling any that are unset from `env_file` (the repo's `.env`)."""
        load_env_file(env_file)
        return cls(
            provider=os.environ.get("LLM_PROVIDER", "groq"),
            api_key=os.environ.get("LLM_API_KEY"),
            model=os.environ.get("LLM_MODEL"),
            base_url=os.environ.get("LLM_BASE_URL"),
            **kwargs,
        )

    def next_action(self, task: str, observation: Observation, history: list) -> Action:
        messages = build_messages(task, observation, history)
        for _ in range(self._max_invalid + 1):
            content = self._complete(messages)
            try:
                return parse_action(content)
            except ValidationError as e:
                problem = "; ".join(err["msg"] for err in e.errors())
                messages = [
                    *messages,
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": f"Invalid reply: {problem}. Reply with one "
                        "JSON object in the format given.",
                    },
                ]
        raise ProviderError(f"no valid action after {self._max_invalid + 1} replies")

    def _complete(self, messages: list[dict]) -> str:
        """One reply's text. Live, it always comes from the API and is recorded;
        a recording is read only in replay mode, so a live run can never be a
        replay in disguise."""
        request = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        cached = self._cache / f"{key}.json" if self._cache else None
        if self.replay:
            if not cached.exists():
                raise ProviderError(f"replay: no recorded reply for request {key[:12]}")
            return json.loads(cached.read_text(encoding="utf-8"))["content"]

        content = self._call(request)
        if cached:
            cached.parent.mkdir(parents=True, exist_ok=True)
            entry = {"model_id": self.model_id, "request": request, "content": content}
            cached.write_text(json.dumps(entry, indent=1) + "\n", encoding="utf-8")
        return content

    def _call(self, request: dict) -> str:
        # Cloudflare in front of Groq rejects urllib's default User-Agent (error 1010).
        headers = {"Content-Type": "application/json", "User-Agent": "simux/0.1"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        body = json.dumps(request).encode()
        delay = 2.0
        for attempt in range(1, self._max_attempts + 1):
            try:
                status, reply_headers, raw = self._post(self._url, headers, body)
            except OSError as e:  # connection refused, timeout, DNS
                status, reply_headers, raw = 0, {}, str(e).encode()
            if status == 200:
                try:
                    return json.loads(raw)["choices"][0]["message"]["content"] or ""
                except (ValueError, KeyError, IndexError, TypeError) as e:
                    raise ProviderError(f"unexpected reply shape: {raw[:200]!r}") from e
            if status not in RETRY_STATUS and status != 0:
                raise ProviderError(f"HTTP {status}: {raw[:200].decode(errors='replace')}")
            wait = _retry_after(reply_headers) or delay
            if wait > self._max_wait_s:  # a daily quota, not a per-minute limit
                raise ProviderError(f"HTTP {status}: retry after {wait:.0f}s; quota spent")
            if attempt < self._max_attempts:
                self._sleep(wait)
                delay *= 2
        raise ProviderError(f"HTTP {status} after {self._max_attempts} attempts")


def _retry_after(headers: dict[str, str]) -> float | None:
    value = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
    try:
        return float(value) if value is not None else None
    except ValueError:  # an HTTP date; fall back to our own backoff
        return None
