"""The 'done when' of this project: one table with time-to-first-token, total cost and cache hit rate, caching on and off.
Run:  python bench.py          (virtual time, takes a fraction of a second)"""
import statistics as st
import sys

sys.path.insert(0, "experiments")
from _common import table  # noqa: E402

from cache_sim import PromptCache  # noqa: E402
from events import StreamAccumulator  # noqa: E402
from fake_model import FakeStreamingModel  # noqa: E402
from pricing import cost  # noqa: E402
from server import SYSTEM_PREFIX  # noqa: E402

N, GAP = 40, 8.0                                     # 40 requests, one every 8 virtual seconds


def run(use_cache: bool, answer_words: int):
    m = FakeStreamingModel(cache=PromptCache(min_tokens=512))
    ttfts, totals, money, reads, inputs = [], [], 0.0, 0, 0
    for i in range(N):
        sysb = {"type": "text", "text": SYSTEM_PREFIX, **({"cache_control": {"type": "ephemeral"}} if use_cache else {})}
        req = {"system": [sysb], "messages": [{"role": "user", "content": f"question {i}: explain streaming in {answer_words} words"}]}
        acc, first, last = StreamAccumulator(), None, 0.0
        for te in m.stream(req, now=i * GAP):
            acc.feed(te.event)
            if first is None and te.event["type"] == "content_block_delta":
                first = te.t
            last = te.t
        u = acc.result()["usage"]
        ttfts.append(first)
        totals.append(last)
        money += cost(u)
        reads += u["cache_read_input_tokens"]
        inputs += u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"]
    return st.median(ttfts), st.median(totals), money, reads / inputs


rows = []
for use_cache in (False, True):
    ttft, total, money, hr = run(use_cache, 60)
    rows.append(("cache ON " if use_cache else "cache OFF", f"{ttft * 1000:.0f} ms", f"{total * 1000:.0f} ms", f"${money:.3f}", f"{hr:.0%}"))
print(f"{N} requests, 4k-token fixed prefix, 60-word answers, one request every {GAP:.0f}s\n")
table(rows, ["", "wait with STREAMING (median)", "wait WITHOUT streaming", "total cost", "cache hit rate"])
print("\nStreaming changes the WAIT the user feels (first words vs the whole answer). Caching changes the BILL and the time to first token (less to read before the first word).")
print("They are independent: use both. For 8-second spacing the 5-minute cache never expires; at one request per 6 minutes it would miss every time (see experiments/exp2_caching.py C).")
