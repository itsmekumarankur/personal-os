"""EXPERIMENT 2 — the test-driven loop, step by step: write, run, read the failure, fix, run again.
Run: python experiments/exp2_tdd_loop.py"""
from _common import table

from fake_coder import FakeCoder
from job import run_job
from sandbox import LocalProcessSandbox, NamespaceSandbox

sb = NamespaceSandbox() if NamespaceSandbox.available() else LocalProcessSandbox()
r = run_job("slugify", FakeCoder("slugify"), sb)
rows = []
for row in r.audit.rows:
    detail = ""
    if "tests" in row:
        t = row["tests"]
        detail = "OK" if t["ok"] else "failing: " + ", ".join(t["failing"])
    elif "error" in row:
        detail = "ERROR " + row["error"][:50]
    args = ", ".join(f"{k}={v}" for k, v in row["args"].items())[:44]
    rows.append((row["step"], row["tool"], args, detail))
print(f"sandbox: {sb.level}\n")
table(rows, ["step", "tool", "arguments", "result"])
o = r.outcome
print(f"\nstatus: {o.status} | steps: {o.steps} | stop: {o.stop_reason} | model said done: {o.model_claimed_done}")
print("The harness re-ran the tests itself at the end (the extra run_tests row). The model's 'all tests pass' is a claim, not evidence.\n")
print("The deliverable is a PATCH for a human to review, not a silent change:\n")
print(r.outcome.patch)
print(f"workspace directory removed after the job: {r.dir_removed}")

print("\n== a task that cannot be solved: stop instead of looping ==")
r2 = run_job("impossible", FakeCoder("impossible"), sb)
print(f"status: {r2.outcome.status} after {r2.outcome.steps} steps -> {r2.outcome.stop_reason}")
print("Two tests contradict each other (add(2,2)==4 and ==5). A loop without a brake would alternate fixes until the budget is gone.")
print("\n== a model that tries to cheat by editing the tests ==")
r3 = run_job("impossible", FakeCoder("impossible", cheat=True), sb)
for row in r3.audit.rows:
    if row["tool"] == "str_replace":
        print("attempt:", row["args"]["path"], "->", row.get("error"))
print("The workspace refuses; status:", r3.outcome.status)
