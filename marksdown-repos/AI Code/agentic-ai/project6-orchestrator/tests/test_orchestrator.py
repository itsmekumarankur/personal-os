"""Tests run without an API key: the model is replaced by a scripted fake."""
import sys
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm  # noqa: E402
import orchestrator as orch  # noqa: E402
from main import app  # noqa: E402


def plan_reply(n=3, extra=""):
    tasks = "".join(
        f"<task><title>Part {i}</title><description>DESC-{i} do thing {i}</description></task>"
        for i in range(1, n + 1)
    )
    return f"<analysis>ANALYSIS</analysis><tasks>{tasks}{extra}</tasks>"


def make_fake(plan=None, fail_parts=(), barrier=None, calls=None):
    """Plans with `plan`, answers workers, then synthesizes. Records every call."""
    calls = calls if calls is not None else []

    def fake(prompt, system_prompt, model=None, temperature=0.1, max_tokens=2048):
        calls.append({"system": system_prompt, "prompt": prompt, "model": model})
        if "You are the lead engineer. You receive a goal" in system_prompt:
            return plan if plan is not None else plan_reply(3)
        if "You are a worker engineer" in system_prompt:
            if barrier is not None:
                barrier.wait(timeout=5)          # opens only if all workers run at the same time
            for i in fail_parts:
                if f"DESC-{i} " in prompt:
                    raise RuntimeError("boom")
            idx = prompt.split("DESC-")[1].split(" ")[0]
            return f"<response>RESULT-{idx}</response>"
        if "writing the final answer" in system_prompt:
            return "<final>FINAL ANSWER</final>"
        raise AssertionError("unexpected call")

    return fake


@pytest.fixture
def calls(monkeypatch):
    c = []
    monkeypatch.setattr(llm, "llm_call", make_fake(calls=c))
    return c


# ---------- planning ----------

def test_parse_tasks_reads_titles_and_descriptions():
    tasks, truncated = orch.parse_tasks(plan_reply(3), max_tasks=5)
    assert [t["id"] for t in tasks] == [1, 2, 3]
    assert tasks[1]["title"] == "Part 2"
    assert "DESC-2" in tasks[1]["description"]
    assert truncated is False


def test_parse_tasks_caps_the_number_of_tasks():
    tasks, truncated = orch.parse_tasks(plan_reply(10), max_tasks=4)
    assert len(tasks) == 4 and truncated is True


def test_parse_tasks_skips_tasks_without_description_and_names_untitled_ones():
    text = ("<tasks><task><title>A</title></task>"
            "<task><description>only description</description></task></tasks>")
    tasks, _ = orch.parse_tasks(text, 5)
    assert len(tasks) == 1 and tasks[0]["title"] == "Task 1"


def test_garbage_plan_falls_back_to_one_task(monkeypatch):
    monkeypatch.setattr(llm, "llm_call", make_fake(plan="I cannot help with that"))
    r = orch.orchestrate("DESC-1 my goal", 4)   # the fake worker keys on DESC-n
    assert r["fallback"] is True
    assert len(r["tasks"]) == 1 and r["tasks"][0]["title"] == "Whole goal"
    assert "single task" in r["analysis"]


def test_hard_cap_cannot_be_exceeded(monkeypatch):
    monkeypatch.setattr(llm, "llm_call", make_fake(plan=plan_reply(20)))
    r = orch.orchestrate("g", max_tasks=999)
    assert len(r["tasks"]) == orch.HARD_MAX_TASKS and r["truncated"] is True


# ---------- workers ----------

def test_workers_run_at_the_same_time(monkeypatch):
    barrier = threading.Barrier(3)       # fails (timeout) if the 3 workers run one after another
    monkeypatch.setattr(llm, "llm_call", make_fake(plan=plan_reply(3), barrier=barrier))
    r = orch.orchestrate("g", 5)
    assert r["complete"] is True and len(r["tasks"]) == 3


def test_worker_sees_own_task_and_only_titles_of_the_others(calls):
    orch.orchestrate("THE GOAL", 5)
    worker_prompts = [c["prompt"] for c in calls if "You are a worker engineer" in c["system"]]
    p1 = next(p for p in worker_prompts if "DESC-1 " in p)
    assert "THE GOAL" in p1
    assert "Part 2" in p1 and "Part 3" in p1           # titles of the others
    assert "DESC-2" not in p1 and "DESC-3" not in p1   # but not their descriptions


def test_workers_use_worker_model_and_lead_uses_main_model(calls):
    orch.orchestrate("g", 5)
    for c in calls:
        if "worker engineer" in c["system"]:
            assert c["model"] == llm.WORKER_MODEL
        else:
            assert c["model"] == llm.MODEL


# ---------- failure handling ----------

def test_one_failed_worker_is_reported_and_synthesis_knows(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "llm_call", make_fake(fail_parts=(2,), calls=calls))
    r = orch.orchestrate("g", 5)
    assert r["complete"] is False
    assert [t["ok"] for t in r["tasks"]] == [True, False, True]
    assert "RuntimeError" in r["tasks"][1]["error"]
    synth_prompt = next(c["prompt"] for c in calls if "writing the final answer" in c["system"])
    assert "FAILED" in synth_prompt and "RESULT-1" in synth_prompt and "RESULT-3" in synth_prompt


def test_all_workers_failing_raises_and_skips_synthesis(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "llm_call", make_fake(fail_parts=(1, 2, 3), calls=calls))
    with pytest.raises(orch.AllWorkersFailed):
        orch.orchestrate("g", 5)
    assert not any("writing the final answer" in c["system"] for c in calls)


def test_worker_without_response_tag_counts_as_failed(monkeypatch):
    def fake(prompt, system_prompt, model=None, temperature=0.1, max_tokens=2048):
        if "You are the lead engineer. You receive" in system_prompt:
            return plan_reply(2)
        if "worker engineer" in system_prompt:
            return "no tags here" if "DESC-1 " in prompt else "<response>ok</response>"
        return "<final>F</final>"
    monkeypatch.setattr(llm, "llm_call", fake)
    r = orch.orchestrate("g", 5)
    assert [t["ok"] for t in r["tasks"]] == [False, True]


# ---------- result shape ----------

def test_final_answer_and_timing(calls):
    r = orch.orchestrate("g", 5)
    assert r["final"] == "FINAL ANSWER"
    assert r["analysis"] == "ANALYSIS"
    assert set(r["timing"]) == {"plan_seconds", "workers_wall_seconds", "workers_sum_seconds",
                                "synthesis_seconds", "total_seconds"}
    assert len(calls) == 1 + 3 + 1       # plan + 3 workers + synthesis


# ---------- API ----------

def test_api_health_and_orchestrate(monkeypatch):
    monkeypatch.setattr(llm, "llm_call", make_fake())
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    r = client.post("/orchestrate", json={"goal": "do it", "max_tasks": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["final"] == "FINAL ANSWER" and body["complete"] is True and len(body["tasks"]) == 3


def test_api_validates_input():
    client = TestClient(app)
    assert client.post("/orchestrate", json={"goal": ""}).status_code == 422
    assert client.post("/orchestrate", json={"goal": "x" * 8001}).status_code == 422
    assert client.post("/orchestrate", json={"goal": "x", "max_tasks": 99}).status_code == 422


def test_api_returns_502_when_all_workers_fail(monkeypatch):
    monkeypatch.setattr(llm, "llm_call", make_fake(fail_parts=(1, 2, 3)))
    r = TestClient(app).post("/orchestrate", json={"goal": "x"})
    assert r.status_code == 502
