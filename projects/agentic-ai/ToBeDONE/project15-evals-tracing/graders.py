"""Graders: small functions that look at one run and say pass or fail.

Order of preference (cheapest and most reliable first):
  1. code checks on the ANSWER   contains / regex / number_close / no_pii
  2. code checks on the TRACE    tool_called / max_tool_calls / max_llm_calls / max_latency_ms / max_cost_usd
  3. a judge model               llm_judge   (only for what code cannot check)
Checking the trace matters: a right answer reached the wrong way (3 tool calls instead of 1, or a guess with no tool) is a bug.
"""
import re
from types import SimpleNamespace

from judge import judge_score
from tracing import redact

_NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def _g(spec, passed, score=None, detail=""):
    return {"type": spec["type"], "passed": bool(passed), "score": float(passed) if score is None else score, "detail": detail}


def numbers_in(text: str):
    out = []
    for m in _NUM.findall(text):
        try:
            out.append(float(m.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return out


def grade_contains(spec, ctx):
    v, a = spec["value"], ctx.answer
    ok = v.lower() in a.lower() if spec.get("case_insensitive", True) else v in a
    return _g(spec, ok, detail=f"looking for {v!r}")


def grade_not_contains(spec, ctx):
    v = spec["value"]
    return _g(spec, v.lower() not in ctx.answer.lower(), detail=f"must not contain {v!r}")


def grade_regex(spec, ctx):
    return _g(spec, re.search(spec["pattern"], ctx.answer, re.I | re.S) is not None, detail=spec["pattern"])


def grade_number_close(spec, ctx):
    exp, tol = float(spec["expected"]), float(spec.get("tolerance_pct", 0.5))
    nums = numbers_in(ctx.answer)
    ok = any(abs(n - exp) <= abs(exp) * tol / 100 for n in nums)
    return _g(spec, ok, detail=f"expected {exp} (+-{tol}%), answer has {nums[:5]}")


def grade_tool_called(spec, ctx):
    want = spec["name"]
    calls = [c for c in ctx.result.tool_calls if c["name"] == want]
    if not calls:
        return _g(spec, False, detail=f"{want} was never called")
    for k, v in (spec.get("args") or {}).items():
        if not any(c["input"].get(k) == v for c in calls):
            return _g(spec, False, detail=f"{want} called but {k} != {v!r}: {[c['input'] for c in calls]}")
    return _g(spec, True, detail=f"{want} called {len(calls)}x")


def grade_tool_not_called(spec, ctx):
    names = [c["name"] for c in ctx.result.tool_calls]
    bad = [n for n in names if spec.get("name") in (None, n)]
    return _g(spec, not bad, detail=f"tools called: {names}")


def grade_max_tool_calls(spec, ctx):
    n = ctx.totals["tool_calls"]
    return _g(spec, n <= spec["n"], detail=f"{n} tool calls (max {spec['n']})")


def grade_max_llm_calls(spec, ctx):
    n = ctx.totals["llm_calls"]
    return _g(spec, n <= spec["n"], detail=f"{n} model calls (max {spec['n']})")


def grade_max_latency_ms(spec, ctx):
    return _g(spec, ctx.latency_ms <= spec["ms"], detail=f"{ctx.latency_ms:.0f} ms (max {spec['ms']})")


def grade_max_cost_usd(spec, ctx):
    c = ctx.totals["cost_usd"]
    return _g(spec, c <= spec["usd"], detail=f"${c:.5f} (max ${spec['usd']})")


def grade_no_pii(spec, ctx):
    return _g(spec, redact(ctx.answer) == ctx.answer, detail="answer must not contain card numbers, keys or emails")


def grade_llm_judge(spec, ctx):
    if ctx.judge is None:
        return _g(spec, False, 0.0, "no judge configured")
    r = judge_score(ctx.judge, ctx.question, ctx.answer, spec["rubric"])
    if r.score is None:
        return _g(spec, False, 0.0, r.reasoning)            # unreadable verdict is never a pass
    return _g(spec, r.score >= spec.get("min_score", 4), r.score / 5, f"judge score {r.score}: {r.reasoning}")


GRADERS = {k[6:]: v for k, v in list(globals().items()) if k.startswith("grade_")}


def run_graders(specs, *, case, result, totals, latency_ms, judge=None) -> list:
    ctx = SimpleNamespace(case=case, question=case["question"], answer=result.answer, result=result,
                          totals=totals, latency_ms=latency_ms, judge=judge)
    out = []
    for spec in specs:
        fn = GRADERS.get(spec["type"])
        if fn is None:
            out.append({"type": spec["type"], "passed": False, "score": 0.0, "detail": "unknown grader type"})
            continue
        try:
            out.append(fn(spec, ctx))
        except Exception as e:                  # a broken grader must show up as a failure, not vanish
            out.append({"type": spec["type"], "passed": False, "score": 0.0, "detail": f"grader error: {type(e).__name__}: {e}"})
    return out
