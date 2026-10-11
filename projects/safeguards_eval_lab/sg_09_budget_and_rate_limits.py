"""SG-09  Resource safeguards: step cap, token/cost budget, time limit, rate limit.  No LLM needed.
Run: python sg_09_budget_and_rate_limits.py"""
import time


class BudgetExceeded(Exception):
    pass


class Budget:
    """One object per user request. Every model/tool call must pass through .charge()."""

    def __init__(self, max_steps=6, max_tokens=2000, max_seconds=5.0, max_cost_usd=0.02):
        self.max_steps, self.max_tokens, self.max_seconds, self.max_cost = max_steps, max_tokens, max_seconds, max_cost_usd
        self.steps = self.tokens = 0
        self.cost = 0.0
        self.t0 = time.monotonic()

    def charge(self, tokens: int, usd_per_1k: float = 0.003):
        self.steps += 1
        self.tokens += tokens
        self.cost += tokens / 1000 * usd_per_1k
        if self.steps > self.max_steps:                    raise BudgetExceeded(f"step cap {self.max_steps} hit")
        if self.tokens > self.max_tokens:                  raise BudgetExceeded(f"token cap {self.max_tokens} hit")
        if self.cost > self.max_cost:                      raise BudgetExceeded(f"cost cap ${self.max_cost} hit")
        if time.monotonic() - self.t0 > self.max_seconds:  raise BudgetExceeded(f"time cap {self.max_seconds}s hit")


class TokenBucket:
    """Classic rate limiter: capacity tokens, refills at `rate` per second. One bucket per user."""

    def __init__(self, capacity=3, rate=1.0):
        self.capacity, self.rate, self.tokens, self.last = capacity, rate, float(capacity), time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


print("--- 1) a confused agent that loops forever is stopped by the budget ---")
b = Budget(max_steps=5, max_tokens=10_000)
try:
    while True:                                  # simulated agent loop that never reaches a final answer
        b.charge(tokens=300)
        print(f"  step {b.steps}: tokens used so far = {b.tokens}")
except BudgetExceeded as e:
    print("  STOPPED:", e)

print("\n--- 2) a cost cap catches an expensive request ---")
b = Budget(max_steps=100, max_tokens=10**9, max_cost_usd=0.01)
try:
    for _ in range(100):
        b.charge(tokens=1500)
except BudgetExceeded as e:
    print("  STOPPED:", e, f"(spent ${b.cost:.4f})")

print("\n--- 3) rate limit: 6 rapid requests from one user, bucket holds 3 ---")
bucket = TokenBucket(capacity=3, rate=1.0)
print("  ", ["allowed" if bucket.allow() else "REJECTED" for _ in range(6)])
time.sleep(1.1)
print("   after 1.1s pause:", "allowed" if bucket.allow() else "REJECTED")

print("\nWhere real code uses this: read response.usage_metadata after each LLM call and pass it to charge();")
print("LangGraph also has recursion_limit (LG-05) as a built-in step cap.")


"""
            USER SENDS REQUEST
                    |
                    v
        +-------------------------+
        | CREATE REQUEST BUDGET   |
        | Max steps:   6          |
        | Max tokens:  2,000      |
        | Max time:    5 seconds  |
        | Max cost:    $0.02      |
        +-------------------------+
                    |
                    v
        +-------------------------+
        | AI AGENT CALLS LLM/TOOL |
        +-------------------------+
                    |
                    v
        +-------------------------+
        | CHARGE THE BUDGET       |
        | Count steps, tokens,    |
        | estimated cost and time |
        +-------------------------+
                    |
                    v
        +-------------------------+
        | ANY LIMIT EXCEEDED?     |
        +-------------------------+
                    |
             +------+------+
             |             |
            YES            NO
             |             |
             v             v
      +---------------+  CONTINUE
      | STOP AGENT    |      |
      | Raise error   |      v
      +---------------+  NEXT STEP
                              |
                              |
                    Repeats until the
                    agent finishes or
                    reaches a limit


       SEPARATE PROTECTION: RATE LIMIT
       --------------------------------

          USER SENDS A REQUEST
                    |
                    v
        +-------------------------+
        | TOKEN BUCKET CHECK      |
        | Does the user have      |
        | an available token?     |
        +-------------------------+
                    |
             +------+------+
             |             |
        TOKEN AVAILABLE   NO TOKEN
             |             |
             v             v
          ALLOW         REJECT
          REQUEST       REQUEST

       Bucket refills over time
"""