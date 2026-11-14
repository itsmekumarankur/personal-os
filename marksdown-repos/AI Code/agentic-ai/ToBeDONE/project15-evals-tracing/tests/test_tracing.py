import json
import random
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from tracing import (
    Clock,
    JsonlExporter,
    MemoryExporter,
    OtlpHttpExporter,
    Tracer,
    build_tree,
    extract_traceparent,
    luhn_ok,
    redact,
    render_tree,
    to_otlp,
)


def make(**kw):
    clock = Clock()
    ex = MemoryExporter()
    return Tracer([ex], clock=clock, rng=random.Random(1), **kw), ex, clock


def one(ex):
    return ex.all()[0]


# ---------- spans form a tree ----------

def test_nesting_and_timing():
    tr, ex, clock = make()
    with tr.span("root"):
        clock.advance(10)
        with tr.span("child-a"):
            clock.advance(20)
        with tr.span("child-b"):
            clock.advance(5)
    spans = {s.name: s for s in one(ex)}
    assert spans["root"].parent_id is None
    assert spans["child-a"].parent_id == spans["root"].span_id == spans["child-b"].parent_id
    assert len({s.trace_id for s in spans.values()}) == 1
    assert spans["root"].duration_ms == 35 and spans["child-a"].duration_ms == 20
    roots, kids = build_tree(list(spans.values()))
    assert [s.name for s in kids[roots[0].span_id]] == ["child-a", "child-b"]


def test_separate_requests_get_separate_traces():
    tr, ex, _ = make()
    with tr.span("a"):
        pass
    with tr.span("b"):
        pass
    assert len(ex.all()) == 2 and one(ex)[0].trace_id != ex.all()[1][0].trace_id


def test_exception_marks_error_and_reraises():
    tr, ex, _ = make()
    with pytest.raises(ValueError):
        with tr.span("root"):
            with tr.span("boom"):
                raise ValueError("bad input")
    spans = {s.name: s for s in one(ex)}
    assert spans["boom"].status == "ERROR" and "bad input" in spans["boom"].status_message
    assert spans["root"].status == "ERROR"          # the error travels up through the parents
    assert spans["boom"].events[0]["name"] == "exception"


def test_threads_need_a_context_snapshot():
    tr, ex, _ = make()
    with tr.span("root"):
        ctx = tr.snapshot()
        with ThreadPoolExecutor(2) as pool:
            def work(name):
                with tr.span(name):
                    pass
            futs = [pool.submit(ctx.copy().run, work, "with-ctx")]
            futs.append(pool.submit(work, "no-ctx"))
            [f.result() for f in futs]
    traces = ex.all()
    names = {s.name: s for t in traces for s in t}
    root = names["root"]
    assert names["with-ctx"].parent_id == root.span_id and names["with-ctx"].trace_id == root.trace_id
    assert names["no-ctx"].trace_id != root.trace_id          # without the snapshot the span is an orphan in its own trace


# ---------- sampling ----------

def test_head_sampling_drops_most_boring_traces():
    ex = MemoryExporter(1000)
    tr = Tracer([ex], sample_rate=0.1, clock=Clock(), rng=random.Random(7))
    for _ in range(500):
        with tr.span("ok"):
            pass
    assert 20 <= len(ex.all()) <= 90                # about 10 percent of 500


def test_errors_and_slow_traces_are_always_kept():
    ex = MemoryExporter(1000)
    clock = Clock()
    tr = Tracer([ex], sample_rate=0.0, slow_ms=100, clock=clock, rng=random.Random(3))
    with tr.span("fine"):
        clock.advance(5)
    with pytest.raises(RuntimeError):
        with tr.span("failing"):
            raise RuntimeError("x")
    with tr.span("slow"):
        clock.advance(500)
    assert sorted(t[0].name for t in ex.all()) == ["failing", "slow"]


def test_remote_parent_continues_the_trace_and_respects_sampled_flag():
    ex = MemoryExporter()
    tr = Tracer([ex], sample_rate=1.0, clock=Clock(), rng=random.Random(2))
    parent = extract_traceparent({"Traceparent": "00-" + "a" * 32 + "-" + "b" * 16 + "-01"})
    with tr.span("server", remote_parent=parent):
        with tr.span("inner"):
            pass
    spans = one(ex)
    assert {s.trace_id for s in spans} == {"a" * 32}
    assert next(s for s in spans if s.name == "server").parent_id == "b" * 16
    dropped = extract_traceparent({"traceparent": "00-" + "c" * 32 + "-" + "d" * 16 + "-00"})
    with tr.span("server2", remote_parent=dropped):
        pass
    assert len(ex.all()) == 1                       # caller said 'not sampled', so we do not keep it


def test_traceparent_roundtrip_and_bad_values():
    tr, ex, _ = make()
    with tr.span("client") as sp:
        h = tr.inject()
    got = extract_traceparent(h)
    assert got == (sp.trace_id, sp.span_id, True)
    for bad in ("", "garbage", "00-" + "0" * 32 + "-" + "1" * 16 + "-01", "01-" + "a" * 32 + "-" + "b" * 16 + "-01",
                "00-" + "a" * 31 + "-" + "b" * 16 + "-01"):
        assert extract_traceparent({"traceparent": bad}) is None
    assert tr.inject() == {}                         # outside a span there is nothing to inject


# ---------- what we are willing to store ----------

def test_luhn():
    assert luhn_ok("4111111111111111") and not luhn_ok("4111111111111112")


def test_redaction():
    t = "card 4111 1111 1111 1111 key sk-abcdefghijklmnop1234 mail a.b@example.com order 1234567890123"
    r = redact(t)
    assert "[CARD]" in r and "[KEY]" in r and "[EMAIL]" in r
    assert "1234567890123" in r                      # a long number that fails the Luhn check is not a card


@pytest.mark.parametrize("mode,check", [
    ("off", lambda v: v is None),
    ("hash", lambda v: v.startswith("sha256:") and "4111" not in v),
    ("truncate", lambda v: "[CARD]" in v and v.endswith("chars]")),
    ("full", lambda v: "[CARD]" in v and len(v) > 300),
])
def test_content_policy(mode, check):
    tr, _, _ = make(content=mode)
    text = "my card is 4111 1111 1111 1111 " + "x" * 400
    assert check(tr.content(text))


# ---------- exporters and formats ----------

def test_ring_buffer_keeps_only_the_newest():
    ex = MemoryExporter(max_traces=3)
    tr = Tracer([ex], clock=Clock(), rng=random.Random(5))
    ids = []
    for _ in range(6):
        with tr.span("r") as s:
            ids.append(s.trace_id)
    assert [t[0].trace_id for t in ex.all()] == ids[-3:]


def test_jsonl_exporter(tmp_path):
    path = tmp_path / "spans.jsonl"
    tr = Tracer([JsonlExporter(path)], clock=Clock(), rng=random.Random(5))
    with tr.span("root", {"a": 1}):
        with tr.span("kid"):
            pass
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["name"] for r in rows] == ["root", "kid"] and rows[0]["attrs"] == {"a": 1}


def test_otlp_shape():
    tr, ex, clock = make()
    with tr.span("root", {"n": 3, "ok": True, "f": 1.5, "s": "x"}, kind="server"):
        clock.advance(2)
        with tr.span("kid"):
            pass
    body = to_otlp(one(ex), "svc")
    rs = body["resourceSpans"][0]
    assert rs["resource"]["attributes"][0]["value"]["stringValue"] == "svc"
    spans = rs["scopeSpans"][0]["spans"]
    root = next(s for s in spans if s["name"] == "root")
    assert len(root["traceId"]) == 32 and len(root["spanId"]) == 16 and "parentSpanId" not in root
    attrs = {a["key"]: a["value"] for a in root["attributes"]}
    assert attrs["n"] == {"intValue": "3"} and attrs["ok"] == {"boolValue": True} and attrs["f"] == {"doubleValue": 1.5}
    assert root["kind"] == 2 and int(root["endTimeUnixNano"]) - int(root["startTimeUnixNano"]) == 2_000_000
    kid = next(s for s in spans if s["name"] == "kid")
    assert kid["parentSpanId"] == root["spanId"]


def test_otlp_http_exporter_posts_and_never_raises():
    seen = []
    client = httpx.Client(transport=httpx.MockTransport(lambda req: (seen.append(req), httpx.Response(200))[1]))
    tr = Tracer([OtlpHttpExporter("http://collector:4318/", client)], clock=Clock(), rng=random.Random(1))
    with tr.span("root"):
        pass
    assert seen[0].url == "http://collector:4318/v1/traces" and json.loads(seen[0].content)["resourceSpans"]

    def boom(req):
        raise httpx.ConnectError("collector down")
    tr2 = Tracer([OtlpHttpExporter("http://x", httpx.Client(transport=httpx.MockTransport(boom)))], clock=Clock())
    with tr2.span("root"):
        pass                                          # tracing problems must never break the request


def test_a_broken_exporter_does_not_break_the_request():
    class Bad:
        def export(self, spans):
            raise RuntimeError("disk full")
    tr = Tracer([Bad(), MemoryExporter()], clock=Clock())
    with tr.span("root"):
        pass
    assert len(tr.exporters[1].all()) == 1


def test_render_tree_is_readable():
    tr, ex, clock = make()
    with tr.span("agent.run"):
        with tr.span("chat m", {"gen_ai.usage.input_tokens": 10, "gen_ai.usage.output_tokens": 5, "cost.usd": 0.0001}):
            clock.advance(100)
        with tr.span("execute_tool t"):
            clock.advance(10)
    text = render_tree(one(ex))
    lines = text.splitlines()
    assert lines[0].startswith("agent.run") and "|- chat m" in lines[1] and "`- execute_tool t" in lines[2]
    assert "in=10 out=5" in lines[1] and "$0.00010" in lines[1]
