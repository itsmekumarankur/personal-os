"""Starts auth server + MCP server + A2A agent in threads on free ports. Used by demo.py and by the tests."""
import socket
import threading
import time
from dataclasses import dataclass, field

import httpx
import uvicorn

from a2a_server import A2AService, create_a2a_app
from advisor import Advisor
from audit import AuditLog, RateLimiter
from auth_server import create_auth_app
from config import Settings, default_clients
from mcp_server import create_mcp_app
from orchestrator import make_emi_fn
from resource_auth import JwksCache, JwtVerifier
from tokens import KeyStore

ORCH, ADV, RO = "o" * 8 + "orchestrator-secret", "a" * 8 + "advisor-secret-xxxxx", "r" * 8 + "readonly-secret-xxxxx"


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _serve(app, port):
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    t = threading.Thread(target=srv.run, daemon=True)
    t.start()
    return srv, t


@dataclass
class Stack:
    settings: Settings
    keys: KeyStore
    mcp_audit: AuditLog
    a2a_audit: AuditLog
    service: A2AService
    mcp_app: object
    servers: list = field(default_factory=list)
    secrets: dict = field(default_factory=dict)

    def stop(self):
        for srv, t in self.servers:
            srv.should_exit = True
        for srv, t in self.servers:
            t.join(timeout=5)


def start_stack(advisor: Advisor | None = None, rate_limit: int = 60, blocking_timeout: float = 10.0, pins=None, keys: KeyStore | None = None) -> Stack:
    ap, mp, a2p = free_port(), free_port(), free_port()
    st = Settings(issuer=f"http://127.0.0.1:{ap}", mcp_url=f"http://127.0.0.1:{mp}/mcp", a2a_base=f"http://127.0.0.1:{a2p}",
                  clients=default_clients(ORCH, ADV, RO), rate_limit_per_min=rate_limit)
    keys = keys or KeyStore()
    mcp_audit, a2a_audit = AuditLog(), AuditLog()
    jwks = JwksCache(url=st.issuer + "/jwks.json")
    mcp_app = create_mcp_app(st, JwtVerifier(jwks, st.issuer, st.mcp_url), audit=mcp_audit, limiter=RateLimiter(rate_limit), port=mp)
    adv = advisor or Advisor(make_emi_fn(st, ADV, pins=pins))
    service = A2AService(st, adv, audit=a2a_audit, blocking_timeout=blocking_timeout)
    a2a_app = create_a2a_app(st, JwtVerifier(jwks, st.issuer, st.a2a_url), service)
    servers = [_serve(create_auth_app(st, keys), ap), _serve(mcp_app, mp), _serve(a2a_app, a2p)]
    for url in (st.issuer, st.mcp_url.rsplit("/", 1)[0], st.a2a_base):
        for _ in range(100):
            try:
                if httpx.get(url + "/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.05)
        else:
            raise RuntimeError(f"{url} did not start")
    return Stack(st, keys, mcp_audit, a2a_audit, service, mcp_app, servers, {"orchestrator": ORCH, "loan-advisor": ADV, "readonly-dashboard": RO})
