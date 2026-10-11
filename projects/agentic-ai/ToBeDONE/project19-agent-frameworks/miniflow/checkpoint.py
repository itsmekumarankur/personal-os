"""CHECKPOINTS: after every superstep the framework saves (thread, step, state, what-runs-next, status).

What that buys you (all demonstrated in experiments):
  * CRASH RECOVERY   - resume from the last good step instead of starting over (and re-paying for the LLM calls)
  * HUMAN IN THE LOOP - pause for approval for hours; the process can exit; resume later, even on another machine
  * TIME TRAVEL      - look at the state at step N, fork a new thread from it with a patched value, re-run from there
  * MEMORY           - the same thread_id continues a conversation
What it does NOT buy you: exactly-once side effects. A node that crashed AFTER sending an email is re-run from its start. See exp2.
"""
import copy
import json
import sqlite3


class MemoryCheckpointer:
    def __init__(self):
        self._d: dict[str, list[dict]] = {}

    def put(self, thread: str, ckpt: dict):
        self._d.setdefault(thread, []).append(copy.deepcopy(ckpt))

    def latest(self, thread: str):
        h = self._d.get(thread)
        return copy.deepcopy(h[-1]) if h else None

    def history(self, thread: str) -> list:
        return copy.deepcopy(self._d.get(thread, []))

    def get(self, thread: str, step: int):
        for c in reversed(self._d.get(thread, [])):
            if c["step"] == step:
                return copy.deepcopy(c)
        return None


class SqliteCheckpointer:
    """Same interface, but durable: a different process (or tomorrow) can resume. State must be JSON-serialisable: that is a real constraint of every framework."""

    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("create table if not exists ckpt (id integer primary key autoincrement, thread text, step integer, body text)")
        self.db.commit()

    def put(self, thread: str, ckpt: dict):
        self.db.execute("insert into ckpt (thread, step, body) values (?,?,?)", (thread, ckpt["step"], json.dumps(ckpt)))
        self.db.commit()

    def latest(self, thread: str):
        r = self.db.execute("select body from ckpt where thread=? order by id desc limit 1", (thread,)).fetchone()
        return json.loads(r[0]) if r else None

    def history(self, thread: str) -> list:
        return [json.loads(r[0]) for r in self.db.execute("select body from ckpt where thread=? order by id", (thread,))]

    def get(self, thread: str, step: int):
        r = self.db.execute("select body from ckpt where thread=? and step=? order by id desc limit 1", (thread, step)).fetchone()
        return json.loads(r[0]) if r else None
