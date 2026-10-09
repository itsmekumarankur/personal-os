"""How a program gets its tokens: ask the auth server, keep the token until shortly before it expires."""
import time

import httpx

EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"


class AuthError(Exception):
    pass


class TokenProvider:
    def __init__(self, token_url: str, client_id: str, client_secret: str, http: httpx.Client | None = None, clock=time.time, skew: int = 30):
        self.url, self.cid, self.secret = token_url, client_id, client_secret
        self.http, self.clock, self.skew = http or httpx.Client(timeout=10), clock, skew
        self._cache: dict = {}

    def _post(self, data: dict) -> dict:
        r = self.http.post(self.url, data=data, auth=(self.cid, self.secret))
        if r.status_code != 200:
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            raise AuthError(f"{r.status_code} {body.get('error', 'error')}: {body.get('error_description', '')}")
        return r.json()

    def get(self, resource: str, scopes: list) -> str:
        """client_credentials: 'I am this client, give me a token for THIS service with THESE scopes'."""
        key = (resource, tuple(sorted(scopes)))
        hit = self._cache.get(key)
        if hit and hit[1] - self.skew > self.clock():
            return hit[0]
        j = self._post({"grant_type": "client_credentials", "resource": resource, "scope": " ".join(scopes)})
        self._cache[key] = (j["access_token"], self.clock() + j["expires_in"])
        return j["access_token"]

    def exchange(self, subject_token: str, resource: str, scopes: list | None = None) -> str:
        """token exchange: 'someone gave me THIS token; give me a smaller one for ANOTHER service, on their behalf'. Not cached."""
        data = {"grant_type": EXCHANGE, "subject_token": subject_token, "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "resource": resource}
        if scopes:
            data["scope"] = " ".join(scopes)
        return self._post(data)["access_token"]
