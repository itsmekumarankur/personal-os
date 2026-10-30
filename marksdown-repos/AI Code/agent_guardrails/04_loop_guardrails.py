"""
04 LOOP GUARDRAILS  -  "an agent is a while-loop; make sure it ends"

Agents think -> act -> observe -> repeat. Without limits that loop can run forever and burn money.
Five brakes (all independent, any one stops the run):
  1. MAX STEPS         hard ceiling on iterations
  2. TOKEN/COST BUDGET stop when the spend limit is reached
  3. WALL-CLOCK        deadline for the whole task
  4. REPEAT DETECTION  same tool + same arguments again and again = stuck
  5. NO-PROGRESS       different calls but the same observation = going nowhere

When a brake fires, the agent must stop SAFELY: return a partial answer + reason, never crash silently.
Time is simulated (virtual clock) so this demo runs instantly.
Run: python 04_loop_guardrails.py
"""
from collections import Counter

MAX_STEPS, TOKEN_BUDGET, DEADLINE_S = 8, 3000, 10.0
MAX_REPEAT, MAX_SAME_OBSERVATION = 2, 3


def run_agent(name, script):
    """script(step_no) -> dict(tool,args,obs,tokens,secs,done) : a fake model+tool pair"""
    tokens = elapsed = 0.0
    sigs, observations = Counter(), []
    for n in range(1, MAX_STEPS + 2):
        if n > MAX_STEPS:
            return name, f"STOPPED max steps ({MAX_STEPS}) reached"
        s = script(n)
        tokens += s["tokens"]
        elapsed += s["secs"]
        sig = (s["tool"], s["args"])
        sigs[sig] += 1
        observations.append(s["obs"])
        print(f"      step {n}: {s['tool']}({s['args']}) -> {s['obs'][:34]!r}  tokens={int(tokens)} t={elapsed:.1f}s")
        if s["done"]:
            return name, f"FINISHED normally in {n} steps"
        if tokens > TOKEN_BUDGET:
            return name, f"STOPPED token budget ({int(tokens)} > {TOKEN_BUDGET})"
        if elapsed > DEADLINE_S:
            return name, f"STOPPED deadline ({elapsed:.1f}s > {DEADLINE_S}s)"
        if sigs[sig] > MAX_REPEAT:
            return name, f"STOPPED repeated call {sig} x{sigs[sig]}"
        if len(observations) >= MAX_SAME_OBSERVATION and len(set(observations[-MAX_SAME_OBSERVATION:])) == 1:
            return name, f"STOPPED no progress (same observation {MAX_SAME_OBSERVATION}x)"


def step(tool, args, obs, tokens=300, secs=1.0, done=False):
    return dict(tool=tool, args=args, obs=obs, tokens=tokens, secs=secs, done=done)


SCENARIOS = {
    "healthy: look up, compute, answer":
        lambda n: [step("get_holdings", "ACC1", "INFY x5, TCS x2"), step("get_price", "INFY", "1500"),
                   step("answer", "-", "Portfolio is 15,500", done=True)][n - 1],
    "stuck: calls same API again and again":
        lambda n: step("get_price", "INFY", f"timeout #{n}"),
    "going in circles: new args, same result":
        lambda n: step("search_docs", f"query v{n}", "no results found"),
    "token hog: huge context each step":
        lambda n: step("read_report", f"page {n}", f"page {n} text", tokens=1100),
    "slow tool: 4s per call":
        lambda n: step("slow_api", f"call {n}", f"partial {n}", secs=4.0),
    "runaway: always something new to do":
        lambda n: step("explore", f"item {n}", f"found item {n}"),
}

if __name__ == "__main__":
    results = []
    for name, script in SCENARIOS.items():
        print(f"\n  >> {name}")
        results.append(run_agent(name, script))
    print("\nSUMMARY")
    for name, outcome in results:
        print(f"  {name:<44} {outcome}")
