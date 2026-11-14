"""A small tracer shaped like OpenTelemetry, written out so you can see how tracing works.

Words:
  trace  = the story of ONE request.   span = one step inside it (has a start, an end, a parent).
  Spans form a tree:  agent.run -> chat -> execute_tool -> chat ...
  context = "which span am I inside right now?"  (a ContextVar, so threads/async do not mix up)

What is here and why:
  * Tracer.span()          a context manager: start a span, end it, mark errors
  * sampling               keep all errors and slow traces, and only a share of the boring ones
  * content policy         prompts and answers are sensitive: off / hash / truncate / full, and always redacted
  * traceparent            the W3C header that carries trace ids between services (used in Project 16)
  * to_otlp()              converts spans to OTLP JSON, the format real collectors (Jaeger, Tempo, Datadog...) accept
Attribute names follow the OpenTelemetry GenAI conventions (gen_ai.*). Those conventions are still
marked experimental, so check the current names before you send data to a real backend.
"""
import contextvars
import hashlib
import json
import random
import re
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field

_current = contextvars.ContextVar("current_span", default=None)


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str | None
    name: str
    start_ns: int
    kind: str = "internal"
    end_ns: int | None = None
    attrs: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    status: str = "UNSET"            # UNSET | OK | ERROR
    status_message: str = ""
    seq: int = 0                      # start order, to sort spans that start at the same instant

    @property
    def duration_ms(self) -> float:
        return 0.0 if self.end_ns is None else (self.end_ns - self.start_ns) / 1e6

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["duration_ms"] = round(self.duration_ms, 3)
        return d


# ---------------------------------------------------------------- redaction + content policy

def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        n = int(ch)
        if alt:
            n *= 2
            n -= 9 if n > 9 else 0
        total += n
        alt = not alt
    return total % 10 == 0


_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_KEY = re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def redact(text: str) -> str:
    def card(m):
        digits = re.sub(r"\D", "", m.group(0))
        return "[CARD]" if 13 <= len(digits) <= 19 and luhn_ok(digits) else m.group(0)
    text = _CARD.sub(card, text)
    text = _KEY.sub("[KEY]", text)
    return _EMAIL.sub("[EMAIL]", text)


class Clock:
    """A clock you can move by hand. Tests use it so latency is exact and nothing sleeps."""

    def __init__(self, start_ns: int = 1_700_000_000_000_000_000):
        self.t = start_ns

    def now_ns(self) -> int:
        return self.t

    def advance(self, ms: float):
        self.t += int(ms * 1e6)


# ---------------------------------------------------------------- exporters

class MemoryExporter:
    """Keeps the last N traces in memory (a ring buffer). Good for tests and for the /traces API."""

    def __init__(self, max_traces: int = 500):
        self.max = max_traces
        self.traces: "OrderedDict[str, list[Span]]" = OrderedDict()
        self._lock = threading.Lock()

    def export(self, spans: list):
        with self._lock:
            self.traces[spans[0].trace_id] = list(spans)
            while len(self.traces) > self.max:
                self.traces.popitem(last=False)

    def get(self, trace_id: str):
        with self._lock:
            return self.traces.get(trace_id)

    def all(self):
        with self._lock:
            return list(self.traces.values())


class JsonlExporter:
    """Appends one JSON line per span. Easy to grep, easy to load into pandas."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()

    def export(self, spans: list):
        with self._lock, open(self.path, "a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps(s.to_dict(), default=str) + "\n")


def _otlp_value(v):
    if isinstance(v, bool):
        return {"boolValue": v}
    if isinstance(v, int):
        return {"intValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    return {"stringValue": str(v)}


_KIND = {"internal": 1, "server": 2, "client": 3, "producer": 4, "consumer": 5}
_STATUS = {"UNSET": 0, "OK": 1, "ERROR": 2}


def to_otlp(spans: list, service_name: str = "agent-service") -> dict:
    """The OTLP/JSON body for POST {collector}/v1/traces."""
    return {"resourceSpans": [{
        "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service_name}}]},
        "scopeSpans": [{"scope": {"name": "project15.tracing"}, "spans": [{
            "traceId": s.trace_id, "spanId": s.span_id,
            **({"parentSpanId": s.parent_id} if s.parent_id else {}),
            "name": s.name, "kind": _KIND.get(s.kind, 1),
            "startTimeUnixNano": str(s.start_ns), "endTimeUnixNano": str(s.end_ns or s.start_ns),
            "attributes": [{"key": k, "value": _otlp_value(v)} for k, v in s.attrs.items()],
            "events": [{"name": e["name"], "timeUnixNano": str(e["time_ns"]),
                        "attributes": [{"key": k, "value": _otlp_value(v)} for k, v in e.get("attrs", {}).items()]}
                       for e in s.events],
            "status": {"code": _STATUS[s.status], **({"message": s.status_message} if s.status_message else {})},
        } for s in spans]}],
    }]}


class OtlpHttpExporter:
    """Posts OTLP JSON to a collector. Not run against a real collector in this project (tests use a mock)."""

    def __init__(self, endpoint: str, client=None, service_name: str = "agent-service"):
        import httpx
        self.url = endpoint.rstrip("/") + "/v1/traces"
        self.client = client or httpx.Client(timeout=5)
        self.service = service_name

    def export(self, spans: list):
        try:
            self.client.post(self.url, json=to_otlp(spans, self.service))
        except Exception:                # tracing must never break the request
            pass


# ---------------------------------------------------------------- W3C traceparent

_TP = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def extract_traceparent(headers: dict):
    """Returns (trace_id, parent_span_id, sampled) or None if absent or malformed."""
    value = {k.lower(): v for k, v in headers.items()}.get("traceparent", "")
    m = _TP.match(value.strip())
    if not m or m.group(1) == "0" * 32 or m.group(2) == "0" * 16:
        return None
    return m.group(1), m.group(2), bool(int(m.group(3), 16) & 1)


# ---------------------------------------------------------------- tracer

class Tracer:
    def __init__(self, exporters=(), sample_rate: float = 1.0, slow_ms: float | None = None,
                 content: str = "truncate", max_chars: int = 300, clock=None, rng=None):
        assert content in ("off", "hash", "truncate", "full")
        self.exporters = list(exporters)
        self.sample_rate, self.slow_ms = sample_rate, slow_ms
        self.content_mode, self.max_chars = content, max_chars
        self.now = clock.now_ns if clock else time.time_ns
        self.rng = rng or random.Random()
        self._buf: dict = {}                       # trace_id -> spans waiting for the local root to finish
        self._sampled: dict = {}                   # trace_id -> head-sampling decision
        self._lock = threading.Lock()
        self._seq = 0

    # -- helpers
    def content(self, text) -> str | None:
        """What we are willing to store about a prompt or an answer."""
        if self.content_mode == "off" or text is None:
            return None
        text = str(text)
        if self.content_mode == "hash":
            return "sha256:" + hashlib.sha256(text.encode()).hexdigest()[:12]
        text = redact(text)
        if self.content_mode == "truncate" and len(text) > self.max_chars:
            return text[: self.max_chars] + f"...[+{len(text) - self.max_chars} chars]"
        return text

    def current(self):
        return _current.get()

    def inject(self) -> dict:
        s = _current.get()
        if not s:
            return {}
        sampled = "01" if self._sampled.get(s.trace_id, True) else "00"
        return {"traceparent": f"00-{s.trace_id}-{s.span_id}-{sampled}"}

    # -- the main entry point
    @contextmanager
    def span(self, name: str, attrs: dict | None = None, kind: str = "internal", remote_parent=None):
        parent = _current.get()
        if remote_parent and parent is None:
            trace_id, parent_id, remote_sampled = remote_parent
            local_root = True
        elif parent is not None:
            trace_id, parent_id, local_root = parent.trace_id, parent.span_id, False
        else:
            trace_id, parent_id, local_root = "%032x" % self.rng.getrandbits(128), None, True
        sp = Span(trace_id, "%016x" % self.rng.getrandbits(64), parent_id, name, self.now(), kind, attrs=dict(attrs or {}))
        if local_root:
            decided = remote_sampled if remote_parent else (self.rng.random() < self.sample_rate)
            with self._lock:
                self._sampled[trace_id] = decided
        with self._lock:
            self._seq += 1
            sp.seq = self._seq
        token = _current.set(sp)
        try:
            yield sp
            if sp.status == "UNSET":
                sp.status = "OK"
        except BaseException as e:
            sp.status, sp.status_message = "ERROR", f"{type(e).__name__}: {e}"[:300]
            sp.events.append({"name": "exception", "time_ns": self.now(),
                              "attrs": {"exception.type": type(e).__name__, "exception.message": str(e)[:300]}})
            raise
        finally:
            _current.reset(token)
            sp.end_ns = self.now()
            self._finish(sp, local_root)

    def _finish(self, sp: Span, local_root: bool):
        with self._lock:
            self._buf.setdefault(sp.trace_id, []).append(sp)
            if not local_root:
                return
            spans = self._buf.pop(sp.trace_id)
            head = self._sampled.pop(sp.trace_id, True)
        has_error = any(s.status == "ERROR" for s in spans)
        slow = self.slow_ms is not None and sp.duration_ms >= self.slow_ms
        if head or has_error or slow:                 # tail rule: never drop errors or slow traces
            spans.sort(key=lambda s: (s.start_ns, s.seq))
            for ex in self.exporters:
                try:
                    ex.export(spans)
                except Exception:
                    pass

    @staticmethod
    def snapshot():
        """Threads do not inherit the current span by themselves. Do:  ctx = tracer.snapshot(); pool.submit(ctx.run, fn, arg)"""
        return contextvars.copy_context()


# ---------------------------------------------------------------- reading traces

def build_tree(spans: list):
    by_parent: dict = {}
    for s in sorted(spans, key=lambda s: (s.start_ns, s.seq)):
        by_parent.setdefault(s.parent_id, []).append(s)
    ids = {s.span_id for s in spans}
    roots = [s for s in spans if s.parent_id is None or s.parent_id not in ids]
    return sorted(roots, key=lambda s: (s.start_ns, s.seq)), by_parent


def render_tree(spans: list, width: int = 24) -> str:
    """ASCII waterfall:  name, duration, and a bar showing where in the request the step ran."""
    if not spans:
        return "(empty trace)"
    t0 = min(s.start_ns for s in spans)
    total = max(1, max(s.end_ns or s.start_ns for s in spans) - t0)
    roots, kids = build_tree(spans)
    out = []

    def line(s, prefix, label_prefix):
        a = int((s.start_ns - t0) / total * width)
        b = max(a + 1, int(((s.end_ns or s.start_ns) - t0) / total * width))
        bar = "." * a + "#" * (b - a) + "." * (width - b)
        extra = []
        if "cost.usd" in s.attrs:
            extra.append(f"${s.attrs['cost.usd']:.5f}")
        if "gen_ai.usage.input_tokens" in s.attrs:
            extra.append(f"in={s.attrs['gen_ai.usage.input_tokens']} out={s.attrs.get('gen_ai.usage.output_tokens', 0)}")
        if s.status == "ERROR":
            extra.append("ERROR " + s.status_message[:40])
        out.append(f"{(label_prefix + s.name):<44} {s.duration_ms:8.1f}ms |{bar}| {' '.join(extra)}".rstrip())
        children = kids.get(s.span_id, [])
        for i, c in enumerate(children):
            last = i == len(children) - 1
            line(c, prefix + ("   " if last else "|  "), prefix + ("`- " if last else "|- "))

    for r in roots:
        line(r, "", "")
    return "\n".join(out)
