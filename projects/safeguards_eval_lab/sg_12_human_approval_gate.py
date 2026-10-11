"""SG-12  Risk tiers + human approval for dangerous tools.  No LLM needed.
Run: python sg_12_human_approval_gate.py   (LG-15 shows the same idea with LangGraph's interrupt())"""
from dataclasses import dataclass

# Tier by blast radius: what is the worst thing this tool can do if the model is tricked or wrong?
TOOL_TIERS = {
    "search_docs":     "LOW",      # read-only, no side effects          -> run automatically
    "send_email":      "MEDIUM",   # reversible-ish, external side effect -> run, but log + rate limit
    "transfer_funds":  "HIGH",     # irreversible, money moves            -> human must approve
    "delete_account":  "HIGH",
}


@dataclass
class Decision:
    allowed: bool
    reason: str


def approver_cli(tool: str, args: dict) -> bool:
    """Replace with Slack button / ticket / UI prompt. Here a scripted 'human' keeps the demo runnable."""
    scripted = {"transfer_funds": args.get("amount", 0) <= 50_000}      # human would reject big transfers
    return scripted.get(tool, False)


def execute_tool(tool: str, args: dict, approver=approver_cli) -> Decision:
    tier = TOOL_TIERS.get(tool)
    if tier is None:
        return Decision(False, "unknown tool: deny by default")
    if tier == "HIGH":
        if not approver(tool, args):
            return Decision(False, "human approver rejected")
        return Decision(True, "approved by human, executed")
    return Decision(True, f"{tier} tier: executed automatically")


for tool, args in [
    ("search_docs", {"q": "leave policy"}),
    ("send_email", {"to": "x@y.com"}),
    ("transfer_funds", {"amount": 20_000}),
    ("transfer_funds", {"amount": 900_000}),
    ("rm_rf", {}),
]:
    d = execute_tool(tool, args)
    print(f"{tool:15} {str(args):22} -> {'ALLOW' if d.allowed else 'DENY '} | {d.reason}")

print("\nTwo design rules: (1) the approval screen shows the REAL arguments the tool will run with, not the model's")
print("description of them; (2) approval is requested by code that wraps the tool, so the model cannot skip it.")
