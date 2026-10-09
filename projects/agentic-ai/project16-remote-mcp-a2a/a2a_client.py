"""Calling another agent over A2A.

The agent card is UNTRUSTED CONTENT written by whoever runs that server. Before we send a bearer token anywhere we check:
  1. the card's endpoint is on the SAME origin we discovered it from (a card must not redirect our token to another host)
  2. the endpoint is not a private / loopback / link-local address (SSRF), unless the caller says allow_local=True (demo and tests)
  3. https is used (unless allow_local)
"""
import ipaddress
import socket
import time
from urllib.parse import urlsplit

import httpx

import a2a_types as T
from propagation import new_traceparent


class A2AError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


class UnsafeCard(Exception):
    pass


def _origin(url: str) -> tuple:
    p = urlsplit(url)
    return p.scheme, p.hostname, p.port or (443 if p.scheme == "https" else 80)


def is_private_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True                                       # cannot resolve = do not call
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return True
    return False


def endpoint_from_card(card: dict) -> str:
    for i in card.get("supportedInterfaces") or []:
        if i.get("protocolBinding") == "JSONRPC" and i.get("url"):
            return i["url"]
    if card.get("url"):                                   # older cards
        return card["url"]
    raise UnsafeCard("card has no JSON-RPC endpoint")


class A2AClient:
    def __init__(self, base_url: str, get_token, allow_local: bool = False, traceparent: str | None = None, http: httpx.Client | None = None):
        self.base, self.get_token, self.allow_local = base_url.rstrip("/"), get_token, allow_local
        self.traceparent = traceparent or new_traceparent()
        self.http = http or httpx.Client(timeout=30, follow_redirects=False)   # a redirect could carry the token elsewhere
        self.card: dict | None = None
        self.endpoint: str | None = None
        self._id = 0

    def discover(self) -> dict:
        r = self.http.get(self.base + "/.well-known/agent-card.json")
        r.raise_for_status()
        card = r.json()
        endpoint = endpoint_from_card(card)
        if _origin(endpoint) != _origin(self.base):
            raise UnsafeCard(f"card points to a different origin ({endpoint}); refusing to send a token there")
        host = urlsplit(endpoint).hostname or ""
        if not self.allow_local:
            if urlsplit(endpoint).scheme != "https":
                raise UnsafeCard("endpoint must use https")
            if is_private_host(host):
                raise UnsafeCard("endpoint resolves to a private or loopback address")
        self.card, self.endpoint = card, endpoint
        return card

    def audience(self) -> str:
        """The value to put in the token request's 'resource': exactly the endpoint the card named."""
        if not self.endpoint:
            self.discover()
        return self.endpoint

    def _rpc(self, method: str, params: dict) -> dict:
        if not self.endpoint:
            self.discover()
        self._id += 1
        r = self.http.post(self.endpoint, json={"jsonrpc": "2.0", "id": self._id, "method": method, "params": params},
                           headers={"Authorization": f"Bearer {self.get_token()}", "traceparent": self.traceparent})
        if r.status_code in (401, 403):
            raise A2AError(r.status_code, r.headers.get("www-authenticate", "unauthorized"))
        body = r.json()
        if "error" in body:
            raise A2AError(body["error"]["code"], body["error"]["message"])
        return body["result"]

    def send(self, text: str, task_id: str | None = None, context_id: str | None = None, return_immediately: bool = False) -> dict:
        msg = T.make_message("user", text, context_id, task_id)
        cfg = {"returnImmediately": True} if return_immediately else {}
        return self._rpc("SendMessage", {"message": msg, "configuration": cfg})["task"]

    def get(self, task_id: str) -> dict:
        return self._rpc("GetTask", {"id": task_id})

    def cancel(self, task_id: str) -> dict:
        return self._rpc("CancelTask", {"id": task_id})

    def wait(self, task_id: str, timeout: float = 10.0, interval: float = 0.1) -> dict:
        """Poll until the task is finished or is waiting for us."""
        end = time.monotonic() + timeout
        while True:
            t = self.get(task_id)
            if t["status"]["state"] in T.TERMINAL | T.INTERRUPTED:
                return t
            if time.monotonic() > end:
                raise TimeoutError("task did not settle in time")
            time.sleep(interval)

    def run(self, text: str, answer_fn=None, max_turns: int = 4) -> dict:
        """Send, and while the agent asks for more input, ask answer_fn(question) -> reply. Same task id throughout."""
        t = self.send(text)
        for _ in range(max_turns):
            state = t["status"]["state"]
            if state == T.WORKING:
                t = self.wait(t["id"])
                continue
            if state != T.INPUT_REQUIRED:
                return t
            question = " ".join(T.part_text(p) for p in t["status"].get("message", {}).get("parts", []))
            reply = answer_fn(question) if answer_fn else None
            if not reply:
                return t                                  # nobody to answer: hand the waiting task back to the caller
            t = self.send(reply, task_id=t["id"], context_id=t["contextId"])
        return t


def task_text(task: dict) -> str:
    return " ".join(T.part_text(p) for p in task["status"].get("message", {}).get("parts", []))
