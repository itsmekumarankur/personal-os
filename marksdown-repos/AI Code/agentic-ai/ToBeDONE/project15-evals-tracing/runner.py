"""Run every case, grade it, keep the trace. One JSON file per run, so two runs can be compared later.

Pass rule: a run of a case passes only if EVERY grader passes. With repeats > 1 each case gets a pass RATE (0.67 means
2 of 3 repeats passed). A case that is sometimes right and sometimes wrong is called FLAKY, and it is a finding on its own.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from graders import run_graders
from pricing import trace_totals
from stats import mean, percentile
from tracing import Span


def load_cases(path) -> list:
    cases = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        c = json.loads(line)
        for k in ("id", "category", "question", "graders"):
            if k not in c:
                raise ValueError(f"{path}:{n} missing {k!r}")
        c.setdefault("critical", False)
        c.setdefault("tags", [])
        cases.append(c)
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ids")
    return cases


def _one(case, runtime_factory, judge, repeat):
    agent, tracer, exporter = runtime_factory()
    try:
        result = agent.run(case["question"], case_id=case["id"])
        err = None
    except Exception as e:                       # a crashed agent is a failed case, not a crashed eval
        result, err = None, f"{type(e).__name__}: {e}"
    traces = exporter.all()
    spans = traces[0] if traces else []
    root = next((s for s in spans if s.parent_id is None), None)
    latency = root.duration_ms if root else 0.0
    totals = trace_totals(spans)
    if result is None:
        return {"repeat": repeat, "passed": False, "graders": [], "answer": "", "error": err, "latency_ms": latency,
                "cost_usd": totals["cost_usd"], "llm_calls": totals["llm_calls"], "tool_calls": [], "trace_id": root.trace_id if root else "",
                "trace": [s.to_dict() for s in spans]}
    grades = run_graders(case["graders"], case=case, result=result, totals=totals, latency_ms=latency, judge=judge)
    return {"repeat": repeat, "passed": all(g["passed"] for g in grades) and result.finished, "graders": grades,
            "answer": result.answer, "error": None, "latency_ms": round(latency, 3), "cost_usd": totals["cost_usd"],
            "llm_calls": totals["llm_calls"], "input_tokens": totals["input_tokens"], "output_tokens": totals["output_tokens"],
            "tool_calls": result.tool_calls, "trace_id": result.trace_id, "trace": [s.to_dict() for s in spans]}


def run_suite(cases, runtime_factory, judge=None, repeats=1, workers=4, name="run", meta=None) -> dict:
    jobs = [(c, r) for c in cases for r in range(repeats)]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        outs = list(pool.map(lambda j: _one(j[0], runtime_factory, judge, j[1]), jobs))
    by_case: dict = {}
    for (c, _), o in zip(jobs, outs):
        by_case.setdefault(c["id"], []).append(o)
    out_cases = []
    for c in cases:
        reps = by_case[c["id"]]
        rate = mean([1.0 if r["passed"] else 0.0 for r in reps])
        out_cases.append({"id": c["id"], "category": c["category"], "critical": c["critical"], "tags": c["tags"],
                          "question": c["question"], "pass_rate": rate, "flaky": 0.0 < rate < 1.0, "repeats": reps})
    run = {"meta": {"name": name, "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "repeats": repeats, **(meta or {})},
           "cases": out_cases}
    run["summary"] = summarize(run)
    return run


def summarize(run: dict) -> dict:
    cases = run["cases"]
    reps = [r for c in cases for r in c["repeats"]]
    cats: dict = {}
    for c in cases:
        cats.setdefault(c["category"], []).append(c["pass_rate"])
    lat = [r["latency_ms"] for r in reps]
    return {
        "cases": len(cases), "runs": len(reps),
        "pass_rate": round(mean([c["pass_rate"] for c in cases]), 4),
        "by_category": {k: round(mean(v), 4) for k, v in sorted(cats.items())},
        "flaky_cases": [c["id"] for c in cases if c["flaky"]],
        "critical_failures": [c["id"] for c in cases if c["critical"] and c["pass_rate"] < 1.0],
        "latency_p50_ms": round(percentile(lat, 50), 1), "latency_p95_ms": round(percentile(lat, 95), 1),
        "cost_usd_total": round(sum(r["cost_usd"] for r in reps), 6),
        "cost_usd_per_run": round(mean([r["cost_usd"] for r in reps]), 6),
        "avg_llm_calls": round(mean([r["llm_calls"] for r in reps]), 2),
    }


def save_run(run: dict, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(run, indent=1), encoding="utf-8")


def load_run(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def spans_from_run(trace_dicts) -> list:
    return [Span(trace_id=d["trace_id"], span_id=d["span_id"], parent_id=d["parent_id"], name=d["name"], start_ns=d["start_ns"],
                 kind=d["kind"], end_ns=d["end_ns"], attrs=d["attrs"], events=d["events"], status=d["status"],
                 status_message=d["status_message"], seq=d.get("seq", 0)) for d in trace_dicts]
