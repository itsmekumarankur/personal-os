"""TRACING: every node / model call / tool call becomes a span (name, kind, start, duration, attributes, children).
Frameworks ship this because debugging an agent without a trace is guessing. Same idea as Project 15, built in."""
import time
from contextlib import contextmanager


class Tracer:
    def __init__(self):
        self.root = {"name": "run", "kind": "root", "children": [], "dur": 0.0, "attrs": {}}
        self._stack = [self.root]

    @contextmanager
    def span(self, name: str, kind: str = "step", **attrs):
        s = {"name": name, "kind": kind, "children": [], "attrs": dict(attrs), "dur": 0.0}
        self._stack[-1]["children"].append(s)
        self._stack.append(s)
        t0 = time.perf_counter()
        try:
            yield s
        except BaseException as e:
            s["attrs"]["error"] = type(e).__name__
            raise
        finally:
            s["dur"] = round(time.perf_counter() - t0, 4)
            self._stack.pop()

    def render(self) -> str:
        lines = []

        def walk(s, depth):
            if s is not self.root:
                a = " ".join(f"{k}={v}" for k, v in s["attrs"].items())
                lines.append("  " * (depth - 1) + f"{s['kind']:<9} {s['name']}" + (f"   {a}" if a else ""))
            for c in s["children"]:
                walk(c, depth + 1)

        walk(self.root, 0)
        return "\n".join(lines)

    def spans(self, kind: str | None = None) -> list:
        out = []

        def walk(s):
            if kind is None or s["kind"] == kind:
                out.append(s)
            for c in s["children"]:
                walk(c)

        walk(self.root)
        return out
