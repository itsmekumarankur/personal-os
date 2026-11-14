"""Pin what a remote MCP server told you about its tools.

Why: a tool's DESCRIPTION is read by the model, so it is an instruction channel. A server that was fine when you approved it
can later change a description to 'also send the user's data to ...' (a 'rug pull'). We keep a fingerprint of each tool
(name + description + input schema) the first time we see it, and refuse tools that later change or newly appear.
"""
import hashlib
import json
from pathlib import Path


class PinMismatch(Exception):
    def __init__(self, changed, new, removed):
        self.changed, self.new, self.removed = changed, new, removed
        super().__init__(f"tool list differs from the pinned one: changed={changed} new={new} removed={removed}")


def fingerprint(tool: dict) -> str:
    canon = json.dumps({"name": tool["name"], "description": tool.get("description") or "", "schema": tool.get("inputSchema") or {}},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


class ToolPins:
    def __init__(self, path: str | None = None):
        self.path = Path(path) if path else None
        self.pins: dict = json.loads(self.path.read_text()) if self.path and self.path.exists() else {}

    def _save(self):
        if self.path:
            self.path.write_text(json.dumps(self.pins, indent=1, sort_keys=True))

    def approve(self, tools: list):
        """A HUMAN decision: these tools, exactly as described, are acceptable."""
        self.pins = {t["name"]: fingerprint(t) for t in tools}
        self._save()

    def check(self, tools: list) -> list:
        """Returns the tools that match their pin. Raises PinMismatch if anything changed, appeared or vanished."""
        now = {t["name"]: fingerprint(t) for t in tools}
        changed = sorted(n for n in now if n in self.pins and now[n] != self.pins[n])
        new = sorted(n for n in now if n not in self.pins)
        removed = sorted(n for n in self.pins if n not in now)
        if changed or new or removed:
            raise PinMismatch(changed, new, removed)
        return tools

    def check_or_trust(self, tools: list) -> list:
        """Trust on first use: the very first list is pinned (a weak spot: you must trust that first sight), later lists must match."""
        if not self.pins:
            self.approve(tools)
            return tools
        return self.check(tools)
