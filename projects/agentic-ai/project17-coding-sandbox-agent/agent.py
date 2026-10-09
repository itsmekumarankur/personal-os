"""The coding loop:  look -> edit -> RUN -> read the failure -> edit ...   with brakes.

Brakes (each stops a different runaway):
  max_steps          the loop cannot go on forever
  max_same_failure   the SAME set of failing tests 3 times = stuck; stop and report instead of burning money
  wall budget        total sandbox seconds for the job
  independent check  when the model says 'done', the HARNESS runs the tests itself on a pristine copy of them. The model's claim is not evidence.
"""
import time
from dataclasses import dataclass, field

from tools import TOOL_DEFS, ToolRunner

SYSTEM = ("You are a careful coding agent working in a small Python repository. Make the tests pass by changing the code under test. "
          "You cannot edit tests/. Run the tests after every change. Do not try to reach the network or files outside the workspace; you will not be able to.")


@dataclass
class JobOutcome:
    status: str                  # solved | unsolved | stuck | step_limit | budget | tampered
    steps: int = 0
    final_tests: dict = field(default_factory=dict)
    patch: str = ""
    model_claimed_done: bool = False
    transcript: list = field(default_factory=list)
    stop_reason: str = ""
    sandbox_seconds: float = 0.0


def run_agent(model, runner: ToolRunner, task: str, max_steps: int = 30, max_same_failure: int = 3, sandbox_budget_s: float = 120.0) -> JobOutcome:
    messages = [{"role": "user", "content": task}]
    seen: dict = {}
    out = JobOutcome("unsolved")
    spent = 0.0
    for step in range(1, max_steps + 1):
        content = model(SYSTEM, messages, TOOL_DEFS)
        messages.append({"role": "assistant", "content": content})
        uses = [b for b in content if b["type"] == "tool_use"]
        out.steps = step
        if not uses:
            out.model_claimed_done = True
            out.stop_reason = "model finished"
            break
        results = []
        for u in uses:
            t0 = time.monotonic()
            text, is_err = runner.execute(u["name"], u["input"], step)
            spent += time.monotonic() - t0 if u["name"] in ("run_python", "run_tests") else 0
            results.append({"type": "tool_result", "tool_use_id": u["id"], "content": text, **({"is_error": True} if is_err else {})})
            if u["name"] == "run_tests" and runner.last_tests and not runner.last_tests["ok"]:
                sig = tuple(runner.last_tests["failing"]) or ("<no test results: crash or timeout>",)
                seen[sig] = seen.get(sig, 0) + 1
        messages.append({"role": "user", "content": results})
        if seen and max(seen.values()) >= max_same_failure:
            out.status, out.stop_reason = "stuck", f"the same failure appeared {max(seen.values())} times: {max(seen, key=seen.get)}"
            break
        if spent > sandbox_budget_s:
            out.status, out.stop_reason = "budget", f"sandbox time budget of {sandbox_budget_s}s used"
            break
    else:
        out.status, out.stop_reason = "step_limit", f"{max_steps} steps used"
    # ---- do not trust the claim: verify independently
    tampered = runner.ws.restore_protected()
    text, _ = runner.execute("run_tests", {}, step=out.steps + 1)
    out.final_tests = dict(runner.last_tests or {})
    out.patch = runner.ws.patch()
    out.transcript = messages
    out.sandbox_seconds = round(spent, 2)
    if out.final_tests.get("ok"):
        out.status = "solved"
    elif out.status == "unsolved" and out.model_claimed_done:
        out.status = "unsolved"                                 # the model said "done" but the tests disagree: reported as it is
    if tampered:
        out.status = "tampered" if not out.final_tests.get("ok") else out.status
    return out
