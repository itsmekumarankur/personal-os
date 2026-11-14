"""The remote MCP server: bank tools over HTTP, protected by OAuth tokens.

What the MCP SDK does for us:  /mcp (streamable HTTP), the session handshake, the 401 + WWW-Authenticate reply,
and /.well-known/oauth-protected-resource (RFC 9728) so a client can discover which auth server to ask.
What WE add:  audience check (resource_auth.py), PER-TOOL scopes, ownership checks, rate limit, audit log.

Tool -> scope
    calculate_emi         tools:basic
    get_account_summary   accounts:read
    list_transactions     accounts:read
    freeze_card           cards:write      (a write; nobody in this demo is allowed to get this scope by default)
"""
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

import bank
from audit import AuditLog, RateLimiter
from config import S_BASIC, S_CARDS, S_READ, Settings
from resource_auth import JwtVerifier


class Denied(Exception):
    """Shown to the model as a tool error. Keep the text short and free of secrets."""


def build_mcp(settings: Settings, verifier: JwtVerifier, audit: AuditLog | None = None, limiter: RateLimiter | None = None,
              host: str = "127.0.0.1", port: int = 8002) -> FastMCP:
    audit = audit or AuditLog(settings.audit_path)
    limiter = limiter or RateLimiter(settings.rate_limit_per_min)
    mcp = FastMCP(
        "bank-tools",
        token_verifier=verifier,
        auth=AuthSettings(issuer_url=settings.issuer, resource_server_url=settings.mcp_url, required_scopes=[]),
        host=host, port=port, streamable_http_path="/mcp",
        # blocks DNS-rebinding: a web page in the user's browser must not be able to talk to a server on localhost
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=settings.allowed_hosts,
                                                     allowed_origins=[]),
    )
    mcp.audit, mcp.limiter = audit, limiter

    def guard(ctx: Context, tool: str, scope: str, args: dict):
        """The single door every tool goes through."""
        req = ctx.request_context.request
        tok = req.user.access_token                      # set by the SDK after our verifier accepted the token
        trace = req.headers.get("traceparent", "")
        base = {"client": tok.client_id, "actor": tok.actor, "cid": tok.cid, "tool": tool, "scope": scope,
                "args": sorted(args), "trace": trace.split("-")[1] if trace.count("-") == 3 else None}
        if scope not in tok.scopes:
            audit.record(**base, outcome="denied_scope")
            raise Denied(f"insufficient_scope: this tool needs {scope}")
        if not limiter.allow(tok.client_id):
            audit.record(**base, outcome="rate_limited")
            raise Denied("rate_limited: slow down")
        return tok, base

    def done(base, outcome="ok"):
        audit.record(**base, outcome=outcome)

    def run(ctx, tool, scope, args, fn):
        tok, base = guard(ctx, tool, scope, args)
        try:
            out = fn(tok)
        except bank.NotYours as e:
            done(base, "not_found")
            raise Denied(str(e))
        except ValueError as e:
            done(base, "bad_input")
            raise Denied(str(e))
        done(base)
        return out

    @mcp.tool()
    def calculate_emi(principal: float, annual_rate_pct: float, months: int, ctx: Context) -> dict:
        """Monthly instalment (EMI) for a loan. Needs scope tools:basic."""
        return run(ctx, "calculate_emi", S_BASIC, {"principal": 1, "annual_rate_pct": 1, "months": 1},
                   lambda t: bank.calculate_emi(principal, annual_rate_pct, months))

    @mcp.tool()
    def get_account_summary(account_id: str, ctx: Context) -> dict:
        """Balance and type of one of the caller's accounts. Needs scope accounts:read."""
        return run(ctx, "get_account_summary", S_READ, {"account_id": 1}, lambda t: bank.account_summary(account_id, t.cid or ""))

    @mcp.tool()
    def list_transactions(account_id: str, ctx: Context, limit: int = 10) -> list:
        """Recent transactions of one of the caller's accounts. Needs scope accounts:read."""
        return run(ctx, "list_transactions", S_READ, {"account_id": 1, "limit": 1}, lambda t: bank.list_transactions(account_id, t.cid or "", limit))

    @mcp.tool()
    def freeze_card(card_id: str, ctx: Context) -> dict:
        """Freeze one of the caller's cards. A WRITE action. Needs scope cards:write."""
        return run(ctx, "freeze_card", S_CARDS, {"card_id": 1}, lambda t: bank.freeze_card(card_id, t.cid or ""))

    # The SDK (1.12.4) advertises .../mcp/.well-known/oauth-protected-resource in the 401 header but serves the document at the
    # root. A client that follows the header gets a 404, so we serve the document at the advertised path and at the RFC 9728 path.
    def _metadata(request: Request):
        return JSONResponse({"resource": settings.mcp_url, "authorization_servers": [settings.issuer],
                             "bearer_methods_supported": ["header"], "scopes_supported": [S_BASIC, S_READ, S_CARDS]})

    for path in ("/mcp/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"):
        mcp.custom_route(path, methods=["GET"])(_metadata)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(request: Request):
        return JSONResponse({"status": "ok"})

    return mcp


def create_mcp_app(settings: Settings, verifier: JwtVerifier, audit=None, limiter=None, host: str = "127.0.0.1", port: int = 8002):
    mcp = build_mcp(settings, verifier, audit, limiter, host=host, port=port)
    app = mcp.streamable_http_app()
    app.state.mcp = mcp
    return app
