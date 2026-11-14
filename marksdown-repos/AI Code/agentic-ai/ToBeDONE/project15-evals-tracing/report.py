"""One self-contained HTML page for a run (and optionally a comparison). Collapsible sections, no scripts."""
from html import escape

from runner import spans_from_run
from tracing import render_tree


def _table(rows, head):
    th = "".join(f"<th>{escape(str(h))}</th>" for h in head)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def render_report(run: dict, comparison: dict | None = None) -> str:
    s = run["summary"]
    parts = [f"<h1>Eval report: {escape(run['meta']['name'])}</h1>",
             _table([[s["cases"], s["runs"], s["pass_rate"], s["latency_p50_ms"], s["latency_p95_ms"], s["cost_usd_per_run"], s["avg_llm_calls"]]],
                    ["cases", "runs", "pass rate", "p50 ms", "p95 ms", "cost / run (USD)", "avg model calls"]),
             "<h2>By category</h2>", _table([[k, v] for k, v in s["by_category"].items()], ["category", "pass rate"])]
    if s["critical_failures"]:
        parts.append(f"<p class='bad'><b>Critical cases failing:</b> {escape(', '.join(s['critical_failures']))}</p>")
    if s["flaky_cases"]:
        parts.append(f"<p><b>Flaky (sometimes pass, sometimes fail):</b> {escape(', '.join(s['flaky_cases']))}</p>")
    if comparison:
        v = comparison["verdict"]
        parts.append(f"<h2>Comparison with baseline: {'PASS' if v['passed'] else 'FAIL'}</h2>")
        parts.append("<ul>" + "".join(f"<li>{escape(r)}</li>" for r in v["reasons"]) + "</ul>")
        o = comparison["overall"]
        parts.append(f"<p>pass rate {o['base']} to {o['cand']} (delta {o['delta']}, 95% interval {o['ci95']}), sign test p = {o['sign_test_p']}</p>")
    parts.append("<h2>Cases</h2>")
    for c in sorted(run["cases"], key=lambda c: (c["pass_rate"], c["id"])):
        mark = "PASS" if c["pass_rate"] == 1 else "FAIL" if c["pass_rate"] == 0 else "FLAKY"
        r = c["repeats"][0]
        gr = _table([[g["type"], "yes" if g["passed"] else "NO", g["detail"]] for g in r["graders"]], ["grader", "passed", "detail"])
        tree = escape(render_tree(spans_from_run(r["trace"]))) if r.get("trace") else ""
        parts.append(f"<details {'open' if mark != 'PASS' else ''}><summary>{mark} &middot; {escape(c['id'])} &middot; {escape(c['category'])}"
                     f"{' &middot; critical' if c['critical'] else ''}</summary><p><b>Question:</b> {escape(c['question'])}</p>"
                     f"<p><b>Answer:</b> {escape(r['answer'])}</p>{gr}<h4>Trace</h4><pre>{tree}</pre></details>")
    style = ("body{font:15px/1.5 system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;background:#fff;color:#1b2433}"
             "table{border-collapse:collapse;margin:.5rem 0}td,th{border:1px solid #ccd;padding:.25rem .6rem;text-align:left}"
             "pre{background:#eef2f7;padding:.6rem;overflow:auto;font-size:12px}details{border:1px solid #ccd;margin:.4rem 0;padding:.3rem .6rem}"
             ".bad{color:#b00020}")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Eval report</title><style>{style}</style></head><body>{''.join(parts)}</body></html>"
