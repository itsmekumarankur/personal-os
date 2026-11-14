"""Logs, metrics and request ids.

Logs are one JSON object per line, so CloudWatch Logs Insights (or any log tool) can filter on fields.
Customer messages and model answers are NOT logged: only sizes, ids, tool names and outcomes.
Metrics use the Prometheus text format at /metrics.
"""
import json
import logging
import re
import uuid
from contextvars import ContextVar

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def new_request_id(incoming: str | None) -> str:
    """Accept a caller's X-Request-ID only if it is harmless; otherwise make one."""
    return incoming if incoming and SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or request_id_var.get(),
        }
        entry.update(getattr(record, "ctx", {}))
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


log = logging.getLogger("platform")


def log_event(event: str, level: int = logging.INFO, request_id: str | None = None, **fields) -> None:
    log.log(level, event, extra={"ctx": {"event": event, **fields}, "request_id": request_id})


REGISTRY = CollectorRegistry()
REQUESTS = Counter("agent_http_requests_total", "HTTP requests", ["endpoint", "status"], registry=REGISTRY)
LATENCY = Histogram("agent_http_request_seconds", "HTTP request time", ["endpoint"], registry=REGISTRY,
                    buckets=(0.05, 0.25, 1, 2.5, 5, 10, 30, 60))
TOOL_CALLS = Counter("agent_tool_calls_total", "Tool calls by outcome", ["tool", "outcome"], registry=REGISTRY)
GUARDRAIL = Counter("agent_guardrail_events_total", "Guardrail events", ["kind"], registry=REGISTRY)
APPROVALS = Counter("agent_approvals_total", "Approval events", ["event"], registry=REGISTRY)
TOKENS = Counter("agent_llm_tokens_total", "Model tokens", ["direction"], registry=REGISTRY)
LLM_ERRORS = Counter("agent_llm_errors_total", "Failed model calls", registry=REGISTRY)
PENDING = Gauge("agent_pending_approvals", "Approvals waiting for a human", registry=REGISTRY)


def render_metrics() -> bytes:
    return generate_latest(REGISTRY)
