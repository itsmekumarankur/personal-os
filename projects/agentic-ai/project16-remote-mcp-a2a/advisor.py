"""The loan-advisor 'brain'. Deliberately plain code (no model), so the PROTOCOL is the thing you study.

It does three things an A2A agent often does:
  * decides if the request is something it handles at all          -> REJECTED
  * asks for missing details instead of guessing                   -> INPUT_REQUIRED
  * does the work by calling a tool on another service (MCP)       -> COMPLETED with an artifact, or FAILED
"""
import re
from dataclasses import dataclass, field

_NUM = r"(\d[\d,]*(?:\.\d+)?)"
LOAN_WORDS = ("loan", "emi", "instalment", "installment", "borrow", "mortgage")


@dataclass
class StepResult:
    state: str
    text: str
    artifacts: list = field(default_factory=list)


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def parse_loan(text: str, known: dict) -> dict:
    """Picks the amount, rate and tenure out of free text. Adds to what we already know."""
    t = text.lower()
    out = dict(known)
    m = re.search(_NUM + r"\s*(lakh|lac|crore|k)\b", t)
    if m:
        out["principal"] = _num(m.group(1)) * {"lakh": 1e5, "lac": 1e5, "crore": 1e7, "k": 1e3}[m.group(2)]
    else:
        for n in re.findall(_NUM, t):
            v = _num(n)
            if v >= 1000 and not re.search(re.escape(n) + r"\s*(%|percent|months?|years?|yrs?)", t):
                out["principal"] = v
                break
    m = re.search(_NUM + r"\s*(%|percent)", t)
    if m:
        out["rate"] = _num(m.group(1))
    m = re.search(_NUM + r"\s*(years?|yrs?|months?)", t)
    if m:
        n = _num(m.group(1))
        out["months"] = int(n * 12) if m.group(2).startswith(("y",)) else int(n)
    return out


QUESTIONS = {"principal": "the loan amount", "rate": "the yearly interest rate in percent", "months": "the tenure (for example 5 years or 60 months)"}


class Advisor:
    def __init__(self, emi_fn, before_work=None):
        """emi_fn(principal, rate, months, subject_token, traceparent) -> {'emi':..,'total_payable':..,'total_interest':..}"""
        self.emi_fn, self.before_work = emi_fn, before_work

    def step(self, memory: dict, text: str, subject_token: str, traceparent: str | None) -> StepResult:
        if self.before_work:
            self.before_work()
        memory["loan"] = parse_loan(text, memory.get("loan", {}))
        loan = memory["loan"]
        if not loan and not any(w in text.lower() for w in LOAN_WORDS):
            return StepResult("TASK_STATE_REJECTED", "I only help with loan instalments (EMI). I cannot see accounts or move money.")
        missing = [k for k in ("principal", "rate", "months") if k not in loan]
        if missing:
            return StepResult("TASK_STATE_INPUT_REQUIRED", "To work out the EMI I still need " + ", ".join(QUESTIONS[k] for k in missing) + ".")
        try:
            r = self.emi_fn(loan["principal"], loan["rate"], loan["months"], subject_token, traceparent)
        except Exception:                                                   # never show internals to another agent
            return StepResult("TASK_STATE_FAILED", "I could not complete the calculation right now.")
        summary = (f"EMI {r['emi']:.2f} per month for {loan['months']} months on {loan['principal']:.0f} at {loan['rate']}%. "
                   f"Total interest {r['total_interest']:.2f}, total payable {r['total_payable']:.2f}.")
        return StepResult("TASK_STATE_COMPLETED", summary, [{"artifactId": "emi-result", "name": "EMI result",
                                                             "parts": [{"text": summary}, {"data": {**r, **loan}}]}])
