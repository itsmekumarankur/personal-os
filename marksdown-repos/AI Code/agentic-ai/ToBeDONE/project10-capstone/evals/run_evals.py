"""Behaviour checks against the REAL model, end to end through the HTTP API.

Unit tests prove the code around the model is right. They cannot tell you whether the model, with
this prompt and these tools, behaves well. These cases do. Run them before a release and whenever
you change the prompt, the tools or the model:

    export ANTHROPIC_API_KEY=your_anthropic_key
    python evals/run_evals.py                      # all cases
    python evals/run_evals.py --cases my.jsonl

Costs a few cents. Models are not perfectly repeatable: if a case fails, run it again, then decide
whether the prompt, the tool descriptions or the case needs to change. Exit code 1 if anything fails.
Each case uses a fresh in-memory database and sample bank, so cases cannot affect each other.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from config import Settings, parse_api_keys  # noqa: E402
from main import create_app  # noqa: E402

KEYS = {
    "eval-customer-1-key-0001": {"id": "cust-1", "role": "customer", "account_id": "A-1001"},
    "eval-customer-2-key-0002": {"id": "cust-2", "role": "customer", "account_id": "A-1002"},
    "eval-approver-key-000003": {"id": "approver-1", "role": "approver"},
    "eval-ops-key-0000000004": {"id": "ops-1", "role": "ops"},
}
KEY_FOR = {"cust-1": "eval-customer-1-key-0001", "cust-2": "eval-customer-2-key-0002"}
APPROVER = "eval-approver-key-000003"


def load_cases(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def run_case(case: dict) -> list[str]:
    """Returns a list of failure descriptions (empty = pass)."""
    settings = Settings(api_keys=parse_api_keys(json.dumps(KEYS)), db_path=":memory:",
                        rate_limit_per_min=1000, daily_token_budget=10_000_000)
    app = create_app(settings, configure_logging=False)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {KEY_FOR[case['as']]}"}

    conv_id, last = None, {}
    for message in case["messages"]:
        body = {"message": message, **({"conversation_id": conv_id} if conv_id else {})}
        r = client.post("/v1/chat", json=body, headers=headers)
        if r.status_code != 200:
            return [f"HTTP {r.status_code}: {r.text[:200]}"]
        last = r.json()
        conv_id = last.get("conversation_id") or conv_id

    expect, failures = case["expect"], []
    reply = last.get("reply", "")
    bank = app.state.deps.bank
    pending = client.get("/v1/approvals", headers={"Authorization": f"Bearer {APPROVER}"}).json()

    if "status" in expect and last.get("status") != expect["status"]:
        failures.append(f"status is {last.get('status')!r}, expected {expect['status']!r}")
    if "approval_tool" in expect and not any(a["tool"] == expect["approval_tool"] for a in pending):
        failures.append(f"no pending approval for {expect['approval_tool']!r}")
    if "approvals" in expect and len(pending) != expect["approvals"]:
        failures.append(f"{len(pending)} approvals, expected {expect['approvals']}")
    if "refunds" in expect and len(bank.refunds()) != expect["refunds"]:
        failures.append(f"{len(bank.refunds())} refunds executed, expected {expect['refunds']}")
    for card, status in expect.get("card_status", {}).items():
        if bank.card(card)["status"] != status:
            failures.append(f"card {card} is {bank.card(card)['status']!r}, expected {status!r}")
    for pattern in expect.get("reply_regex", []):
        if not re.search(pattern, reply, re.IGNORECASE):
            failures.append(f"reply does not match /{pattern}/: {reply[:160]!r}")
    for pattern in expect.get("reply_not_regex", []):
        if re.search(pattern, reply, re.IGNORECASE):
            failures.append(f"reply matches forbidden /{pattern}/: {reply[:160]!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default=str(Path(__file__).with_name("cases.jsonl")))
    args = parser.parse_args()

    failed = 0
    for case in load_cases(args.cases):
        problems = run_case(case)
        print(f"{'PASS' if not problems else 'FAIL'}  {case['name']}")
        for p in problems:
            print(f"      - {p}")
        failed += bool(problems)
    print(f"\n{failed} failed" if failed else "\nall passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
