import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.contracts import Action, FocusedElement, Observation
from agent.llm import (
    PROMPT_HASH,
    SYSTEM_PROMPT,
    LLMClient,
    ProviderError,
    build_messages,
    load_env_file,
    parse_action,
)

TREE = '- textbox "Full name" [ref=e1]\n- button "Send" [ref=e2]'
CLICK = '{"thought": "send it", "action": "click", "ref": "e2", "text": null, "key": null}'


def obs(step=0, notes=()):
    return Observation(step=step, tree=TREE, url_path="/signup-a.html", persona_notes=list(notes))


def reply(content, status=200, headers=None):
    body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
    return status, headers or {}, body


class FakeHTTP:
    """Plays canned responses in order and keeps every request it was sent."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, url, headers, body):
        self.requests.append((url, headers, json.loads(body)))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def client(http, **kwargs):
    kwargs.setdefault("api_key", "test-key")
    return LLMClient(post=http, sleep=lambda s: http.requests.append(("sleep", s, None)), **kwargs)


def sleeps(http):
    return [r[1] for r in http.requests if r[0] == "sleep"]


class TestPrompt:
    def test_holds_no_persona_limit(self):
        # Constraints, not roleplay: the template is shared by every persona,
        # so it must not name one or any of their limits.
        lowered = SYSTEM_PROMPT.lower()
        for word in ("persona", "error-prone", "mistake", "typo", "memory", "literacy"):
            assert word not in lowered

    def test_first_step_sends_task_and_page(self):
        system, user = build_messages("Create an account", obs(), [])
        assert system == {"role": "system", "content": SYSTEM_PROMPT}
        assert user["content"].startswith("Task: Create an account\n\nStep 0.")
        assert TREE in user["content"] and "Focused: nothing" in user["content"]

    def test_history_is_replayed_as_turns(self):
        # The loop's Turn; built here without importing the loop (no Playwright).
        past = SimpleNamespace(observation=obs(0), action=parse_action(CLICK), result="ok")
        messages = build_messages("t", obs(1, ["Nothing visibly changed."]), [past])
        assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
        assert messages[1]["content"].startswith("Task: t")
        assert json.loads(messages[2]["content"])["ref"] == "e2"
        assert "Note: Nothing visibly changed." in messages[3]["content"]

    def test_focus_is_shown(self):
        focused = obs().model_copy(
            update={"focused": FocusedElement(ref="e1", role="textbox", name="Full name")}
        )
        assert (
            'Focused: textbox "Full name" [ref=e1]'
            in build_messages("t", focused, [])[1]["content"]
        )

    def test_prompt_hash_is_logged_with_the_model(self):
        assert client(FakeHTTP()).prompt_hash == PROMPT_HASH and len(PROMPT_HASH) == 16


class TestRequest:
    def test_temperature_zero_json_and_key(self):
        http = FakeHTTP(reply(CLICK))
        action = client(http, provider="groq").next_action("t", obs(), [])
        assert action == Action(thought="send it", action="click", ref="e2")
        url, headers, body = http.requests[0]
        assert url == "https://api.groq.com/openai/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["User-Agent"] == "simux/0.1"
        assert body["temperature"] == 0 and body["response_format"] == {"type": "json_object"}
        assert body["model"] == "openai/gpt-oss-120b"

    def test_model_id_names_provider_and_model(self):
        c = client(FakeHTTP(), provider="openrouter", model="some/model")
        assert c.model_id == "openrouter/some/model"

    def test_ollama_needs_no_key(self):
        http = FakeHTTP(reply(CLICK))
        LLMClient(provider="ollama", post=http).next_action("t", obs(), [])
        assert "Authorization" not in http.requests[0][1]

    def test_key_required(self):
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            LLMClient(provider="groq")

    def test_unknown_provider(self):
        with pytest.raises(ValueError, match="unknown provider"):
            LLMClient(provider="nope", api_key="k")

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("LLM_API_KEY", "k")
        monkeypatch.setenv("LLM_MODEL", "gemini-x")
        assert LLMClient.from_env(env_file=Path("missing")).model_id == "gemini/gemini-x"


class TestEnvFile:
    @pytest.fixture(autouse=True)
    def clean_env(self, monkeypatch):
        for name in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
            monkeypatch.delenv(name, raising=False)

    def test_from_env_reads_the_file(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("# keys\n\nLLM_PROVIDER=openrouter\nexport LLM_API_KEY = 'sk-1'\n")
        c = LLMClient.from_env(env_file=env)
        assert c.model_id.startswith("openrouter/") and c._key == "sk-1"

    def test_environment_wins_over_the_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "from-shell")
        env = tmp_path / ".env"
        env.write_text('LLM_API_KEY="from-file"\n')
        load_env_file(env)
        assert os.environ["LLM_API_KEY"] == "from-shell"

    def test_value_keeps_inner_equals_and_quotes(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text('LLM_BASE_URL=http://h/v1?a=b\nLLM_MODEL="it\'s"\n')
        load_env_file(env)
        assert os.environ["LLM_BASE_URL"] == "http://h/v1?a=b"
        assert os.environ["LLM_MODEL"] == "it's"

    def test_missing_file_is_fine(self, tmp_path):
        load_env_file(tmp_path / "nope")
        assert "LLM_API_KEY" not in os.environ


class TestOutput:
    def test_fenced_json_is_accepted(self):
        assert parse_action(f"```json\n{CLICK}\n```").ref == "e2"

    def test_invalid_reply_is_sent_back_then_retried(self):
        http = FakeHTTP(reply("I will click Send"), reply(CLICK))
        assert client(http).next_action("t", obs(), []).ref == "e2"
        retry = http.requests[1][2]["messages"]
        assert retry[-2] == {"role": "assistant", "content": "I will click Send"}
        assert retry[-1]["content"].startswith("Invalid reply:")

    def test_contract_violation_is_invalid(self):
        # Valid JSON, but `click` without a ref breaks the Action contract.
        no_ref = '{"thought": "x", "action": "click"}'
        http = FakeHTTP(reply(no_ref), reply(CLICK))
        assert client(http).next_action("t", obs(), []).ref == "e2"
        assert "needs a ref" in http.requests[1][2]["messages"][-1]["content"]

    def test_invalid_every_time_aborts(self):
        http = FakeHTTP(*[reply("nope")] * 3)
        with pytest.raises(ProviderError, match="no valid action after 3"):
            client(http, max_invalid=2).next_action("t", obs(), [])


class TestRateLimits:
    def test_429_honours_retry_after(self):
        http = FakeHTTP(reply("", 429, {"retry-after": "7"}), reply(CLICK))
        assert client(http).next_action("t", obs(), []).ref == "e2"
        assert sleeps(http) == [7.0]

    def test_backoff_doubles_without_retry_after(self):
        http = FakeHTTP(reply("", 503), reply("", 429), reply(CLICK))
        client(http).next_action("t", obs(), [])
        assert sleeps(http) == [2.0, 4.0]

    def test_network_error_is_retried(self):
        http = FakeHTTP(ConnectionRefusedError("refused"), reply(CLICK))
        assert client(http).next_action("t", obs(), []).ref == "e2"
        assert sleeps(http) == [2.0]

    def test_long_retry_after_is_a_spent_quota(self):
        http = FakeHTTP(reply("", 429, {"Retry-After": "3600"}))
        with pytest.raises(ProviderError, match="quota spent"):
            client(http).next_action("t", obs(), [])
        assert sleeps(http) == []

    def test_gives_up_after_max_attempts(self):
        http = FakeHTTP(*[reply("", 429)] * 3)
        with pytest.raises(ProviderError, match="after 3 attempts"):
            client(http, max_attempts=3).next_action("t", obs(), [])

    def test_bad_key_is_not_retried(self):
        http = FakeHTTP(reply("", 401))
        with pytest.raises(ProviderError, match="HTTP 401"):
            client(http).next_action("t", obs(), [])
        assert len(http.requests) == 1


class TestRecordReplay:
    def test_replay_makes_no_call(self, tmp_path):
        recorder = FakeHTTP(reply(CLICK))
        recorded = client(recorder, cache_dir=tmp_path).next_action("t", obs(), [])
        assert len(list(tmp_path.glob("*.json"))) == 1

        def no_network(*args):
            raise AssertionError("replay must not call the API")

        replayed = LLMClient(cache_dir=tmp_path, replay=True, post=no_network)
        assert replayed.next_action("t", obs(), []) == recorded

    def test_live_run_never_reads_the_recording(self, tmp_path):
        # A rehearsal's recording must not turn a later live run into a replay.
        http = FakeHTTP(reply(CLICK), reply(CLICK))
        c = client(http, cache_dir=tmp_path)
        c.next_action("t", obs(), [])
        c.next_action("t", obs(), [])
        assert len(http.requests) == 2

    def test_replay_of_an_unrecorded_step_aborts(self, tmp_path):
        with pytest.raises(ProviderError, match="no recorded reply"):
            LLMClient(cache_dir=tmp_path, replay=True).next_action("t", obs(), [])

    def test_a_different_page_is_a_different_request(self, tmp_path):
        http = FakeHTTP(reply(CLICK), reply(CLICK))
        c = client(http, cache_dir=tmp_path)
        c.next_action("t", obs(0), [])
        c.next_action("t", obs(1), [])
        assert len(list(tmp_path.glob("*.json"))) == 2
