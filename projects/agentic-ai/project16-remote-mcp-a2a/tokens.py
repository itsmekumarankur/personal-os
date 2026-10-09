"""Signing and checking access tokens (JWTs).

A JWT is three base64 parts: header . claims . signature.  The signature proves the auth server wrote it.
We use RS256: the auth server signs with a PRIVATE key, every other service checks with the PUBLIC key (published as JWKS).
Why not a shared secret (HS256)? Then every service that can CHECK tokens could also MINT them.

Claims we use:
  iss  who issued it            aud  which service it is FOR (a token for the MCP server must not work on the A2A agent)
  sub  who it is about          exp  when it dies             scope  what it allows (space separated)
  cid  the customer it acts for act  the agent acting on someone's behalf (token exchange)
"""
import time
import uuid

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ALG = "RS256"


class TokenError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


class KeyStore:
    """Holds one signing key. In production keys live in a KMS/HSM and rotate; here one key is made at start-up."""

    def __init__(self, private_pem: bytes | None = None, kid: str | None = None):
        if private_pem:
            self._key = serialization.load_pem_private_key(private_pem, password=None)
        else:
            self._key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = kid or "key-" + uuid.uuid4().hex[:8]

    def private_pem(self) -> bytes:
        return self._key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())

    def jwks(self) -> dict:
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(self._key.public_key(), as_dict=True)
        jwk.update({"kid": self.kid, "use": "sig", "alg": ALG})
        return {"keys": [jwk]}

    def sign(self, claims: dict) -> str:
        return jwt.encode(claims, self._key, algorithm=ALG, headers={"kid": self.kid})


def make_claims(*, issuer, subject, audience, scopes, ttl, cid=None, actor=None, now=None) -> dict:
    now = int(now if now is not None else time.time())
    c = {"iss": issuer, "sub": subject, "aud": audience, "scope": " ".join(sorted(set(scopes))),
         "iat": now, "nbf": now, "exp": now + ttl, "jti": uuid.uuid4().hex}
    if cid:
        c["cid"] = cid
    if actor:
        c["act"] = {"sub": actor}
    return c


def verify_jwt(token: str, jwks: dict, *, issuer: str, audience: str, leeway: int = 0) -> dict:
    """Returns the claims or raises TokenError. Every check is explicit so you can see what protects you:
       1 the algorithm must be RS256   (blocks 'alg: none' and the HS256-with-public-key trick)
       2 the key id must be one we know
       3 the signature must match
       4 iss, aud, exp, nbf must be right and present"""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise TokenError("malformed", "not a JWT")
    if header.get("alg") != ALG:
        raise TokenError("bad_alg", f"alg {header.get('alg')!r} is not accepted")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")), None)
    if key is None:
        raise TokenError("unknown_key", "kid not in JWKS")
    try:
        return jwt.decode(token, jwt.algorithms.RSAAlgorithm.from_jwk(key), algorithms=[ALG], audience=audience, issuer=issuer,
                          leeway=leeway, options={"require": ["exp", "iat", "iss", "aud", "sub"]})
    except jwt.ExpiredSignatureError:
        raise TokenError("expired")
    except jwt.InvalidAudienceError:
        raise TokenError("wrong_audience", f"token is not for {audience}")
    except jwt.InvalidIssuerError:
        raise TokenError("wrong_issuer")
    except jwt.MissingRequiredClaimError as e:
        raise TokenError("missing_claim", str(e))
    except jwt.PyJWTError as e:
        raise TokenError("invalid", type(e).__name__)


def scopes_of(claims: dict) -> list:
    return [s for s in str(claims.get("scope", "")).split(" ") if s]
