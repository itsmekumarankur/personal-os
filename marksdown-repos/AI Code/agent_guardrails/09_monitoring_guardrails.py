"""
09 MONITORING GUARDRAILS  -  "watch the fleet, notice trouble, and stop it automatically"

Guardrails 01-08 act per request. Monitoring looks at the SYSTEM over time:
  - METRICS       requests, guardrail blocks, tool errors, cost per minute
  - RULES         block-rate above 30%  -> someone is probing us (WARN)
  - ANOMALY       traffic far above its own baseline (mean + 3 standard deviations)  -> CRITICAL
  - KILL SWITCH   trips automatically after 2 consecutive CRITICAL minutes: agent stops acting,
                  pages a human, and stays OFF until a person resets it
  - DASHBOARD     a few numbers a human can read in 10 seconds

Time is simulated (one loop = one minute) so the demo is instant and deterministic.
Run: python 09_monitoring_guardrails.py
"""
import random
import statistics

BLOCK_RATE_WARN = 0.30
COST_PER_REQUEST = 0.002        # USD, model + tool spend
COST_BUDGET_PER_MIN = 0.20


class KillSwitch:
    def __init__(self):
        self.tripped = False
        self.consecutive_critical = 0

    def feed(self, critical):
        self.consecutive_critical = self.consecutive_critical + 1 if critical else 0
        if self.consecutive_critical >= 2 and not self.tripped:
            self.tripped = True
            return True
        return False

    def reset(self, human):
        print(f"   [kill switch reset by {human}]")
        self.tripped, self.consecutive_critical = False, 0


def traffic(minute, rng):
    """fake traffic: normal until minute 9, then an attack burst"""
    if minute < 9:
        reqs = rng.randint(18, 24)
        blocked = rng.randint(0, 3)
    else:
        reqs = rng.randint(110, 140)
        blocked = int(reqs * rng.uniform(0.55, 0.70))
    return reqs, blocked


if __name__ == "__main__":
    rng = random.Random(42)
    kill = KillSwitch()
    history = []
    print(f"{'min':>3} {'reqs':>5} {'blocked':>7} {'block%':>7} {'cost$':>6}  {'state':<10} alerts")
    for minute in range(1, 16):
        if kill.tripped:
            reqs, blocked, served = 0, 0, False                  # agent is OFF: requests are refused upfront
            print(f"{minute:>3} {'-':>5} {'-':>7} {'-':>7} {'-':>6}  {'KILLED':<10} all requests refused, on-call paged")
            if minute == 13:
                kill.reset("oncall-priya")
            continue
        reqs, blocked = traffic(minute, rng)
        alerts, critical = [], False
        block_rate = blocked / reqs
        cost = reqs * COST_PER_REQUEST
        if block_rate > BLOCK_RATE_WARN:
            alerts.append(f"WARN block-rate {block_rate:.0%} > {BLOCK_RATE_WARN:.0%}")
        if cost > COST_BUDGET_PER_MIN:
            alerts.append(f"WARN cost ${cost:.2f}/min over budget")
        if len(history) >= 5:
            mean, sd = statistics.mean(history), statistics.pstdev(history) or 1.0
            if reqs > mean + 3 * sd:
                alerts.append(f"ANOMALY traffic {reqs} vs baseline {mean:.0f} (+3sd = {mean + 3 * sd:.0f})")
                critical = True
        if not critical:
            history.append(reqs)                                  # never learn the attack as "normal"
        tripped_now = kill.feed(critical)
        if tripped_now:
            alerts.append("KILL SWITCH TRIPPED")
        state = "KILLED" if kill.tripped else ("ALERT" if alerts else "ok")
        print(f"{minute:>3} {reqs:>5} {blocked:>7} {block_rate:>7.0%} {cost:>6.2f}  {state:<10} {'; '.join(alerts)}")
    print("\nWhat to monitor in real agent fleets: block rate by guardrail, tool error rate, steps per task, "
          "tokens per task, approval wait time, fallback rate, and user thumbs-down.")
