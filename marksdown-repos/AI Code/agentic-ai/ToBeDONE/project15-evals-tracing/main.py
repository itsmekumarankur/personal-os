"""A small HTTP service: ask the agent a question, then look at the trace of what happened.

  POST /ask               run the agent; the response carries the trace_id (and an X-Trace-Id header)
  GET  /traces            recent traces (summary)
  GET  /traces/{id}       the full span tree as JSON, plus an ASCII waterfall
  GET  /traces/{id}/otlp  the same trace as OTLP JSON, ready to POST to a collector
  GET  /stats             counts, errors, latency p50/p95, tokens, cost over the stored traces
Set DEMO_FAKE=1 to use the fake model (no API key). Set TRACE_CONTENT=off|hash|truncate|full to control what text is stored.
"""
import os

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from agent import SupportAgent, anthropic_model_fn
from demo_fake import FakeModel
from pricing import load_pricing, trace_totals
from stats import percentile
from tracing import MemoryExporter, Tracer, extract_traceparent, render_tree, to_otlp


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def create_app(model_fn=None, tracer: Tracer | None = None) -> FastAPI:
    exporter = MemoryExporter(max_traces=int(os.environ.get("MAX_TRACES", "500")))
    tracer = tracer or Tracer([exporter], sample_rate=float(os.environ.get("TRACE_SAMPLE_RATE", "1.0")),
                              slow_ms=float(os.environ.get("TRACE_SLOW_MS", "0")) or None,
                              content=os.environ.get("TRACE_CONTENT", "truncate"))
    if tracer.exporters:
        exporter = next((e for e in tracer.exporters if isinstance(e, MemoryExporter)), exporter)
    else:
        tracer.exporters.append(exporter)
    model_name = os.environ.get("MODEL", "demo-model")
    if model_fn is None:
        model_fn = FakeModel("good") if os.environ.get("DEMO_FAKE") == "1" else anthropic_model_fn(model_name)
    agent = SupportAgent(model_fn, tracer, load_pricing(), model_name)
    app = FastAPI(title="Project 15: evals and tracing")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ask")
    def ask(req: Ask, request: Request):
        from fastapi.responses import JSONResponse
        res = agent.run(req.question, remote_parent=extract_traceparent(dict(request.headers)))
        return JSONResponse({"answer": res.answer, "finished": res.finished, "trace_id": res.trace_id},
                            headers={"X-Trace-Id": res.trace_id})

    @app.get("/traces")
    def traces(limit: int = 20):
        out = []
        for spans in reversed(exporter.all()[-max(1, min(limit, 200)):]):
            root = next((s for s in spans if s.parent_id is None or s.name == "agent.run"), spans[0])
            t = trace_totals(spans)
            out.append({"trace_id": root.trace_id, "name": root.name, "status": root.status, "duration_ms": round(root.duration_ms, 1), **t})
        return out

    @app.get("/traces/{trace_id}")
    def trace(trace_id: str):
        spans = exporter.get(trace_id)
        if spans is None:
            raise HTTPException(404, "trace not found (it may have been dropped by sampling or pushed out of the buffer)")
        return {"trace_id": trace_id, "spans": [s.to_dict() for s in spans], "waterfall": render_tree(spans)}

    @app.get("/traces/{trace_id}/otlp")
    def trace_otlp(trace_id: str):
        spans = exporter.get(trace_id)
        if spans is None:
            raise HTTPException(404, "trace not found")
        return to_otlp(spans, "project15-agent")

    @app.get("/stats")
    def stats():
        all_t = exporter.all()
        roots = [next((s for s in sp if s.name == "agent.run"), sp[0]) for sp in all_t]
        lat = [r.duration_ms for r in roots]
        totals = [trace_totals(sp) for sp in all_t]
        return {"traces": len(all_t), "errors": sum(1 for r in roots if r.status == "ERROR"),
                "latency_p50_ms": round(percentile(lat, 50), 1), "latency_p95_ms": round(percentile(lat, 95), 1),
                "input_tokens": sum(t["input_tokens"] for t in totals), "output_tokens": sum(t["output_tokens"] for t in totals),
                "cost_usd": round(sum(t["cost_usd"] for t in totals), 6)}
    return app


def app_factory():
    return create_app()
