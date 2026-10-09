import datetime as dt
import json

import pytest
from fastapi.testclient import TestClient

import server
import structured
from cache_sim import InvalidRequest, PromptCache
from events import StreamAccumulator, StreamError, sse_line
from fake_model import FakeStreamingModel
from partial_json import parse_partial
from pricing import cost, hit_rate
from sse_client import parse_sse

SRC = "Invoice INV-1042 from Acme Traders dated 2025-03-14. Items: 3 x Widget @ 120.50; 2 x Gadget @ 99.99. Total: 561.48 INR."
TODAY = dt.date(2026, 10, 8)
POLICY = "Policy clause. " * 700


def req(system=POLICY, q="hi", cc=True):
    return {"system": [{"type": "text", "text": system, **({"cache_control": {"type": "ephemeral"}} if cc else {})}], "messages": [{"role": "user", "content": q}]}


# ---------------- streaming
def test_stream_equals_non_stream():
    m = FakeStreamingModel()
    r = req(cc=False)
    acc = StreamAccumulator()
    for te in m.stream(r):
        acc.feed(te.event)
    assert acc.result()["content"] == m.create(r)["content"]


def test_tool_input_is_only_valid_after_block_stop():
    m = FakeStreamingModel()
    acc, raw, parsed_before_end = StreamAccumulator(), "", 0
    for te in m.stream(structured.request_for(SRC)):
        d = te.event.get("delta", {})
        if d.get("type") == "input_json_delta":
            raw += d["partial_json"]
            try:
                json.loads(raw)
                parsed_before_end += 1
            except ValueError:
                pass
        acc.feed(te.event)
    assert acc.result()["content"][0]["input"]["invoice_no"] == "INV-1042"
    assert parsed_before_end == 1                      # only the very last fragment completes the document


def test_midstream_error_keeps_text_drops_unfinished_tool():
    acc = StreamAccumulator()
    with pytest.raises(StreamError) as e:
        for te in FakeStreamingModel(fail_after_events=6).stream(req(cc=False)):
            acc.feed(te.event)
    assert e.value.etype == "overloaded_error" and e.value.partial["content"][0]["text"]
    acc = StreamAccumulator()
    with pytest.raises(StreamError) as e:
        for te in FakeStreamingModel(fail_after_events=6).stream(structured.request_for(SRC)):
            acc.feed(te.event)
    assert e.value.partial["content"] == []


def test_unknown_events_and_ping_are_ignored():
    acc = StreamAccumulator().feed({"type": "ping"}).feed({"type": "brand_new_event", "x": 1})
    assert acc.ignored == ["brand_new_event"]


def test_incomplete_stream_is_an_error():
    with pytest.raises(StreamError):
        StreamAccumulator().feed({"type": "message_start", "message": {"usage": {}}}).result()


def test_sse_roundtrip_and_comments():
    text = sse_line({"type": "x", "a": 1}, "7") + ": ping\n\n" + sse_line({"type": "y"}, "8")
    evs = list(parse_sse(text.splitlines(True)))
    assert [e["event"] for e in evs] == ["x", "y"] and evs[0]["id"] == "7"


def test_partial_json_never_invents_complete_values():
    full = '{"a": "hello", "b": [1, 2, 3], "c": {"d": true}}'
    for n in range(1, len(full)):
        v = parse_partial(full[:n])
        assert v is None or isinstance(v, (dict, list))
    assert parse_partial(full) == json.loads(full)
    assert parse_partial('{"total": 56')["total"] == 56            # a hint only: the real value is 561.48


# ---------------- caching
def test_second_identical_prefix_hits_and_costs_less():
    c = PromptCache()
    u1, u2 = c.process(req(q="a"), 0.0), c.process(req(q="b"), 10.0)
    assert u1["cache_creation_input_tokens"] > 0 and u1["cache_read_input_tokens"] == 0
    assert u2["cache_read_input_tokens"] == u1["cache_creation_input_tokens"] and u2["cache_creation_input_tokens"] == 0
    assert cost(u2) < cost(u1) and hit_rate(u2) > 0.9


def test_one_character_in_the_prefix_misses():
    c = PromptCache()
    c.process(req(), 0.0)
    assert c.process(req(system=POLICY.replace("Policy", "policy", 1)), 1.0)["cache_read_input_tokens"] == 0


def test_ttl_expiry_and_refresh():
    c = PromptCache()
    c.process(req(), 0.0)
    assert c.process(req(), 250.0)["cache_read_input_tokens"] > 0            # hit refreshes
    assert c.process(req(), 500.0)["cache_read_input_tokens"] > 0            # 250 s after refresh: still alive
    assert c.process(req(), 900.0)["cache_read_input_tokens"] == 0           # 400 s after last hit: expired


def test_one_hour_ttl_survives():
    r = req()
    r["system"][0]["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
    c = PromptCache()
    u = c.process(r, 0.0)
    assert u["cache_creation"]["ephemeral_1h_input_tokens"] > 0
    assert c.process(r, 1800.0)["cache_read_input_tokens"] > 0


def test_below_minimum_is_silently_uncached():
    u = PromptCache(min_tokens=1024).process(req(system="short"), 0.0)
    assert u["cache_creation_input_tokens"] == 0 and u["cache_read_input_tokens"] == 0


def test_max_four_breakpoints():
    r = req()
    r["messages"] = [{"role": "user", "content": [{"type": "text", "text": f"x{i}", "cache_control": {"type": "ephemeral"}}]} for i in range(4)]
    with pytest.raises(InvalidRequest):
        PromptCache().process(r, 0.0)


def test_parallel_cold_requests_both_write():
    m = FakeStreamingModel(cache=PromptCache())
    a = list(m.stream(req(q="1"), now=0.0))
    b = list(m.stream(req(q="2"), now=0.01))
    c = list(m.stream(req(q="3"), now=a[0].t + 0.01))
    assert b[0].event["message"]["usage"]["cache_creation_input_tokens"] > 0
    assert c[0].event["message"]["usage"]["cache_read_input_tokens"] > 0


def test_cached_request_has_shorter_time_to_first_token():
    m = FakeStreamingModel(cache=PromptCache())
    first = next(iter(m.stream(req(q="1"), now=0.0))).t
    second = next(iter(m.stream(req(q="2"), now=100.0))).t
    assert second < first / 2


# ---------------- structured
@pytest.mark.parametrize("mode,ok", [("good", True), ("sloppy", True), ("hallucinating", True), ("flaky", True), ("stubborn", False)])
def test_full_pipeline(mode, ok):
    m = FakeStreamingModel(mode=mode)
    if ok:
        r = structured.extract(lambda q: m.create(q), SRC, today=TODAY)
        assert r.value.total == 561.48 and r.value.vendor == "Acme Traders"
    else:
        with pytest.raises(structured.ExtractionFailed) as e:
            structured.extract(lambda q: m.create(q), SRC, today=TODAY)
        assert len(e.value.attempts) == 3


def test_valid_json_can_still_be_wrong_and_only_semantic_check_sees_it():
    m = FakeStreamingModel(mode="hallucinating")
    r = structured.extract(lambda q: m.create(q), SRC, max_attempts=1, semantic=False)
    assert r.value.total != 561.48                                           # schema-only ACCEPTED a wrong answer
    with pytest.raises(structured.ExtractionFailed) as e:
        structured.extract(lambda q: m.create(q), SRC, max_attempts=1, semantic=True, today=TODAY)
    assert any("add up" in x for x in e.value.attempts[0]["errors"])


def test_future_date_is_caught():
    inv, _ = structured.schema_errors({"invoice_no": "INV-1", "vendor": "Acme", "date": "2030-01-01", "currency": "INR",
                                       "items": [{"description": "W", "quantity": 1, "unit_price": 1}], "total": 1})
    assert inv is None                                                       # INV-1 has one digit: schema pattern needs 2+


def test_tolerant_text_fallback():
    assert structured.tolerant_json_from_text('Sure!\n```json\n{"a": 1}\n```') == {"a": 1}


# ---------------- server
def test_server_stream_and_metrics():
    c = TestClient(server.create_app(time_scale=0.001))
    r = c.post("/chat", json={"message": "explain streaming in 20 words"})
    assert r.headers["cache-control"] == "no-cache" and r.headers["x-accel-buffering"] == "no"
    evs = list(parse_sse(r.text.splitlines(True)))
    assert evs[0]["event"] == "open" and evs[-1]["event"] == "done" and "message_stop" in [e["event"] for e in evs]
    c.post("/chat", json={"message": "again"})
    assert c.get("/metrics").json()["cache_hit_rate"] > 0.4


def test_server_extract_ok_and_422():
    good = TestClient(server.create_app(FakeStreamingModel(), time_scale=0.001))
    assert good.post("/extract", json={"text": SRC}).json()["invoice"]["total"] == 561.48
    bad = TestClient(server.create_app(FakeStreamingModel(mode="stubborn"), time_scale=0.001))
    r = bad.post("/extract", json={"text": SRC})
    assert r.status_code == 422 and len(r.json()["attempts"]) == 3


def test_server_validation():
    c = TestClient(server.create_app(time_scale=0.001))
    assert c.post("/chat", json={"message": ""}).status_code == 422
    assert c.get("/chat/nope").status_code == 404
