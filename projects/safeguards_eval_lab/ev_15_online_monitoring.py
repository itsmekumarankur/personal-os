"""EV-15  Evaluation does not stop at release: sample live traffic, track rolling quality, alert on drift.
No LLM (simulated traffic).  Run: python ev_15_online_monitoring.py"""
import random

rng = random.Random(11)
N, WINDOW, SAMPLE_RATE = 400, 50, 0.40
CHANGE_AT = 180                                   # at request 180 someone ships a worse prompt / the data drifts

stream = []
for i in range(N):
    p_good = 0.92 if i < CHANGE_AT else 0.60       # true (hidden) quality of the system
    good = rng.random() < p_good
    stream.append({"id": i, "good": good,
                   "format_ok": rng.random() < (0.99 if i < CHANGE_AT else 0.93),     # cheap check on 100% of traffic
                   "thumbs_down": (not good) and rng.random() < 0.35 or (good and rng.random() < 0.02)})

judged = [r for r in stream if rng.random() < SAMPLE_RATE]            # expensive judge only on a 20% random sample
print(f"{N} requests, {len(judged)} sampled for judging ({SAMPLE_RATE:.0%}), rolling window = {WINDOW} requests\n")
print(f"{'requests':>10} {'format ok':>10} {'thumbs-down':>12} {'judged quality':>15}  status")

baseline_quality = 0.90
breaches, first_alert = 0, None
for end in range(WINDOW, N + 1, WINDOW):
    window = stream[end - WINDOW:end]
    fmt = sum(r["format_ok"] for r in window) / WINDOW
    td = sum(r["thumbs_down"] for r in window) / WINDOW
    jw = [r for r in judged if end - WINDOW <= r["id"] < end]
    q = sum(r["good"] for r in jw) / len(jw) if jw else float("nan")
    bad = q < baseline_quality - 0.10 or td > 0.15
    breaches = breaches + 1 if bad else 0                  # require 2 bad windows in a row: one noisy window is not an incident
    status = ""
    if bad and breaches < 2:
        status = "(watch: 1 bad window)"
    if breaches >= 2:
        status = "ALERT: sustained quality drift"
        first_alert = first_alert or (end - WINDOW, end)
    print(f"{end - WINDOW:>4}-{end:<5} {fmt:>10.0%} {td:>12.0%} {q:>15.0%}  {status}")

print(f"\nThe real change happened at request {CHANGE_AT}. First alert: window {first_alert[0]}-{first_alert[1]}." if first_alert else "\nNo alert fired.")
print("Small samples are noisy, so alerts use a rolling window AND require consecutive breaches (debouncing).")
print("""
Signals used in production, cheapest to most expensive:
  1. hard checks on 100% of traffic: JSON valid, no leaks, guard-trip rate (SG-16), latency, errors
  2. user feedback: thumbs-down rate, retries, escalations to a human agent, abandoned sessions
  3. LLM judge on a random SAMPLE (EV-03/06/07) - sampling keeps cost flat as traffic grows
  4. human review of a small slice, especially everything the judge or users flagged
Close the loop: failures found online become new golden-set rows (EV-01), so the next release is tested against them.
Tools that do this at scale: LangSmith, Langfuse, Arize Phoenix, Braintrust - same ideas, with dashboards.""")
