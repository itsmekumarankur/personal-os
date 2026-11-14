"""Settings shared by the three services, and the list of known OAuth clients.

Three services run side by side:
    auth server   :8001   hands out tokens                 (who are you, what may you do, for which service?)
    MCP server    :8002   remote tools over HTTP           (the 'resource' that needs a token)
    A2A agent     :8003   a loan-advisor agent over HTTP   (another resource that needs a token)
"""
import hashlib
import os
from dataclasses import dataclass, field


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


@dataclass
class ClientRecord:
    secret_sha256: str                      # we store a hash of a long random secret, never the secret itself
    scopes: list                            # the most this client may ever ask for
    customer_id: str | None = None          # the customer this client acts for (goes into the token as 'cid')
    exchange_scopes: list = field(default_factory=list)   # what it may ask for when swapping a token for another service


@dataclass
class Settings:
    issuer: str = "http://127.0.0.1:8001"
    mcp_url: str = "http://127.0.0.1:8002/mcp"
    a2a_base: str = "http://127.0.0.1:8003"
    token_ttl: int = 300
    clients: dict = field(default_factory=dict)
    allowed_hosts: list = field(default_factory=lambda: ["127.0.0.1:*", "localhost:*"])
    rate_limit_per_min: int = 60
    audit_path: str | None = None

    @property
    def a2a_url(self) -> str:               # the JSON-RPC endpoint; also the 'audience' of tokens meant for the agent
        return self.a2a_base + "/a2a"

    @property
    def resources(self) -> set:
        return {self.mcp_url, self.a2a_url}


# scopes: small and specific, so a token can be small and specific too
S_BASIC, S_READ, S_CARDS, S_A2A = "tools:basic", "accounts:read", "cards:write", "a2a:invoke"
ALL_SCOPES = [S_BASIC, S_READ, S_CARDS, S_A2A]


def default_clients(orch_secret: str, advisor_secret: str, readonly_secret: str) -> dict:
    return {
        # the app that talks to the user. It acts for customer cust-1001.
        "orchestrator": ClientRecord(sha256_hex(orch_secret), [S_A2A, S_READ, S_BASIC], customer_id="cust-1001"),
        # the loan-advisor agent. It may swap an orchestrator token for a short MCP token, but only for these scopes.
        "loan-advisor": ClientRecord(sha256_hex(advisor_secret), [S_BASIC], customer_id=None, exchange_scopes=[S_BASIC, S_READ]),
        # a dashboard that can only read
        "readonly-dashboard": ClientRecord(sha256_hex(readonly_secret), [S_READ], customer_id="cust-1001"),
    }


def load_settings() -> Settings:
    """Reads secrets from the environment. Refuses to start with missing or weak secrets."""
    secrets = {k: os.environ.get(k, "") for k in ("ORCH_SECRET", "ADVISOR_SECRET", "READONLY_SECRET")}
    for k, v in secrets.items():
        if len(v) < 24:
            raise RuntimeError(f"{k} must be set to a random string of at least 24 characters")
    return Settings(
        issuer=os.environ.get("ISSUER", "http://127.0.0.1:8001"),
        mcp_url=os.environ.get("MCP_URL", "http://127.0.0.1:8002/mcp"),
        a2a_base=os.environ.get("A2A_BASE", "http://127.0.0.1:8003"),
        clients=default_clients(secrets["ORCH_SECRET"], secrets["ADVISOR_SECRET"], secrets["READONLY_SECRET"]),
        allowed_hosts=os.environ.get("ALLOWED_HOSTS", "127.0.0.1:*,localhost:*").split(","),
        audit_path=os.environ.get("AUDIT_PATH") or None,
    )
