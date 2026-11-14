"""EXPERIMENT 3 — structured output: which layer catches which kind of wrong?
Run:  python experiments/exp3_structured.py"""
import datetime as dt

from _common import table

from fake_model import FakeStreamingModel
from structured import ExtractionFailed, extract

SRC = "Invoice INV-1042 from Acme Traders dated 2025-03-14. Items: 3 x Widget @ 120.50; 2 x Gadget @ 99.99. Total: 561.48 INR."
TODAY = dt.date(2026, 10, 8)
rows = []
for mode in ("good", "sloppy", "hallucinating", "flaky", "stubborn"):
    for label, kw in (("schema only, no retry", dict(semantic=False, max_attempts=1)),
                      ("schema + semantic, no retry", dict(semantic=True, max_attempts=1)),
                      ("schema + semantic + repair x3", dict(semantic=True, max_attempts=3))):
        m = FakeStreamingModel(mode=mode)
        try:
            r = extract(lambda q: m.create(q), SRC, today=TODAY, **kw)
            wrong = abs(r.value.total - 561.48) > 0.001 or r.value.vendor != "Acme Traders"
            out = "ACCEPTED but WRONG !!" if wrong else f"ok (attempt {len(r.attempts)})"
        except ExtractionFailed as e:
            out = f"rejected after {len(e.attempts)}: {e.attempts[-1]['kind']}"
        rows.append((mode, label, out))
table(rows, ["model behaviour", "pipeline", "result"])
print("\nRead the 'hallucinating' rows: the JSON is perfectly valid, so a schema-only pipeline ACCEPTS the wrong total and a made-up vendor.")
print("Only the semantic layer (items add up, vendor appears in the source) catches it, and only repair turns it into a correct answer.")
print("'stubborn' shows the loop must end: after N attempts we raise, with every attempt's errors, instead of looping or guessing.")

print("\n== what the repair message looks like (this is all the model sees) ==")
m = FakeStreamingModel(mode="sloppy")
seen = []
extract(lambda q: (seen.append(q), m.create(q))[1], SRC, today=TODAY)
print(seen[1]["messages"][-1]["content"][0]["content"])
