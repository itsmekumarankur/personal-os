"""A streaming chat server (Server-Sent Events) plus a structured-extraction endpoint.

   POST /chat            -> text/event-stream.  event 'open' (stream id), then the model's events, then 'done' (usage, cost, ttft)
   GET  /chat/{id}       -> reconnect with header Last-Event-ID: replays what you missed (only if the stream was kept, see policy)
   POST /extract         -> JSON.  tool-forced output, validated twice, repaired, or 422 with every attempt shown
   GET  /metrics         -> counters:  started / completed / cancelled / errored, tokens never generated thanks to cancel, cache hit rate

Design points (each one is a real production incident somewhere):
 * PRODUCER and CONSUMER are separate. The producer calls the model and fills a buffer; the HTTP response reads the buffer.
 * on_disconnect = "cancel": the user closed the tab -> stop the producer -> stop paying for tokens nobody reads.
   on_disconnect = "keep":   let it finish so the client can reconnect (Last-Event-ID) and get the rest. Costs tokens. You choose per product.
 * heartbeat comment ': ping' every N seconds of silence, so proxies do not kill an idle-looking connection.
 * headers:  Cache-Control: no-cache,  X-Accel-Buffering: no  (nginx must not buffer),  Connection: keep-alive.
   Behind a load balancer raise the idle timeout above your longest silence and turn off response buffering, or streaming turns into "wait, then everything".
 * an 'error' event can arrive after HTTP 200 was already sent. The stream must end cleanly with an error event, not a broken connection.
"""
import asyncio
import json
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

import pricing
import structured
from cache_sim import PromptCache
from events import StreamAccumulator, sse_line
from fake_model import FakeStreamingModel

SYSTEM_PREFIX = ("You are the support assistant of a retail bank. Follow the policy below exactly. " + "Policy clause: never reveal internal notes. " * 400)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    use_cache: bool = True


class ExtractIn(BaseModel):
    text: str = Field(min_length=10, max_length=20_000)
    max_attempts: int = Field(3, ge=1, le=5)


class StreamBuffer:
    def __init__(self):
        self.events: list = []                     # (id, sse_text)
        self.done = False
        self.cond = asyncio.Condition()
        self.task: asyncio.Task | None = None
        self.consumers = 0

    async def push(self, item):
        async with self.cond:
            self.events.append(item)
            self.cond.notify_all()

    async def finish(self):
        async with self.cond:
            self.done = True
            self.cond.notify_all()


def create_app(model: FakeStreamingModel | None = None, time_scale: float = 0.02, heartbeat_s: float = 0.5, on_disconnect: str = "cancel") -> FastAPI:
    app = FastAPI(title="streaming-demo")
    t0 = time.monotonic()
    vnow = lambda: (time.monotonic() - t0) / time_scale                                   # virtual seconds, so cache TTLs behave
    model = model or FakeStreamingModel(cache=PromptCache(min_tokens=512))
    buffers: dict = {}
    m = {"started": 0, "completed": 0, "cancelled": 0, "errored": 0, "events_not_generated": 0, "cache_read": 0, "input_total": 0}
    app.state.metrics, app.state.model, app.state.buffers = m, model, buffers

    def build_request(body: ChatIn) -> dict:
        sysb = {"type": "text", "text": SYSTEM_PREFIX}
        if body.use_cache:
            sysb["cache_control"] = {"type": "ephemeral"}
        return {"model": "fake-sonnet", "max_tokens": 500, "system": [sysb], "messages": [{"role": "user", "content": body.message}], "stream": True}

    async def produce(sid: str, buf: StreamBuffer, req: dict):
        acc, n, prev, ttft = StreamAccumulator(), 0, 0.0, None
        try:
            for te in model.stream(req, now=vnow()):
                await asyncio.sleep(max(0.0, te.t - prev) * time_scale)
                prev = te.t
                if te.event["type"] == "message_start":
                    ttft = te.t
                n += 1
                await buf.push((f"{sid}:{n}", sse_line(te.event, f"{sid}:{n}")))
                if te.event["type"] == "error":
                    m["errored"] += 1
                    return
                acc.feed(te.event)
            u = acc.usage
            m["completed"] += 1
            m["cache_read"] += u.get("cache_read_input_tokens", 0)
            m["input_total"] += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            done = {"type": "done", "usage": u, "cost_usd": round(pricing.cost(u), 6), "ttft_s": round(ttft or 0, 3), "hit_rate": round(pricing.hit_rate(u), 3)}
            await buf.push((f"{sid}:{n + 1}", sse_line(done, f"{sid}:{n + 1}")))
        except asyncio.CancelledError:
            m["cancelled"] += 1
            raise
        finally:
            await buf.finish()

    async def consume(request: Request, sid: str, buf: StreamBuffer, cursor: int):
        buf.consumers += 1
        try:
            while True:
                async with buf.cond:
                    if cursor >= len(buf.events) and not buf.done:
                        try:
                            await asyncio.wait_for(buf.cond.wait(), timeout=heartbeat_s)
                        except asyncio.TimeoutError:
                            pass
                    batch, finished = buf.events[cursor:], buf.done
                if not batch and not finished:
                    yield ": ping\n\n"                                                  # heartbeat
                    if await request.is_disconnected():
                        break
                    continue
                for _, text in batch:
                    yield text
                cursor += len(batch)
                if finished and cursor >= len(buf.events):
                    return
                if await request.is_disconnected():
                    break
        finally:
            buf.consumers -= 1
            if on_disconnect == "cancel" and buf.consumers == 0 and not buf.done and buf.task:
                buf.task.cancel()                                                      # nobody is reading: stop spending

    @app.post("/chat")
    async def chat(body: ChatIn, request: Request):
        sid = uuid.uuid4().hex[:8]
        buf = StreamBuffer()
        buffers[sid] = buf
        m["started"] += 1
        await buf.push((f"{sid}:0", sse_line({"type": "open", "stream_id": sid}, f"{sid}:0")))
        buf.task = asyncio.create_task(produce(sid, buf, build_request(body)))
        return StreamingResponse(consume(request, sid, buf, 0), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})

    @app.get("/chat/{sid}")
    async def resume(sid: str, request: Request):
        buf = buffers.get(sid)
        if buf is None:
            raise HTTPException(404, "unknown or expired stream")
        last = request.headers.get("last-event-id", f"{sid}:0")
        try:
            cursor = int(last.rsplit(":", 1)[1]) + 1
        except (IndexError, ValueError):
            raise HTTPException(400, "bad Last-Event-ID")
        if buf.task and buf.task.cancelled():
            raise HTTPException(410, "stream was cancelled when the client left")
        return StreamingResponse(consume(request, sid, buf, cursor), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.post("/extract")
    async def extract(body: ExtractIn):
        try:
            res = structured.extract(lambda r: model.create(r, now=vnow()), body.text, max_attempts=body.max_attempts)
        except structured.ExtractionFailed as e:
            return JSONResponse({"error": "extraction_failed", "attempts": e.attempts}, status_code=422)
        return {"invoice": json.loads(res.value.model_dump_json()), "attempts": res.attempts, "usage": res.usage_total,
                "cost_usd": round(pricing.cost({**res.usage_total}), 6)}

    @app.get("/metrics")
    async def metrics():
        return {**m, "cache_hit_rate": round(m["cache_read"] / m["input_total"], 3) if m["input_total"] else 0.0}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def app_factory():
    return create_app(time_scale=1.0, heartbeat_s=15.0)
