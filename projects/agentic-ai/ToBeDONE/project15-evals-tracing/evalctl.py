"""Command line for the eval platform. Every command works without an API key when you use the fake modes.

  python evalctl.py run --agent fake-good     --out runs/good.json
  python evalctl.py run --agent fake-degraded --out runs/bad.json
  python evalctl.py compare runs/good.json runs/bad.json
  python evalctl.py gate    runs/good.json runs/bad.json        # exit code 1 if the candidate must not ship
  python evalctl.py report  runs/bad.json --baseline runs/good.json --out report.html
  python evalctl.py trace   runs/bad.json emi_5y
  python evalctl.py calibrate --judge heuristic
"""
import argparse
import json
import sys
from pathlib import Path

from compare import Thresholds, compare, format_comparison
from judge import calibrate
from report import render_report
from runner import load_cases, load_run, run_suite, save_run, spans_from_run
from runtime import MODES, make_judge, make_runtime_factory
from tracing import render_tree

HERE = Path(__file__).parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="evalctl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--agent", choices=MODES, default="fake-good")
    r.add_argument("--judge", choices=("none", "heuristic", "anthropic"), default="heuristic")
    r.add_argument("--cases", default=str(HERE / "evals" / "cases.jsonl"))
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--out", required=True)
    for name in ("compare", "gate"):
        c = sub.add_parser(name)
        c.add_argument("baseline")
        c.add_argument("candidate")
        c.add_argument("--max-drop", type=float, default=0.03)
        c.add_argument("--max-category-drop", type=float, default=0.10)
        c.add_argument("--max-cost-increase", type=float, default=25.0)
        c.add_argument("--max-p95-increase", type=float, default=30.0)
    rp = sub.add_parser("report")
    rp.add_argument("run")
    rp.add_argument("--baseline")
    rp.add_argument("--out", default="report.html")
    t = sub.add_parser("trace")
    t.add_argument("run")
    t.add_argument("case_id")
    cal = sub.add_parser("calibrate")
    cal.add_argument("--judge", choices=("heuristic", "anthropic"), default="heuristic")
    cal.add_argument("--labels", default=str(HERE / "calibration" / "human_labels.jsonl"))
    a = ap.parse_args(argv)

    if a.cmd == "run":
        run = run_suite(load_cases(a.cases), make_runtime_factory(a.agent), make_judge(a.judge), a.repeats, a.workers,
                        name=Path(a.out).stem, meta={"agent": a.agent, "judge": a.judge})
        save_run(run, a.out)
        print(json.dumps(run["summary"], indent=1))
        return 0
    if a.cmd in ("compare", "gate"):
        th = Thresholds(a.max_drop, a.max_category_drop, a.max_cost_increase, a.max_p95_increase)
        cmp = compare(load_run(a.baseline), load_run(a.candidate), th)
        print(format_comparison(cmp))
        return 0 if (a.cmd == "compare" or cmp["verdict"]["passed"]) else 1
    if a.cmd == "report":
        run = load_run(a.run)
        cmp = compare(load_run(a.baseline), run) if a.baseline else None
        Path(a.out).write_text(render_report(run, cmp), encoding="utf-8")
        print("wrote", a.out)
        return 0
    if a.cmd == "trace":
        run = load_run(a.run)
        case = next((c for c in run["cases"] if c["id"] == a.case_id), None)
        if not case:
            print("no such case", file=sys.stderr)
            return 2
        print(render_tree(spans_from_run(case["repeats"][0]["trace"])))
        return 0
    if a.cmd == "calibrate":
        items = [json.loads(line) for line in Path(a.labels).read_text(encoding="utf-8").splitlines() if line.strip()]
        res = calibrate(make_judge(a.judge), items)
        print({k: v for k, v in res.items() if k != "rows"})
        for row in res["rows"]:
            if row["human"] != row["judge"]:
                print("DISAGREE", row)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
