"""Streaming events, shaped like the Anthropic Messages API stream (checked against the docs on the day I wrote this).

   message_start            a Message with empty content; usage has input + cache numbers
   content_block_start      block #index begins (text | tool_use | thinking)
   content_block_delta      text_delta | input_json_delta (a PIECE OF A JSON STRING) | thinking_delta | signature_delta
   content_block_stop       block #index is finished  <- only now is a tool_use input safe to json.loads
   message_delta            stop_reason + CUMULATIVE output_tokens
   message_stop             end
   ping                     keep-alive, can appear anywhere
   error                    can appear in the MIDDLE of a stream (e.g. overloaded_error); HTTP status was already 200
Clients must ignore event types they do not know (new ones get added).
"""
import json
from dataclasses import dataclass, field


class StreamError(Exception):
    def __init__(self, etype: str, message: str, partial: dict | None = None):
        super().__init__(f"{etype}: {message}")
        self.etype, self.message, self.partial = etype, message, partial


@dataclass
class TimedEvent:
    t: float            # seconds since the request was sent (virtual time in the fake model)
    event: dict


@dataclass
class StreamAccumulator:
    """Rebuilds the final Message from raw events. This is what an SDK 'stream helper' does for you."""
    message: dict = field(default_factory=dict)
    blocks: dict = field(default_factory=dict)          # index -> block (tool_use keeps a '_json' string while it grows)
    stop_reason: str | None = None
    usage: dict = field(default_factory=dict)
    finished: bool = False
    ignored: list = field(default_factory=list)

    def feed(self, ev: dict):
        t = ev.get("type")
        if t == "message_start":
            self.message = dict(ev["message"])
            self.usage = dict(ev["message"].get("usage", {}))
        elif t == "content_block_start":
            b = dict(ev["content_block"])
            if b["type"] == "tool_use":
                b["_json"] = ""
                b.pop("input", None)                                  # the {} in content_block_start is a placeholder, not the input
            self.blocks[ev["index"]] = b
        elif t == "content_block_delta":
            b, d = self.blocks[ev["index"]], ev["delta"]
            if d["type"] == "text_delta":
                b["text"] = b.get("text", "") + d["text"]
            elif d["type"] == "input_json_delta":
                b["_json"] += d["partial_json"]
            elif d["type"] == "thinking_delta":
                b["thinking"] = b.get("thinking", "") + d["thinking"]
            elif d["type"] == "signature_delta":
                b["signature"] = d["signature"]
            else:
                self.ignored.append(d["type"])
        elif t == "content_block_stop":
            b = self.blocks[ev["index"]]
            if b["type"] == "tool_use":
                b["input"] = json.loads(b.pop("_json") or "{}")       # NOW it is complete; before this it is a fragment
        elif t == "message_delta":
            self.stop_reason = ev["delta"].get("stop_reason", self.stop_reason)
            self.usage.update(ev.get("usage", {}))                    # cumulative: later numbers replace earlier ones
        elif t == "message_stop":
            self.finished = True
        elif t == "ping":
            pass
        elif t == "error":
            raise StreamError(ev["error"]["type"], ev["error"]["message"], self.partial())
        else:
            self.ignored.append(t)                                    # unknown event: ignore, never crash
        return self

    def partial(self) -> dict:
        """What we have so far. Text can be kept; an unfinished tool_use must be thrown away."""
        content = [dict(b) for _, b in sorted(self.blocks.items()) if b["type"] == "text" or "input" in b]
        return {"content": content, "usage": self.usage}

    def result(self) -> dict:
        if not self.finished:
            raise StreamError("incomplete_stream", "stream ended before message_stop", self.partial())
        content = [{k: v for k, v in b.items() if not k.startswith("_")} for _, b in sorted(self.blocks.items())]
        return {**self.message, "content": content, "stop_reason": self.stop_reason, "usage": self.usage}


def sse_line(ev: dict, event_id: str | None = None) -> str:
    """One event in Server-Sent-Events wire format. Blank line = end of event."""
    head = f"id: {event_id}\n" if event_id else ""
    return f"{head}event: {ev['type']}\ndata: {json.dumps(ev, separators=(',', ':'))}\n\n"
