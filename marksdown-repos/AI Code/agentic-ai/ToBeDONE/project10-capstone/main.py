import logging
import re
import time
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

import agent
import guardrails
from bank import Bank
from config import Principal, Settings, load_settings
from observability import (GUARDRAIL, LATENCY, PENDING, REQUESTS, log_event, new_request_id,
                           render_metrics, request_id_var, setup_logging)
from ratelimit import RateLimiter
from store import Store

CONV_ID = r"^[a-f0-9]{32}$"
BLOCKED_REPLY = ("I can't help with that request. I can help with your account, transactions, "
                 "loan calculations, card freezes and refund requests.")


class ChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, pattern=CONV_ID)
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    conversation_id: str | None
    status: str                       # active | awaiting_approval | blocked
    reply: str
    approval_id: str | None = None


class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    note: str = Field(default="", max_length=300)


def create_app(settings: Settings | None = None, configure_logging: bool = True) -> FastAPI:
    settings = settings or load_settings()           # stops the service at start-up if the settings are bad
    if configure_logging:
        setup_logging(settings.log_level)

    docs = {} if settings.enable_docs else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="Agentic AI — Project 10: Capstone platform", **docs)
    deps = agent.Deps(settings, Store(settings.db_path), Bank())
    limiter = RateLimiter(settings.rate_limit_per_min)
    app.state.deps = deps
    PENDING.set(deps.store.count_pending())

    # ---------- request id, timing, metrics, access log ----------
    @app.middleware("http")
    async def observe(request: Request, call_next):
        rid = new_request_id(request.headers.get("x-request-id"))
        token = request_id_var.set(rid)
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001 - never show internals to the caller
            logging.getLogger("platform").exception("unhandled error")
            response = JSONResponse({"error": "internal_error", "request_id": rid}, status_code=500)
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        endpoint = route.path if route is not None else "unmatched"   # a template, never the raw URL
        REQUESTS.labels(endpoint, str(response.status_code)).inc()
        LATENCY.labels(endpoint).observe(elapsed)
        response.headers["X-Request-ID"] = rid
        log_event("http_request", request_id=rid, method=request.method, path=endpoint,
                  status=response.status_code, ms=round(elapsed * 1000),
                  principal=getattr(request.state, "principal_id", None))
        request_id_var.reset(token)
        return response

    # ---------- authentication, authorization, rate limit ----------
    def require(role: str):
        def dependency(request: Request, authorization: str | None = Header(default=None)) -> Principal:
            token = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else ""
            principal = settings.authenticate(token) if token else None
            if principal is None:
                GUARDRAIL.labels("auth_failed").inc()
                log_event("auth_failed", logging.WARNING, request.state.request_id)
                raise HTTPException(401, "Missing or invalid API key", headers={"WWW-Authenticate": "Bearer"})
            request.state.principal_id = principal.id
            if principal.role != role:
                GUARDRAIL.labels("forbidden").inc()
                raise HTTPException(403, "This key cannot use this endpoint")
            if role == "customer":
                allowed, retry = limiter.check(principal.id)
                if not allowed:
                    GUARDRAIL.labels("rate_limited").inc()
                    raise HTTPException(429, "Too many requests", headers={"Retry-After": str(retry)})
            return principal
        return dependency

    customer, approver, ops = require("customer"), require("approver"), require("ops")

    def texts(conv: dict) -> list[dict]:
        out = []
        for m in conv["messages"]:
            if isinstance(m["content"], str):
                out.append({"role": m["role"], "text": m["content"]})
            elif m["role"] == "assistant":
                t = "\n".join(b["text"] for b in m["content"] if b["type"] == "text").strip()
                if t:
                    out.append({"role": "assistant", "text": t})
        return out

    def approval_view(a: dict) -> dict:
        conv = deps.store.get_conversation(a["conversation_id"])
        last_msg = next((t["text"] for t in reversed(texts(conv)) if t["role"] == "user"), "") if conv else ""
        return {"id": a["id"], "status": a["status"], "tool": a["tool"], "args": a["args"],
                "description": a["description"], "customer": a["requested_by"],
                "customer_message": last_msg, "decided_by": a["decided_by"], "note": a["note"],
                "result": a["result"], "created": a["created"], "decided": a["decided"]}

    # ---------- public endpoints ----------
    @app.get("/health")
    def health():
        return {"status": "ok"}                       # liveness: no dependencies, so a slow database never kills the task

    @app.get("/ready")
    def ready():
        try:
            deps.store.ping()
        except Exception:  # noqa: BLE001
            raise HTTPException(503, "database not ready")
        return {"status": "ready"}

    # ---------- customers ----------
    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, request: Request, principal: Principal = Depends(customer)):
        rid = request.state.request_id
        text, kinds = guardrails.redact(req.message)           # the model and the database never see card numbers
        for kind in kinds:
            agent.guard_event(deps, f"input_{kind}", rid, principal.id)
        if guardrails.looks_like_injection(text):
            agent.guard_event(deps, "prompt_injection", rid, principal.id)
            if settings.input_guard == "block":
                return ChatResponse(conversation_id=req.conversation_id, status="blocked", reply=BLOCKED_REPLY)

        conv_id = req.conversation_id
        if conv_id:
            conv = deps.store.get_conversation(conv_id)
            if conv is None or conv["customer_id"] != principal.id:
                raise HTTPException(404, "Conversation not found")      # same answer for "missing" and "not yours"
            if conv["status"] != "active":
                raise HTTPException(409, "This conversation is waiting for a human decision")
        else:
            conv_id = deps.store.create_conversation(principal.id)

        try:
            result = agent.converse(deps, principal, conv_id, text, rid)
        except agent.BudgetExceeded:
            raise HTTPException(429, "Daily usage limit reached", headers={"Retry-After": "3600"})
        except agent.ModelUnavailable:
            raise HTTPException(502, "The assistant is temporarily unavailable")
        deps.store.audit(rid, principal.id, "chat", {"conversation_id": conv_id, "status": result["status"],
                                                     "chars": len(text)})
        return ChatResponse(conversation_id=conv_id, **result)

    @app.get("/v1/conversations/{conversation_id}")
    def conversation(conversation_id: str, principal: Principal = Depends(customer)):
        conv = deps.store.get_conversation(conversation_id) if re.match(CONV_ID, conversation_id) else None
        if conv is None or conv["customer_id"] != principal.id:
            raise HTTPException(404, "Conversation not found")
        return {"conversation_id": conv["id"], "status": conv["status"],
                "approval_id": conv["pending_approval_id"] if conv["status"] == "awaiting_approval" else None,
                "messages": texts(conv)}

    # ---------- human reviewers ----------
    @app.get("/v1/approvals")
    def approvals(status: Literal["pending", "approved", "rejected", "failed"] | None = "pending",
                  principal: Principal = Depends(approver)):
        return [approval_view(a) for a in deps.store.list_approvals(status)]

    @app.post("/v1/approvals/{approval_id}/decision")
    def decision(approval_id: str, body: DecisionRequest, request: Request, background: BackgroundTasks,
                 principal: Principal = Depends(approver)):
        rid = request.state.request_id
        try:
            result = agent.decide(deps, approval_id, body.decision, body.note, principal, rid)
        except agent.NotFound:
            raise HTTPException(404, "Approval not found")
        except agent.AlreadyDecided:
            raise HTTPException(409, "This approval has already been decided")
        # The model's follow-up message runs after the reviewer gets their answer.
        background.add_task(agent.continue_after_decision, deps, approval_id, rid)
        return approval_view(result)

    # ---------- operations ----------
    @app.get("/v1/audit")
    def audit(limit: int = 100, principal: Principal = Depends(ops)):
        return deps.store.list_audit(max(1, min(limit, 500)))

    @app.get("/metrics")
    def metrics(principal: Principal = Depends(ops)):
        return Response(render_metrics(), media_type=CONTENT_TYPE_LATEST)

    return app
