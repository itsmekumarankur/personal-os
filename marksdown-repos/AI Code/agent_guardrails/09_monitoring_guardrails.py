"""
09 MONITORING GUARDRAILS  -  "watch the fleet, notice trouble, and stop it automatically"
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


"""
HENGLISH SUMMARY:
Imagine ek bank ne apna AI Wealth Assistant deploy kiya hai, jo thousands of customers ki portfolio queries aur investment requests handle karta hai. Ab tak ke guardrails (01–08) har individual request ko secure kar rahe the, lekin bank ko ye bhi dekhna hai ki poora AI system time ke saath healthy aur secure chal raha hai ya nahi. Iske liye MONITORING guardrail kaam karta hai. Sabse pehle METRICS collect hote hain, jaise kitne requests aaye, kitne block hue, tool errors kitne aaye aur har minute AI par kitna paisa spend ho raha hai. Phir RULES check karte hain ki agar 30% se zyada requests block ho rahi hain, toh ho sakta hai koi attacker system ko probe kar raha ho, isliye WARN alert generate hota hai. Uske baad ANOMALY DETECTION normal traffic ka baseline banata hai aur agar traffic average se 3 standard deviations zyada ho jata hai, toh CRITICAL alert generate karta hai. Maan lo normally 20 requests per minute aati hain, lekin suddenly 120 requests aane lagti hain, toh system ise suspicious traffic burst samajh sakta hai. Agar lagatar 2 minutes tak CRITICAL anomaly detect hoti hai, toh KILL SWITCH automatically AI agent ko OFF kar deta hai, naye requests refuse karta hai aur human on-call engineer ko alert bhejta hai. Agent tab tak OFF rehta hai jab tak human engineer manually reset nahi karta. Finally, DASHBOARD ye saare important numbers ek jagah dikhata hai, taaki engineer 10 seconds mein samajh sake ki system healthy hai, warning mein hai ya completely stopped hai. Is demo mein har loop ek minute represent karta hai aur minute 9 ke baad attack traffic simulate hota hai. Simple baat: Monitoring guardrail AI ke individual actions ko nahi, balki poore AI system ki health, security, traffic aur cost ko continuously monitor karta hai; aur problem serious hone par automatically agent ko stop kar deta hai.
"""


"""
                 AI WEALTH ASSISTANT
                         |
                         v
              +----------------------+
              |  MONITORING LAYER    |
              |  Watch entire system |
              +----------------------+
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
   1. METRICS         2. RULES         3. ANOMALY
   Collect data       Fixed limits     Detect unusual
        |                |             traffic
        |                |                |
        v                v                v
   - Requests         Block > 30%      Baseline traffic
   - Blocked          = WARN           (Mean + 3 SD)
   - Tool errors                         |
   - Cost/minute                         v
   - Cost/request                    CRITICAL ALERT
        |                                |
        +----------------+---------------+
                         |
                         v
                 4. KILL SWITCH
                         |
                 2 consecutive
                 CRITICAL minutes
                         |
                         v
                +------------------+
                |   AGENT OFF      |
                |   STOP ACTIONS   |
                +------------------+
                         |
              +----------+----------+
              |                     |
              v                     v
        REFUSE REQUESTS       PAGE HUMAN
                                    |
                                    v
                            HUMAN MANUAL RESET
                                    |
                                    v
                              AGENT ON
                                |
                                v
                        5. DASHBOARD
                                |
                                v
                        Human sees status
                        within 10 seconds
                                |
                    +-----------+-----------+
                    |           |           |
                    v           v           v
                GREEN       YELLOW       RED
                    OK          WARN       KILLED



Attack scenario — How it works::
==================================

       NORMAL TRAFFIC                ATTACK TRAFFIC
       (Minute 1–8)                  (Minute 9 onwards)
             |                             |
             v                             v
       18–24 requests                 110–140 requests
             |                             |
             v                             v
       Normal baseline              Traffic spike
                                           |
                                           v
                                    Mean + 3 SD crossed?
                                           |
                                           v
                                    CRITICAL ALERT
                                           |
                                  +--------+--------+
                                  |                 |
                               Minute 1          Minute 2
                               CRITICAL          CRITICAL
                                  |                 |
                                  +--------+--------+
                                           |
                                           v
                                     KILL SWITCH
                                           |
                                           v
                                      AGENT OFF
                                           |
                                           v
                                   Human is paged
                                           |
                                           v
                                  Manual reset only
"""