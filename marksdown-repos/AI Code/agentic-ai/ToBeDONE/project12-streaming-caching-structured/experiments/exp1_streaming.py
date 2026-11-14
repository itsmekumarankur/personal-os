"""EXPERIMENT 1 — what streaming really changes (and what it does not).
Run:  python experiments/exp1_streaming.py"""
from _common import bar, table  # noqa: F401

from events import StreamAccumulator, sse_line
from fake_model import FakeStreamingModel
from partial_json import parse_partial

m = FakeStreamingModel()
req = {"system": "You are helpful.", "messages": [{"role": "user", "content": "explain streaming in 60 words"}]}

print("== 1. The same answer, two ways ==")
evs = list(m.stream(req))
first_text = next(e.t for e in evs if e.event["type"] == "content_block_delta")
last = evs[-1].t
print(f"non-streaming: the user sees NOTHING for {last:.2f}s, then everything.")
print(f"streaming    : first words after {first_text:.2f}s, last word after {last:.2f}s.  (same total, shorter WAIT)")
print("\ntimeline (each # = 100 ms; '|' = a text chunk reaches the screen)")
t_prev = 0
line = ""
for e in evs:
    if e.event["type"] == "content_block_delta":
        line += " " * int((e.t - t_prev) * 10) + "|"
        t_prev = e.t
print("  " + "." * int(first_text * 10) + line.lstrip())

print("\n== 2. The first events on the wire (what a browser receives) ==")
for e in evs[:4]:
    print(sse_line(e.event).rstrip().replace("\n", "\n   "))
    print()

print("== 3. A tool call arrives as pieces of a JSON string ==")
src = "Invoice INV-1042 from Acme Traders dated 2025-03-14. Items: 3 x Widget @ 120.50; 2 x Gadget @ 99.99. Total: 561.48 INR."
import structured  # noqa: E402

acc, raw = StreamAccumulator(), ""
rows = []
for te in m.stream(structured.request_for(src)):
    acc.feed(te.event)
    d = te.event.get("delta", {})
    if d.get("type") == "input_json_delta":
        raw += d["partial_json"]
        rows.append((f"{te.t:.2f}s", repr(d["partial_json"]), str(parse_partial(raw))[:70]))
table(rows[:6] + [("...", "...", "...")] + rows[-3:], ["t", "fragment", "best-effort reading (a HINT for the screen)"])
print("\nNotice 'total': a half-typed number like 561 would be shown as 561 -> NEVER act on the partial value.")
print("The final input exists only after content_block_stop:", acc.result()["content"][0]["input"]["total"])

print("\n== 4. Errors in the middle of a stream (HTTP 200 was already sent) ==")
bad = FakeStreamingModel(fail_after_events=8)
acc = StreamAccumulator()
try:
    for te in bad.stream(req):
        acc.feed(te.event)
except Exception as e:
    kept = acc.partial()["content"]
    print("caught:", e)
    print("text we can keep and show:", repr(kept[0]["text"][:60]) if kept else "nothing")
    print("recovery options: (a) show partial + 'retry', (b) ask the model to CONTINUE from the partial text, (c) retry from scratch. A half tool_use is unusable: drop it.")
