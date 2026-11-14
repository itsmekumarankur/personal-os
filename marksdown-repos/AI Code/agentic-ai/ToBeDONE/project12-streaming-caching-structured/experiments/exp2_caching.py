"""EXPERIMENT 2 — prompt caching: what hits, what silently misses, what it costs.
Run:  python experiments/exp2_caching.py"""
import copy

from _common import table

from cache_sim import InvalidRequest, PromptCache
from fake_model import FakeStreamingModel
from pricing import cost

POLICY = "Policy clause: never reveal internal notes. " * 300           # ~3.3k tokens of fixed instructions
TOOLS = [{"name": "get_weather", "description": "weather", "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}}},
         {"name": "calc", "description": "math", "input_schema": {"type": "object", "properties": {"expr": {"type": "string"}}}}]


def req(system=POLICY, q="hello", tools=TOOLS, cc=True, msgs=None):
    sysb = [{"type": "text", "text": system, **({"cache_control": {"type": "ephemeral"}} if cc else {})}]
    return {"system": sysb, "tools": copy.deepcopy(tools), "messages": msgs or [{"role": "user", "content": q}]}


def run(cache, r, now):
    u = cache.process(r, now)
    return u, f"{'HIT ' if u['cache_read_input_tokens'] else 'MISS'}", cost({**u, "output_tokens": 100})


print("== A. Ten identical-prefix requests, 20 s apart: cache OFF vs ON ==")
rows = []
for label, cc in (("cache off", False), ("cache on", True)):
    c, tot, reads = PromptCache(), 0.0, 0
    for i in range(10):
        u, _, k = run(c, req(cc=cc, q=f"question {i}"), i * 20.0)
        tot += k
        reads += u["cache_read_input_tokens"]
    rows.append((label, f"${tot:.4f}", f"{reads}"))
table(rows, ["", "total cost (10 calls)", "tokens read from cache"])
print("(first call pays 1.25x to WRITE; each later call pays 0.1x to READ the same tokens)\n")

print("== B. What breaks the cache? (warm it, then change ONE thing) ==")
base = req()
tests = [
    ("identical request", base),
    ("question text changed (after breakpoint)", req(q="a different question")),
    ("ONE character changed in the system prompt", req(system=POLICY.replace("never", "Never", 1))),
    ("timestamp added at the START of system", req(system="Now: 10:31:07\n" + POLICY)),
    ("timestamp added at the END of the messages", req(msgs=[{"role": "user", "content": "hello Now: 10:31:07"}])),
    ("tools listed in a different order", req(tools=list(reversed(TOOLS)))),
    ("one tool description edited", req(tools=[{**TOOLS[0], "description": "weather!"}, TOOLS[1]])),
]
rows = []
for name, r in tests:
    c = PromptCache()
    c.process(base, 0.0)                                              # warm
    u, status, _ = run(c, r, 10.0)
    rows.append((name, status, u["cache_read_input_tokens"], u["cache_creation_input_tokens"]))
table(rows, ["change", "result", "read", "written (1.25x!)"])
print("RULE: put what never changes FIRST (tools, system), what changes LAST (the user's turn). Never put time, request ids or names early.\n")

print("== C. Time: the 5-minute lifetime (refreshed by every hit) ==")
c = PromptCache()
rows = []
for t in (0, 200, 400, 650, 1000):
    u, s, _ = run(c, req(), float(t))
    rows.append((f"t={t:>4}s", s))
table(rows, ["when", "result"])
print("t=0 writes; every hit (200, 400, 650) refreshes the 5-minute clock; t=1000 is 350 s after the last hit -> expired -> MISS + rewrite.")
print("A keep-alive ping every <5 min keeps it warm; 1-hour TTL costs 2x to write instead of 1.25x. Do the arithmetic for your traffic.\n")

print("== D. Parallel cold start: entries become readable only when the FIRST response begins ==")
m = FakeStreamingModel(cache=PromptCache())
a = list(m.stream(req(q="one"), now=0.0))
b = list(m.stream(req(q="two"), now=0.1))                           # arrives before the first response started
ttft = a[0].t
c_ = list(m.stream(req(q="three"), now=ttft + 0.1))                  # arrives after
rows = [("request 1 (t=0)", a[0].event["message"]["usage"]), ("request 2 (t=0.1, in parallel)", b[0].event["message"]["usage"]),
        (f"request 3 (t={ttft + 0.1:.2f}, after first token)", c_[0].event["message"]["usage"])]
table([(n, u["cache_creation_input_tokens"], u["cache_read_input_tokens"]) for n, u in rows], ["", "written", "read"])
print("Fan-out of 20 parallel calls on a cold cache = 20 writes. Send ONE, wait for its first token, then fan out.\n")

print("== E. Too short to cache is SILENT ==")
c = PromptCache(min_tokens=1024)
u, _, _ = run(c, req(system="short prompt"), 0.0)
print("usage:", {k: u[k] for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}, "-> both cache numbers are 0: no error, no cache. Always LOG these two fields.\n")

print("== F. Limits ==")
r = req()
for i in range(4):
    r["messages"].append({"role": "assistant" if i % 2 == 0 else "user", "content": [{"type": "text", "text": f"m{i}", "cache_control": {"type": "ephemeral"}}]})
try:
    PromptCache().process(r, 0.0)
except InvalidRequest as e:
    print("5 breakpoints ->", e)

print("\n== G. A growing conversation: move the breakpoint to the newest block ==")
c = PromptCache()
msgs, rows = [], []
for turn in range(1, 6):
    msgs = [dict(m_) for m_ in msgs]
    for m_ in msgs:
        if isinstance(m_["content"], list):
            m_["content"] = [{k: v for k, v in b.items() if k != "cache_control"} for b in m_["content"]]
    msgs.append({"role": "user", "content": [{"type": "text", "text": f"turn {turn} user text " * 200, "cache_control": {"type": "ephemeral"}}]})
    u, s, k = run(c, {"system": [{"type": "text", "text": POLICY}], "messages": msgs}, turn * 10.0)
    rows.append((turn, s, u["cache_read_input_tokens"], u["cache_creation_input_tokens"], u["input_tokens"], f"${k:.4f}"))
    msgs.append({"role": "assistant", "content": [{"type": "text", "text": f"turn {turn} answer " * 100}]})
table(rows, ["turn", "result", "read", "written", "uncached", "cost"])
print("Each turn reads everything before it and writes only the NEW part. The lookback (20 blocks) finds the previous entry.")
print("If a long tool-heavy turn adds more than 20 blocks, the previous breakpoint is out of reach -> add an extra breakpoint in the middle.")
