"""A deterministic stand-in for the model whose behaviour depends ONLY on what is in its context window.
That is the whole point: if something was cleared, summarised away or never shown, this 'model' cannot use it, exactly like a real one.

How it decides (all from the visible messages):
  * progress   = the highest read_log shard it can still SEE (in a tool_use block, a summary, a note or the pinned ledger) + 1.
                 (In this task the newest tool call is always visible, so progress survives every strategy. Real agents lose their place
                 when 'where am I' lives only in OLD messages, e.g. a to-do list inside a cleared tool result.)
  * facts      = lines containing 'FACT:' / 'USER-CONSTRAINT:' anywhere in its context.
  * notetaker  = also calls write_note when a tool result contains a FACT/USER-CONSTRAINT line, and read_notes before answering if it cannot see the facts.
  * confabulate= when the real fact is missing, answers with a lookalike it can see (a decoy) instead of saying 'I don't know'.
It is NOT a language model. Real models are fuzzier; they may also forget things that ARE visible (see README: lost in the middle).
"""
import json
import re

from world import CODE, REGION  # noqa: F401  (REGION/CODE only for readers of this file)

FACT_RE = re.compile(r"(FACT: .*|USER-CONSTRAINT: .*)")


def _blocks(m):
    return m["content"] if isinstance(m["content"], list) else [{"type": "text", "text": m["content"]}]


def visible_text(system: str, messages: list) -> str:
    parts = [system]
    for m in messages:
        for b in _blocks(m):
            if b.get("type") == "text":
                parts.append(b["text"])
            elif b.get("type") == "tool_result":
                parts.append(str(b["content"]))
    return "\n".join(parts)


def visible_progress(system: str, messages: list) -> int:
    best = 0
    for m in messages:
        for b in _blocks(m):
            if b.get("type") == "tool_use" and b["name"] == "read_log":
                best = max(best, int(b["input"].get("shard", 0)))
    blob = visible_text(system, messages)
    for pat in (r"NEXT_SHARD=(\d+)", r"next_shard: (\d+)"):
        for mm in re.finditer(pat, blob):
            best = max(best, int(mm.group(1)) - 1)
    return best


class ContextAgentModel:
    def __init__(self, total_shards: int = 100, notetaker: bool = False, confabulate: bool = False):
        self.total, self.notetaker, self.confabulate = total_shards, notetaker, confabulate
        self._n = 0

    def _use(self, name, args):
        self._n += 1
        return [{"type": "tool_use", "id": f"tu_{self._n:04d}", "name": name, "input": args}]

    def __call__(self, system: str, messages: list) -> list:
        blob = visible_text(system, messages)
        last = messages[-1]
        # 1. notetaker reacts to what it just read
        if self.notetaker and last["role"] == "user" and isinstance(last["content"], list):
            for b in last["content"]:
                if b.get("type") == "tool_result":
                    mm = FACT_RE.search(str(b["content"]))
                    if mm:
                        key = "approval_code" if "FACT" in mm.group(1) else "constraint"
                        return self._use("write_note", {"key": key, "value": mm.group(1)})
        done = visible_progress(system, messages)
        if self.notetaker and last["role"] == "user" and isinstance(last["content"], list) and done and done % 10 == 0:
            tool_names = [b["name"] for m in messages[-3:] for b in _blocks(m) if b.get("type") == "tool_use"]
            if "write_note" not in tool_names:
                return self._use("write_note", {"key": "next_shard", "value": str(done + 1)})
        if done < self.total:
            return self._use("read_log", {"shard": done + 1})
        # 2. time to answer
        code = re.search(r"FACT: refund approval code is (K7-[A-Z]+-\d{4})", blob) or re.search(r"approval_code: FACT: refund approval code is (K7-[A-Z]+-\d{4})", blob)
        region = re.search(r"do not modify anything in region ([a-z0-9-]+)", blob)
        if self.notetaker and not (code and region) and not any(b.get("name") == "read_notes" for m in messages[-4:] for b in _blocks(m) if b.get("type") == "tool_use"):
            return self._use("read_notes", {})
        if code and region:
            return [{"type": "text", "text": f"The current refund approval code is {code.group(1)} and the frozen region is {region.group(1)}."}]
        if self.confabulate:
            lookalike = re.findall(r"K7-[A-Z]+-\d{4}", blob)
            guess = lookalike[0] if lookalike else "K7-ALPHA-0000"
            return [{"type": "text", "text": f"The current refund approval code is {guess} and the frozen region is {region.group(1) if region else 'ap-south-1'}."}]
        missing = [n for n, v in (("approval code", code), ("frozen region", region)) if not v]
        return [{"type": "text", "text": "I cannot find: " + ", ".join(missing) + " (not in my context)."}]


def dumps(x) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), default=str)
