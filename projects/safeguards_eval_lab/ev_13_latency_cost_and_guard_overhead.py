"""EV-13  Quality is not the only metric: latency percentiles, cost per request, and what your guardrails add.
No LLM (simulated measurements).  Run: python ev_13_latency_cost_and_guard_overhead.py"""
import random, statistics, time

rng = random.Random(7)
PRICE_PER_1K = {"input": 0.0008, "output": 0.004}        # example prices in USD per 1K tokens (check your provider)

# 200 simulated requests: latency has a long tail (a few very slow ones), tokens vary
requests = []
for _ in range(200):
    lat = rng.lognormvariate(0.2, 0.55)                  # seconds
    requests.append({"latency": lat, "in": rng.randint(300, 1800), "out": rng.randint(60, 500)})


def pct(values, p):
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


lat = [r["latency"] for r in requests]
print("--- latency ---")
print(f"mean={statistics.mean(lat):.2f}s  p50={pct(lat, 50):.2f}s  p95={pct(lat, 95):.2f}s  p99={pct(lat, 99):.2f}s  max={max(lat):.2f}s")
slo = 3.0
print(f"SLO p95 < {slo}s : {'MET' if pct(lat, 95) < slo else 'VIOLATED'}   (averages hide the slow tail users actually feel)")

cost = [r["in"] / 1000 * PRICE_PER_1K["input"] + r["out"] / 1000 * PRICE_PER_1K["output"] for r in requests]
print("\n--- cost ---")
print(f"avg cost/request = ${statistics.mean(cost):.4f}   p95 = ${pct(cost, 95):.4f}   per 1,000 requests = ${sum(cost) / len(cost) * 1000:.2f}")
worst = sorted(range(len(requests)), key=lambda i: -cost[i])[:3]
print("3 most expensive requests (tokens in/out):", [(requests[i]['in'], requests[i]['out']) for i in worst])

print("\n--- what do the guardrails add? (regex measured for real, model-based ones typical/simulated) ---")
import re
pattern = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
text = "My email is ankur.k@example.com " * 20
t0 = time.perf_counter()
for _ in range(2000):
    pattern.findall(text)
regex_ms = (time.perf_counter() - t0) / 2000 * 1000
stages = [("PII regex (measured)", regex_ms, 0.0), ("injection heuristics", 0.2, 0.0),
          ("LLM judge: injection (simulated)", 650.0, 0.0006), ("LLM judge: moderation (simulated)", 600.0, 0.0006)]
print(f"{'stage':36}{'added latency':>16}{'added cost/request':>22}")
for name, ms, usd in stages:
    print(f"{name:36}{ms:>13.2f} ms{usd:>19.4f} $")
print("\nTake-away: deterministic guards cost ~nothing, each judge call costs ~0.6s and extra money.")
print("Run guards in parallel with the main model call where possible, run cheap ones first, and only call the judge")
print("when the cheap layers are unsure. Track these numbers on the same dashboard as quality.")
