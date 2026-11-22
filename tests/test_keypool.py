"""Switching API keys when one runs out, without mixing models in one
evaluation (agent/keypool.py)."""

import pytest

from agent.keypool import KeyPool, clients_from_env, is_quota_error


class FakeClient:
    def __init__(self, model_id):
        self.model_id = model_id


def test_keys_load_in_order(monkeypatch, tmp_path):
    for k in list(__import__("os").environ):
        if k.startswith("LLM_"):
            monkeypatch.delenv(k)
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_API_KEY", "k1")
    monkeypatch.setenv("LLM_PROVIDER_2", "gemini")
    monkeypatch.setenv("LLM_API_KEY_2", "k2")
    monkeypatch.setenv("LLM_PROVIDER_4", "groq")  # no key: skipped
    clients = clients_from_env(tmp_path / "none.env")
    assert [c.model_id for c in clients] == ["groq/openai/gpt-oss-120b", "gemini/gemini-3.8-flash"]


def test_switches_to_the_next_key_for_the_same_model():
    a, b = FakeClient("groq/m"), FakeClient("groq/m")
    pool = KeyPool([a, b], pinned_model="groq/m")
    assert pool.current() is a
    assert pool.spent() is True and pool.current() is b
    assert pool.spent() is False and pool.current() is None


def test_never_switches_a_pinned_evaluation_to_another_model():
    groq, gemini = FakeClient("groq/m"), FakeClient("gemini/g")
    pool = KeyPool([groq, gemini], pinned_model="groq/m")
    assert pool.spent() is False  # Gemini is not offered to a Groq evaluation


def test_a_new_evaluation_takes_the_first_key_with_quota_then_pins():
    groq, gemini = FakeClient("groq/m"), FakeClient("gemini/g")
    pool = KeyPool([groq, gemini])
    assert pool.spent() is True and pool.current() is gemini  # Groq ran out first
    pool.pin("gemini/g")
    assert pool.current() is gemini and pool.pinned == "gemini/g"


def test_missing_key_for_the_pinned_model_stops_clearly():
    with pytest.raises(SystemExit, match="no key for it"):
        KeyPool([FakeClient("gemini/g")], pinned_model="groq/m")


def test_quota_errors():
    assert is_quota_error("HTTP 429: retry after 652s; quota spent")
    assert is_quota_error("HTTP 429 after 5 attempts")
    assert not is_quota_error("HTTP 401: bad key")
