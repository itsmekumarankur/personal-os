"""AGENT LOOP WITH HANDOFFS AND GUARDRAILS (the OpenAI-Agents-SDK / multi-agent idea).

Two ways frameworks let several agents cooperate. Know which you are using:

  HANDOFF       control TRANSFERS. The triage agent calls transfer_to_refunds; from then on the refunds agent is the one talking to the user,
                with its own instructions and its own (smaller) tool list. One active agent at a time.
  AGENT-AS-TOOL control STAYS. A manager agent calls a specialist like a function and gets a result back (Project 6/13 sub-agents).

Handoff is implemented here the way it really works: it is just a TOOL CALL whose effect is 'change which agent runs next'. No magic.

Guardrails are checks that run OUTSIDE the model: input guardrails before the first model call, output guardrails on the final answer, and a tool
hook before each tool call. They are code, so the model cannot talk its way past them.
"""
import json
from dataclasses import dataclass, field
from typing import Callable

from .trace import Tracer


class GuardrailTripped(Exception):
    def __init__(self, where: str, reason: str):
        super().__init__(f"{where}: {reason}")
        self.where, self.reason = where, reason


@dataclass
class Agent:
    name: str
    instructions: str
    tools: dict = field(default_factory=dict)            # name -> python callable(**kwargs) -> str
    handoffs: list = field(default_factory=list)         # other Agent objects this one may transfer to

    def tool_defs(self) -> list:
        defs = [{"name": n, "description": (f.__doc__ or n).strip().split("\n")[0], "input_schema": {"type": "object"}} for n, f in self.tools.items()]
        defs += [{"name": f"transfer_to_{a.name}", "description": f"Hand the conversation to the {a.name} agent.", "input_schema": {"type": "object"}} for a in self.handoffs]
        return defs


@dataclass
class RunOutput:
    status: str                                           # done | blocked | max_turns | handoff_loop
    final_text: str = ""
    last_agent: str = ""
    turns: int = 0
    handoff_path: list = field(default_factory=list)      # ['triage', 'refunds']
    blocked_by: str | None = None
    messages: list = field(default_factory=list)
    denied_tool_calls: list = field(default_factory=list)


def run_agents(start: Agent, user_input: str, model: Callable, *, input_guardrails=(), output_guardrails=(), before_tool=(), on_handoff=(),
               max_turns: int = 12, max_handoffs: int = 4, tracer: Tracer | None = None) -> RunOutput:
    """model(agent, messages) -> list of content blocks ({'type':'text'|'tool_use', ...}). The agent object tells the model which instructions/tools apply."""
    tracer = tracer or Tracer()
    out = RunOutput("done", last_agent=start.name, handoff_path=[start.name])
    messages = [{"role": "user", "content": user_input}]
    out.messages = messages
    active = start
    with tracer.span(f"run start={start.name}", "run"):
        try:
            for g in input_guardrails:
                with tracer.span(getattr(g, "__name__", "guardrail"), "guardrail", where="input"):
                    reason = g(user_input)
                if reason:
                    raise GuardrailTripped("input:" + getattr(g, "__name__", "guardrail"), reason)
        except GuardrailTripped as e:
            out.status, out.blocked_by, out.final_text = "blocked", e.where, "Sorry, I can't help with that request."
            return out
        for turn in range(1, max_turns + 1):
            out.turns = turn
            with tracer.span(f"model:{active.name}", "model", turn=turn):
                content = model(active, messages)
            messages.append({"role": "assistant", "content": content})
            uses = [b for b in content if b["type"] == "tool_use"]
            if not uses:
                text = "".join(b.get("text", "") for b in content if b["type"] == "text")
                for g in output_guardrails:
                    with tracer.span(getattr(g, "__name__", "guardrail"), "guardrail", where="output"):
                        reason = g(text)
                    if reason:
                        out.status, out.blocked_by, out.final_text = "blocked", "output:" + getattr(g, "__name__", "guardrail"), "Sorry, I can't share that."
                        out.last_agent = active.name
                        return out
                out.final_text, out.last_agent = text, active.name
                return out
            results = []
            for u in uses:
                name, args = u["name"], u.get("input", {})
                if name.startswith("transfer_to_"):
                    target = next((a for a in active.handoffs if f"transfer_to_{a.name}" == name), None)
                    if target is None:
                        results.append({"type": "tool_result", "tool_use_id": u["id"], "is_error": True, "content": f"{active.name} cannot hand off to that agent."})
                        continue
                    with tracer.span(f"handoff {active.name} -> {target.name}", "handoff"):
                        for h in on_handoff:
                            h(active.name, target.name)
                    active = target
                    out.handoff_path.append(target.name)
                    results.append({"type": "tool_result", "tool_use_id": u["id"], "content": f"Transferred to {target.name}."})
                    if len(out.handoff_path) - 1 > max_handoffs:
                        out.status, out.last_agent = "handoff_loop", active.name
                        return out
                    continue
                fn = active.tools.get(name)
                if fn is None:                                            # per-agent tool allow-list: a tool that exists elsewhere is NOT available here
                    results.append({"type": "tool_result", "tool_use_id": u["id"], "is_error": True, "content": f"unknown tool {name!r} for agent {active.name}"})
                    continue
                denial = next((d for d in (h(active.name, name, args) for h in before_tool) if d), None)
                if denial:
                    out.denied_tool_calls.append((active.name, name, denial))
                    with tracer.span(name, "tool", agent=active.name, denied=True):
                        pass
                    results.append({"type": "tool_result", "tool_use_id": u["id"], "is_error": True, "content": f"DENIED: {denial}"})
                    continue
                with tracer.span(name, "tool", agent=active.name):
                    try:
                        res = fn(**args)
                        results.append({"type": "tool_result", "tool_use_id": u["id"], "content": res if isinstance(res, str) else json.dumps(res)})
                    except Exception as e:                                # noqa: BLE001
                        results.append({"type": "tool_result", "tool_use_id": u["id"], "is_error": True, "content": f"{type(e).__name__}: {e}"})
            messages.append({"role": "user", "content": results})
        out.status, out.last_agent = "max_turns", active.name
        return out
