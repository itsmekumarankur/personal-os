"""The A2A agent server: an agent card (who am I, what can I do, how do I authenticate) and a JSON-RPC endpoint.

  GET  /.well-known/agent-card.json    public. Anyone may read the card. It must contain no secrets.
  POST /a2a                            JSON-RPC 2.0, needs a bearer token whose audience is THIS endpoint and scope a2a:invoke

Task life (the heart of A2A): a request becomes a TASK that lives on, with a state you can poll.
      SUBMITTED -> WORKING -> COMPLETED
                      |   \\-> FAILED
                      |-> INPUT_REQUIRED --(caller answers, same task id)--> WORKING
                      \\-> CANCELED (caller asked)          REJECTED (agent will not do this)
Terminal states never change again. A late 'completed' must not overwrite a 'canceled' (checked under a lock).
"""
import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import anyio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import a2a_types as T
from advisor import Advisor
from audit import AuditLog
from config import S_A2A, Settings
from propagation import new_traceparent, trace_id_of
from resource_auth import JwtVerifier
from tokens import TokenError, scopes_of

MAX_BODY = 64 * 1024
MAX_TEXT = 4000


class TaskRecord:
    def __init__(self, owner: str, context_id: str):
        self.id, self.context_id, self.owner = uuid.uuid4().hex, context_id, owner
        self.state, self.status_message = T.SUBMITTED, None
        self.artifacts, self.history, self.memory = [], [], {}
        self.lock, self.settled = threading.RLock(), threading.Event()

    def to_task(self, history_length: int | None = None) -> dict:
        with self.lock:
            hist = self.history if history_length is None else self.history[-history_length:] if history_length > 0 else []
            t = {"id": self.id, "contextId": self.context_id,
                 "status": {"state": self.state, "timestamp": T.now_iso(), **({"message": self.status_message} if self.status_message else {})}}
            if self.artifacts:
                t["artifacts"] = list(self.artifacts)
            if hist:
                t["history"] = list(hist)
            return t


class A2AService:
    def __init__(self, settings: Settings, advisor: Advisor, audit: AuditLog | None = None, blocking_timeout: float = 10.0, workers: int = 4):
        self.settings, self.advisor = settings, advisor
        self.audit = audit or AuditLog(settings.audit_path)
        self.tasks: dict = {}
        self.blocking_timeout = blocking_timeout
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self._lock = threading.Lock()

    # ---------- state machine
    def _move(self, rec: TaskRecord, new: str, message: dict | None = None, artifacts: list | None = None) -> bool:
        with rec.lock:
            if new not in T.ALLOWED[rec.state]:
                return False                                              # e.g. COMPLETED after CANCELED is simply ignored
            rec.state = new
            if message is not None:
                rec.status_message = message
                rec.history.append(message)
            if artifacts:
                rec.artifacts.extend(artifacts)
            if new == T.WORKING:
                rec.settled.clear()
            else:
                rec.settled.set()                                         # terminal or waiting for the caller
            return True

    # ---------- methods
    def send_message(self, params: dict, owner: str, token: str, traceparent: str) -> dict:
        msg = params.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "user" or not isinstance(msg.get("parts"), list) or not msg["parts"]:
            raise T.RpcError(T.INVALID_PARAMS, "message needs role 'user' and at least one part")
        if len(msg["parts"]) > 5:
            raise T.RpcError(T.INVALID_PARAMS, "too many parts")
        text = " ".join(T.part_text(p) for p in msg["parts"]).strip()
        if not text or len(text) > MAX_TEXT:
            raise T.RpcError(T.INVALID_PARAMS, f"text must be 1 to {MAX_TEXT} characters")
        cfg = params.get("configuration") or {}
        task_id = msg.get("taskId")
        if task_id:
            rec = self._get(task_id, owner)
            with rec.lock:
                if rec.state != T.INPUT_REQUIRED:
                    raise T.RpcError(T.INVALID_PARAMS, f"task is {rec.state.removeprefix('TASK_STATE_').lower()}, not waiting for input")
                rec.history.append(msg)
                self._move(rec, T.WORKING)
        else:
            rec = TaskRecord(owner, msg.get("contextId") or uuid.uuid4().hex)
            rec.history.append(msg)
            with self._lock:
                self.tasks[rec.id] = rec
            self._move(rec, T.WORKING)
        self.pool.submit(self._work, rec, text, token, new_traceparent(traceparent))
        if not cfg.get("returnImmediately"):
            rec.settled.wait(self.blocking_timeout)                       # default: wait for done or waiting-for-input
        return {"task": rec.to_task(cfg.get("historyLength"))}

    def _work(self, rec: TaskRecord, text: str, token: str, traceparent: str):
        try:
            res = self.advisor.step(rec.memory, text, token, traceparent)
            reply = T.make_message("agent", res.text, rec.context_id, rec.id)
            self._move(rec, res.state, reply, res.artifacts)
            outcome = res.state.removeprefix("TASK_STATE_").lower()
        except Exception:
            self._move(rec, T.FAILED, T.make_message("agent", "Something went wrong on my side.", rec.context_id, rec.id))
            outcome = "crashed"
        self.audit.record(service="a2a", event="task_step", client=rec.owner, task=rec.id, outcome=outcome, trace=trace_id_of(traceparent))

    def _get(self, task_id, owner: str) -> TaskRecord:
        rec = self.tasks.get(task_id) if isinstance(task_id, str) else None
        if rec is None or rec.owner != owner:                            # someone else's task looks exactly like a missing one
            raise T.RpcError(T.TASK_NOT_FOUND, "task not found")
        return rec

    def get_task(self, params: dict, owner: str) -> dict:
        return self._get(params.get("id"), owner).to_task(params.get("historyLength"))

    def cancel_task(self, params: dict, owner: str) -> dict:
        rec = self._get(params.get("id"), owner)
        if not self._move(rec, T.CANCELED, T.make_message("agent", "Canceled at your request.", rec.context_id, rec.id)):
            raise T.RpcError(T.TASK_NOT_CANCELABLE, f"task is already {rec.state.removeprefix('TASK_STATE_').lower()}")
        return rec.to_task()

    # ---------- JSON-RPC envelope
    def handle_rpc(self, raw: bytes, owner: str, token: str, traceparent: str) -> dict:
        try:
            req = json.loads(raw)
        except ValueError:
            return T.rpc_error(None, T.PARSE_ERROR, "invalid JSON")
        if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or not isinstance(req.get("method"), str):
            return T.rpc_error(req.get("id") if isinstance(req, dict) else None, T.INVALID_REQUEST, "not a JSON-RPC 2.0 request")
        rid, method, params = req.get("id"), req["method"], req.get("params", {})
        if not isinstance(params, dict):
            return T.rpc_error(rid, T.INVALID_PARAMS, "params must be an object")
        try:
            if method == "SendMessage":
                result = self.send_message(params, owner, token, traceparent)
            elif method == "GetTask":
                result = self.get_task(params, owner)
            elif method == "CancelTask":
                result = self.cancel_task(params, owner)
            elif method in T.UNSUPPORTED_METHODS:
                raise T.RpcError(T.UNSUPPORTED_OPERATION, f"{method} is not supported by this agent (see the agent card capabilities)")
            else:
                raise T.RpcError(T.METHOD_NOT_FOUND, f"unknown method {method}")
        except T.RpcError as e:
            return T.rpc_error(rid, e.code, e.message, e.data)
        return T.rpc_result(rid, result)


def _unauth(status: int, error: str, desc: str, base: str) -> JSONResponse:
    return JSONResponse({"error": error, "error_description": desc}, status_code=status,
                        headers={"WWW-Authenticate": f'Bearer error="{error}", error_description="{desc}", resource="{base}"'})


def create_a2a_app(settings: Settings, verifier: JwtVerifier, service: A2AService) -> Starlette:
    async def card(request):
        return JSONResponse(T.agent_card(settings.a2a_url, settings.issuer))

    async def rpc(request: Request):
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return _unauth(401, "invalid_token", "Authentication required", settings.a2a_url)
        token = auth[7:]
        try:
            claims = verifier.check(token)
        except TokenError as e:
            return _unauth(401, "invalid_token", e.code, settings.a2a_url)
        if S_A2A not in scopes_of(claims):
            return _unauth(403, "insufficient_scope", f"Required scope: {S_A2A}", settings.a2a_url)
        body = await request.body()
        if len(body) > MAX_BODY:
            return JSONResponse(T.rpc_error(None, T.INVALID_REQUEST, "request too large"), status_code=413)
        tp = request.headers.get("traceparent", "")
        out = await anyio.to_thread.run_sync(service.handle_rpc, body, claims["sub"], token, tp)
        return JSONResponse(out)

    async def health(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/.well-known/agent-card.json", card), Route("/a2a", rpc, methods=["POST"]), Route("/health", health)])
    app.state.service = service
    return app
