"""Reading Server-Sent Events by hand, so you see the wire format.
  field lines:  id: / event: / data: / retry: / ': comment' (comments are keep-alives, ignore them). A blank line ends one event.
  'data:' can repeat; the pieces are joined with newlines."""
import json
import time

import httpx


def parse_sse(lines):
    ev = {"id": None, "event": "message", "data": []}
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line == "":
            if ev["data"]:
                yield {"id": ev["id"], "event": ev["event"], "data": "\n".join(ev["data"])}
            ev = {"id": None, "event": "message", "data": []}
        elif line.startswith(":"):
            continue
        else:
            field, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value
            if field == "data":
                ev["data"].append(value)
            elif field in ("id", "event"):
                ev[field] = value


def stream_chat(url: str, body: dict, last_event_id: str | None = None, stop_after: int | None = None, timeout: float = 30.0):
    """Yields (seconds_since_start, sse_event). stop_after=N closes the connection early (a user closing the tab)."""
    headers = {"Accept": "text/event-stream"}
    if last_event_id:
        headers["Last-Event-ID"] = last_event_id
    t0, n = time.perf_counter(), 0
    with httpx.Client(timeout=timeout) as c:
        with c.stream("POST", url, json=body, headers=headers) as r:
            r.raise_for_status()
            for ev in parse_sse(r.iter_lines()):
                n += 1
                yield time.perf_counter() - t0, ev
                if stop_after and n >= stop_after:
                    return


def data_of(ev: dict) -> dict:
    return json.loads(ev["data"])
