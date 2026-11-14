import json

import pytest
from conftest import provider

import a2a_types as T
from a2a_client import task_text
from orchestrator import make_orchestrator_client
from stack import ORCH, start_stack
from tool_pinning import ToolPins


def test_full_story_with_one_trace_id_everywhere(stack):
    c = make_orchestrator_client(stack.settings, ORCH)
    before_m, before_a = len(stack.mcp_audit.all()), len(stack.a2a_audit.all())
    t = c.run("loan of 5 lakh at 9%", answer_fn=lambda q: "5 years")
    assert t["status"]["state"] == T.COMPLETED
    trace = c.traceparent.split("-")[1]
    m_rows = [r for r in stack.mcp_audit.all()[before_m:] if r["tool"] == "calculate_emi"]
    a_rows = [r for r in stack.a2a_audit.all()[before_a:] if r["event"] == "task_step"]
    assert m_rows and {r["trace"] for r in m_rows} == {trace}
    assert {r["trace"] for r in a_rows} == {trace} and len(a_rows) == 2
    assert m_rows[0]["client"] == "orchestrator" and m_rows[0]["actor"] == "loan-advisor" and m_rows[0]["cid"] == "cust-1001"


def test_the_agent_token_cannot_be_used_directly_on_other_tools(stack):
    """The advisor holds an exchanged token with ONLY tools:basic. Even if it was stolen, accounts are out of reach."""
    import asyncio

    from mcp_client import RemoteMCP, ToolFailed
    s = stack.settings
    a = provider(stack).get(s.a2a_url, ["a2a:invoke", "tools:basic", "accounts:read"])
    b = provider(stack, "loan-advisor").exchange(a, s.mcp_url, ["tools:basic"])
    with pytest.raises(ToolFailed, match="insufficient_scope"):
        asyncio.run(RemoteMCP(s.mcp_url, lambda: b).call_tool("get_account_summary", {"account_id": "acc-1"}))


def test_default_exchange_gives_only_what_the_caller_delegated(stack):
    import httpx
    s = stack.settings
    a = provider(stack).get(s.a2a_url, ["a2a:invoke", "tools:basic"])
    r = httpx.post(s.issuer + "/token", data={"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "subject_token": a, "resource": s.mcp_url},
                   auth=("loan-advisor", stack.secrets["loan-advisor"])).json()
    assert r["scope"] == "tools:basic"


def test_rug_pulled_mcp_server_makes_the_agent_fail_closed():
    pins = ToolPins()
    pins.approve([{"name": "calculate_emi", "description": "what I reviewed last month", "inputSchema": {}}])
    k = start_stack(pins=pins)
    try:
        t = make_orchestrator_client(k.settings, ORCH).send("loan of 1000 at 5% for 1 year")
        assert t["status"]["state"] == T.FAILED and "pinned" not in task_text(t)
        assert not [r for r in k.mcp_audit.all() if r["tool"] == "calculate_emi"]          # the call was never made
    finally:
        k.stop()


def test_two_tasks_do_not_mix_memory(stack):
    c = make_orchestrator_client(stack.settings, ORCH)
    a = c.send("loan of 100000 at 10%")
    b = c.send("loan of 900000 at 7%")
    a2 = c.send("1 year", task_id=a["id"], context_id=a["contextId"])
    b2 = c.send("10 years", task_id=b["id"], context_id=b["contextId"])
    da, db = a2["artifacts"][0]["parts"][1]["data"], b2["artifacts"][0]["parts"][1]["data"]
    assert (da["principal"], da["months"]) == (100000, 12) and (db["principal"], db["months"]) == (900000, 120)
    assert json.dumps(da) != json.dumps(db)
