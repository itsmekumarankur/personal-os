"""Run the orchestrator from the terminal.

    python cli.py samples/goal.md
    python cli.py samples/goal.md --max-tasks 3
"""
import argparse
from pathlib import Path

from orchestrator import orchestrate

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument("--max-tasks", type=int, default=4)
args = parser.parse_args()

r = orchestrate(Path(args.file).read_text(encoding="utf-8"), args.max_tasks)

print("=== PLAN (decided by the model) ===")
print(r["analysis"])
for t in r["tasks"]:
    status = "ok" if t["ok"] else f"FAILED: {t['error']}"
    print(f"  {t['id']}. {t['title']}  [{status}, {t['seconds']}s]")
if r["truncated"]:
    print("  (the plan had more tasks than allowed; extra tasks were dropped)")
if r["fallback"]:
    print("  (the planner gave nothing usable; ran as one task)")

print("\n=== FINAL ANSWER ===")
print(r["final"])

t = r["timing"]
print(f"\ncomplete: {r['complete']}   total {t['total_seconds']}s "
      f"(plan {t['plan_seconds']}s, workers {t['workers_wall_seconds']}s wall / "
      f"{t['workers_sum_seconds']}s if one by one, synthesis {t['synthesis_seconds']}s)")
