"""State that must survive a restart: conversations, approvals, the audit log, token usage.

SQLite is used because it needs no server and the Python standard library has it. Its limits are
real: one writer at a time, and it should not sit on a network file system under heavy use. It is
fine for one instance. Before running several instances, replace this class with Postgres or
DynamoDB; the methods are the whole interface the rest of the code uses.
"""
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, status TEXT NOT NULL,
    messages TEXT NOT NULL, pending_results TEXT, pending_approval_id TEXT,
    created TEXT NOT NULL, updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, tool_use_id TEXT NOT NULL, tool TEXT NOT NULL,
    args TEXT NOT NULL, description TEXT NOT NULL, requested_by TEXT NOT NULL, status TEXT NOT NULL,
    decided_by TEXT, note TEXT, result TEXT, created TEXT NOT NULL, decided TEXT);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, request_id TEXT, actor TEXT,
    event TEXT NOT NULL, details TEXT);
CREATE TABLE IF NOT EXISTS usage (
    principal_id TEXT NOT NULL, day TEXT NOT NULL, tokens INTEGER NOT NULL, PRIMARY KEY (principal_id, day));
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            import os
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA busy_timeout = 5000")
        with self._lock, self._db:
            self._db.executescript(SCHEMA)

    def ping(self) -> bool:
        with self._lock:
            return self._db.execute("SELECT 1").fetchone()[0] == 1

    # ---------- conversations ----------
    def create_conversation(self, customer_id: str) -> str:
        cid = uuid.uuid4().hex
        with self._lock, self._db:
            self._db.execute("INSERT INTO conversations VALUES (?,?,?,?,?,?,?,?)",
                             (cid, customer_id, "active", "[]", None, None, now(), now()))
        return cid

    def get_conversation(self, cid: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["messages"] = json.loads(d["messages"])
        d["pending_results"] = json.loads(d["pending_results"]) if d["pending_results"] else None
        return d

    def save_conversation(self, cid: str, messages: list, status: str,
                          pending_results: list | None = None, pending_approval_id: str | None = None) -> None:
        with self._lock, self._db:
            self._db.execute(
                "UPDATE conversations SET messages=?, status=?, pending_results=?, pending_approval_id=?, updated=? WHERE id=?",
                (json.dumps(messages), status, json.dumps(pending_results) if pending_results is not None else None,
                 pending_approval_id, now(), cid))

    # ---------- approvals ----------
    def create_approval(self, conversation_id: str, tool_use_id: str, tool: str, args: dict,
                        description: str, requested_by: str) -> str:
        aid = uuid.uuid4().hex[:12]
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO approvals (id, conversation_id, tool_use_id, tool, args, description, requested_by, status, created)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (aid, conversation_id, tool_use_id, tool, json.dumps(args), description, requested_by, "pending", now()))
        return aid

    @staticmethod
    def _approval(row) -> dict:
        d = dict(row)
        d["args"] = json.loads(d["args"])
        return d

    def get_approval(self, aid: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM approvals WHERE id = ?", (aid,)).fetchone()
        return self._approval(row) if row else None

    def list_approvals(self, status: str | None = None, limit: int = 50) -> list[dict]:
        q, params = "SELECT * FROM approvals", []
        if status:
            q += " WHERE status = ?"
            params.append(status)
        q += " ORDER BY created, rowid LIMIT ?"
        params.append(limit)
        with self._lock:
            return [self._approval(r) for r in self._db.execute(q, params).fetchall()]

    def decide_approval(self, aid: str, status: str, decided_by: str, note: str) -> bool:
        """Move pending -> approved/rejected. True only for the single caller that wins the race."""
        with self._lock, self._db:
            cur = self._db.execute(
                "UPDATE approvals SET status=?, decided_by=?, note=?, decided=? WHERE id=? AND status='pending'",
                (status, decided_by, note, now(), aid))
            return cur.rowcount == 1

    def set_approval_result(self, aid: str, result: str, status: str | None = None) -> None:
        with self._lock, self._db:
            if status:
                self._db.execute("UPDATE approvals SET result=?, status=? WHERE id=?", (result, status, aid))
            else:
                self._db.execute("UPDATE approvals SET result=? WHERE id=?", (result, aid))

    def count_pending(self) -> int:
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()[0]

    # ---------- audit ----------
    def audit(self, request_id: str | None, actor: str | None, event: str, details: dict | None = None) -> None:
        with self._lock, self._db:
            self._db.execute("INSERT INTO audit (ts, request_id, actor, event, details) VALUES (?,?,?,?,?)",
                             (now(), request_id, actor, event, json.dumps(details or {})))

    def list_audit(self, limit: int = 100) -> list[dict]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in reversed(rows):
            d = dict(r)
            d["details"] = json.loads(d["details"])
            out.append(d)
        return out

    # ---------- usage ----------
    def add_usage(self, principal_id: str, tokens: int) -> None:
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO usage VALUES (?,?,?) ON CONFLICT(principal_id, day) DO UPDATE SET tokens = tokens + excluded.tokens",
                (principal_id, today(), tokens))

    def get_usage(self, principal_id: str) -> int:
        with self._lock:
            row = self._db.execute("SELECT tokens FROM usage WHERE principal_id=? AND day=?",
                                   (principal_id, today())).fetchone()
        return row[0] if row else 0
