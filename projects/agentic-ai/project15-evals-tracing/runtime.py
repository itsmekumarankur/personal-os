"""Builds (agent, tracer, exporter) for a run. 'fake-*' modes need no API key."""
import os

from agent import SupportAgent, anthropic_model_fn
from demo_fake import FakeModel, HeuristicJudge
from pricing import load_pricing
from tracing import Clock, MemoryExporter, Tracer

MODES = ("fake-good", "fake-degraded", "fake-chatty", "anthropic")


def make_runtime_factory(mode: str, content: str = "truncate", model_name: str | None = None):
    pricing = load_pricing()
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")

    def factory():
        exporter = MemoryExporter(max_traces=5)
        if mode.startswith("fake-"):
            clock = Clock()
            tracer = Tracer([exporter], content=content, clock=clock)
            model_fn = FakeModel(mode.split("-", 1)[1], clock=clock)
            return SupportAgent(model_fn, tracer, pricing, model_name or "demo-model"), tracer, exporter
        name = model_name or os.environ.get("MODEL", "demo-model")
        tracer = Tracer([exporter], content=content)
        return SupportAgent(anthropic_model_fn(name), tracer, pricing, name), tracer, exporter
    return factory


def make_judge(kind: str):
    if kind == "none":
        return None
    if kind == "heuristic":
        return HeuristicJudge()
    if kind == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        model = os.environ.get("JUDGE_MODEL", os.environ.get("MODEL", "claude-sonnet-4-5"))

        def call(prompt):
            r = client.messages.create(model=model, max_tokens=300, temperature=0, messages=[{"role": "user", "content": prompt}])
            return r.content[0].text
        return call
    raise ValueError("judge must be none, heuristic or anthropic")
