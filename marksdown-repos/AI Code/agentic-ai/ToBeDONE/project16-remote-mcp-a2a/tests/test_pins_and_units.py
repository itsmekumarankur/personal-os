import pytest

import a2a_types as T
from advisor import parse_loan
from audit import AuditLog, RateLimiter
from bank import NotYours, calculate_emi, freeze_card
from propagation import new_traceparent, trace_id_of
from tool_pinning import PinMismatch, ToolPins, fingerprint

T1 = {"name": "a", "description": "does a", "inputSchema": {"type": "object"}}
T2 = {"name": "b", "description": "does b", "inputSchema": {"type": "object"}}


def test_fingerprint_covers_name_description_schema():
    base = fingerprint(T1)
    assert fingerprint({**T1, "description": "does a!"}) != base
    assert fingerprint({**T1, "inputSchema": {"type": "object", "properties": {"x": {}}}}) != base
    assert fingerprint({**T1, "name": "z"}) != base
    assert fingerprint(dict(reversed(list(T1.items())))) == base


def test_pins_detect_changed_new_removed():
    p = ToolPins()
    p.approve([T1, T2])
    assert p.check([T2, T1])
    with pytest.raises(PinMismatch) as e:
        p.check([{**T1, "description": "evil"}, T2])
    assert e.value.changed == ["a"]
    with pytest.raises(PinMismatch) as e:
        p.check([T1, T2, {"name": "c"}])
    assert e.value.new == ["c"]
    with pytest.raises(PinMismatch) as e:
        p.check([T1])
    assert e.value.removed == ["b"]


def test_trust_on_first_use_then_strict(tmp_path):
    f = tmp_path / "pins.json"
    p = ToolPins(str(f))
    p.check_or_trust([T1])
    assert ToolPins(str(f)).pins == p.pins                               # persisted
    with pytest.raises(PinMismatch):
        ToolPins(str(f)).check_or_trust([{**T1, "description": "x"}])


def test_traceparent():
    tp = new_traceparent()
    child = new_traceparent(tp)
    assert trace_id_of(child) == trace_id_of(tp) and child != tp
    assert trace_id_of(new_traceparent("garbage")) is not None
    assert trace_id_of("nope") is None
    assert trace_id_of(new_traceparent("00-" + "0" * 32 + "-" + "1" * 16 + "-01")) != "0" * 32


def test_rate_limiter_window():
    now = [0.0]
    r = RateLimiter(2, window=60, clock=lambda: now[0])
    assert r.allow("a") and r.allow("a") and not r.allow("a")
    assert r.allow("b")
    now[0] = 61
    assert r.allow("a")


def test_audit_file(tmp_path):
    f = tmp_path / "a.jsonl"
    a = AuditLog(str(f))
    a.record(x=1)
    assert '"x": 1' in f.read_text() and a.all()[0]["x"] == 1


def test_emi_known_values():
    assert calculate_emi(500000, 9, 60)["emi"] == 10379.18
    assert calculate_emi(1200, 0, 12)["emi"] == 100.0
    with pytest.raises(ValueError):
        calculate_emi(0, 5, 12)


def test_ownership_helper():
    with pytest.raises(NotYours):
        freeze_card("card-9", "cust-1001")


@pytest.mark.parametrize("text,expect", [
    ("I want a loan of 5 lakh at 9% for 5 years", {"principal": 500000, "rate": 9, "months": 60}),
    ("200000 at 12.5% over 24 months", {"principal": 200000, "rate": 12.5, "months": 24}),
    ("loan of 2 crore", {"principal": 2e7}),
    ("50k loan at 10 percent for 2 yrs", {"principal": 50000, "rate": 10, "months": 24}),
    ("1,50,000 at 8%", {"rate": 8}),
    ("hello", {}),
])
def test_parse_loan(text, expect):
    got = parse_loan(text, {})
    for k, v in expect.items():
        assert got[k] == v


def test_parse_loan_accumulates():
    k = parse_loan("loan 100000 at 10%", {})
    assert parse_loan("for 3 years", k) == {"principal": 100000, "rate": 10, "months": 36}


def test_state_machine_terminals_are_final():
    for s in T.TERMINAL:
        assert T.ALLOWED[s] == set()
    assert T.WORKING in T.ALLOWED[T.INPUT_REQUIRED] and T.COMPLETED not in T.ALLOWED[T.INPUT_REQUIRED]
