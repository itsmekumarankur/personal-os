"""A fake streaming model. No network, no key. It does three jobs so you can study the plumbing:

 1. LATENCY SHAPE   time to first token (TTFT) = prefill time (depends on how many input tokens were NOT served from cache)
                    then tokens arrive at a steady rate. The numbers are invented but the SHAPE is real.
 2. EVENT SHAPE     emits the same event sequence as the real API: message_start ... content_block_delta ... message_stop,
                    with tool input arriving as small pieces of a JSON string.
 3. MISBEHAVIOUR    modes that return bad structured output so the validation / repair code has something to catch.

modes (for invoice extraction):  good | sloppy | hallucinating | flaky | stubborn
   sloppy        wrong TYPES (strings for numbers), missing field       -> caught by the SCHEMA
   hallucinating valid types but wrong VALUES (total off, invented vendor suffix) -> caught only by SEMANTIC checks
   flaky         sloppy first, correct after it is shown the validation error (what a repair loop is for)
   stubborn      repeats the same wrong answer forever (the loop must give up)
"""
import json
import re
from dataclasses import dataclass

from cache_sim import PromptCache
from events import TimedEvent
from tokens import count_text

PREFILL_BASE_MS, PREFILL_MS_PER_TOKEN, PREFILL_MS_PER_CACHED_TOKEN, DECODE_MS_PER_TOKEN = 120.0, 0.25, 0.02, 20.0


def extract_invoice(text: str) -> dict:
    inv = re.search(r"Invoice\s+(\S+?)\s+from\s+(.+?)\s+dated\s+(\d{4}-\d{2}-\d{2})", text)
    items = [{"description": d.strip(), "quantity": int(q), "unit_price": float(p)}
             for q, d, p in re.findall(r"(\d+)\s*x\s*([A-Za-z ]+?)\s*@\s*(\d+(?:\.\d+)?)", text)]
    tot = re.search(r"Total:\s*([\d.]+)\s*([A-Z]{3})", text)
    return {"invoice_no": inv.group(1), "vendor": inv.group(2), "date": inv.group(3), "currency": tot.group(2),
            "items": items, "total": float(tot.group(1))} if inv and tot else {}


def _damage(good: dict, mode: str) -> dict:
    bad = json.loads(json.dumps(good))
    if mode == "sloppy":
        bad["total"] = f"{good['total']} {good['currency']}"            # a string with a unit, not a number
        bad["items"][0]["quantity"] = str(good["items"][0]["quantity"])
        del bad["currency"]
    elif mode == "hallucinating":
        bad["total"] = round(good["total"] * 1.10, 2)                    # well-formed, plausible, WRONG
        bad["vendor"] = good["vendor"] + " Ltd"                          # not in the source text
    return bad


def _repair(good: dict, bad: dict, feedback: str) -> dict:
    """Fix exactly the fields the feedback names (a very polite model)."""
    out = json.loads(json.dumps(bad))
    for k in good:
        if re.search(rf"\b{k}\b", feedback):
            out[k] = good[k]
    for k in good:
        out.setdefault(k, good[k]) if "missing" in feedback and k in feedback else None
    return out


@dataclass
class FakeStreamingModel:
    mode: str = "good"
    cache: PromptCache | None = None
    fail_after_events: int | None = None         # inject a mid-stream overloaded_error
    chunk_chars: int = 10
    words_per_chunk: int = 2
    model_name: str = "fake-sonnet"
    calls: int = 0

    # ------------------------------------------------------------ decide what to say
    def _decide(self, request: dict) -> list:
        msgs = request["messages"]
        first_user = msgs[0]["content"] if isinstance(msgs[0]["content"], str) else " ".join(b.get("text", "") for b in msgs[0]["content"])
        tc = request.get("tool_choice") or {}
        last = msgs[-1]
        feedback = ""
        if isinstance(last["content"], list):
            for b in last["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                    feedback = str(b["content"])
        if tc.get("type") == "tool" and tc.get("name") == "record_invoice":
            good = extract_invoice(first_user)
            if self.mode == "good":
                out = good
            elif self.mode == "flaky":
                out = _damage(good, "sloppy") if not feedback else good
            elif self.mode == "stubborn":
                out = _damage(good, "sloppy")
            elif self.mode in ("sloppy", "hallucinating"):
                bad = _damage(good, self.mode)
                out = _repair(good, bad, feedback) if feedback else bad
            else:
                out = good
            return [{"type": "tool_use", "id": f"toolu_{self.calls:04d}", "name": "record_invoice", "input": out}]
        m = re.search(r"weather in ([A-Za-z ]+)", first_user, re.I)
        if m and any(t["name"] == "get_weather" for t in request.get("tools", [])) and not (isinstance(last["content"], list)):
            return [{"type": "text", "text": "Let me check. "},
                    {"type": "tool_use", "id": f"toolu_{self.calls:04d}", "name": "get_weather", "input": {"location": m.group(1).strip()}}]
        words = ("Streaming sends the answer as it is written so the reader starts reading after the first few words instead of waiting "
                 "for the whole reply. The total time is the same but the waiting feels much shorter. ").split()
        n = int(re.search(r"(\d+) words", first_user).group(1)) if re.search(r"(\d+) words", first_user) else 40
        text = " ".join((words * (n // len(words) + 1))[:n])
        return [{"type": "text", "text": text}]

    # ------------------------------------------------------------ the stream
    def stream(self, request: dict, now: float = 0.0):
        """Yields TimedEvent. t is virtual seconds after the request was sent."""
        self.calls += 1
        content = self._decide(request)
        out_tokens = sum(count_text(b.get("text", "")) + count_text(json.dumps(b.get("input", {}))) for b in content)
        # --- prefill time depends on what the cache could NOT serve
        usage = {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
        if self.cache is not None:
            # entries written by THIS request become readable when the response starts (t = ttft), so commit_at = now + ttft.
            # We need usage first to know ttft, so process() with a provisional commit time and then fix the entries' availability.
            before = set(self.cache.entries)
            usage = self.cache.process(request, now, commit_at=now + 10_000)
        else:
            from cache_sim import flatten
            usage["input_tokens"] = sum(n for _, _, n, _ in flatten(request))
        prefill_ms = PREFILL_BASE_MS + PREFILL_MS_PER_TOKEN * (usage["input_tokens"] + usage["cache_creation_input_tokens"]) \
            + PREFILL_MS_PER_CACHED_TOKEN * usage["cache_read_input_tokens"]
        ttft = prefill_ms / 1000
        if self.cache is not None:
            for k in set(self.cache.entries) - before:
                self.cache.entries[k].available_at = now + ttft                 # readable once the first response begins
        t = ttft
        msg = {"id": f"msg_{self.calls:06d}", "type": "message", "role": "assistant", "content": [], "model": self.model_name,
               "stop_reason": None, "stop_sequence": None, "usage": {**usage, "output_tokens": 1}}
        events = [TimedEvent(t, {"type": "message_start", "message": msg})]
        emitted = 0
        step = DECODE_MS_PER_TOKEN / 1000
        for i, b in enumerate(content):
            if b["type"] == "text":
                events.append(TimedEvent(t, {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}}))
                words = b["text"].split(" ")
                for j in range(0, len(words), self.words_per_chunk):
                    piece = " ".join(words[j:j + self.words_per_chunk]) + (" " if j + self.words_per_chunk < len(words) else "")
                    t += step * count_text(piece)
                    emitted += count_text(piece)
                    events.append(TimedEvent(t, {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": piece}}))
            else:
                events.append(TimedEvent(t, {"type": "content_block_start", "index": i,
                                             "content_block": {"type": "tool_use", "id": b["id"], "name": b["name"], "input": {}}}))
                raw = json.dumps(b["input"])
                for j in range(0, len(raw), self.chunk_chars):
                    t += step * 2
                    emitted += 2
                    events.append(TimedEvent(t, {"type": "content_block_delta", "index": i,
                                                 "delta": {"type": "input_json_delta", "partial_json": raw[j:j + self.chunk_chars]}}))
            events.append(TimedEvent(t, {"type": "content_block_stop", "index": i}))
        stop = "tool_use" if any(b["type"] == "tool_use" for b in content) else "end_turn"
        events.append(TimedEvent(t, {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": out_tokens}}))
        events.append(TimedEvent(t, {"type": "message_stop"}))
        for n, ev in enumerate(events):
            if self.fail_after_events is not None and n == self.fail_after_events:
                yield TimedEvent(ev.t, {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}})
                return
            yield ev

    def create(self, request: dict, now: float = 0.0) -> dict:
        """Non-streaming call: same content, but you only see it at the end (t = last event)."""
        from events import StreamAccumulator
        acc, last_t = StreamAccumulator(), now
        for te in self.stream(request, now):
            acc.feed(te.event)
            last_t = te.t
        msg = acc.result()
        msg["_latency_s"] = last_t
        return msg
