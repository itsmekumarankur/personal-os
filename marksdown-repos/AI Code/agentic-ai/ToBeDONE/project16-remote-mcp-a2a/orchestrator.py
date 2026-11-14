"""Wiring: the three roles and how tokens move between them.

   user -> ORCHESTRATOR --(token A: aud=A2A agent, scopes a2a:invoke + tools:basic)--> LOAN ADVISOR (A2A)
                                                     LOAN ADVISOR --(token exchange)--> token B: aud=MCP, scopes tools:basic, act=loan-advisor
                                                     LOAN ADVISOR --(token B)--> MCP server -> calculate_emi
Token A is useless at the MCP server (wrong audience). Token B is useless at the A2A agent. Nothing is passed through.
"""
import httpx

from a2a_client import A2AClient
from config import S_A2A, S_BASIC, Settings
from mcp_client import RemoteMCP
from oauth_client import TokenProvider
from tool_pinning import ToolPins


def make_emi_fn(settings: Settings, advisor_secret: str, pins: ToolPins | None = None, http: httpx.Client | None = None):
    """The loan advisor's way of reaching the MCP server: swap the caller's token for a small MCP token, then call the tool."""
    provider = TokenProvider(settings.issuer + "/token", "loan-advisor", advisor_secret, http=http)

    def emi_fn(principal, rate, months, subject_token, traceparent):
        mcp = RemoteMCP(settings.mcp_url, lambda: provider.exchange(subject_token, settings.mcp_url, [S_BASIC]), pins=pins, traceparent=traceparent)
        import json
        return json.loads(mcp.call_tool_sync("calculate_emi", {"principal": principal, "annual_rate_pct": rate, "months": months}))
    return emi_fn


def make_orchestrator_client(settings: Settings, orch_secret: str, scopes: list | None = None, allow_local: bool = True,
                             traceparent: str | None = None) -> A2AClient:
    """An A2A client whose tokens come from the orchestrator's OAuth client. The token's audience is the card's endpoint."""
    provider = TokenProvider(settings.issuer + "/token", "orchestrator", orch_secret)
    holder: dict = {}
    client = A2AClient(settings.a2a_base, lambda: provider.get(holder["client"].audience(), scopes or [S_A2A, S_BASIC]),
                       allow_local=allow_local, traceparent=traceparent)
    holder["client"] = client
    return client
