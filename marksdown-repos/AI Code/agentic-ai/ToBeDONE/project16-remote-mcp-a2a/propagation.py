"""W3C traceparent, so one user request can be followed across the orchestrator, the A2A agent and the MCP server.
   traceparent: 00-<32 hex trace id>-<16 hex span id>-01      (same format as Project 15)"""
import re
import secrets

_TP = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def new_traceparent(parent: str | None = None) -> str:
    """A new span id inside the same trace (or a brand new trace when there is no valid parent)."""
    m = _TP.match((parent or "").strip())
    trace = m.group(1) if m and m.group(1) != "0" * 32 else secrets.token_hex(16)
    return f"00-{trace}-{secrets.token_hex(8)}-01"


def trace_id_of(traceparent: str | None) -> str | None:
    m = _TP.match((traceparent or "").strip())
    return m.group(1) if m else None
