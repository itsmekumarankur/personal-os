import json
from types import SimpleNamespace as NS

import pytest

from agent import SupportAgent
from demo_fake import FakeModel
from pricing import UnknownModel, cost_usd, load_pricing, trace_totals
from tools import calculate_emi, lookup_fee
from tracing import Clock, MemoryExporter, Tracer

PRICING = {"m": {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75}}


def test_cost_arithmetic():
    # 1,000 in at 3 per million = 0.003 ; 200 out at 15 per million = 0.003
    assert cost_usd(PRICING, "m", 1000, 200) == pytest.approx(0.006)
    assert cost_usd(PRICING, "m", 0, 0, cache_read=1_000_000) == pytest.approx(0.3)


def test_unknown_model_is_an_error_not_free():
    with pytest.raises(UnknownModel):
        cost_usd(PRICING, "other", 10, 10)


def test_pricing_file_loads_and_hides_comment():
    p = load_pricing()
    assert "demo-model" in p and not any(k.startswith("_") for k in p)


def test_tools():
    assert calculate_emi(500000, 9, 60) == "10379.18"
    assert calculate_emi(120000, 0, 12) == "10000.00"
    with pytest.raises(ValueError):
        calculate_emi(-1, 9, 60)
    with pytest.raises(ValueError, match="unknown product"):
        lookup_fee("nope")


def build(mode="good"):
    clock = Clock()
    ex = MemoryExporter()
    tr = Tracer([ex], clock=clock, content="full")
    return SupportAgent(FakeModel(mode, clock=clock), tr, load_pricing()), ex


def test_agent_makes_the_expected_span_tree():
    agent, ex = build()
    r = agent.run("EMI for a loan of 500000 at 9% for 5 years?", case_id="c1")
    assert r.finished and "10379.18" in r.answer and r.turns == 2
    spans = ex.all()[0]
    names = [s.name for s in spans]
    assert names == ["agent.run", "chat demo-model", "execute_tool calculate_emi", "chat demo-model"]
    root = spans[0]
    assert root.attrs["eval.case_id"] == "c1" and root.attrs["agent.finished"] is True
    chat = spans[1]
    assert chat.attrs["gen_ai.operation.name"] == "chat" and chat.attrs["gen_ai.usage.input_tokens"] > 0
    assert chat.attrs["cost.usd"] > 0
    assert spans[2].attrs["gen_ai.tool.name"] == "calculate_emi"


def test_trace_totals_add_up():
    agent, ex = build()
    agent.run("EMI for a loan of 500000 at 9% for 5 years?")
    spans = ex.all()[0]
    t = trace_totals(spans)
    chats = [s for s in spans if s.attrs.get("gen_ai.operation.name") == "chat"]
    assert t["llm_calls"] == 2 and t["tool_calls"] == 1 and t["errors"] == 0
    assert t["cost_usd"] == pytest.approx(sum(s.attrs["cost.usd"] for s in chats))
    assert t["input_tokens"] == sum(s.attrs["gen_ai.usage.input_tokens"] for s in chats)


def test_tool_error_is_visible_in_the_trace_and_goes_back_to_the_model():
    agent, ex = build()
    r = agent.run("What is the fee for the platinum lounge pass?")
    assert "could not find" in r.answer and r.tool_calls[0]["is_error"] is True
    spans = ex.all()[0]
    tool = next(s for s in spans if s.name.startswith("execute_tool"))
    assert tool.status == "ERROR" and tool.attrs["tool.is_error"] is True
    assert spans[0].status == "OK"                    # the run itself finished fine


def test_turn_limit_marks_the_run_as_error():
    def looping(messages):
        blk = NS(type="tool_use", id="x", name="lookup_fee", input={"product": "late_payment"})
        return NS(stop_reason="tool_use", content=[blk], usage=NS(input_tokens=5, output_tokens=5))
    ex = MemoryExporter()
    agent = SupportAgent(looping, Tracer([ex], clock=Clock()), load_pricing(), max_turns=3)
    r = agent.run("loop")
    assert not r.finished and len(r.tool_calls) == 3
    assert ex.all()[0][0].status == "ERROR"


def test_content_policy_applies_to_prompts():
    clock = Clock()
    ex = MemoryExporter()
    agent = SupportAgent(FakeModel("good", clock=clock), Tracer([ex], clock=clock, content="off"), load_pricing())
    agent.run("hello, my card is 4111 1111 1111 1111")
    root = ex.all()[0][0]
    assert root.attrs["input.value"] is None and "4111" not in json.dumps(root.to_dict(), default=str)


def test_degraded_model_is_visibly_different():
    agent, ex = build("degraded")
    r = agent.run("EMI for a loan of 500000 at 9% for 5 years?")
    assert r.tool_calls == [] and "10379" not in r.answer
