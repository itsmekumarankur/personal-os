import base64
import hashlib
import hmac
import json
import time

import pytest

from tokens import ALG, KeyStore, TokenError, make_claims, scopes_of, verify_jwt

ISS, AUD = "http://auth", "http://svc"


def claims(**kw):
    base = dict(issuer=ISS, subject="c1", audience=AUD, scopes=["a", "b"], ttl=60)
    base.update(kw)
    return make_claims(**base)


def b64(d: bytes) -> str:
    return base64.urlsafe_b64encode(d).rstrip(b"=").decode()


@pytest.fixture(scope="module")
def ks():
    return KeyStore()


def test_roundtrip(ks):
    c = verify_jwt(ks.sign(claims(cid="cust-1", actor="agent")), ks.jwks(), issuer=ISS, audience=AUD)
    assert c["sub"] == "c1" and c["cid"] == "cust-1" and c["act"] == {"sub": "agent"}
    assert scopes_of(c) == ["a", "b"]


def test_expired(ks):
    t = ks.sign(claims(now=time.time() - 1000))
    with pytest.raises(TokenError) as e:
        verify_jwt(t, ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "expired"


def test_wrong_audience_is_the_key_defence(ks):
    with pytest.raises(TokenError) as e:
        verify_jwt(ks.sign(claims(audience="http://other")), ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "wrong_audience"


def test_wrong_issuer(ks):
    with pytest.raises(TokenError) as e:
        verify_jwt(ks.sign(claims(issuer="http://evil")), ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "wrong_issuer"


def test_tampered_payload(ks):
    h, p, s = ks.sign(claims(scopes=["a"])).split(".")
    evil = json.loads(base64.urlsafe_b64decode(p + "=="))
    evil["scope"] = "a cards:write"
    with pytest.raises(TokenError) as e:
        verify_jwt(f"{h}.{b64(json.dumps(evil).encode())}.{s}", ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "invalid"


def test_alg_none_refused(ks):
    h = b64(json.dumps({"alg": "none", "typ": "JWT", "kid": ks.kid}).encode())
    p = b64(json.dumps(claims()).encode())
    with pytest.raises(TokenError) as e:
        verify_jwt(f"{h}.{p}.", ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "bad_alg"


def test_hs256_with_public_key_as_secret_refused(ks):
    """The classic confusion attack: sign with HMAC using the (public!) key bytes and hope the server uses the key as an HMAC secret."""
    public_bytes = json.dumps(ks.jwks()["keys"][0]).encode()
    h = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": ks.kid}).encode())
    p = b64(json.dumps(claims()).encode())
    sig = b64(hmac.new(public_bytes, f"{h}.{p}".encode(), hashlib.sha256).digest())
    with pytest.raises(TokenError) as e:
        verify_jwt(f"{h}.{p}.{sig}", ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "bad_alg"


def test_unknown_kid(ks):
    other = KeyStore()
    with pytest.raises(TokenError) as e:
        verify_jwt(other.sign(claims()), ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "unknown_key"


def test_same_kid_different_key_fails_signature(ks):
    imposter = KeyStore(kid=ks.kid)
    with pytest.raises(TokenError) as e:
        verify_jwt(imposter.sign(claims()), ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "invalid"


def test_missing_required_claim(ks):
    import jwt
    c = claims()
    del c["aud"]
    t = jwt.encode(c, ks._key, algorithm=ALG, headers={"kid": ks.kid})
    with pytest.raises(TokenError) as e:
        verify_jwt(t, ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "missing_claim"


def test_garbage(ks):
    with pytest.raises(TokenError) as e:
        verify_jwt("not-a-jwt", ks.jwks(), issuer=ISS, audience=AUD)
    assert e.value.code == "malformed"


def test_key_survives_pem_roundtrip(ks):
    again = KeyStore(ks.private_pem(), kid=ks.kid)
    verify_jwt(again.sign(claims()), ks.jwks(), issuer=ISS, audience=AUD)


def test_jwks_has_no_private_parts(ks):
    k = ks.jwks()["keys"][0]
    assert not {"d", "p", "q", "dp", "dq", "qi"} & set(k)
