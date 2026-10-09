"""GRAPH WORKFLOW ENGINE (the LangGraph idea in ~200 lines).

Vocabulary
  node         a function  state -> update   (optionally  (state, ctx) -> update, where ctx can pause the run)
  edge         'after A, run B'.   conditional edge: a router function looks at the state and names the next node(s)
  superstep    all nodes that are due run 'at the same time' against the SAME input state; their updates are then merged with the reducers
  checkpoint   saved after each superstep
  interrupt    a node asks a human; the run STOPS (state saved); resume(value) later re-runs that node from its top, and ctx.interrupt() now returns the value

Why a graph and not just a function?  Because the framework, not your code, owns 'where are we', so it can pause, resume, retry, fork, stream and trace
any workflow without you re-implementing control flow each time. The price: your logic must be expressed as nodes and edges, and state must be serialisable.
"""
import inspect
import time
from dataclasses import dataclass, field

from .state import apply_update
from .trace import Tracer

END = "__end__"
_NONE = object()


class GraphError(Exception):
    pass


class Interrupt(Exception):
    def __init__(self, payload):
        super().__init__("interrupted")
        self.payload = payload


class Ctx:
    def __init__(self, node: str, resume=_NONE):
        self.node, self._resume = node, resume

    def interrupt(self, payload):
        """First time: stop the whole run and surface `payload` to a human. After resume: return what the human said.
        CAREFUL: on resume the node runs again FROM THE TOP, so anything before this line happens twice."""
        if self._resume is _NONE:
            raise Interrupt(payload)
        return self._resume


@dataclass
class RunResult:
    status: str                     # done | interrupted | error | step_limit
    state: dict
    thread: str
    step: int
    next: list = field(default_factory=list)
    interrupt: dict | None = None
    error: str | None = None
    ran: list = field(default_factory=list)      # node names executed IN THIS CALL, in order (handy for teaching/tests)


class Graph:
    def __init__(self, reducers: dict | None = None, defaults: dict | None = None):
        self.reducers, self.defaults = reducers or {}, defaults or {}
        self.nodes: dict = {}
        self.edges: dict[str, list[str]] = {}
        self.routers: dict = {}
        self.entry: str | None = None

    def add_node(self, name, fn):
        if name in self.nodes or name == END:
            raise GraphError(f"bad or duplicate node name {name!r}")
        self.nodes[name] = fn
        return self

    def add_edge(self, a, b):
        self.edges.setdefault(a, []).append(b)
        return self

    def add_conditional(self, a, router):
        self.routers[a] = router
        return self

    def set_entry(self, name):
        self.entry = name
        return self

    def compile(self, checkpointer=None, max_steps: int = 25) -> "Compiled":
        if self.entry not in self.nodes:
            raise GraphError("entry node missing")
        for n in self.nodes:
            if n not in self.edges and n not in self.routers:
                raise GraphError(f"node {n!r} has no outgoing edge (use add_edge(..., END) to finish)")
        for a, bs in self.edges.items():
            for b in bs:
                if b != END and b not in self.nodes:
                    raise GraphError(f"edge {a}->{b}: unknown node")
        return Compiled(self, checkpointer, max_steps)


class Compiled:
    def __init__(self, g: Graph, cp, max_steps: int):
        self.g, self.cp, self.max_steps = g, cp, max_steps

    # ------------------------------------------------------------------ public API
    def invoke(self, input: dict | None = None, thread: str = "t1", resume=_NONE, tracer: Tracer | None = None, hooks: dict | None = None) -> RunResult:
        tracer, hooks = tracer or Tracer(), hooks or {}
        ck = self.cp.latest(thread) if self.cp else None
        if resume is not _NONE:
            if not ck or ck["status"] != "interrupted":
                raise GraphError("nothing to resume: the thread is not waiting for input")
            ck["resumes"][ck["interrupt"]["node"]] = resume
            ck["status"], ck["interrupt"] = "running", None
        elif input is None:
            if not ck or ck["status"] in ("done",):
                raise GraphError("nothing to continue (no thread, or it already finished)")
            if ck["status"] == "interrupted":
                raise GraphError("this thread is waiting for a human: call invoke(resume=...)")
            ck["status"] = "running"
        else:
            base = ck["state"] if ck else dict(self.g.defaults)
            ck = {"step": (ck["step"] + 1) if ck else 0, "state": apply_update(base, input, self.g.reducers), "next": [self.g.entry], "status": "running",
                  "interrupt": None, "resumes": {}, "pending": {}, "error": None}
            self._save(thread, ck)
        return self._loop(thread, ck, tracer, hooks)

    def history(self, thread: str) -> list:
        return self.cp.history(thread)

    def fork(self, thread: str, step: int, new_thread: str, patch: dict | None = None):
        """TIME TRAVEL: copy the checkpoint at `step` into a new thread, optionally patching state. invoke(thread=new_thread) continues from there."""
        ck = self.cp.get(thread, step)
        if not ck:
            raise GraphError(f"no checkpoint at step {step}")
        ck["state"] = {**ck["state"], **(patch or {})}
        ck["status"], ck["interrupt"], ck["error"], ck["pending"], ck["resumes"] = "running", None, None, {}, {}
        self.cp.put(new_thread, ck)
        return ck

    # ------------------------------------------------------------------ engine
    def _save(self, thread, ck):
        if self.cp:
            self.cp.put(thread, ck)

    def _result(self, thread, ck, ran, **kw):
        return RunResult(status=ck["status"], state=ck["state"], thread=thread, step=ck["step"], next=list(ck["next"]), interrupt=ck["interrupt"],
                         error=ck["error"], ran=ran, **kw)

    def _loop(self, thread, ck, tracer, hooks) -> RunResult:
        ran: list = []
        taken = 0
        with tracer.span(f"graph thread={thread}", "graph"):
            while True:
                if not ck["next"]:
                    ck["status"] = "done"
                    self._save(thread, ck)
                    return self._result(thread, ck, ran)
                if taken >= self.max_steps:                                   # the recursion limit: every loop in a graph needs one
                    ck["status"], ck["error"] = "step_limit", f"stopped after {self.max_steps} supersteps in this call"
                    self._save(thread, ck)
                    return self._result(thread, ck, ran)
                taken += 1
                updates, failure, asked = dict(ck["pending"]), None, None
                for name in sorted(ck["next"]):
                    if name in updates:                                       # finished before a sibling failed: do not run it twice
                        continue
                    fn = self.g.nodes[name]
                    resume = ck["resumes"].get(name, _NONE)
                    t0 = time.perf_counter()
                    try:
                        with tracer.span(name, "node", step=ck["step"]):
                            for h in hooks.get("before_node", []):
                                h(name, ck["state"])
                            upd = fn(ck["state"], Ctx(name, resume)) if len(inspect.signature(fn).parameters) >= 2 else fn(ck["state"])
                            if upd is not None and not isinstance(upd, dict):
                                raise GraphError(f"node {name!r} must return a dict update or None, got {type(upd).__name__}")
                            updates[name] = upd or {}
                            for h in hooks.get("after_node", []):
                                h(name, updates[name], time.perf_counter() - t0)
                        ran.append(name)
                    except Interrupt as i:
                        asked = {"node": name, "payload": i.payload}
                        break
                    except Exception as e:                                     # noqa: BLE001  - any node failure is a checkpointed, resumable event
                        failure = f"{name}: {type(e).__name__}: {e}"
                        break
                if asked or failure:
                    ck["pending"] = updates
                    ck["status"] = "interrupted" if asked else "error"
                    ck["interrupt"], ck["error"] = asked, failure
                    self._save(thread, ck)
                    return self._result(thread, ck, ran)
                state = ck["state"]
                for name in sorted(updates):                                   # merge in a fixed order so runs are reproducible
                    state = apply_update(state, updates[name], self.g.reducers)
                nxt: list = []
                for name in sorted(updates):
                    for t in self._targets(name, state):
                        if t != END and t not in nxt:
                            nxt.append(t)
                ck = {"step": ck["step"] + 1, "state": state, "next": nxt, "status": "running", "interrupt": None, "resumes": {}, "pending": {}, "error": None}
                self._save(thread, ck)

    def _targets(self, name, state) -> list:
        out = list(self.g.edges.get(name, []))
        if name in self.g.routers:
            r = self.g.routers[name](state)
            out += r if isinstance(r, list) else [r]
        for t in out:
            if t != END and t not in self.g.nodes:
                raise GraphError(f"router/edge from {name!r} named unknown node {t!r}")
        return out
