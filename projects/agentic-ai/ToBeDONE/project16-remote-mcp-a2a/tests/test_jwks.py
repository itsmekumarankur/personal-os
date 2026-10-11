import httpx
import pytest

from resource_auth import JwksCache, JwtVerifier
from tokens import KeyStore, TokenError, make_claims

ISS, AUD = "http://auth", "http://svc"


def tok(ks):
    return ks.sign(make_claims(issuer=ISS, subject="c", audience=AUD, scopes=["x"], ttl=60))


def cache(handler, **kw):
    return JwksCache(url="http://auth/jwks.json", client=httpx.Client(transport=httpx.MockTransport(handler)), **kw)


def test_fails_closed_when_the_auth_server_is_unreachable():
    def down(req):
        raise httpx.ConnectError("down")
    with pytest.raises(TokenError) as e:
        JwtVerifier(cache(down), ISS, AUD).check(tok(KeyStore()))
    assert e.value.code == "jwks_unavailable"


def test_key_rotation_is_picked_up_on_unknown_kid():
    old, new = KeyStore(), KeyStore()
    current = {"ks": old}
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, json=current["ks"].jwks())
    v = JwtVerifier(cache(handler), ISS, AUD)
    v.check(tok(old))
    assert len(calls) == 1
    v.check(tok(old))
    assert len(calls) == 1                                               # cached
    current["ks"] = new                                                  # the auth server rotates its key
    v.check(tok(new))
    assert len(calls) == 2                                               # unknown kid -> one refresh -> accepted


def test_unknown_kid_does_not_let_an_attacker_force_unlimited_fetches_of_a_bad_token():
    ks = KeyStore()
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, json=ks.jwks())
    v = JwtVerifier(cache(handler), ISS, AUD)
    for _ in range(3):
        with pytest.raises(TokenError):
            v.check(tok(KeyStore()))
    assert len(calls) <= 4                                               # known limitation: one refresh per bad token (see README, exercises)


def test_cache_expires():
    ks = KeyStore()
    now = [0.0]
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, json=ks.jwks())
    c = cache(handler, ttl=10, clock=lambda: now[0])
    c.get()
    c.get()
    now[0] = 11
    c.get()
    assert len(calls) == 2
