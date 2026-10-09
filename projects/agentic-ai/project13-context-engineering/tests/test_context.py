import pytest

from agent import run
from context_manager import FACT_LINE, STRATEGIES, ContextManager
from fake_model import ContextAgentModel, visible_progress
from tokens import count_text
from world import CODE, REGION, World


def paired(view):
    uses = {b["id"] for m in view if m["role"] == "assistant" for b in m["content"] if b["type"] == "tool_use"}
    res = {b["tool_use_id"] for m in view if m["role"] == "user" and isinstance(m["content"], list) for b in m["content"] if b["type"] == "tool_result"}
    return res <= uses


def test_world_is_deterministic_and_plants_facts():
    w = World()
    assert w.shard_text(5) == World().shard_text(5)
    assert f"FACT: refund approval code is {CODE}" in w.shard_text(3)
    assert REGION in w.shard_text(7) and "K7-ALPHA-1180" in w.shard_text(12)
    assert "FACT" not in w.shard_text(4)


def test_a_shard_is_big_enough_to_matter():
    assert 500 < count_text(World().shard_text(1)) < 1500


def test_naive_overflows_the_window():
    r = run("naive")
    assert r.overflow_at and 15 < r.overflow_at < 40 and not r.correct


@pytest.mark.parametrize("name", ["window", "clear_results", "clear_results+inputs", "summarize_lossy", "summarize_structured", "clear+ledger", "summarize_lossy+ledger", "clear+notes"])
def test_managed_strategies_stay_under_budget_and_finish(name):
    r = run(name)
    assert r.overflow_at is None and r.peak_tokens <= STRATEGIES[name].budget and r.steps >= 100


@pytest.mark.parametrize("name,ok", [("window", False), ("clear_results", False), ("summarize_lossy", False), ("summarize_structured", True),
                                     ("clear+ledger", True), ("summarize_lossy+ledger", True), ("clear+notes", True)])
def test_step3_fact_at_step_100(name, ok):
    assert run(name).correct is ok


def test_recency_hides_forgetting():
    assert run("window", world=World(code_at=97, region_at=98)).correct


def test_clear_results_keeps_calls_and_pairs():
    cm = ContextManager(STRATEGIES["clear_results"])
    w = World()
    m = ContextAgentModel()
    cm.add({"role": "user", "content": "task"})
    for _ in range(40):
        system, view = cm.prepare()
        content = m(system, view)
        cm.add({"role": "assistant", "content": content})
        u = content[0]
        cm.add({"role": "user", "content": [{"type": "tool_result", "tool_use_id": u["id"], "content": w.call(u["name"], u["input"])}]})
    assert cm.cleared > 0 and paired(cm.view)
    cleared = [b["content"] for m_ in cm.view if m_["role"] == "user" and isinstance(m_["content"], list) for b in m_["content"] if str(b["content"]).startswith("[cleared")]
    assert cleared and "read_log(shard=" in cleared[0]
    assert len(cm.transcript) == 81                      # nothing is ever lost from the audit transcript
    assert visible_progress(cm.system, cm.view) == 40    # the agent still knows how far it got


def test_newest_results_are_never_cleared():
    r = run("clear_results")
    assert r.correct is False and r.cleared > 50


def test_window_never_starts_on_orphan_tool_result():
    cm = ContextManager(STRATEGIES["window"])
    w, m = World(), ContextAgentModel()
    cm.add({"role": "user", "content": "task"})
    for _ in range(60):
        system, view = cm.prepare()
        assert paired(view)
        content = m(system, view)
        cm.add({"role": "assistant", "content": content})
        cm.add({"role": "user", "content": [{"type": "tool_result", "tool_use_id": content[0]["id"], "content": w.call(content[0]["name"], content[0]["input"])}]})


def test_ledger_extracts_verbatim_and_dedupes():
    cm = ContextManager(STRATEGIES["clear+ledger"])
    for _ in range(2):
        cm.add({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": World().shard_text(3)}]})
    assert cm.ledger_items == [f"FACT: refund approval code is {CODE}"]
    assert "<must_keep>" in cm.system and CODE in cm.system


def test_summary_verifier_reinserts_dropped_facts():
    r = run("summarize_lossy+ledger")
    assert r.correct and r.ledger


def test_eager_clearing_breaks_the_cache_far_more_than_batch():
    eager, batch = run("clear_eager"), run("clear_batch")
    assert eager.prefix_breaks > 4 * batch.prefix_breaks
    assert eager.cached_cost_units > 2 * batch.cached_cost_units


def test_cache_makes_append_only_cheap():
    r = run("naive", max_steps=20)
    assert r.cached_cost_units < 0.3 * r.billed_tokens


def test_confabulation_is_worse_than_honesty():
    honest = run("summarize_lossy", world=World(decoy_at=95))
    liar = run("summarize_lossy", model=ContextAgentModel(confabulate=True), world=World(decoy_at=95))
    assert "cannot find" in honest.answer and liar.detail["wrong_decoy"]


def test_notes_survive_clearing_but_only_if_written():
    r = run("clear+notes")
    assert r.notes["approval_code"].endswith(CODE) and "ap-south-1" in r.notes["constraint"]
    assert run("clear_results").notes == {}


def test_search_beats_stuffing():
    w = World()
    corpus = sum(count_text(w.shard_text(n)) for n in range(1, 101))
    hits = w.call("search_logs", {"query": "FACT:"})
    assert CODE in hits and count_text(hits) < corpus / 50


def test_facts_regex_matches_only_flagged_lines():
    assert FACT_LINE.findall("noise\nFACT: x\nmore\nUSER-CONSTRAINT: y\nfact: nope") == ["FACT: x", "USER-CONSTRAINT: y"]
