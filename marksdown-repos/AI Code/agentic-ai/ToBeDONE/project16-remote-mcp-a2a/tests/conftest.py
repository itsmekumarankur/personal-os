import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_client import RemoteMCP  # noqa: E402
from oauth_client import TokenProvider  # noqa: E402
from stack import start_stack  # noqa: E402


@pytest.fixture(scope="session")
def stack():
    k = start_stack(rate_limit=10_000)
    yield k
    k.stop()


def provider(k, client="orchestrator"):
    return TokenProvider(k.settings.issuer + "/token", client, k.secrets[client])


def token(k, resource, scopes, client="orchestrator"):
    return provider(k, client).get(resource, scopes)


def forge(k, *, audience, scopes, subject="orchestrator", cid="cust-1001", ttl=300, issuer=None, now=None):
    """Mint a validly SIGNED token with any claims (the tests hold the signing key). Shows what the services do with odd tokens."""
    from tokens import make_claims
    return k.keys.sign(make_claims(issuer=issuer or k.settings.issuer, subject=subject, audience=audience, scopes=scopes, ttl=ttl, cid=cid, now=now))


def call(k, tok, name, args, pins=None, url=None):
    return asyncio.run(RemoteMCP(url or k.settings.mcp_url, lambda: tok, pins=pins).call_tool(name, args))
