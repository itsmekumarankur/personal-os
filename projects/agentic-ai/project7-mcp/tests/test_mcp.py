"""Tests run without an API key. The model is replaced by a scripted fake.
Two layers are tested for real: the MCP protocol (in memory, and over a real stdio child process)."""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bank  # noqa: E402
import main as main_mod  # noqa: E402
import mcp_agent  # noqa: E402
from server import mcp as server_mcp  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def in_memory_session():
    return create_connected_server_and_client_session(server_mcp._mcp_server)


# ---------- fake model ----------

def tool_use(name, args, id_="tu_1"):
    return SimpleNamespace(stop_reason="tool_use", content=[
        SimpleNamespace(type="text", text="Let me check."),
        SimpleNamespace(type="tool_use", id=id_, name=name, input=args),
    ])


def final(text):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)])


def scripted(*responses, seen=None):
    queue = list(responses)

    async def model_call(system, messages, tools):
        if seen is not None:
            seen.append({"messages": json.loads(json.dumps(messages)), "tools": [t["name"] for t in tools]})
        return queue.pop(0)

    return model_call


# ---------- bank logic (no MCP, no AI) ----------

def test_emi_matches_the_formula():
    r = bank.emi(100000, 12, 12)
    assert r["monthly_emi"] == pytest.approx(8884.88, abs=0.01)
    assert r["total_interest"] == pytest.approx(r["total_payable"] - 100000, abs=0.01)


def test_emi_with_zero_rate_is_plain_division():
    assert bank.emi(120000, 0, 12)["monthly_emi"] == 10000.0


@pytest.mark.parametrize("args", [(0, 10, 12), (1000, -1, 12), (1000, 101, 12), (1000, 10, 0), (1000, 10, 481)])
def test_emi_rejects_bad_input(args):
    with pytest.raises(ValueError):
        bank.emi(*args)


def test_account_and_transaction_lookups():
    assert bank.account_summary("A-1001")["balance"] == 125000.50
    assert len(bank.transactions("A-1001", 3)) == 3
    with pytest.raises(ValueError):
        bank.account_summary("nope")
    with pytest.raises(ValueError):
        bank.transactions("A-1001", 0)


# ---------- the MCP protocol, in memory ----------

def test_server_lists_its_tools_with_schemas():
    async def go():
        async with in_memory_session() as s:
            return (await s.list_tools()).tools
    tools = {t.name: t for t in run(go())}
    assert set(tools) == {"calculate_emi", "get_account_summary", "list_transactions"}
    assert set(tools["calculate_emi"].inputSchema["required"]) == {"principal", "annual_rate_percent", "months"}
    assert "monthly loan instalment" in tools["calculate_emi"].description      # docstring became the description


def test_call_tool_returns_text_and_errors_are_flagged():
    async def go():
        async with in_memory_session() as s:
            ok = await s.call_tool("calculate_emi", {"principal": 100000, "annual_rate_percent": 12, "months": 12})
            bad = await s.call_tool("get_account_summary", {"account_id": "nope"})
            return ok, bad
    ok, bad = run(go())
    assert ok.isError is False and "8884.88" in ok.content[0].text
    assert bad.isError is True and "unknown account_id" in bad.content[0].text


def test_resource_can_be_read():
    async def go():
        async with in_memory_session() as s:
            return await s.read_resource("policy://fees")
    res = run(go())
    assert "fee policy" in res.contents[0].text


# ---------- the real transport: a child process over stdio ----------

def test_stdio_child_process_works():
    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = [t.name for t in (await s.list_tools()).tools]
                out = await s.call_tool("list_transactions", {"account_id": "A-1002"})
                return names, out
    names, out = run(go())
    assert "calculate_emi" in names
    assert "Customer payment" in out.content[0].text


def test_child_process_does_not_inherit_the_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-key")
    assert "ANTHROPIC_API_KEY" not in get_default_environment()


# ---------- converting tools ----------

def test_mcp_tool_becomes_an_anthropic_tool():
    async def go():
        async with in_memory_session() as s:
            return await mcp_agent.list_tools(s)
    tools = run(go())
    t = next(t for t in tools if t["name"] == "get_account_summary")
    assert set(t) == {"name", "description", "input_schema"}
    assert t["input_schema"]["type"] == "object"


# ---------- the agent loop ----------

def test_agent_calls_a_tool_and_answers():
    seen = []
    model = scripted(
        tool_use("calculate_emi", {"principal": 100000, "annual_rate_percent": 12, "months": 12}),
        final("Your EMI is 8,884.88."),
        seen=seen,
    )

    async def go():
        async with in_memory_session() as s:
            return await mcp_agent.run_agent(s, "EMI?", model_call=model)
    r = run(go())
    assert r["reply"] == "Your EMI is 8,884.88."
    assert r["turns"] == 2 and r["truncated"] is False
    assert r["tool_calls"] == [{"name": "calculate_emi", "is_error": False,
                                "input": {"principal": 100000, "annual_rate_percent": 12, "months": 12}}]
    # the tool result really went back to the model
    result_msg = seen[1]["messages"][-1]["content"][0]
    assert result_msg["type"] == "tool_result" and result_msg["tool_use_id"] == "tu_1"
    assert "8884.88" in result_msg["content"]


def test_tool_error_goes_back_to_the_model_as_an_error():
    seen = []
    model = scripted(tool_use("get_account_summary", {"account_id": "zzz"}), final("No such account."), seen=seen)

    async def go():
        async with in_memory_session() as s:
            return await mcp_agent.run_agent(s, "x", model_call=model)
    r = run(go())
    assert r["tool_calls"][0]["is_error"] is True
    assert seen[1]["messages"][-1]["content"][0]["is_error"] is True


def test_allowlist_hides_tools_and_blocks_calls():
    seen = []
    model = scripted(tool_use("get_account_summary", {"account_id": "A-1001"}), final("Cannot."), seen=seen)

    async def go():
        async with in_memory_session() as s:
            return await mcp_agent.run_agent(s, "x", model_call=model, allowed={"calculate_emi"})
    r = run(go())
    assert seen[0]["tools"] == ["calculate_emi"]                       # the model was never offered the others
    assert r["tool_calls"][0]["is_error"] is True                      # and a made-up call is refused
    assert "not available" in seen[1]["messages"][-1]["content"][0]["content"]


def test_allowed_names_reads_the_environment(monkeypatch):
    monkeypatch.delenv("ALLOWED_TOOLS", raising=False)
    assert mcp_agent.allowed_names() is None
    monkeypatch.setenv("ALLOWED_TOOLS", "a, b ,")
    assert mcp_agent.allowed_names() == {"a", "b"}


def test_loop_stops_after_max_turns():
    endless = [tool_use("calculate_emi", {"principal": 1000, "annual_rate_percent": 5, "months": 6}, f"t{i}")
               for i in range(10)]

    async def go():
        async with in_memory_session() as s:
            return await mcp_agent.run_agent(s, "x", model_call=scripted(*endless), max_turns=3)
    r = run(go())
    assert r["truncated"] is True and r["turns"] == 3 and len(r["tool_calls"]) == 3


def test_long_tool_results_are_cut():
    big = SimpleNamespace(content=[SimpleNamespace(type="text", text="x" * 10000)], isError=False)
    assert len(mcp_agent._result_text(big)) < mcp_agent.MAX_RESULT_CHARS + 20


# ---------- the FastAPI service (starts the real MCP child process) ----------

def test_api_tools_and_chat(monkeypatch):
    monkeypatch.setattr(main_mod, "model_call", scripted(
        tool_use("list_transactions", {"account_id": "A-1001", "limit": 2}),
        final("Latest: salary credit, electricity bill."),
    ))
    with TestClient(main_mod.app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        names = {t["name"] for t in client.get("/tools").json()}
        assert names == {"calculate_emi", "get_account_summary", "list_transactions"}
        r = client.post("/chat", json={"message": "last 2 transactions of A-1001"})
        assert r.status_code == 200
        body = r.json()
        assert body["reply"].startswith("Latest") and body["tool_calls"][0]["name"] == "list_transactions"


def test_api_allowlist_applies_to_tools_endpoint(monkeypatch):
    monkeypatch.setenv("ALLOWED_TOOLS", "calculate_emi")
    with TestClient(main_mod.app) as client:
        assert [t["name"] for t in client.get("/tools").json()] == ["calculate_emi"]


def test_api_validates_input():
    with TestClient(main_mod.app) as client:
        assert client.post("/chat", json={"message": ""}).status_code == 422
        assert client.post("/chat", json={"message": "x" * 4001}).status_code == 422
