"""A very small OAuth 2.0 authorization server. It teaches the moving parts; it is NOT a replacement for a real one
(Keycloak, Auth0, Cognito, Entra ID...). Missing on purpose: user login screens, authorization-code + PKCE, refresh tokens,
revocation, client registration, rate limiting on /token, key rotation, persistent storage.

Endpoints
  GET  /.well-known/oauth-authorization-server   metadata (RFC 8414): where is /token, what is supported
  GET  /jwks.json                                public keys, so services can check signatures
  POST /token  grant_type=client_credentials     a program proves who it is and gets a token for ONE resource
  POST /token  grant_type=...token-exchange      a service swaps a token it received for a NEW, narrower token for another
                                                 service (on-behalf-of). This is how you avoid 'token passthrough'.
"""
import base64
import hmac

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from config import Settings, sha256_hex
from tokens import KeyStore, TokenError, make_claims, scopes_of, verify_jwt

EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
ACCESS_TOKEN = "urn:ietf:params:oauth:token-type:access_token"


def _err(code: str, desc: str, status: int = 400, headers: dict | None = None):
    return JSONResponse({"error": code, "error_description": desc}, status_code=status,
                        headers={"Cache-Control": "no-store", **(headers or {})})


def _client_credentials(request: Request, form) -> tuple:
    """client_secret_basic (Authorization: Basic ...) or client_secret_post (form fields)."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("basic "):
        try:
            cid, _, secret = base64.b64decode(auth[6:]).decode().partition(":")
            return cid, secret
        except Exception:
            return None, None
    return form.get("client_id"), form.get("client_secret")


def create_auth_app(settings: Settings, keys: KeyStore | None = None) -> Starlette:
    keys = keys or KeyStore()

    async def metadata(request):
        return JSONResponse({
            "issuer": settings.issuer, "token_endpoint": settings.issuer + "/token", "jwks_uri": settings.issuer + "/jwks.json",
            "grant_types_supported": ["client_credentials", EXCHANGE],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "response_types_supported": [], "scopes_supported": sorted({s for c in settings.clients.values() for s in c.scopes + c.exchange_scopes}),
        })

    async def jwks(request):
        return JSONResponse(keys.jwks())

    async def token(request: Request):
        form = await request.form()
        cid, secret = _client_credentials(request, form)
        rec = settings.clients.get(cid or "")
        # always run the comparison, so timing does not reveal whether the client id exists
        expected = rec.secret_sha256 if rec else "0" * 64
        if not (hmac.compare_digest(sha256_hex(secret or ""), expected) and rec):
            return _err("invalid_client", "client authentication failed", 401, {"WWW-Authenticate": 'Basic realm="token"'})
        grant = form.get("grant_type")
        resource = form.get("resource", "")
        if resource not in settings.resources:
            return _err("invalid_target", "unknown resource")
        requested = [s for s in str(form.get("scope", "")).split(" ") if s]

        if grant == "client_credentials":
            allowed = set(rec.scopes)
            if not requested:
                return _err("invalid_scope", "ask for the scopes you need; there is no default")
            if not set(requested) <= allowed:
                return _err("invalid_scope", f"not allowed: {sorted(set(requested) - allowed)}")
            claims = make_claims(issuer=settings.issuer, subject=cid, audience=resource, scopes=requested, ttl=settings.token_ttl, cid=rec.customer_id)
        elif grant == EXCHANGE:
            subject_token = form.get("subject_token", "")
            try:
                # the incoming token must have been issued FOR the service that is now exchanging it
                sub = verify_jwt(subject_token, keys.jwks(), issuer=settings.issuer, audience=settings.a2a_url)
            except TokenError as e:
                return _err("invalid_grant", f"subject_token rejected: {e.code}")
            if cid != "loan-advisor":
                return _err("unauthorized_client", "this client may not use token exchange")
            allowed = set(scopes_of(sub)) & set(rec.exchange_scopes)       # never more than the caller had, never more than the agent may swap
            if not requested:
                requested = sorted(allowed)
            if not set(requested) <= allowed:
                return _err("invalid_scope", f"not allowed in exchange: {sorted(set(requested) - allowed)}")
            claims = make_claims(issuer=settings.issuer, subject=sub["sub"], audience=resource, scopes=requested,
                                 ttl=min(settings.token_ttl, 120), cid=sub.get("cid"), actor=cid)
        else:
            return _err("unsupported_grant_type", f"unsupported grant {grant!r}")
        return JSONResponse({"access_token": keys.sign(claims), "token_type": "Bearer", "expires_in": claims["exp"] - claims["iat"],
                             "scope": claims["scope"], "issued_token_type": ACCESS_TOKEN},
                            headers={"Cache-Control": "no-store", "Pragma": "no-cache"})

    async def health(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/.well-known/oauth-authorization-server", metadata), Route("/jwks.json", jwks),
                            Route("/token", token, methods=["POST"]), Route("/health", health)])
    app.state.keys = keys
    return app
