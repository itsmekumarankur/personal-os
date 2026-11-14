"""Tests run without an API key: the model is replaced by a scripted fake."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chain  # noqa: E402
from chain import extract_xml, run_pipeline  # noqa: E402


def make_fake(verdict="revise", calls=None):
    """Return a fake llm that answers according to which step the prompt asks for."""
    calls = calls if calls is not None else []

    def fake(prompt, system_prompt="", model=None):
        calls.append({"prompt": prompt})
        if "first draft" in prompt:
            return "<draft>DRAFT TEXT</draft>"
        if "demanding editor" in prompt:
            return f"<critique>1. Too vague. Fix: add detail.</critique><verdict>{verdict}</verdict>"
        if "Rewrite the draft" in prompt:
            return "<final>FINAL TEXT</final>"
        raise AssertionError("unexpected prompt")

    return fake


def test_extract_xml():
    assert extract_xml("a <x>hello</x> b", "x") == "hello"
    assert extract_xml("no tags", "x") == ""


def test_revise_path_runs_three_steps_and_passes_context_forward():
    calls = []
    result = run_pipeline("Explain DNS", llm=make_fake("revise", calls))
    assert result["steps_run"] == 3
    assert result["draft"] == "DRAFT TEXT"
    assert result["final"] == "FINAL TEXT"
    assert len(calls) == 3
    # critique sees the draft; polish sees the request, the draft and the critique
    assert "DRAFT TEXT" in calls[1]["prompt"]
    polish = calls[2]["prompt"]
    assert "Explain DNS" in polish and "DRAFT TEXT" in polish and "Too vague" in polish


def test_gate_skips_polish_when_verdict_is_pass():
    calls = []
    result = run_pipeline("Explain DNS", llm=make_fake("pass", calls))
    assert result["steps_run"] == 2
    assert result["final"] == result["draft"] == "DRAFT TEXT"
    assert len(calls) == 2


def test_missing_tags_fall_back_to_raw_text():
    def fake(prompt, system_prompt="", model=None):
        return "plain text without tags"

    result = run_pipeline("anything", llm=fake)
    assert result["draft"] == "plain text without tags"
    assert result["steps_run"] == 3          # no verdict tag -> treated as "revise"
    assert result["verdict"] == "revise"


def test_llm_call_omits_unsupported_temperature(monkeypatch):
    request = {}

    class FakeMessages:
        def create(self, **kwargs):
            request.update(kwargs)
            return SimpleNamespace(
                content=[
                    SimpleNamespace(type="thinking", text=None),
                    SimpleNamespace(type="text", text="reply"),
                ],
                stop_reason="end_turn",
            )

    monkeypatch.setattr(chain, "_get_client", lambda: SimpleNamespace(messages=FakeMessages()))

    assert chain.llm_call("prompt") == "reply"
    assert request["model"] == chain.MODEL
    assert "temperature" not in request


def test_llm_call_reports_response_without_text_blocks(monkeypatch):
    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[SimpleNamespace(type="thinking", text=None)],
                stop_reason="max_tokens",
            )

    monkeypatch.setattr(chain, "_get_client", lambda: SimpleNamespace(messages=FakeMessages()))

    try:
        chain.llm_call("prompt")
    except RuntimeError as exc:
        assert "stop_reason='max_tokens'" in str(exc)
        assert "block_types=['thinking']" in str(exc)
    else:
        raise AssertionError("expected an error for a response without text")


def test_api_endpoint(monkeypatch):
    from fastapi.testclient import TestClient

    import main

    monkeypatch.setattr(chain, "llm_call", make_fake("revise"))
    client = TestClient(main.app)

    assert client.get("/health").json() == {"status": "ok"}

    r = client.post("/write", json={"task": "Explain DNS", "max_words": 100})
    assert r.status_code == 200
    assert r.json()["final"] == "FINAL TEXT"
    assert r.json()["steps_run"] == 3

    assert client.post("/write", json={"task": ""}).status_code == 422
    assert client.post("/write", json={"task": "x", "max_words": 5}).status_code == 422
