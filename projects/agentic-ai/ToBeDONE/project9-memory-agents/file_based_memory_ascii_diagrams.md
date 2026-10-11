"""File-based memory, one private folder per user.



Modelled on Anthropic's memory tool. The official SDK ships a reference implementation,

BetaLocalFilesystemMemoryTool (anthropic/lib/tools/\_beta_builtin_memory_tool.py), and the tool

docs describe the same six commands:  view, create, str_replace, insert, delete, rename.

Paths start with /memories. This file follows that command set, those path rules and the

wording of its results, so what you learn here carries over to the official tool.



Differences from the SDK implementation (and why):

&#x20; \- one folder per user_id, so users cannot see each other's memory,

&#x20; \- limits on file size and on number of files,

&#x20; \- extra checks on every path segment (no hidden files, only .md / .txt),

&#x20; \- a backstop that refuses to save text that looks like a card number, an API key, a password

&#x20;   or an ID number,

&#x20; \- a lock per user, because the web server handles requests in threads,

&#x20; \- a plain tool schema instead of the beta "memory_20250818" tool type, so it works with any

&#x20;   SDK version.

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

USER_ID_RE = re.compile(r"^[A-Za-z0-9\_-]{1,64}$")

SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\_ -]{0,63}$")

ALLOWED_EXTENSIONS = (".md", ".txt")



\# A backstop, not a guarantee. The archivist is also told not to save such things.

SENSITIVE_PATTERNS = [

&#x20;   re.compile(r"\b(?:\d[ -]?){13,19}\b"),                                            # card-like numbers

&#x20;   re.compile(r"(?i)\b(?:password|passwd|api[\_ -]?key|secret|token)\b\s\*[:=]\s\*\S+"),  # key = value

&#x20;   re.compile(r"\bsk-[A-Za-z0-9\_-]{16,}"),                                           # API-key-like

&#x20;   re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),                                            # PAN-like (India)

&#x20;   re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),                                           # Aadhaar-like (India)

]





class MemoryToolError(Exception):

&#x20;   """A problem the model can read and react to. The message goes back as a tool error."""





def \_check_not_sensitive(text: str) -> None:

&#x20;   for pattern in SENSITIVE_PATTERNS:

&#x20;       if pattern.search(text):

&#x20;           raise MemoryToolError(

&#x20;               "Refused: the text looks like a secret or an identity/card number. "

&#x20;               "Do not store such data in memory."

&#x20;           )





def \_fmt_size(n: int) -> str:

&#x20;   for unit in ("B", "K", "M"):

&#x20;       if n < 1024:

&#x20;           return f"{n}{unit}" if unit == "B" else f"{n:.1f}{unit}"

&#x20;       n /= 1024

&#x20;   return f"{n:.1f}G"





def \_atomic_write(path: Path, text: str) -> None:

&#x20;   fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")

&#x20;   try:

&#x20;       with os.fdopen(fd, "w", encoding="utf-8") as f:

&#x20;           f.write(text)

&#x20;       os.chmod(tmp, 0o600)

&#x20;       os.replace(tmp, path)            # readers never see half a file

&#x20;   except BaseException:

&#x20;       if os.path.exists(tmp):

&#x20;           os.unlink(tmp)

&#x20;       raise





class UserMemory:

&#x20;   def \_\_init\_\_(self, root: Path, lock: threading.RLock):

&#x20;       self.root = root

&#x20;       self.\_lock = lock                  # the folder is created on the first write, not on a lookup



&#x20;   \# ---------- paths ----------

&#x20;   def \_resolve(self, path: str) -> Path:

&#x20;       if not isinstance(path, str) or "\x00" in path:

&#x20;           raise MemoryToolError("Invalid path.")

&#x20;       if path != MEMORY_ROOT and not path.startswith(MEMORY_ROOT + "/"):

&#x20;           raise MemoryToolError(f"Path must start with {MEMORY_ROOT}, got: {path}")

&#x20;       parts = [p for p in path[len(MEMORY_ROOT):].split("/") if p]

&#x20;       for part in parts:

&#x20;           if not SEGMENT_RE.match(part):                  # also rejects "..", "." and hidden names

&#x20;               raise MemoryToolError(f"Path {path} contains an invalid name: {part!r}")

&#x20;       full = self.root.joinpath(\*parts)

&#x20;       root = self.root.resolve()

&#x20;       resolved = full.resolve()

&#x20;       if resolved != root and not str(resolved).startswith(str(root) + os.sep):

&#x20;           raise MemoryToolError(f"Path {path} would escape {MEMORY_ROOT} directory")

&#x20;       return resolved



&#x20;   def \_file_count(self) -> int:

&#x20;       return sum(1 for p in self.root.rglob("\*") if p.is_file())



&#x20;   \# ---------- the six commands ----------

&#x20;   def view(self, path: str = MEMORY_ROOT, view_range: list | None = None) -> str:

&#x20;       with self.\_lock:

&#x20;           full = self.\_resolve(path)

&#x20;           if path.rstrip("/") == MEMORY_ROOT and not full.exists():

&#x20;               return (f"Here're the files and directories up to 2 levels deep in {path}, "

&#x20;                       f"excluding hidden items:\n0B\t{path}")

&#x20;           if not full.exists():

&#x20;               raise MemoryToolError(f"The path {path} does not exist. Please provide a valid path.")

&#x20;           if full.is_dir():

&#x20;               lines = [f"{\_fmt_size(full.stat().st_size)}\t{path}"]



&#x20;               def walk(directory: Path, rel: str, depth: int) -> None:

&#x20;                   for item in sorted(directory.iterdir(), key=lambda p: p.name):

&#x20;                       if item.name.startswith("."):

&#x20;                           continue

&#x20;                       item_rel = f"{rel}/{item.name}" if rel else item.name

&#x20;                       suffix = "/" if item.is_dir() else ""

&#x20;                       lines.append(f"{\_fmt_size(item.stat().st_size)}\t{path.rstrip('/')}/{item_rel}{suffix}")

&#x20;                       if item.is_dir() and depth < 2:

&#x20;                           walk(item, item_rel, depth + 1)



&#x20;               walk(full, "", 1)

&#x20;               return (f"Here're the files and directories up to 2 levels deep in {path}, "

&#x20;                       f"excluding hidden items:\n" + "\n".join(lines))

&#x20;           content = full.read_text(encoding="utf-8").split("\n")

&#x20;           start = 1

&#x20;           if view_range and len(view_range) == 2:

&#x20;               first = max(1, int(view_range[0]))

&#x20;               last = len(content) if int(view_range[1]) == -1 else int(view_range[1])

&#x20;               content, start = content[first - 1:last], first

&#x20;           numbered = [f"{str(i + start).rjust(6)}\t{line}" for i, line in enumerate(content)]

&#x20;           return f"Here's the content of {path} with line numbers:\n" + "\n".join(numbered)



&#x20;   def create(self, path: str, file_text: str) -> str:

&#x20;       with self.\_lock:

&#x20;           full = self.\_resolve(path)

&#x20;           if not path.endswith(ALLOWED_EXTENSIONS):

&#x20;               raise MemoryToolError("Memory files must end in .md or .txt")

&#x20;           if full.exists():

&#x20;               raise MemoryToolError(f"File {path} already exists")

&#x20;           self.\_check_size(file_text)

&#x20;           \_check_not_sensitive(file_text)

&#x20;           if self.\_file_count() >= MAX_FILES:

&#x20;               raise MemoryToolError(f"Memory is full ({MAX_FILES} files). Edit or delete a file first.")

&#x20;           full.parent.mkdir(parents=True, exist_ok=True)

&#x20;           \_atomic_write(full, file_text)

&#x20;           return f"File created successfully at: {path}"



&#x20;   def str_replace(self, path: str, old_str: str, new_str: str) -> str:

&#x20;       with self.\_lock:

&#x20;           full = self.\_existing_file(path)

&#x20;           content = full.read_text(encoding="utf-8")

&#x20;           count = content.count(old_str) if old_str else 0

&#x20;           if count == 0:

&#x20;               raise MemoryToolError(

&#x20;                   f"No replacement was performed, old_str \`{old_str}\` did not appear verbatim in {path}.")

&#x20;           if count > 1:

&#x20;               lines, pos = [], 0

&#x20;               while (pos := content.find(old_str, pos)) != -1:

&#x20;                   lines.append(content[:pos].count("\n") + 1)

&#x20;                   pos += 1

&#x20;               raise MemoryToolError(

&#x20;                   f"No replacement was performed. Multiple occurrences of old_str \`{old_str}\` in lines: "

&#x20;                   f"{', '.join(map(str, lines))}. Please ensure it is unique")

&#x20;           \_check_not_sensitive(new_str)

&#x20;           new_content = content.replace(old_str, new_str)

&#x20;           self.\_check_size(new_content)

&#x20;           \_atomic_write(full, new_content)

&#x20;           return f"The memory file {path} has been edited."



&#x20;   def insert(self, path: str, insert_line: int, insert_text: str) -> str:

&#x20;       with self.\_lock:

&#x20;           full = self.\_existing_file(path)

&#x20;           lines = full.read_text(encoding="utf-8").split("\n")

&#x20;           if lines and lines[-1] == "":

&#x20;               lines.pop()

&#x20;           if not 0 <= insert_line <= len(lines):

&#x20;               raise MemoryToolError(

&#x20;                   f"Invalid \`insert_line\` parameter: {insert_line}. It should be within the range [0, {len(lines)}].")

&#x20;           \_check_not_sensitive(insert_text)

&#x20;           lines.insert(insert_line, insert_text.rstrip("\n"))

&#x20;           new_content = "\n".join(lines) + "\n"

&#x20;           self.\_check_size(new_content)

&#x20;           \_atomic_write(full, new_content)

&#x20;           return f"The file {path} has been edited."



&#x20;   def delete(self, path: str) -> str:

&#x20;       with self.\_lock:

&#x20;           if path.rstrip("/") == MEMORY_ROOT:

&#x20;               raise MemoryToolError(f"Cannot delete the {MEMORY_ROOT} directory itself")

&#x20;           full = self.\_resolve(path)

&#x20;           if not full.exists():

&#x20;               raise MemoryToolError(f"The path {path} does not exist")

&#x20;           shutil.rmtree(full) if full.is_dir() else full.unlink()

&#x20;           return f"Successfully deleted {path}"



&#x20;   def rename(self, old_path: str, new_path: str) -> str:

&#x20;       with self.\_lock:

&#x20;           old, new = self.\_resolve(old_path), self.\_resolve(new_path)

&#x20;           if not old.exists():

&#x20;               raise MemoryToolError(f"The path {old_path} does not exist")

&#x20;           if new\.exists():

&#x20;               raise MemoryToolError(f"The destination {new_path} already exists")

&#x20;           if old_path.rstrip("/") == MEMORY_ROOT:

&#x20;               raise MemoryToolError(f"Cannot rename the {MEMORY_ROOT} directory itself")

&#x20;           if old.is_file() and not new_path.endswith(ALLOWED_EXTENSIONS):

&#x20;               raise MemoryToolError("Memory files must end in .md or .txt")

&#x20;           new\.parent.mkdir(parents=True, exist_ok=True)

&#x20;           old.rename(new)

&#x20;           return f"Successfully renamed {old_path} to {new_path}"



&#x20;   \# ---------- helpers ----------

&#x20;   def \_existing_file(self, path: str) -> Path:

&#x20;       full = self.\_resolve(path)

&#x20;       if not full.exists():

&#x20;           raise MemoryToolError(f"The path {path} does not exist. Please provide a valid path.")

&#x20;       if not full.is_file():

&#x20;           raise MemoryToolError(f"The path {path} is not a file.")

&#x20;       return full



&#x20;   @staticmethod

&#x20;   def \_check_size(text: str) -> None:

&#x20;       if len(text.encode("utf-8")) > MAX_FILE_BYTES:

&#x20;           raise MemoryToolError(f"File would be larger than {MAX_FILE_BYTES} bytes. Keep notes short.")



&#x20;   def execute(self, command: dict) -> str:

&#x20;       """Run one tool call coming from the model. Unknown commands and missing fields are tool errors."""

&#x20;       name = command.get("command")

&#x20;       spec = {

&#x20;           "view": (self.view, [], ["path", "view_range"]),

&#x20;           "create": (self.create, ["path", "file_text"], []),

&#x20;           "str_replace": (self.str_replace, ["path", "old_str", "new_str"], []),

&#x20;           "insert": (self.insert, ["path", "insert_line", "insert_text"], []),

&#x20;           "delete": (self.delete, ["path"], []),

&#x20;           "rename": (self.rename, ["old_path", "new_path"], []),

&#x20;       }.get(name)

&#x20;       if spec is None:

&#x20;           raise MemoryToolError(f"Unknown command: {name!r}")

&#x20;       fn, required, optional = spec

&#x20;       missing = [k for k in required if k not in command]

&#x20;       if missing:

&#x20;           raise MemoryToolError(f"Missing parameter(s): {', '.join(missing)}")

&#x20;       kwargs = {k: command[k] for k in required + optional if k in command}

&#x20;       try:

&#x20;           return fn(\*\*kwargs)

&#x20;       except (TypeError, ValueError) as e:

&#x20;           raise MemoryToolError(f"Bad parameter: {e}") from e



&#x20;   def files(self) -> dict[str, str]:

&#x20;       with self.\_lock:

&#x20;           return {f"{MEMORY_ROOT}/{p.relative_to(self.root).as_posix()}": p.read_text(encoding="utf-8")

&#x20;                   for p in sorted(self.root.rglob("\*")) if p.is_file() and not p.name.startswith(".")}



&#x20;   def snapshot(self, max_chars: int = 3000) -> str:

&#x20;       """All memory as text for a prompt, cut at max_chars. At larger sizes use search (Project 2)."""

&#x20;       out, used = [], 0

&#x20;       for path, text in self.files().items():

&#x20;           block = f"## {path}\n{text.strip()}\n"

&#x20;           if used + len(block) > max_chars:

&#x20;               out.append("[memory truncated: use the memory tool to read the rest]")

&#x20;               break

&#x20;           out.append(block)

&#x20;           used += len(block)

&#x20;       return "\n".join(out)



&#x20;   def clear(self) -> None:

&#x20;       with self.\_lock:

&#x20;           if not self.root.exists():

&#x20;               return

&#x20;           for child in self.root.iterdir():

&#x20;               shutil.rmtree(child) if child.is_dir() else child.unlink()





class MemoryStore:

&#x20;   def \_\_init\_\_(self, base_dir: str | Path):

&#x20;       self.base = Path(base_dir)

&#x20;       self.base.mkdir(parents=True, exist_ok=True)

&#x20;       self.\_locks: dict[str, threading.RLock] = {}

&#x20;       self.\_guard = threading.Lock()



&#x20;   def user(self, user_id: str) -> UserMemory:

&#x20;       if not isinstance(user_id, str) or not USER_ID_RE.match(user_id):

&#x20;           raise ValueError("user_id must be 1-64 characters: letters, digits, \_ or -")

&#x20;       with self.\_guard:

&#x20;           lock = self.\_locks.setdefault(user_id, threading.RLock())

&#x20;       return UserMemory(self.base / user_id, lock)



# ASCII Diagrams — File-Based Memory System

## 1. Overall architecture

```python
# ================================================================
# VERY SIMPLE VIEW OF THE WHOLE SYSTEM
# ================================================================
#
#                 AI / MODEL
#                     |
#                     | "create / view / edit / delete"
#                     v
#              +---------------+
#              |  MemoryStore  |
#              +---------------+
#                     |
#                     | user("ankur")
#                     v
#              +---------------+
#              |  UserMemory   |
#              +---------------+
#                     |
#                     v
#              /memories/
#                     |
#                     +-- user1/
#                     |     +-- notes.md
#                     |     +-- profile.txt
#                     |
#                     +-- user2/
#                           +-- notes.md
#
# SIMPLE IDEA:
# Each user gets their OWN folder.
# Memory is simply stored as .md or .txt files.
# ================================================================
```

## 2. MemoryStore — one folder per user

```python
# ================================================================
# MEMORY STORE
# ================================================================
#
#                 MemoryStore
#                      |
#          +-----------+-----------+
#          |                       |
#       User A                  User B
#          |                       |
#     /memories/A             /memories/B
#          |                       |
#     +----+----+              +---+---+
#     |         |              |       |
#  notes.md  todo.txt       notes.md  info.txt
#
# SIMPLE IDEA:
# MemoryStore is like the BUILDING.
# Each user gets their own ROOM.
# Users cannot access each other's room.
# ================================================================
```

## 3. `user()` — get memory for a user

```python
# ================================================================
# GET MEMORY FOR A USER
# ================================================================
#
# user_id = "ankur"
#
#       MemoryStore
#            |
#            | user("ankur")
#            v
#      /memories/ankur/
#            |
#            v
#       UserMemory object
#
# SIMPLE IDEA:
# "Give me the memory belonging to Ankur."
# ================================================================
```

## 4. Path validation — `_resolve()`

```python
# ================================================================
# PATH SAFETY CHECK
# ================================================================
#
# User gives:
#     /memories/ankur/notes.md
#             |
#             v
#       Is path valid?
#             |
#       +-----+-----+
#       |           |
#      YES          NO
#       |           |
#       v           v
#   Allow file    Reject
#
# Also prevents:
#     ../../secret.txt
#     /etc/passwd
#     hidden files
#     invalid file names
#
# SIMPLE IDEA:
# "Before touching a file, make sure the user is allowed
#  to access that location."
# ================================================================
```

## 5. Create memory

```python
# ================================================================
# CREATE A NEW MEMORY FILE
# ================================================================
#
# AI says:
# "Save: User likes Python"
#          |
#          v
#      CREATE FILE
#          |
#          v
# /memories/ankur/profile.md
#          |
#          v
#   "User likes Python"
#
# Before saving:
#   1. Is path valid?
#   2. Is extension .md or .txt?
#   3. Does file already exist?
#   4. Is file too large?
#   5. Does text contain sensitive information?
#   6. Are we below maximum file count?
#
# If everything is OK
#          |
#          v
#       SAVE FILE
# ================================================================
```

## 6. Sensitive-data protection

```python
# ================================================================
# SENSITIVE DATA CHECK
# ================================================================
#
#              Text to save
#                   |
#                   v
#          +------------------+
#          | Security Check   |
#          +------------------+
#                   |
#        +----------+----------+
#        |                     |
#     Looks safe           Looks sensitive
#        |                     |
#        v                     v
#     SAVE IT              REJECT IT
#
# Examples checked:
#   Credit-card-like number
#   Password
#   API key
#   Secret / token
#   PAN-like number
#   Aadhaar-like number
#
# SIMPLE IDEA:
# "Don't accidentally store secrets in memory."
# ================================================================
```

## 7. Atomic write

```python
# ================================================================
# SAFE FILE WRITING
# ================================================================
#
# DON'T DO:
#
#   Write directly to notes.md
#          |
#          X
#   If application crashes halfway,
#   notes.md may become corrupted.
#
#
# DO THIS:
#
#   New content
#       |
#       v
#   .tmp-12345
#       |
#       | write completely
#       v
#   Replace old file
#       |
#       v
#   notes.md
#
# SIMPLE IDEA:
# First prepare the complete new file,
# then replace the old file in one step.
# ================================================================
```

## 8. `view()`

```python
# ================================================================
# VIEW MEMORY
# ================================================================
#
# AI asks:
#     view("/memories/ankur/")
#              |
#              v
#       Find the folder
#              |
#              v
#      +----------------+
#      | ankur/         |
#      |                |
#      | notes.md       |
#      | profile.txt    |
#      | projects/      |
#      +----------------+
#              |
#              v
#      Return file list
#
# If a FILE is requested:
#
#     notes.md
#        |
#        v
#   Read its contents
#        |
#        v
#   Return text + line numbers
# ================================================================
```

## 9. `str_replace()`

```python
# ================================================================
# REPLACE EXISTING TEXT
# ================================================================
#
# File:
#   notes.md
#
# Old:
#   "I use Java"
#
# New:
#   "I use Python"
#
#        old_str
#           |
#           v
#      Find exact text
#           |
#     +-----+-----+
#     |           |
#    FOUND      NOT FOUND
#     |           |
#     v           v
# Replace       ERROR
#     |
#     v
# Save new file
#
# IMPORTANT:
# If old text appears MORE THAN ONCE,
# the code refuses to guess which one to change.
# ================================================================
```

## 10. `insert()`

```python
# ================================================================
# INSERT NEW TEXT
# ================================================================
#
# Existing file:
#
# Line 1: Hello
# Line 2: Java
# Line 3: Kafka
#
# insert_line = 2
#
#             |
#             v
#
# Line 1: Hello
# Line 2: Python       <-- INSERTED
# Line 3: Java
# Line 4: Kafka
#
# SIMPLE IDEA:
# Put new information at a specific line.
# ================================================================
```

## 11. `delete()`

```python
# ================================================================
# DELETE MEMORY
# ================================================================
#
# AI says:
#     delete("/memories/ankur/old_notes.md")
#                       |
#                       v
#                 Find the file
#                       |
#                       v
#                  Delete it
#
# But:
#
#     delete("/memories")
#             |
#             X
#       NOT ALLOWED
#
# SIMPLE IDEA:
# Individual memories can be deleted,
# but the main /memories directory cannot be deleted.
# ================================================================
```

## 12. `rename()`

```python
# ================================================================
# RENAME / MOVE MEMORY
# ================================================================
#
# BEFORE:
#
# /memories/ankur/old.md
#
#          |
#          | rename()
#          v
#
# AFTER:
#
# /memories/ankur/new.md
#
# SIMPLE IDEA:
# Same memory, different name/location.
#
# Safety checks:
#   - Old path must exist
#   - New path must NOT exist
#   - Path must be valid
#   - File must remain .md or .txt
# ================================================================
```

## 13. `execute()` — command dispatcher

```python
# ================================================================
# COMMAND DISPATCHER
# ================================================================
#
# Model sends a command:
#
# {
#     "command": "create",
#     "path": "/memories/ankur/notes.md",
#     "file_text": "I like Python"
# }
#
#                     |
#                     v
#              +-------------+
#              |  execute()  |
#              +-------------+
#                     |
#              What command?
#                     |
#       +------+------+------+------+------+------+
#       |      |      |      |      |      |
#     view   create  replace insert delete rename
#       |      |      |      |      |      |
#       v      v      v      v      v      v
#     view() create() replace() insert() delete() rename()
#
# SIMPLE IDEA:
# execute() is the TRAFFIC POLICE.
#
# It receives the command and sends it
# to the correct function.
# ================================================================
```

## 14. Lock — one operation at a time

```python
# ================================================================
# LOCK = ONE PERSON EDITING AT A TIME
# ================================================================
#
# Imagine two requests arrive together:
#
# Request A ---> edit notes.md
# Request B ---> edit notes.md
#        \          /
#         \        /
#          v      v
#          SAME FILE
#
# Without lock:
#     A + B can interfere with each other
#
# With lock:
#
#       Request A
#           |
#           v
#        [LOCK]
#           |
#        edit file
#           |
#        [UNLOCK]
#           |
#       Request B
#
# SIMPLE IDEA:
# "Only one operation should modify a user's memory
#  at a time."
# ================================================================
```

## 15. Complete flow — master cheat sheet

```python
# =================================================================
#                  FILE-BASED MEMORY SYSTEM
# =================================================================
#
#                         AI MODEL
#                            |
#                            | command
#                            v
#                   +----------------+
#                   |   execute()    |
#                   +----------------+
#                            |
#             +--------------+--------------+
#             |              |              |
#           create          view           edit
#             |              |              |
#             +--------------+--------------+
#                            |
#                            v
#                    +---------------+
#                    |   UserMemory  |
#                    +---------------+
#                            |
#                     security checks
#                            |
#             +--------------+--------------+
#             |              |              |
#          Path check    Sensitive check   Size check
#             |              |              |
#             +--------------+--------------+
#                            |
#                            v
#                     /memories/
#                            |
#             +--------------+--------------+
#             |                             |
#          /ankur/                       /user2/
#             |                             |
#       +-----+------+                +-----+------+
#       |            |                |            |
#    notes.md    profile.txt       notes.md     todo.txt
#
#
# SIX COMMANDS:
#
#   view         -> READ memory
#   create       -> CREATE memory
#   str_replace  -> CHANGE existing text
#   insert       -> ADD text
#   delete       -> REMOVE memory
#   rename       -> RENAME memory
#
# =================================================================
```
