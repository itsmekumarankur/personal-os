"""
08 AUDIT GUARDRAILS  -  "prove what the agent did, who allowed it, and that the log was not changed"

Regulators and incident reviews ask: what did the agent see, decide, and do, and under whose authority?
A good agent audit trail is:
  - COMPLETE      every prompt, tool call, guardrail verdict, approval and output gets an entry
  - STRUCTURED    who / what / why / decision / which policy version (searchable, not free text)
  - REDACTED      PII and secrets are masked BEFORE writing (the log must not become a leak)
  - TAMPER-EVIDENT each entry contains the hash of the previous one (a hash chain, like a mini blockchain).
                  Edit or delete one entry and every later hash breaks.
  - APPEND-ONLY   in production also write to WORM storage / separate account so admins cannot rewrite history
  - REPLAYABLE    enough context (inputs + tool results + versions) to reproduce the decision

Run: python 08_audit_guardrails.py
"""
import hashlib
import json
import re
import time


def redact(text):
    text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN]", text)
    text = re.sub(r"\b(?:\d[ -]?){15}\d\b", "[CARD]", text)
    return re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]", text)


def digest(entry):
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class AuditLog:
    def __init__(self):
        self.entries = []

    def record(self, actor, event, detail, decision="-", policy="v1.4"):
        entry = {"seq": len(self.entries), "ts": round(time.time(), 3), "actor": actor, "event": event,
                 "detail": redact(detail), "decision": decision, "policy": policy,
                 "prev": self.entries[-1]["hash"] if self.entries else "GENESIS"}
        entry["hash"] = digest(entry)
        self.entries.append(entry)


def verify(entries):
    prev = "GENESIS"
    for i, e in enumerate(entries):
        if e["prev"] != prev:
            return False, f"chain broken at position {i}: previous-hash does not match (entry removed or reordered?)"
        if digest(e) != e["hash"]:
            return False, f"entry seq={e['seq']} was modified (hash mismatch)"
        prev = e["hash"]
    return True, "all entries intact"


if __name__ == "__main__":
    log = AuditLog()
    log.record("user:asha", "input", "Send my statement to asha@mail.com, PAN ABCDE1234F", "ALLOWED(pii redacted)")
    log.record("agent:wealth-1", "tool_call", "get_statement(account=ACC123456)", "ALLOWED")
    log.record("agent:wealth-1", "action", "place_order BUY 50 TCS value=200000", "NEEDS_APPROVAL")
    log.record("human:priya", "approval", "approved order R2 note='verified with customer'", "APPROVED")
    log.record("agent:wealth-1", "output", "Order placed. Card 4111 1111 1111 1111 on file.", "ALLOWED(card redacted)")

    print("AUDIT TRAIL (note PAN / email / card are already masked)")
    for e in log.entries:
        print(f"  #{e['seq']} {e['actor']:<14} {e['event']:<10} {e['decision']:<22} prev={e['prev'][:8]} hash={e['hash'][:8]}  {e['detail']}")

    print("\n1) verify untouched log:    ", verify(log.entries))

    forged = [dict(e) for e in log.entries]
    forged[2]["decision"] = "AUTO_APPROVED"                  # attacker hides that approval was needed
    print("2) someone edits entry #2:  ", verify(forged))

    removed = [dict(e) for e in log.entries if e["seq"] != 3]  # attacker deletes the approval record
    print("3) someone deletes entry #3:", verify(removed))

    # smarter attacker edits entry and recomputes ITS hash - but then the NEXT entry's prev no longer matches
    smart = [dict(e) for e in log.entries]
    smart[2]["decision"] = "AUTO_APPROVED"
    smart[2]["hash"] = digest(smart[2])
    print("4) edit + recompute hash:   ", verify(smart))
    print("\nTo defeat even a full rewrite, periodically publish the latest hash somewhere outside the admin's control.")
