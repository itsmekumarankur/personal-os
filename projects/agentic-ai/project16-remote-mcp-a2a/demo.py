"""Runs the whole story on your laptop with no Docker:  python demo.py
Three real HTTP servers start on free ports. Read the output top to bottom; each step says what the protocol is doing."""
import asyncio
import logging

import httpx

from a2a_client import A2AClient, A2AError, task_text
from mcp_client import RemoteMCP
from oauth_client import TokenProvider
from orchestrator import make_orchestrator_client
from stack import ORCH, start_stack


def step(n, title):
    print(f"\n=== {n}. {title}")


def main():
    logging.disable(logging.INFO)
    k = start_stack()
    s = k.settings
    try:
        step(1, "Discovery: what does the MCP server say when I have no token?")
        r = httpx.post(s.mcp_url, json={}, headers={"Accept": "application/json, text/event-stream"})
        print("   status", r.status_code, "| WWW-Authenticate:", r.headers.get("www-authenticate"))
        meta = httpx.get(s.mcp_url.rsplit("/", 1)[0] + "/.well-known/oauth-protected-resource").json()
        print("   protected-resource metadata ->", meta["authorization_servers"])

        step(2, "OAuth client_credentials: orchestrator asks for a token for the MCP server only")
        prov = TokenProvider(s.issuer + "/token", "orchestrator", ORCH)
        tok = prov.get(s.mcp_url, ["accounts:read"])
        print("   got a JWT, audience =", s.mcp_url)
        mcp = RemoteMCP(s.mcp_url, lambda: tok)
        print("   my account:", asyncio.run(mcp.call_tool("get_account_summary", {"account_id": "acc-1"})))
        try:
            asyncio.run(mcp.call_tool("get_account_summary", {"account_id": "acc-9"}))
        except Exception as e:
            print("   someone else's account ->", e)
        try:
            asyncio.run(mcp.call_tool("freeze_card", {"card_id": "card-1"}))
        except Exception as e:
            print("   write tool without scope ->", e)

        step(3, "Token passthrough attack: use the MCP token against the A2A agent")
        bad = A2AClient(s.a2a_base, lambda: tok, allow_local=True)
        try:
            bad.send("loan 1000 at 5% for 1 year")
        except A2AError as e:
            print("   refused:", e)

        step(4, "A2A: orchestrator -> loan advisor (INPUT_REQUIRED, then the answer, same task id)")
        c = make_orchestrator_client(s, ORCH)
        print("   agent card skills:", [x["id"] for x in c.discover()["skills"]])
        t = c.send("I want a loan of 5 lakh at 9%")
        print("   state:", t["status"]["state"], "|", task_text(t))
        t2 = c.send("for 5 years", task_id=t["id"], context_id=t["contextId"])
        print("   state:", t2["status"]["state"], "|", task_text(t2))
        print("   same task id:", t["id"] == t2["id"])

        step(5, "What the MCP server saw: the advisor acted ON BEHALF of the orchestrator")
        for row in k.mcp_audit.all():
            print("   ", {x: row[x] for x in ("client", "actor", "cid", "tool", "outcome", "trace") if x in row})
        trace = c.traceparent.split("-")[1]
        print("   one trace id across orchestrator, A2A and MCP:", trace in {r.get("trace") for r in k.mcp_audit.all()}, trace)

        step(6, "A caller without the scope cannot even get an A2A token")
        other = TokenProvider(s.issuer + "/token", "readonly-dashboard", k.secrets["readonly-dashboard"])
        print("   (the dashboard has no a2a:invoke scope):", end=" ")
        try:
            other.get(s.a2a_url, ["a2a:invoke"])
        except Exception as e:
            print(e)
    finally:
        k.stop()


if __name__ == "__main__":
    main()
