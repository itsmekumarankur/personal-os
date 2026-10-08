import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

import llm  # noqa: E402
from config import Settings, parse_api_keys  # noqa: E402
from main import create_app  # noqa: E402

KEYS = {
    "cust1-key-aaaaaaaaaaaaaaaa": {"id": "cust-1", "role": "customer", "account_id": "A-1001"},
    "cust2-key-bbbbbbbbbbbbbbbb": {"id": "cust-2", "role": "customer", "account_id": "A-1002"},
    "appr1-key-cccccccccccccccc": {"id": "approver-1", "role": "approver"},
    "ops01-key-dddddddddddddddd": {"id": "ops-1", "role": "ops"},
}
C1, C2, AP, OPS = list(KEYS)


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def make_settings(db_path=":memory:", **overrides):
    base = dict(api_keys=parse_api_keys(json.dumps(KEYS)), db_path=str(db_path), rate_limit_per_min=1000)
    base.update(overrides)
    return Settings(**base)


def text(t, tokens=(10, 5)):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=t)],
                           usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]))


def tool(*calls, tokens=(10, 5)):
    """calls: (name, input) pairs requested in ONE assistant turn."""
    blocks = [SimpleNamespace(type="tool_use", id=f"tu_{i}", name=n, input=a) for i, (n, a) in enumerate(calls)]
    return SimpleNamespace(stop_reason="tool_use", content=blocks,
                           usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]))


class Script:
    """A fake create_message. Hands out the scripted responses in order and records every call."""

    def __init__(self, *responses):
        self.queue = list(responses)
        self.calls = []

    def __call__(self, system, messages, tools, model, temperature=0.0, max_tokens=1024):
        self.calls.append({"system": system, "messages": copy.deepcopy(messages),
                           "tools": [t["name"] for t in tools], "model": model})
        if not self.queue:
            raise AssertionError("the model was called more often than scripted")
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def script(monkeypatch):
    def install(*responses):
        s = Script(*responses)
        monkeypatch.setattr(llm, "create_message", s)
        return s
    return install


@pytest.fixture
def make_client(tmp_path):
    def build(**overrides):
        app = create_app(make_settings(tmp_path / "p.db", **overrides), configure_logging=False)
        return TestClient(app), app
    return build


@pytest.fixture
def client(make_client):
    return make_client()[0]
