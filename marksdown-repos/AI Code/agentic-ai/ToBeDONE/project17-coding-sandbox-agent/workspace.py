"""The agent's file tools, with the checks a real product needs. The model controls the ARGUMENTS, so every argument is hostile until proven otherwise.

Commands (the same shape as the 'text editor' tools coding agents are trained on):  view, create, str_replace, insert, list_dir
Safety rules, each with a test:
  * PATH JAIL      absolute paths, '..', NUL bytes and symlinks that lead outside the workspace are refused (resolved with realpath, then checked)
  * PROTECTED      tests/ cannot be edited by the agent (otherwise 'make the tests pass' is solved by deleting the tests)
                   and are restored from a pristine copy before every test run, in case executed CODE rewrote them
  * str_replace    must match exactly ONE place; the error says what to do (zero matches / many matches) so the model can recover
  * LIMITS         max file size, max number of files, max lines returned by view
  * SNAPSHOTS      the starting state is kept, so the result is a reviewable PATCH, never a silent change
"""
import difflib
import os
from pathlib import Path


class WorkspaceError(Exception):
    pass


class Workspace:
    def __init__(self, root: str, protected: tuple = ("tests/",), max_file_bytes: int = 100_000, max_files: int = 200, max_view_lines: int = 300):
        self.root = Path(root).resolve()
        self.protected, self.max_file_bytes, self.max_files, self.max_view_lines = protected, max_file_bytes, max_files, max_view_lines
        self.initial = self._read_all()
        self.pristine_protected = {p: b for p, b in self.initial.items() if self._is_protected(p)}
        self.edits = 0

    # ---------------------------------------------------------------- helpers
    def _is_protected(self, rel: str) -> bool:
        return any(rel == p.rstrip("/") or rel.startswith(p) for p in self.protected)

    def _read_all(self) -> dict:
        out = {}
        for dp, dns, fns in os.walk(self.root):
            dns[:] = [d for d in dns if d not in ("__pycache__", ".git")]
            for fn in fns:
                full = Path(dp) / fn
                if full.is_symlink() or not full.is_file():
                    continue
                out[str(full.relative_to(self.root))] = full.read_bytes()
        return out

    def resolve(self, rel: str) -> Path:
        if not isinstance(rel, str) or not rel or "\x00" in rel:
            raise WorkspaceError("path must be a non-empty relative string")
        if rel.startswith(("/", "~")) or ".." in Path(rel).parts:
            raise WorkspaceError(f"path '{rel}' must be relative and stay inside the workspace")
        p = (self.root / rel).resolve()                                   # follows symlinks
        if p != self.root and self.root not in p.parents:
            raise WorkspaceError(f"path '{rel}' leads outside the workspace")
        return p

    def _rel(self, p: Path) -> str:
        return str(p.relative_to(self.root))

    def _check_writable(self, rel: str):
        if self._is_protected(os.path.normpath(rel)):
            raise WorkspaceError(f"'{rel}' is protected (tests are read-only for the agent). Fix the code under test instead.")

    def _check_size(self, text: str):
        if len(text.encode()) > self.max_file_bytes:
            raise WorkspaceError(f"file would be {len(text.encode())} bytes; the limit is {self.max_file_bytes}")

    # ---------------------------------------------------------------- commands
    def list_dir(self, path: str = ".") -> str:
        p = self.resolve(path)
        if not p.is_dir():
            raise WorkspaceError(f"'{path}' is not a directory")
        rows = []
        for c in sorted(p.iterdir()):
            if c.name in ("__pycache__", ".git"):
                continue
            rows.append(f"{self._rel(c)}{'/' if c.is_dir() else f'  ({c.stat().st_size} bytes)'}")
        return "\n".join(rows) or "(empty)"

    def view(self, path: str, view_range: list | None = None) -> str:
        p = self.resolve(path)
        if p.is_dir():
            return self.list_dir(path)
        if not p.is_file():
            raise WorkspaceError(f"'{path}' does not exist")
        data = p.read_bytes()
        if b"\x00" in data[:2000]:
            raise WorkspaceError(f"'{path}' looks binary; refusing to show it")
        lines = data.decode("utf-8", "replace").splitlines()
        lo, hi = (1, len(lines)) if not view_range else (max(1, int(view_range[0])), len(lines) if int(view_range[1]) == -1 else min(len(lines), int(view_range[1])))
        shown = lines[lo - 1:hi][:self.max_view_lines]
        text = "\n".join(f"{i:>5}\t{ln}" for i, ln in enumerate(shown, lo))
        if hi - lo + 1 > self.max_view_lines:
            text += f"\n... ({len(lines)} lines total; showing {lo}-{lo + len(shown) - 1}. Use view_range for the rest.)"
        return text

    def create(self, path: str, file_text: str) -> str:
        p = self.resolve(path)
        self._check_writable(os.path.normpath(path))
        self._check_size(file_text)
        if p.exists():
            raise WorkspaceError(f"'{path}' already exists. Use str_replace to change it (create never overwrites).")
        if len(self._read_all()) >= self.max_files:
            raise WorkspaceError(f"too many files (limit {self.max_files})")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(file_text)
        self.edits += 1
        return f"created {path} ({len(file_text.splitlines())} lines)"

    def str_replace(self, path: str, old_str: str, new_str: str) -> str:
        p = self.resolve(path)
        self._check_writable(os.path.normpath(path))
        if not p.is_file():
            raise WorkspaceError(f"'{path}' does not exist")
        text = p.read_text()
        n = text.count(old_str) if old_str else 0
        if n == 0:
            raise WorkspaceError("no match for old_str. It must match the file EXACTLY, including spaces and indentation. View the file again and copy the lines.")
        if n > 1:
            raise WorkspaceError(f"old_str matches {n} places. Include more surrounding lines so it matches exactly one.")
        new_text = text.replace(old_str, new_str, 1)
        self._check_size(new_text)
        p.write_text(new_text)
        self.edits += 1
        line = text[:text.index(old_str)].count("\n") + 1
        return f"edited {path} at line {line}"

    def insert(self, path: str, insert_line: int, new_str: str) -> str:
        p = self.resolve(path)
        self._check_writable(os.path.normpath(path))
        if not p.is_file():
            raise WorkspaceError(f"'{path}' does not exist")
        lines = p.read_text().splitlines(keepends=True)
        if not 0 <= int(insert_line) <= len(lines):
            raise WorkspaceError(f"insert_line must be between 0 and {len(lines)}")
        lines[int(insert_line):int(insert_line)] = [new_str if new_str.endswith("\n") else new_str + "\n"]
        text = "".join(lines)
        self._check_size(text)
        p.write_text(text)
        self.edits += 1
        return f"inserted after line {insert_line} of {path}"

    # ---------------------------------------------------------------- protection and patch
    def tampered(self) -> list:
        """Protected files that differ from the pristine copy (e.g. rewritten by code the agent EXECUTED)."""
        bad = []
        for rel, data in self.pristine_protected.items():
            p = self.root / rel
            if not p.is_file() or p.read_bytes() != data:
                bad.append(rel)
        for rel in self._read_all():
            if self._is_protected(rel) and rel not in self.pristine_protected:
                bad.append(rel + " (new file)")
        return sorted(bad)

    def restore_protected(self) -> list:
        bad = self.tampered()
        for rel in bad:
            if rel.endswith(" (new file)"):
                (self.root / rel[:-11]).unlink(missing_ok=True)
        for rel, data in self.pristine_protected.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        return bad

    def patch(self) -> str:
        now = self._read_all()
        out = []
        for rel in sorted(set(self.initial) | set(now)):
            a, b = self.initial.get(rel), now.get(rel)
            if a == b or rel.endswith(".pyc"):
                continue
            out += list(difflib.unified_diff((a or b"").decode("utf-8", "replace").splitlines(True), (b or b"").decode("utf-8", "replace").splitlines(True),
                                             f"a/{rel}" if a is not None else "/dev/null", f"b/{rel}" if b is not None else "/dev/null"))
        return "".join(out)
