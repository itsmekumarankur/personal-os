import json
import threading

import httpx
import pytest
from conftest import forge, provider, token  # noqa: F401

import a2a_types as T
from a2a_client import A2AClient, A2AError, task_text
from advisor import Advisor
from config import ClientRecord, sha256_hex
from orchestrator import make_orchestrator_client
from stack import ORCH, start_stack


def client(k, **kw):
    return make_orchestrator_client(k.settings, ORCH, **kw)


def raw(k, payload, tok=None, content=None):
    tok = tok or token(k, k.settings.a2a_url, ["a2a:invoke", "tools:basic"])
    return httpx.post(k.settings.a2a_url, content=content if content is not None else json.dumps(payload),
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})


def rpc(k, method, params, **kw):
    return raw(k, {"jsonrpc": "2.0", "id": 7, "method": method, "params": params}, **kw).json()


def test_agent_card_is_public_and_has_no_secrets(stack):
    r = httpx.get(stack.settings.a2a_base + "/.well-known/agent-card.json")
    card = r.json()
    assert card["skills"][0]["id"] == "emi-advice" and card["supportedInterfaces"][0]["url"] == stack.settings.a2a_url
    assert card["capabilities"]["streaming"] is False
    text = r.text
    for secret in (stack.secrets["orchestrator"], stack.secrets["loan-advisor"], "BEGIN"):
        assert secret not in text
    assert card["securitySchemes"]["oauth2"]["flows"]["clientCredentials"]["tokenUrl"] == stack.settings.issuer + "/token"


def test_rpc_needs_a_token(stack):
    r = httpx.post(stack.settings.a2a_url, json={})
    assert r.status_code == 401 and r.headers["www-authenticate"].startswith("Bearer")


def test_token_for_the_mcp_server_is_refused(stack):
    r = httpx.post(stack.settings.a2a_url, json={}, headers={"Authorization": "Bearer " + token(stack, stack.settings.mcp_url, ["tools:basic"])})
    assert r.status_code == 401 and "wrong_audience" in r.headers["www-authenticate"]


def test_missing_scope_is_403(stack):
    t = forge(stack, audience=stack.settings.a2a_url, scopes=["tools:basic"])
    r = httpx.post(stack.settings.a2a_url, json={}, headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 403 and "insufficient_scope" in r.headers["www-authenticate"]


def test_json_rpc_errors(stack):
    assert raw(stack, None, content="{not json").json()["error"]["code"] == T.PARSE_ERROR
    assert raw(stack, {"hello": 1}).json()["error"]["code"] == T.INVALID_REQUEST
    assert raw(stack, {"jsonrpc": "2.0", "id": 1, "method": "Nope"}).json()["error"]["code"] == T.METHOD_NOT_FOUND
    assert raw(stack, {"jsonrpc": "2.0", "id": 1, "method": "GetTask", "params": [1]}).json()["error"]["code"] == T.INVALID_PARAMS
    assert rpc(stack, "GetTask", {"id": "nope"})["error"]["code"] == T.TASK_NOT_FOUND
    for m in ("SendStreamingMessage", "ListTasks", "SubscribeToTask"):
        assert rpc(stack, m, {})["error"]["code"] == T.UNSUPPORTED_OPERATION


def test_response_echoes_request_id(stack):
    assert rpc(stack, "GetTask", {"id": "x"})["id"] == 7


@pytest.mark.parametrize("msg", [None, {"role": "agent", "parts": [{"text": "x"}]}, {"role": "user", "parts": []}, {"role": "user", "parts": [{"text": " "}]},
                                 {"role": "user", "parts": [{"text": "x" * 4001}]}, {"role": "user", "parts": [{"text": "a"}] * 6}])
def test_bad_messages_are_invalid_params(stack, msg):
    assert rpc(stack, "SendMessage", {"message": msg})["error"]["code"] == T.INVALID_PARAMS


def test_oversized_body(stack):
    r = raw(stack, None, content="x" * 70_000)
    assert r.status_code == 413


def test_off_topic_is_rejected(stack):
    t = client(stack).send("what is the weather in Chennai")
    assert t["status"]["state"] == T.REJECTED and "only help with loan" in task_text(t)


def test_input_required_then_complete_on_the_same_task(stack):
    c = client(stack)
    t1 = c.send("I want a loan of 5 lakh at 9%")
    assert t1["status"]["state"] == T.INPUT_REQUIRED and "tenure" in task_text(t1)
    t2 = c.send("for 5 years", task_id=t1["id"], context_id=t1["contextId"])
    assert t2["id"] == t1["id"] and t2["status"]["state"] == T.COMPLETED
    art = t2["artifacts"][0]
    assert art["parts"][1]["data"]["emi"] == 10379.18 and "10379.18" in task_text(t2)
    assert len(t2["history"]) >= 4                                    # user, agent question, user, agent answer


def test_run_loop_answers_questions(stack):
    questions = []
    t = client(stack).run("loan of 100000 at 10%", answer_fn=lambda q: (questions.append(q), "for 2 years")[1])
    assert t["status"]["state"] == T.COMPLETED and len(questions) == 1


def test_run_hands_back_waiting_task_when_nobody_can_answer(stack):
    t = client(stack).run("loan of 100000 at 10%")
    assert t["status"]["state"] == T.INPUT_REQUIRED


def test_cannot_continue_a_finished_task(stack):
    c = client(stack)
    t = c.send("loan of 1000 at 5% for 1 year")
    assert t["status"]["state"] == T.COMPLETED
    with pytest.raises(A2AError) as e:
        c.send("and more", task_id=t["id"])
    assert e.value.code == T.INVALID_PARAMS


def test_get_task(stack):
    c = client(stack)
    t = c.send("loan of 1000 at 5% for 1 year")
    assert c.get(t["id"])["status"]["state"] == T.COMPLETED


def test_other_callers_task_looks_like_it_does_not_exist(stack):
    stack.settings.clients["intruder"] = ClientRecord(sha256_hex("i" * 30), ["a2a:invoke"], customer_id="cust-2002")
    t = client(stack).send("loan of 1000 at 5% for 1 year")
    from oauth_client import TokenProvider
    tp = TokenProvider(stack.settings.issuer + "/token", "intruder", "i" * 30)
    other = A2AClient(stack.settings.a2a_base, lambda: tp.get(stack.settings.a2a_url, ["a2a:invoke"]), allow_local=True)
    for call in (lambda: other.get(t["id"]), lambda: other.cancel(t["id"]), lambda: other.send("x", task_id=t["id"])):
        with pytest.raises(A2AError) as e:
            call()
        assert e.value.code == T.TASK_NOT_FOUND
    missing = pytest.raises(A2AError, other.get, "does-not-exist")
    assert missing.value.message == "task not found"                   # identical wording: ids cannot be probed


def test_missing_delegated_scope_fails_safely_without_leaking(stack):
    t = client(stack, scopes=["a2a:invoke"]).send("loan of 1000 at 5% for 1 year")      # orchestrator did not delegate tools:basic
    assert t["status"]["state"] == T.FAILED
    msg = task_text(t)
    assert "could not complete" in msg and "invalid_scope" not in msg and "Traceback" not in msg and "http" not in msg


def test_cancel_wins_the_race_against_completion():
    gate = threading.Event()
    adv = Advisor(lambda *a: {"emi": 1.0, "total_payable": 12.0, "total_interest": 0.0}, before_work=lambda: gate.wait(5))
    k = start_stack(advisor=adv)
    try:
        c = make_orchestrator_client(k.settings, ORCH)
        t = c.send("loan of 1200 at 0% for 1 year", return_immediately=True)
        assert t["status"]["state"] == T.WORKING
        assert c.cancel(t["id"])["status"]["state"] == T.CANCELED
        gate.set()                                                    # the worker now finishes and tries to write COMPLETED
        k.service.pool.shutdown(wait=True)
        final = c.get(t["id"])
        assert final["status"]["state"] == T.CANCELED and "artifacts" not in final
        with pytest.raises(A2AError) as e:
            c.cancel(t["id"])
        assert e.value.code == T.TASK_NOT_CANCELABLE
    finally:
        gate.set()
        k.stop()


def test_cannot_cancel_a_completed_task(stack):
    c = client(stack)
    t = c.send("loan of 1000 at 5% for 1 year")
    with pytest.raises(A2AError) as e:
        c.cancel(t["id"])
    assert e.value.code == T.TASK_NOT_CANCELABLE


def test_return_immediately_then_poll():
    gate = threading.Event()
    adv = Advisor(lambda *a: {"emi": 1.0, "total_payable": 12.0, "total_interest": 0.0}, before_work=lambda: gate.wait(5))
    k = start_stack(advisor=adv)
    try:
        c = make_orchestrator_client(k.settings, ORCH)
        t = c.send("loan of 1200 at 0% for 1 year", return_immediately=True)
        assert t["status"]["state"] == T.WORKING
        gate.set()
        assert c.wait(t["id"])["status"]["state"] == T.COMPLETED
    finally:
        gate.set()
        k.stop()


def test_blocking_send_gives_up_waiting_but_task_continues():
    gate = threading.Event()
    adv = Advisor(lambda *a: {"emi": 1.0, "total_payable": 12.0, "total_interest": 0.0}, before_work=lambda: gate.wait(5))
    k = start_stack(advisor=adv, blocking_timeout=0.2)
    try:
        c = make_orchestrator_client(k.settings, ORCH)
        t = c.send("loan of 1200 at 0% for 1 year")                  # not return_immediately, but the server's wait ran out
        assert t["status"]["state"] == T.WORKING
        gate.set()
        assert c.wait(t["id"])["status"]["state"] == T.COMPLETED
    finally:
        gate.set()
        k.stop()


def test_crashing_agent_becomes_failed_with_a_generic_message():
    def boom(*a):
        raise RuntimeError("database password is hunter2")
    adv = Advisor(lambda *a: {})
    adv.step = lambda *a, **kw: boom()
    k = start_stack(advisor=adv)
    try:
        t = make_orchestrator_client(k.settings, ORCH).send("loan of 1000 at 5% for 1 year")
        assert t["status"]["state"] == T.FAILED and "hunter2" not in json.dumps(t)
        assert k.a2a_audit.all()[-1]["outcome"] == "crashed"
    finally:
        k.stop()


def test_late_result_cannot_overwrite_a_terminal_state(stack):
    from a2a_server import TaskRecord
    rec = TaskRecord("o", "c")
    stack.service._move(rec, T.WORKING)
    assert stack.service._move(rec, T.FAILED) and not stack.service._move(rec, T.COMPLETED) and rec.state == T.FAILED
