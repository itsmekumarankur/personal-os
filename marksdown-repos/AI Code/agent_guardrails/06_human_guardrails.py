"""
06 HUMAN GUARDRAILS (human-in-the-loop)  -  "some decisions must not be made by an agent alone"

When to bring a human in:
  - IMPACT      value above a threshold, irreversible, legal or customer-visible actions
  - UNCERTAINTY the agent's own confidence is low, or its checks disagree
  - POLICY      first-time beneficiary, unusual pattern, regulated action
How to do it safely:
  - REQUIRED LEVEL   bigger risk -> more senior approver
  - FOUR-EYES        high risk needs TWO distinct approvers
  - NO SELF-APPROVAL the person (or agent owner) who asked cannot approve
  - FAIL CLOSED      no answer before the timeout = DENIED, never "auto-approve because nobody replied"
  - SHOW CONTEXT     the approver sees action, reason, risk and the agent's evidence

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
