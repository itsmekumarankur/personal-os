"""A2A (agent-to-agent) message shapes, in ONE file so a spec change touches one place.

What I confirmed against the published specification (version 1.0.0 at a2a-protocol.org when I checked):
  JSON-RPC methods  SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, GetExtendedAgentCard
  Task states       TASK_STATE_WORKING, _INPUT_REQUIRED, _AUTH_REQUIRED, _COMPLETED, _FAILED, _CANCELED, _REJECTED (and _SUBMITTED)
  Message fields    role, parts, messageId, contextId (and taskId when continuing a task)
  SendMessage       params {message, configuration{returnImmediately, historyLength}}; waits for a finished or interrupted state by default
What I could NOT confirm and took from earlier versions or my own judgement: the agent-card path /.well-known/agent-card.json,
the exact Part and Artifact JSON shapes, the numeric JSON-RPC error codes for A2A errors, and the SendMessage result wrapper.
This is a TEACHING SUBSET, not a certified implementation. Check the spec (and an official SDK) before you interoperate with anyone.
"""
import time
import uuid

# ---- task states
SUBMITTED, WORKING = "TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"
INPUT_REQUIRED, AUTH_REQUIRED = "TASK_STATE_INPUT_REQUIRED", "TASK_STATE_AUTH_REQUIRED"
COMPLETED, FAILED, CANCELED, REJECTED = "TASK_STATE_COMPLETED", "TASK_STATE_FAILED", "TASK_STATE_CANCELED", "TASK_STATE_REJECTED"
TERMINAL = {COMPLETED, FAILED, CANCELED, REJECTED}
INTERRUPTED = {INPUT_REQUIRED, AUTH_REQUIRED}                    # the agent is waiting for the CALLER
ALLOWED = {                                                      # who may move where
    SUBMITTED: {WORKING, REJECTED, CANCELED, FAILED},
    WORKING: {INPUT_REQUIRED, AUTH_REQUIRED, COMPLETED, FAILED, CANCELED, REJECTED},
    INPUT_REQUIRED: {WORKING, CANCELED, FAILED},
    AUTH_REQUIRED: {WORKING, CANCELED, FAILED},
    COMPLETED: set(), FAILED: set(), CANCELED: set(), REJECTED: set(),
}

# ---- JSON-RPC errors
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = -32700, -32600, -32601, -32602, -32603
TASK_NOT_FOUND, TASK_NOT_CANCELABLE, PUSH_NOT_SUPPORTED, UNSUPPORTED_OPERATION = -32001, -32002, -32003, -32004

METHODS = {"SendMessage", "GetTask", "CancelTask"}
UNSUPPORTED_METHODS = {"SendStreamingMessage", "ListTasks", "SubscribeToTask", "GetExtendedAgentCard"}


class RpcError(Exception):
    def __init__(self, code: int, message: str, data=None):
        super().__init__(message)
        self.code, self.message, self.data = code, message, data


def rpc_result(id_, result) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def rpc_error(id_, code, message, data=None) -> dict:
    e = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": e}


def text_part(t: str) -> dict:
    return {"text": t}


def data_part(d: dict) -> dict:
    return {"data": d}


def part_text(part: dict) -> str:
    """Tolerant reader: accepts {'text': ..} and the older {'kind':'text','text': ..}."""
    return part.get("text", "") if isinstance(part, dict) else ""


def make_message(role: str, text: str, context_id=None, task_id=None, data: dict | None = None) -> dict:
    parts = [text_part(text)] + ([data_part(data)] if data else [])
    m = {"messageId": uuid.uuid4().hex, "role": role, "parts": parts}
    if context_id:
        m["contextId"] = context_id
    if task_id:
        m["taskId"] = task_id
    return m


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def agent_card(a2a_url: str, issuer: str) -> dict:
    return {
        "name": "Loan Advisor", "description": "Works out loan instalments (EMI). Asks for missing details. Cannot see accounts or move money.",
        "version": "1.0.0", "provider": {"organization": "Demo Bank"},
        "supportedInterfaces": [{"url": a2a_url, "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
        "url": a2a_url,                                           # older clients look for this
        "capabilities": {"streaming": False, "pushNotifications": False, "extendedAgentCard": False},
        "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain", "application/json"],
        "skills": [{"id": "emi-advice", "name": "EMI advice", "tags": ["loan", "emi"],
                    "description": "Monthly instalment, total interest and total payable for a loan of a given amount, rate and tenure.",
                    "examples": ["I want a loan of 500000 at 9% for 5 years", "What is the EMI on 200000 at 12% over 24 months?"]}],
        "securitySchemes": {"oauth2": {"type": "oauth2", "flows": {"clientCredentials": {"tokenUrl": issuer + "/token",
                                                                                         "scopes": {"a2a:invoke": "send tasks to this agent"}}}}},
        "security": [{"oauth2": ["a2a:invoke"]}],
    }
