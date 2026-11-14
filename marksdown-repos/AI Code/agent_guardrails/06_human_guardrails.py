"""
06 HUMAN GUARDRAILS (human-in-the-loop)  -  "some decisions must not be made by an agent alone"

Run: python 06_human_guardrails.py
"""
from dataclasses import dataclass

CONFIDENCE_FLOOR = 0.70


@dataclass
class Request:
    id: str
    action: str
    amount: float
    confidence: float
    requested_by: str


@dataclass
class Approval:
    approver: str
    level: int            # 1 = officer, 2 = senior manager
    approve: bool
    note: str = ""


def policy(req):
    """-> (approvals_needed, minimum_level, reason)"""
    if req.amount > 200_000:
        return 2, 2, "very high value: four-eyes with senior approvers"
    if req.amount > 20_000:
        return 1, 1, "above auto limit: one officer approval"
    if req.confidence < CONFIDENCE_FLOOR:
        return 1, 1, f"agent confidence {req.confidence:.2f} below {CONFIDENCE_FLOOR}: human double-check"
    return 0, 0, "within limits and confident: no human needed"


def decide(req, responses):
    needed, min_level, why = policy(req)
    print(f"   policy: {why}")
    if needed == 0:
        return "AUTO-APPROVED (no human required)"
    valid, seen = [], set()
    for r in responses:
        if r.approver == req.requested_by:
            print(f"   ignored {r.approver}: self-approval not allowed")
            continue
        if r.level < min_level:
            print(f"   ignored {r.approver}: level {r.level} < required {min_level}")
            continue
        if r.approver in seen:
            print(f"   ignored duplicate vote from {r.approver}")
            continue
        seen.add(r.approver)
        if not r.approve:
            return f"REJECTED by {r.approver} ({r.note})  -> agent must not proceed"
        valid.append(r)
    if len(valid) >= needed:
        return "APPROVED by " + " + ".join(v.approver for v in valid)
    if not responses:
        return "TIMEOUT -> DENIED (fail closed)"
    return f"INSUFFICIENT approvals ({len(valid)}/{needed}) -> DENIED"


if __name__ == "__main__":
    cases = [
        ("small and confident",             Request("R1", "buy INFY", 7_500, 0.95, "agent-7"), []),
        ("medium, officer approves",        Request("R2", "buy TCS", 40_000, 0.90, "agent-7"), [Approval("priya", 1, True, "ok")]),
        ("medium, nobody answers",          Request("R3", "buy TCS", 40_000, 0.90, "agent-7"), []),
        ("small but agent unsure",          Request("R4", "sell HDFCBANK", 9_000, 0.55, "agent-7"), [Approval("priya", 1, False, "looks wrong, account has pending KYC")]),
        ("huge: one approval is not enough", Request("R5", "transfer", 500_000, 0.92, "agent-7"), [Approval("rahul", 2, True)]),
        ("huge: junior + self-approval",    Request("R6", "transfer", 500_000, 0.92, "agent-7"),
         [Approval("agent-7", 2, True), Approval("intern", 1, True), Approval("rahul", 2, True)]),
        ("huge: two senior approvers",      Request("R7", "transfer", 500_000, 0.92, "agent-7"), [Approval("rahul", 2, True), Approval("meera", 2, True)]),
    ]
    for label, req, responses in cases:
        print(f"\n>> {label}: {req.action} {req.amount:,.0f} (confidence {req.confidence})")
        print(f"   RESULT: {decide(req, responses)}")


"""
HENGLISH SUMMARY:
Human Guardrail ka simple meaning hai ki AI Agent ko har decision khud lene ki permission nahi hoti. Agar AI koi high-value transaction kar raha hai, koi irreversible action hai, customer ko directly impact karne wala decision hai, ya AI khud confused hai (confidence 70% se kam), toh system human approval maangta hai. Risk jitna bada hoga, approval dene wala person utna senior hona chahiye. Jaise ₹20,000 se upar ke transaction ke liye ek officer ki approval chahiye, aur ₹2 lakh se upar ke transaction ke liye do different senior managers ki approval zaroori hai (Four-Eyes Principle). Jo person ya agent transaction request karta hai, woh khud usko approve nahi kar sakta (No Self-Approval). Approver ko complete context dikhaya jaata hai ki AI kya action lena chahta hai, kyun lena chahta hai aur uske paas kya evidence hai. Agar approver reject kar deta hai, toh AI action execute nahi karega. Aur agar approval ke liye koi reply hi nahi aata ya required approvals nahi milti, toh request automatically DENIED hogi, kabhi bhi default mein approve nahi hogi (Fail Closed). Simple words mein: AI ka kaam decision suggest karna hai, lekin risky decisions mein final permission authorised human hi dega.


"""


"""
             🤖 AI AGENT WANTS TO PERFORM ACTION
                          |
                          ▼
                SHOULD HUMAN APPROVE?
                          |
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       IMPACT          UNCERTAINTY        POLICY
     High value       Confidence < 70%   First beneficiary
     Irreversible     Checks disagree   Unusual pattern
     Legal action     Agent unsure      Regulated action
          |               |                |
          └───────────────┼────────────────┘
                          |
                          ▼
                 HUMAN APPROVAL FLOW
                          |
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
    REQUIRED LEVEL    FOUR-EYES       NO SELF-APPROVAL
    More risk =       High risk =     Requester cannot
    Senior approver   2 approvers     approve own request
          |               |                |
          └───────────────┼────────────────┘
                          |
                          ▼
                    SHOW CONTEXT
             Action + Reason + Risk + Evidence
                          |
                          ▼
                  WAIT FOR APPROVAL
                          |
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       APPROVED         REJECTED         NO REPLY /
       All required     Any rejection    INSUFFICIENT
       approvals        = STOP           APPROVALS
          |               |                |
          ▼               ▼                ▼
       EXECUTE           DENIED           DENIED
                          |
                  FAIL CLOSED
             Never auto-approve on timeout


       💰 APPROVAL POLICY (EXAMPLE CODE)
       --------------------------------
       Amount ≤ ₹20,000  → AUTO-APPROVE*
       ₹20K – ₹2 Lakh    → 1 Officer (Level 1)
       Amount > ₹2 Lakh  → 2 Senior Managers (Level 2)

       *Only if confidence ≥ 70%; otherwise human approval.



Quick Memory Trick:

WHEN → WHO → HOW MANY → CONTEXT → DECISION
- WHEN: Impact, Uncertainty, Policy
- WHO: Required Level
- HOW MANY: Four-Eyes
- SECURITY: No Self-Approval
- CONTEXT: Show Evidence
- DECISION: Fail Closed (No approval = Denied)
"""