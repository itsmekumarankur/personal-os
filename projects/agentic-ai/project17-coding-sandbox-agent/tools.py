"""Turns the model's tool calls into actions, and turns results into text the model can use.

Tool results are CONTEXT (Project 13): keep them short, keep the END (errors are at the bottom), and say plainly what happened.
"""
import re

from audit import AuditLog, digest, risk_flags
from sandbox import Result
from workspace import Workspace, WorkspaceError

TOOL_DEFS = [
    {"name": "list_dir", "description": "List files in a directory of the workspace.", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    {"name": "view", "description": "Show a file with line numbers (optionally view_range [start, end]).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "view_range": {"type": "array", "items": {"type": "integer"}}}, "required": ["path"]}},
    {"name": "create", "description": "Create a NEW file (never overwrites).", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "file_text": {"type": "string"}}, "required": ["path", "file_text"]}},
    {"name": "str_replace", "description": "Replace one exact occurrence of old_str with new_str in a file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_str": {"type": "string"}, "new_str": {"type": "string"}}, "required": ["path", "old_str", "new_str"]}},
    {"name": "insert", "description": "Insert text after a given line number.", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "insert_line": {"type": "integer"}, "new_str": {"type": "string"}}, "required": ["path", "insert_line", "new_str"]}},
    {"name": "run_python", "description": "Run a Python file from the workspace in the sandbox (no network, limited time and memory).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "run_tests", "description": "Run the unittest suite in the sandbox and report failures.", "input_schema": {"type": "object", "properties": {}}},
]


def clip(text: str, limit: int = 3000) -> str:
    """Keep the START and the END of long output (tracebacks and test summaries are at the end); say what was dropped."""
    if len(text) <= limit:
        return text
    head, tail = int(limit * 0.35), int(limit * 0.65)
    return text[:head] + f"\n... [{len(text) - head - tail} characters omitted] ...\n" + text[-tail:]


def parse_unittest(output: str) -> dict:
    ran = re.search(r"Ran (\d+) tests? in", output)
    failed = re.findall(r"^(?:FAIL|ERROR): (\w+) \(", output, re.M)
    return {"ran": int(ran.group(1)) if ran else 0, "failing": sorted(set(failed)), "ok": bool(re.search(r"^OK\b", output, re.M)) and not failed}


def render(r: Result, limits_note: bool = True) -> str:
    parts = [f"exit_code: {r.exit_code if r.exit_code is not None else 'killed by ' + str(r.signal)}  ({r.duration_s}s)"]
    if r.timed_out:
        parts.append("TIMEOUT: the process was killed. Look for an infinite loop or a blocking call (the sandbox has no network and no stdin).")
    if r.output_truncated:
        parts.append("OUTPUT TRUNCATED: the program printed too much and was stopped.")
    if r.stdout.strip():
        parts.append("--- stdout ---\n" + clip(r.stdout))
    if r.stderr.strip():
        parts.append("--- stderr ---\n" + clip(r.stderr))
    return "\n".join(parts)


class ToolRunner:
    def __init__(self, ws: Workspace, sandbox, audit: AuditLog | None = None, path_in_sandbox: str = "/work/"):
        self.ws, self.sb, self.audit = ws, sandbox, audit or AuditLog()
        self.prefix = path_in_sandbox if sandbox.level.startswith("L1") else ""
        self.last_tests: dict | None = None

    def _py(self, args: list):
        return self.sb.python_argv(args)

    def execute(self, name: str, args: dict, step: int = 0) -> tuple:
        """-> (text for the model, is_error). Never raises: errors are information for the model."""
        info = {k: (digest(v) if k in ("file_text", "new_str", "old_str") else v) for k, v in args.items()}
        try:
            if name == "list_dir":
                out = self.ws.list_dir(args.get("path", "."))
            elif name == "view":
                out = self.ws.view(args["path"], args.get("view_range"))
            elif name == "create":
                out = self.ws.create(args["path"], args["file_text"])
            elif name == "str_replace":
                out = self.ws.str_replace(args["path"], args["old_str"], args["new_str"])
            elif name == "insert":
                out = self.ws.insert(args["path"], args["insert_line"], args["new_str"])
            elif name == "run_python":
                path = args["path"]
                code = self.ws.resolve(path).read_text()
                r = self.sb.run(str(self.ws.root), self._py([self.prefix + path]))
                self.audit.record(step=step, tool=name, args=info, sandbox=self.sb.level, exit=r.exit_code, signal=r.signal, timed_out=r.timed_out,
                                  truncated=r.output_truncated, duration=r.duration_s, flags=risk_flags(code))
                return render(r), not r.ok
            elif name == "run_tests":
                restored = self.ws.restore_protected()                    # code that ran earlier may have rewritten the tests
                r = self.sb.run(str(self.ws.root), self._py(["-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"]))
                summary = parse_unittest(r.stdout + "\n" + r.stderr)
                self.last_tests = summary
                self.audit.record(step=step, tool=name, args=info, sandbox=self.sb.level, exit=r.exit_code, timed_out=r.timed_out, duration=r.duration_s,
                                  tests=summary, tampered=restored)
                note = f"\nWARNING: protected test files were modified by executed code and have been restored: {restored}" if restored else ""
                return render(r) + note, not summary["ok"]
            else:
                raise WorkspaceError(f"unknown tool '{name}'")
        except WorkspaceError as e:
            self.audit.record(step=step, tool=name, args=info, error=str(e))
            return f"error: {e}", True
        except (KeyError, TypeError, ValueError) as e:
            self.audit.record(step=step, tool=name, args=info, error=f"bad arguments: {e!r}")
            return f"error: bad arguments for {name}: {e!r}", True
        self.audit.record(step=step, tool=name, args=info, ok=True)
        return out, False
