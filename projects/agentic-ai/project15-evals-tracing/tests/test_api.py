import random

import pytest
from fastapi.testclient import TestClient

from demo_fake import FakeModel
from main import create_app
from tracing import Clock, MemoryExporter, Tracer


@pytest.fixture
def client():
    clock = Clock()
    ex = MemoryExporter()
    tr = Tracer([ex], clock=clock, rng=random.Random(4), content="truncate")
    return TestClient(create_app(FakeModel("good", clock=clock), tr))


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_a_trace_id_and_the_trace_is_readable(client):
    r = client.post("/ask", json={"question": "EMI for a loan of 500000 at 9% for 5 years?"})
    assert r.status_code == 200 and "10379.18" in r.json()["answer"]
    tid = r.json()["trace_id"]
    assert r.headers["x-trace-id"] == tid
    t = client.get(f"/traces/{tid}").json()
    assert [s["name"] for s in t["spans"]][0] == "agent.run" and "execute_tool calculate_emi" in t["waterfall"]
    otlp = client.get(f"/traces/{tid}/otlp").json()
    assert otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]


def test_unknown_trace_is_404(client):
    assert client.get("/traces/" + "0" * 32).status_code == 404
    assert client.get("/traces/" + "0" * 32 + "/otlp").status_code == 404


def test_incoming_traceparent_joins_the_callers_trace(client):
    tp = "00-" + "a" * 32 + "-" + "b" * 16 + "-01"
    r = client.post("/ask", json={"question": "hello"}, headers={"traceparent": tp})
    assert r.json()["trace_id"] == "a" * 32
    assert client.get("/traces/" + "a" * 32).json()["spans"][0]["parent_id"] == "b" * 16


def test_traces_list_and_stats(client):
    for q in ("hello", "What is the late payment fee?", "What is the fee for the platinum lounge pass?"):
        client.post("/ask", json={"question": q})
    lst = client.get("/traces").json()
    assert len(lst) == 3 and all(x["name"] == "agent.run" for x in lst)
    s = client.get("/stats").json()
    assert s["traces"] == 3 and s["cost_usd"] > 0 and s["latency_p95_ms"] >= s["latency_p50_ms"] > 0
    assert s["input_tokens"] > 0


def test_validation(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "x" * 2001}).status_code == 422


def test_stored_traces_hold_no_card_numbers():
    clock = Clock()
    ex = MemoryExporter()
    c = TestClient(create_app(FakeModel("good", clock=clock), Tracer([ex], clock=clock, content="truncate")))
    c.post("/ask", json={"question": "hello my card is 4111 1111 1111 1111"})
    assert "4111" not in str([s.to_dict() for s in ex.all()[0]])
