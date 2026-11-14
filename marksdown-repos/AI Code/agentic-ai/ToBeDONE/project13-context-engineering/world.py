"""The task world: 100 log shards of boring text, with two important lines hidden in them, plus decoys.

   The agent must read every shard (a 'long task'), and at the end answer a question about two facts it met EARLY:
       FACT: refund approval code is K7-ALPHA-2291          (default: shard 3)
       USER-CONSTRAINT: do not modify anything in region ap-south-1 (compliance freeze)     (default: shard 7)
   Decoys: a REVOKED old code (K7-ALPHA-1180) and a line describing the code FORMAT. A model that half-remembers will grab a decoy.
"""
import hashlib
import re

SERVICES = ["auth", "ledger", "payments", "notify", "kyc", "gateway"]
LEVELS = ["INFO", "INFO", "INFO", "INFO", "WARN", "DEBUG"]
CODE, REGION = "K7-ALPHA-2291", "ap-south-1"
QUESTION = "Final question: what is the CURRENT refund approval code, and which region must we not modify? Answer from what you found."


def _h(*a) -> int:
    return int(hashlib.sha256("|".join(map(str, a)).encode()).hexdigest()[:8], 16)


class World:
    def __init__(self, total_shards: int = 100, code_at: int = 3, region_at: int = 7, lines: int = 40, decoy_at: int = 12):
        self.total, self.code_at, self.region_at, self.lines, self.decoy_at = total_shards, code_at, region_at, lines, decoy_at
        self.notes: dict = {}
        self.calls: list = []

    def shard_text(self, n: int) -> str:
        out = [f"=== shard {n:03d} ==="]
        for i in range(self.lines):
            h = _h(n, i)
            out.append(f"2025-03-{1 + n % 28:02d}T{h % 24:02d}:{h % 60:02d}:{(h >> 3) % 60:02d}Z svc-{SERVICES[h % 6]} {LEVELS[(h >> 5) % 6]} "
                       f"request id=req-{h:08x} user=u{h % 9973} latency={h % 900}ms status={200 if h % 17 else 503} path=/v1/{SERVICES[(h >> 7) % 6]}/op{h % 31}")
        if n == self.code_at:
            out.insert(1 + 11, f"FACT: refund approval code is {CODE}")
        if n == self.region_at:
            out.insert(1 + 23, f"USER-CONSTRAINT: do not modify anything in region {REGION} (compliance freeze)")
        if n == self.decoy_at:
            out.insert(15, "NOTE: old approval code K7-ALPHA-1180 was revoked on 2025-02-11")
        if n == 41:
            out.insert(9, "NOTE: approval codes look like K7-<WORD>-<4 digits>")
        return "\n".join(out)

    # ------------------------------------------------------------------ tools
    def call(self, name: str, args: dict) -> str:
        self.calls.append((name, dict(args)))
        if name == "read_log":
            n = int(args.get("shard", 0))
            return self.shard_text(n) if 1 <= n <= self.total else f"error: shard must be 1..{self.total}"
        if name == "search_logs":
            q = str(args.get("query", "")).lower()
            hits = []
            for n in range(1, self.total + 1):
                for line in self.shard_text(n).splitlines():
                    if q and q in line.lower():
                        hits.append(f"shard {n}: {line}")
            return "\n".join(hits[:8]) or "no matches"
        if name == "write_note":
            self.notes[str(args["key"])] = str(args["value"])
            return "saved"
        if name == "read_notes":
            return "\n".join(f"{k}: {v}" for k, v in self.notes.items()) or "(no notes)"
        return f"error: unknown tool {name}"


TOOLS = [
    {"name": "read_log", "description": "Read one log shard (1..N). Large output.", "input_schema": {"type": "object", "properties": {"shard": {"type": "integer"}}}},
    {"name": "search_logs", "description": "Search all shards for a phrase; returns up to 8 matching lines with shard numbers.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}},
    {"name": "write_note", "description": "Save a short note that survives context clearing.", "input_schema": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}}},
    {"name": "read_notes", "description": "Read all saved notes.", "input_schema": {"type": "object", "properties": {}}},
]


def grade(answer: str) -> dict:
    return {"code": CODE in answer, "region": REGION in answer, "correct": CODE in answer and REGION in answer,
            "wrong_decoy": bool(re.search(r"K7-ALPHA-1180", answer))}
