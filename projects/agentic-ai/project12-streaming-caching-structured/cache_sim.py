"""A SIMULATOR of prompt caching, written from the documentation so you can poke it and watch the numbers.
It is not the real service. Rules implemented (from the docs I read on the day I wrote this; check them again before relying on them):

  * the prompt is read in a fixed order:  tools -> system -> messages.  A cache entry is a PREFIX of that sequence.
  * you mark up to 4 breakpoints with cache_control on a block; the prefix ENDING at that block can be cached.
  * a hit needs a 100% identical prefix. One changed character anywhere before the breakpoint = miss for that breakpoint and everything after.
  * prefixes shorter than a model-specific minimum (512 .. 4096 tokens) are silently not cached (usage shows zeros).
  * default lifetime 5 minutes, refreshed for free on every hit; "ttl": "1h" costs more to write.
  * the cache can look back at most 20 blocks from your breakpoint to find an earlier entry.
  * an entry becomes readable only when the FIRST response starts -> N parallel cold requests all pay full price.
  * usage = input_tokens (uncached, after the last breakpoint) + cache_creation_input_tokens + cache_read_input_tokens.
"""
import hashlib
import json
from dataclasses import dataclass, field

from tokens import count_json, count_text

LOOKBACK = 20
MAX_BREAKPOINTS = 4


class InvalidRequest(Exception):
    pass


def _block_text(b) -> str:
    return b if isinstance(b, str) else json.dumps(b, sort_keys=True, separators=(",", ":"), default=str)


def flatten(request: dict) -> list:
    """-> [(block_dict, tokens, cache_control|None)] in the order the service reads them."""
    out = []
    for t in request.get("tools", []):
        out.append(("tool", {k: v for k, v in t.items() if k != "cache_control"}, count_json(t), t.get("cache_control")))
    sysm = request.get("system")
    if isinstance(sysm, str):
        out.append(("system", {"type": "text", "text": sysm}, count_text(sysm), None))
    elif sysm:
        for b in sysm:
            out.append(("system", {k: v for k, v in b.items() if k != "cache_control"}, count_text(b.get("text", "")), b.get("cache_control")))
    for m in request.get("messages", []):
        content = m["content"]
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
        for b in blocks:
            b = dict(b)
            cc = b.pop("cache_control", None)
            n = count_text(b.get("text", "")) if b.get("type") == "text" else count_json(b)
            out.append((m["role"], {"role": m["role"], **b}, n, cc))
    return out


@dataclass
class Entry:
    expires_at: float
    ttl: float
    available_at: float


@dataclass
class PromptCache:
    min_tokens: int = 512
    clock: object = None                       # callable -> now (seconds)
    entries: dict = field(default_factory=dict)
    log: list = field(default_factory=list)

    def process(self, request: dict, now: float, commit_at: float | None = None) -> dict:
        """Returns the 'usage' dict for this request and updates the cache. commit_at = when the response starts (entries become readable then)."""
        blocks = flatten(request)
        commit_at = now if commit_at is None else commit_at
        h, cum, chain = hashlib.sha256(), 0, []
        for kind, b, n, cc in blocks:
            h.update(_block_text(b).encode())
            cum += n
            chain.append((h.copy().hexdigest(), cum, cc))
        total = cum
        bps = [i for i, (_, _, cc) in enumerate(chain) if cc]
        if len(bps) > MAX_BREAKPOINTS:
            raise InvalidRequest(f"at most {MAX_BREAKPOINTS} cache breakpoints, got {len(bps)}")
        usage = {"input_tokens": total, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                 "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}}
        if not bps:
            self.log.append(("no_breakpoint", total))
            return usage
        last = bps[-1]
        # 1. find the longest earlier entry, looking back at most LOOKBACK blocks from each breakpoint
        hit_idx = None
        for bp in reversed(bps):
            for i in range(bp, max(-1, bp - LOOKBACK), -1):
                e = self.entries.get(chain[i][0])
                if e and e.expires_at > now and e.available_at <= now:
                    hit_idx = i
                    e.expires_at = now + e.ttl                                    # a hit refreshes the lifetime
                    break
            if hit_idx is not None:
                break
        read = chain[hit_idx][1] if hit_idx is not None else 0
        # 2. write entries at each breakpoint that is long enough
        created = {"5m": 0, "1h": 0}
        for bp in bps:
            digest, cum_tokens, cc = chain[bp]
            if cum_tokens < self.min_tokens:
                continue
            ttl_label = (cc or {}).get("ttl", "5m")
            ttl = 3600.0 if ttl_label == "1h" else 300.0
            if digest not in self.entries or self.entries[digest].expires_at <= now:
                self.entries[digest] = Entry(now + ttl, ttl, commit_at)
        cacheable_end = chain[last][1]
        if cacheable_end >= self.min_tokens:
            new_tokens = max(0, cacheable_end - read)
            label = "1h" if (chain[last][2] or {}).get("ttl") == "1h" else "5m"
            created[label] = new_tokens
        usage["cache_read_input_tokens"] = read
        usage["cache_creation_input_tokens"] = created["5m"] + created["1h"]
        usage["cache_creation"] = {"ephemeral_5m_input_tokens": created["5m"], "ephemeral_1h_input_tokens": created["1h"]}
        usage["input_tokens"] = total - (read + usage["cache_creation_input_tokens"]) if cacheable_end >= self.min_tokens else total
        self.log.append(("hit" if read else "miss", total, read, usage["cache_creation_input_tokens"]))
        return usage
