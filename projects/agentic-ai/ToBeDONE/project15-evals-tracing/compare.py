"""Compare two runs (baseline vs candidate) and decide whether the candidate may ship.

Two ideas to keep apart:
  * the GATE   fixed rules agreed in advance ('pass rate may not drop by more than 3 points'). Deterministic. CI uses this.
  * the NOISE  a sign test and a bootstrap interval that tell you whether the difference could be luck.
With small test sets the noise is large, so the report prints both and never hides the p-value.
"""
from dataclasses import dataclass

from stats import bootstrap_ci, mean, sign_test_p

EPS = 1e-9


@dataclass
class Thresholds:
    max_pass_drop: float = 0.03               # absolute, 0.03 = 3 points
    max_category_drop: float = 0.10
    max_cost_increase_pct: float = 25.0
    max_p95_latency_increase_pct: float = 30.0
    allow_critical_regression: bool = False


def _pct(base, cand):
    if base == 0:
        return 0.0 if cand == 0 else float("inf")
    return (cand - base) / base * 100


def compare(base: dict, cand: dict, th: Thresholds | None = None) -> dict:
    th = th or Thresholds()
    b = {c["id"]: c for c in base["cases"]}
    k = {c["id"]: c for c in cand["cases"]}
    shared = sorted(set(b) & set(k))
    missing = sorted(set(b) ^ set(k))
    deltas = [k[i]["pass_rate"] - b[i]["pass_rate"] for i in shared]
    improved = [i for i in shared if k[i]["pass_rate"] > b[i]["pass_rate"] + EPS]
    regressed = [i for i in shared if k[i]["pass_rate"] < b[i]["pass_rate"] - EPS]
    crit_reg = [i for i in regressed if k[i]["critical"]]
    cats = {}
    for cat in sorted({k[i]["category"] for i in shared}):
        ids = [i for i in shared if k[i]["category"] == cat]
        cats[cat] = {"base": round(mean([b[i]["pass_rate"] for i in ids]), 4), "cand": round(mean([k[i]["pass_rate"] for i in ids]), 4)}
        cats[cat]["delta"] = round(cats[cat]["cand"] - cats[cat]["base"], 4)
    sb, sc = base["summary"], cand["summary"]
    overall_delta = mean(deltas)
    lo, hi = bootstrap_ci(deltas)
    cost_change = _pct(sb["cost_usd_per_run"], sc["cost_usd_per_run"])
    p95_change = _pct(sb["latency_p95_ms"], sc["latency_p95_ms"])
    reasons = []
    if missing:
        reasons.append(f"cases differ between runs: {missing}")
    if overall_delta < -th.max_pass_drop - EPS:
        reasons.append(f"pass rate dropped {abs(overall_delta):.3f} (limit {th.max_pass_drop})")
    for cat, v in cats.items():
        if v["delta"] < -th.max_category_drop - EPS:
            reasons.append(f"category {cat} dropped {abs(v['delta']):.3f} (limit {th.max_category_drop})")
    if crit_reg and not th.allow_critical_regression:
        reasons.append(f"critical cases regressed: {crit_reg}")
    if cost_change > th.max_cost_increase_pct:
        reasons.append(f"cost per run up {cost_change:.1f}% (limit {th.max_cost_increase_pct}%)")
    if p95_change > th.max_p95_latency_increase_pct:
        reasons.append(f"p95 latency up {p95_change:.1f}% (limit {th.max_p95_latency_increase_pct}%)")
    return {
        "overall": {"base": sb["pass_rate"], "cand": sc["pass_rate"], "delta": round(overall_delta, 4),
                    "ci95": [round(lo, 4), round(hi, 4)], "sign_test_p": round(sign_test_p(len(improved), len(regressed)), 4),
                    "improved": improved, "regressed": regressed, "n_cases": len(shared)},
        "categories": cats, "critical_regressions": crit_reg,
        "cost": {"base": sb["cost_usd_per_run"], "cand": sc["cost_usd_per_run"], "change_pct": round(cost_change, 1)},
        "latency_p95": {"base": sb["latency_p95_ms"], "cand": sc["latency_p95_ms"], "change_pct": round(p95_change, 1)},
        "missing_cases": missing,
        "verdict": {"passed": not reasons, "reasons": reasons},
    }


def format_comparison(c: dict) -> str:
    o = c["overall"]
    lines = [f"pass rate   {o['base']:.3f} -> {o['cand']:.3f}   (delta {o['delta']:+.3f}, 95% interval {o['ci95'][0]:+.3f}..{o['ci95'][1]:+.3f})",
             f"sign test   {len(o['improved'])} better, {len(o['regressed'])} worse, p = {o['sign_test_p']}  "
             + ("(could be luck)" if o["sign_test_p"] >= 0.05 else "(unlikely to be luck)"),
             f"cost / run  {c['cost']['base']:.5f} -> {c['cost']['cand']:.5f}   ({c['cost']['change_pct']:+.1f}%)",
             f"p95 latency {c['latency_p95']['base']:.0f} ms -> {c['latency_p95']['cand']:.0f} ms   ({c['latency_p95']['change_pct']:+.1f}%)"]
    for cat, v in c["categories"].items():
        lines.append(f"  {cat:<8} {v['base']:.2f} -> {v['cand']:.2f}  ({v['delta']:+.2f})")
    if o["regressed"]:
        lines.append("regressed:  " + ", ".join(o["regressed"]))
    if o["improved"]:
        lines.append("improved:   " + ", ".join(o["improved"]))
    lines.append("VERDICT: " + ("PASS" if c["verdict"]["passed"] else "FAIL"))
    lines += ["  - " + r for r in c["verdict"]["reasons"]]
    return "\n".join(lines)
