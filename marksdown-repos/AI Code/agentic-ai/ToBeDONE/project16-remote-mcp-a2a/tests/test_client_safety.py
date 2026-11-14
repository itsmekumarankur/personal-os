import httpx
import pytest

from a2a_client import A2AClient, UnsafeCard, is_private_host


def card_client(card: dict, base="https://agent.example.com", allow_local=False, status=200):
    def handler(req):
        if req.url.path.endswith("agent-card.json"):
            return httpx.Response(status, json=card, headers={"location": "http://evil.example"} if status == 302 else {})
        return httpx.Response(500)
    return A2AClient(base, lambda: "tok", allow_local=allow_local, http=httpx.Client(transport=httpx.MockTransport(handler)))


GOOD = {"supportedInterfaces": [{"url": "https://agent.example.com/a2a", "protocolBinding": "JSONRPC"}]}


@pytest.mark.parametrize("host,expected", [("127.0.0.1", True), ("10.0.0.5", True), ("192.168.1.10", True), ("169.254.169.254", True),
                                           ("0.0.0.0", True), ("::1", True), ("8.8.8.8", False)])
def test_private_hosts(host, expected):
    assert is_private_host(host) is expected


def test_good_card_is_accepted(monkeypatch):
    monkeypatch.setattr("a2a_client.is_private_host", lambda h: False)
    c = card_client(GOOD)
    assert c.discover() and c.audience() == "https://agent.example.com/a2a"


def test_card_pointing_to_another_origin_is_refused(monkeypatch):
    monkeypatch.setattr("a2a_client.is_private_host", lambda h: False)
    c = card_client({"supportedInterfaces": [{"url": "https://evil.example/a2a", "protocolBinding": "JSONRPC"}]})
    with pytest.raises(UnsafeCard, match="different origin"):
        c.discover()


def test_same_host_different_port_is_a_different_origin(monkeypatch):
    monkeypatch.setattr("a2a_client.is_private_host", lambda h: False)
    with pytest.raises(UnsafeCard):
        card_client({"url": "https://agent.example.com:8443/a2a"}).discover()


def test_card_pointing_at_internal_address_is_refused():
    c = card_client({"url": "https://10.0.0.5/a2a"}, base="https://10.0.0.5")
    with pytest.raises(UnsafeCard, match="private"):
        c.discover()


def test_plain_http_refused_unless_local_allowed():
    with pytest.raises(UnsafeCard, match="https"):
        card_client({"url": "http://agent.example.com/a2a"}, base="http://agent.example.com").discover()
    assert card_client({"url": "http://127.0.0.1/a2a"}, base="http://127.0.0.1", allow_local=True).discover()


def test_card_without_endpoint():
    with pytest.raises(UnsafeCard, match="no JSON-RPC"):
        card_client({"name": "x"}).discover()


def test_redirects_are_not_followed():
    with pytest.raises(httpx.HTTPStatusError):
        card_client(GOOD, status=302).discover()


def test_default_http_client_does_not_follow_redirects():
    assert A2AClient("https://x", lambda: "t").http.follow_redirects is False
