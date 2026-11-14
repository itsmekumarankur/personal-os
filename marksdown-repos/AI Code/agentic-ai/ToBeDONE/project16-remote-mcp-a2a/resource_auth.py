"""What a SERVICE (MCP server, A2A agent) does with the token it receives. Shared by both.

The service never calls the auth server for each request. It checks the signature locally with the public keys (JWKS),
and re-reads the keys only when it sees an unknown key id (that is how key rotation works).
The most important line is `audience=`: a token minted for ANOTHER service must be refused here, even though the
signature is perfect. Accepting 'any valid token' is the classic confused-deputy / token-passthrough mistake.
"""
import time

import httpx
from mcp.server.auth.provider import AccessToken

from tokens import TokenError, scopes_of, verify_jwt


class ClaimsAccessToken(AccessToken):
    cid: str | None = None          # customer the caller acts for
    actor: str | None = None        # agent acting on their behalf, if any
    jti: str = ""


class JwksCache:
    def __init__(self, url: str | None = None, static: dict | None = None, ttl: float = 300.0, client: httpx.Client | None = None, clock=time.monotonic):
        self.url, self.static, self.ttl, self.clock = url, static, ttl, clock
        self.client = client or httpx.Client(timeout=5)
        self._jwks, self._at = static, 0.0

    def get(self, force: bool = False) -> dict:
        if self.static is not None:
            return self.static
        if force or self._jwks is None or self.clock() - self._at > self.ttl:
            r = self.client.get(self.url)
            r.raise_for_status()
            self._jwks, self._at = r.json(), self.clock()
        return self._jwks

    def refresh_if_unknown(self, kid: str | None) -> dict:
        jwks = self.get()
        if self.static is None and kid and not any(k.get("kid") == kid for k in jwks.get("keys", [])):
            jwks = self.get(force=True)            # rotation: the auth server may have a new key now
        return jwks


class JwtVerifier:
    """Implements the MCP SDK's TokenVerifier protocol, and a plain check() for the A2A agent."""

    def __init__(self, jwks: JwksCache, issuer: str, audience: str):
        self.jwks, self.issuer, self.audience = jwks, issuer, audience

    def check(self, token: str) -> dict:
        import jwt as pyjwt
        try:
            kid = pyjwt.get_unverified_header(token).get("kid")
        except pyjwt.PyJWTError:
            raise TokenError("malformed", "not a JWT")
        try:
            keys = self.jwks.refresh_if_unknown(kid)
        except httpx.HTTPError:
            raise TokenError("jwks_unavailable", "cannot reach the auth server for keys")   # fail closed
        return verify_jwt(token, keys, issuer=self.issuer, audience=self.audience)

    async def verify_token(self, token: str) -> ClaimsAccessToken | None:
        try:
            c = self.check(token)
        except TokenError:
            return None
        return ClaimsAccessToken(token=token, client_id=c["sub"], scopes=scopes_of(c), expires_at=c["exp"], resource=c["aud"],
                                 cid=c.get("cid"), actor=(c.get("act") or {}).get("sub"), jti=c.get("jti", ""))
