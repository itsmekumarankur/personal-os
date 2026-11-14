import httpx
import pytest
from conftest import forge, provider, token

from oauth_client import AuthError
from tokens import scopes_of, verify_jwt

EX = "urn:ietf:params:oauth:grant-type:token-exchange"


def post(k, auth=("orchestrator", None), **data):
    cid, sec = auth
    return httpx.post(k.settings.issuer + "/token", data=data, auth=(cid, sec or k.secrets[cid]))


def claims_of(k, t, aud):
    return verify_jwt(t, k.keys.jwks(), issuer=k.settings.issuer, audience=aud)


def test_metadata_and_jwks(stack):
    m = httpx.get(stack.settings.issuer + "/.well-known/oauth-authorization-server").json()
    assert m["token_endpoint"].endswith("/token") and "client_credentials" in m["grant_types_supported"]
    assert httpx.get(m["jwks_uri"]).json()["keys"][0]["kid"] == stack.keys.kid


def test_client_credentials_gives_audience_bound_token(stack):
    t = token(stack, stack.settings.mcp_url, ["accounts:read"])
    c = claims_of(stack, t, stack.settings.mcp_url)
    assert c["sub"] == "orchestrator" and c["cid"] == "cust-1001" and scopes_of(c) == ["accounts:read"]
    assert c["exp"] - c["iat"] <= 300


def test_client_secret_post_also_works(stack):
    r = httpx.post(stack.settings.issuer + "/token", data={"grant_type": "client_credentials", "client_id": "orchestrator",
                                                           "client_secret": stack.secrets["orchestrator"], "resource": stack.settings.mcp_url,
                                                           "scope": "accounts:read"})
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("auth", [("orchestrator", "wrong-secret-xxxxxxxxxxxxxxxxxxxx"), ("nobody", "x" * 30)])
def test_bad_client_auth(stack, auth):
    r = post(stack, auth=auth, grant_type="client_credentials", resource=stack.settings.mcp_url, scope="accounts:read")
    assert r.status_code == 401 and r.json()["error"] == "invalid_client"
    assert "secret" not in r.text.lower().replace("client authentication failed", "")


def test_unknown_resource(stack):
    r = post(stack, grant_type="client_credentials", resource="http://evil.example/mcp", scope="accounts:read")
    assert r.json()["error"] == "invalid_target"


def test_scope_must_be_allowed_and_present(stack):
    assert post(stack, grant_type="client_credentials", resource=stack.settings.mcp_url, scope="cards:write").json()["error"] == "invalid_scope"
    assert post(stack, grant_type="client_credentials", resource=stack.settings.mcp_url).json()["error"] == "invalid_scope"


def test_readonly_client_cannot_get_a2a_scope(stack):
    with pytest.raises(AuthError, match="invalid_scope"):
        provider(stack, "readonly-dashboard").get(stack.settings.a2a_url, ["a2a:invoke"])


def test_unsupported_grant(stack):
    assert post(stack, grant_type="password", resource=stack.settings.mcp_url).json()["error"] == "unsupported_grant_type"


def test_exchange_makes_narrow_on_behalf_of_token(stack):
    s = stack.settings
    a = token(stack, s.a2a_url, ["a2a:invoke", "tools:basic", "accounts:read"])
    b = provider(stack, "loan-advisor").exchange(a, s.mcp_url, ["tools:basic"])
    c = claims_of(stack, b, s.mcp_url)
    assert c["sub"] == "orchestrator" and c["act"] == {"sub": "loan-advisor"} and c["cid"] == "cust-1001"
    assert scopes_of(c) == ["tools:basic"] and c["exp"] - c["iat"] <= 120


def test_exchange_never_exceeds_what_the_caller_had(stack):
    s = stack.settings
    a = token(stack, s.a2a_url, ["a2a:invoke"])                          # the orchestrator did NOT delegate tools:basic
    with pytest.raises(AuthError, match="invalid_scope"):
        provider(stack, "loan-advisor").exchange(a, s.mcp_url, ["tools:basic"])


def test_exchange_never_exceeds_what_the_agent_may_swap(stack):
    s = stack.settings
    a = forge(stack, audience=s.a2a_url, scopes=["a2a:invoke", "cards:write"])
    with pytest.raises(AuthError, match="invalid_scope"):
        provider(stack, "loan-advisor").exchange(a, s.mcp_url, ["cards:write"])


def test_exchange_requires_token_issued_for_the_exchanging_service(stack):
    s = stack.settings
    mcp_token = token(stack, s.mcp_url, ["tools:basic"])                 # audience = MCP, not the A2A agent
    with pytest.raises(AuthError, match="invalid_grant"):
        provider(stack, "loan-advisor").exchange(mcp_token, s.mcp_url, ["tools:basic"])


def test_only_the_advisor_may_exchange(stack):
    s = stack.settings
    a = token(stack, s.a2a_url, ["a2a:invoke", "tools:basic"])
    with pytest.raises(AuthError, match="unauthorized_client"):
        provider(stack, "orchestrator").exchange(a, s.mcp_url, ["tools:basic"])


def test_exchange_with_garbage_or_expired_subject(stack):
    s = stack.settings
    with pytest.raises(AuthError, match="invalid_grant"):
        provider(stack, "loan-advisor").exchange("junk", s.mcp_url, ["tools:basic"])
    old = forge(stack, audience=s.a2a_url, scopes=["tools:basic"], now=__import__("time").time() - 9999)
    with pytest.raises(AuthError, match="invalid_grant"):
        provider(stack, "loan-advisor").exchange(old, s.mcp_url, ["tools:basic"])


def test_token_provider_caches_until_near_expiry():
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, json={"access_token": f"t{len(calls)}", "expires_in": 100})
    now = [0.0]
    from oauth_client import TokenProvider
    p = TokenProvider("http://x/token", "c", "s", http=httpx.Client(transport=httpx.MockTransport(handler)), clock=lambda: now[0])
    assert p.get("r", ["a"]) == "t1" and p.get("r", ["a"]) == "t1" and len(calls) == 1
    assert p.get("r", ["b"]) == "t2"                                    # different scopes = different token
    now[0] = 80                                                         # 30 s skew: 100 - 30 = 70 < 80, refresh
    assert p.get("r", ["a"]) == "t3"
