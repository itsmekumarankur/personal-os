"""One entry point per service, for Docker:   python serve.py auth | mcp | a2a
Secrets come from environment variables (see config.load_settings). Services fetch public keys from ISSUER/jwks.json."""
import os
import sys

import uvicorn

from a2a_server import A2AService, create_a2a_app
from advisor import Advisor
from auth_server import create_auth_app
from config import load_settings
from mcp_server import create_mcp_app
from orchestrator import make_emi_fn
from resource_auth import JwksCache, JwtVerifier


def build(which: str):
    s = load_settings()
    if which == "auth":
        return create_auth_app(s), 8001
    jwks = JwksCache(url=s.issuer + "/jwks.json")
    if which == "mcp":
        return create_mcp_app(s, JwtVerifier(jwks, s.issuer, s.mcp_url), host="0.0.0.0"), 8002
    if which == "a2a":
        emi = make_emi_fn(s, os.environ["ADVISOR_SECRET"])
        return create_a2a_app(s, JwtVerifier(jwks, s.issuer, s.a2a_url), A2AService(s, Advisor(emi))), 8003
    raise SystemExit("usage: serve.py auth|mcp|a2a")


if __name__ == "__main__":
    app, port = build(sys.argv[1] if len(sys.argv) > 1 else "")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", port)), log_level="info")
