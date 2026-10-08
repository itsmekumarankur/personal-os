"""File-based memory, one private folder per user.

Modelled on Anthropic's memory tool. The official SDK ships a reference implementation,
BetaLocalFilesystemMemoryTool (anthropic/lib/tools/_beta_builtin_memory_tool.py), and the tool
docs describe the same six commands:  view, create, str_replace, insert, delete, rename.
Paths start with /memories. This file follows that command set, those path rules and the
wording of its results, so what you learn here carries over to the official tool.

Differences from the SDK implementation (and why):
  - one folder per user_id, so users cannot see each other's memory,
  - limits on file size and on number of files,
  - extra checks on every path segment (no hidden files, only .md / .txt),
  - a backstop that refuses to save text that looks like a card number, an API key, a password
    or an ID number,
  - a lock per user, because the web server handles requests in threads,
  - a plain tool schema instead of the beta "memory_20250818" tool type, so it works with any
    SDK version.
"""
import os
import re
import shutil
import tempfile
import threading
from pathlib import Path

MAX_FILE_BYTES = 8000
MAX_FILES = 40
MEMORY_ROOT = "/memories"
USER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$")
ALLOWED_EXTENSIONS = (".md", ".txt")

# A backstop, not a guarantee. The archivist is also told not to save such things.
SENSITIVE_PATTERNS = [
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),                                            # card-like numbers
    re.compile(r"(?i)\b(?:password|passwd|api[_ -]?key|secret|token)\b\s*[:=]\s*\S+"),  # key = value
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),                                           # API-key-like
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),                                            # PAN-like (India)
    re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),                                           # Aadhaar-like (India)
]


class MemoryToolError(Exception):
    """A problem the model can read and react to. The message goes back as a tool error."""


def _check_not_sensitive(text: str) -> None:
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            raise MemoryToolError(
                "Refused: the text looks like a secret or an identity/card number. "
                "Do not store such data in memory."
            )


def _fmt_size(n: int) -> str:
    for unit in ("B", "K", "M"):
        if n < 1024:
            return f"{n}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}G"


def _atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)            # readers never see half a file
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


class UserMemory:
    def __init__(self, root: Path, lock: threading.RLock):
        self.root = root
        self._lock = lock                  # the folder is created on the first write, not on a lookup

    # ---------- paths ----------
    def _resolve(self, path: str) -> Path:
        if not isinstance(path, str) or "\x00" in path:
            raise MemoryToolError("Invalid path.")
        if path != MEMORY_ROOT and not path.startswith(MEMORY_ROOT + "/"):
            raise MemoryToolError(f"Path must start with {MEMORY_ROOT}, got: {path}")
        parts = [p for p in path[len(MEMORY_ROOT):].split("/") if p]
        for part in parts:
            if not SEGMENT_RE.match(part):                  # also rejects "..", "." and hidden names
                raise MemoryToolError(f"Path {path} contains an invalid name: {part!r}")
        full = self.root.joinpath(*parts)
        root = self.root.resolve()
        resolved = full.resolve()
        if resolved != root and not str(resolved).startswith(str(root) + os.sep):
            raise MemoryToolError(f"Path {path} would escape {MEMORY_ROOT} directory")
        return resolved

    def _file_count(self) -> int:
        return sum(1 for p in self.root.rglob("*") if p.is_file())

    # ---------- the six commands ----------
    def view(self, path: str = MEMORY_ROOT, view_range: list | None = None) -> str:
        with self._lock:
            full = self._resolve(path)
            if path.rstrip("/") == MEMORY_ROOT and not full.exists():
                return (f"Here're the files and directories up to 2 levels deep in {path}, "
                        f"excluding hidden items:\n0B\t{path}")
            if not full.exists():
                raise MemoryToolError(f"The path {path} does not exist. Please provide a valid path.")
            if full.is_dir():
                lines = [f"{_fmt_size(full.stat().st_size)}\t{path}"]

                def walk(directory: Path, rel: str, depth: int) -> None:
                    for item in sorted(directory.iterdir(), key=lambda p: p.name):
                        if item.name.startswith("."):
                            continue
                        item_rel = f"{rel}/{item.name}" if rel else item.name
                        suffix = "/" if item.is_dir() else ""
                        lines.append(f"{_fmt_size(item.stat().st_size)}\t{path.rstrip('/')}/{item_rel}{suffix}")
                        if item.is_dir() and depth < 2:
                            walk(item, item_rel, depth + 1)

                walk(full, "", 1)
                return (f"Here're the files and directories up to 2 levels deep in {path}, "
                        f"excluding hidden items:\n" + "\n".join(lines))
            content = full.read_text(encoding="utf-8").split("\n")
            start = 1
            if view_range and len(view_range) == 2:
                first = max(1, int(view_range[0]))
                last = len(content) if int(view_range[1]) == -1 else int(view_range[1])
                content, start = content[first - 1:last], first
            numbered = [f"{str(i + start).rjust(6)}\t{line}" for i, line in enumerate(content)]
            return f"Here's the content of {path} with line numbers:\n" + "\n".join(numbered)

    def create(self, path: str, file_text: str) -> str:
        with self._lock:
            full = self._resolve(path)
            if not path.endswith(ALLOWED_EXTENSIONS):
                raise MemoryToolError("Memory files must end in .md or .txt")
            if full.exists():
                raise MemoryToolError(f"File {path} already exists")
            self._check_size(file_text)
            _check_not_sensitive(file_text)
            if self._file_count() >= MAX_FILES:
                raise MemoryToolError(f"Memory is full ({MAX_FILES} files). Edit or delete a file first.")
            full.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write(full, file_text)
            return f"File created successfully at: {path}"

    def str_replace(self, path: str, old_str: str, new_str: str) -> str:
        with self._lock:
            full = self._existing_file(path)
            content = full.read_text(encoding="utf-8")
            count = content.count(old_str) if old_str else 0
            if count == 0:
                raise MemoryToolError(
                    f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.")
            if count > 1:
                lines, pos = [], 0
                while (pos := content.find(old_str, pos)) != -1:
                    lines.append(content[:pos].count("\n") + 1)
                    pos += 1
                raise MemoryToolError(
                    f"No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines: "
                    f"{', '.join(map(str, lines))}. Please ensure it is unique")
            _check_not_sensitive(new_str)
            new_content = content.replace(old_str, new_str)
            self._check_size(new_content)
            _atomic_write(full, new_content)
            return f"The memory file {path} has been edited."

    def insert(self, path: str, insert_line: int, insert_text: str) -> str:
        with self._lock:
            full = self._existing_file(path)
            lines = full.read_text(encoding="utf-8").split("\n")
            if lines and lines[-1] == "":
                lines.pop()
            if not 0 <= insert_line <= len(lines):
                raise MemoryToolError(
                    f"Invalid `insert_line` parameter: {insert_line}. It should be within the range [0, {len(lines)}].")
            _check_not_sensitive(insert_text)
            lines.insert(insert_line, insert_text.rstrip("\n"))
            new_content = "\n".join(lines) + "\n"
            self._check_size(new_content)
            _atomic_write(full, new_content)
            return f"The file {path} has been edited."

    def delete(self, path: str) -> str:
        with self._lock:
            if path.rstrip("/") == MEMORY_ROOT:
                raise MemoryToolError(f"Cannot delete the {MEMORY_ROOT} directory itself")
            full = self._resolve(path)
            if not full.exists():
                raise MemoryToolError(f"The path {path} does not exist")
            shutil.rmtree(full) if full.is_dir() else full.unlink()
            return f"Successfully deleted {path}"

    def rename(self, old_path: str, new_path: str) -> str:
        with self._lock:
            old, new = self._resolve(old_path), self._resolve(new_path)
            if not old.exists():
                raise MemoryToolError(f"The path {old_path} does not exist")
            if new.exists():
                raise MemoryToolError(f"The destination {new_path} already exists")
            if old_path.rstrip("/") == MEMORY_ROOT:
                raise MemoryToolError(f"Cannot rename the {MEMORY_ROOT} directory itself")
            if old.is_file() and not new_path.endswith(ALLOWED_EXTENSIONS):
                raise MemoryToolError("Memory files must end in .md or .txt")
            new.parent.mkdir(parents=True, exist_ok=True)
            old.rename(new)
            return f"Successfully renamed {old_path} to {new_path}"

    # ---------- helpers ----------
    def _existing_file(self, path: str) -> Path:
        full = self._resolve(path)
        if not full.exists():
            raise MemoryToolError(f"The path {path} does not exist. Please provide a valid path.")
        if not full.is_file():
            raise MemoryToolError(f"The path {path} is not a file.")
        return full

    @staticmethod
    def _check_size(text: str) -> None:
        if len(text.encode("utf-8")) > MAX_FILE_BYTES:
            raise MemoryToolError(f"File would be larger than {MAX_FILE_BYTES} bytes. Keep notes short.")

    def execute(self, command: dict) -> str:
        """Run one tool call coming from the model. Unknown commands and missing fields are tool errors."""
        name = command.get("command")
        spec = {
            "view": (self.view, [], ["path", "view_range"]),
            "create": (self.create, ["path", "file_text"], []),
            "str_replace": (self.str_replace, ["path", "old_str", "new_str"], []),
            "insert": (self.insert, ["path", "insert_line", "insert_text"], []),
            "delete": (self.delete, ["path"], []),
            "rename": (self.rename, ["old_path", "new_path"], []),
        }.get(name)
        if spec is None:
            raise MemoryToolError(f"Unknown command: {name!r}")
        fn, required, optional = spec
        missing = [k for k in required if k not in command]
        if missing:
            raise MemoryToolError(f"Missing parameter(s): {', '.join(missing)}")
        kwargs = {k: command[k] for k in required + optional if k in command}
        try:
            return fn(**kwargs)
        except (TypeError, ValueError) as e:
            raise MemoryToolError(f"Bad parameter: {e}") from e

    def files(self) -> dict[str, str]:
        with self._lock:
            return {f"{MEMORY_ROOT}/{p.relative_to(self.root).as_posix()}": p.read_text(encoding="utf-8")
                    for p in sorted(self.root.rglob("*")) if p.is_file() and not p.name.startswith(".")}

    def snapshot(self, max_chars: int = 3000) -> str:
        """All memory as text for a prompt, cut at max_chars. At larger sizes use search (Project 2)."""
        out, used = [], 0
        for path, text in self.files().items():
            block = f"## {path}\n{text.strip()}\n"
            if used + len(block) > max_chars:
                out.append("[memory truncated: use the memory tool to read the rest]")
                break
            out.append(block)
            used += len(block)
        return "\n".join(out)

    def clear(self) -> None:
        with self._lock:
            if not self.root.exists():
                return
            for child in self.root.iterdir():
                shutil.rmtree(child) if child.is_dir() else child.unlink()


class MemoryStore:
    def __init__(self, base_dir: str | Path):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.RLock] = {}
        self._guard = threading.Lock()

    def user(self, user_id: str) -> UserMemory:
        if not isinstance(user_id, str) or not USER_ID_RE.match(user_id):
            raise ValueError("user_id must be 1-64 characters: letters, digits, _ or -")
        with self._guard:
            lock = self._locks.setdefault(user_id, threading.RLock())
        return UserMemory(self.base / user_id, lock)
