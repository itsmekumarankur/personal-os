"""The agent loop with measurement. One function: run(strategy, ...) -> Result."""
from dataclasses import dataclass, field

from context_manager import STRATEGIES, Config, ContextManager, ContextOverflow, dumps, msg_tokens  # noqa: F401
from fake_model import ContextAgentModel
from tokens import count_text
from world import QUESTION, World, grade

INPUT_PRICE = 1.0                      # relative units: 1.0 per input token, cache write 1.25, cache read 0.1  (see project 12)


@dataclass
class Result:
    strategy: str
    answer: str = ""
    correct: bool = False
    detail: dict = field(default_factory=dict)
    steps: int = 0
    overflow_at: int | None = None
    peak_tokens: int = 0
    billed_tokens: int = 0              # sum over steps of the whole prompt = what you pay for without caching
    cached_cost_units: float = 0.0      # with a moving cache breakpoint: common prefix at 0.1x, the rest at 1.25x
    prefix_breaks: int = 0              # steps where an EARLIER part of the prompt changed
    repeated_calls: int = 0             # same tool call made again (amnesia loop)
    events: list = field(default_factory=list)
    curve: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)
    cleared: int = 0
    ledger: list = field(default_factory=list)


def _common_prefix_tokens(prev: list, now: list) -> tuple:
    tok = 0
    for a, b in zip(prev, now):
        if a != b:
            return tok, True
        tok += count_text(a)
    return tok, False


def run(strategy: str | Config, model: ContextAgentModel | None = None, world: World | None = None, max_steps: int = 260, task: str = QUESTION,
        ask_final: bool = True) -> Result:
    cfg = STRATEGIES[strategy] if isinstance(strategy, str) else strategy
    world = world or World()
    model = model or ContextAgentModel(total_shards=world.total, notetaker=cfg.name.endswith("notes"))
    cm = ContextManager(cfg)
    cm.add({"role": "user", "content": f"Task: read log shards 1..{world.total} one by one with read_log. Note anything that matters. {task if ask_final else ''}"})
    res = Result(cfg.name)
    prev_parts: list = []
    seen_calls: set = set()
    for step in range(1, max_steps + 1):
        try:
            system, view = cm.prepare()
        except ContextOverflow:
            res.overflow_at = step
            res.answer = "(context overflow: the request would have been rejected)"
            break
        parts = [system] + [dumps(m) for m in view]
        total = sum(count_text(p) for p in parts)
        common, broke = _common_prefix_tokens(prev_parts, parts) if prev_parts else (0, False)
        if broke:
            res.prefix_breaks += 1
        res.billed_tokens += total
        res.cached_cost_units += 0.1 * common + 1.25 * (total - common)
        res.peak_tokens = max(res.peak_tokens, total)
        res.curve.append(total)
        prev_parts = parts
        content = model(system, view)
        cm.add({"role": "assistant", "content": content})
        uses = [b for b in content if b["type"] == "tool_use"]
        res.steps = step
        if not uses:
            res.answer = "".join(b["text"] for b in content if b["type"] == "text")
            break
        results = []
        for u in uses:
            key = dumps((u["name"], u["input"]))
            if key in seen_calls and u["name"] == "read_log":
                res.repeated_calls += 1
            seen_calls.add(key)
            results.append({"type": "tool_result", "tool_use_id": u["id"], "content": world.call(u["name"], u["input"])})
        cm.add({"role": "user", "content": results})
        if res.repeated_calls > 25:
            res.answer = "(stuck in a loop: kept re-reading shards it had already read)"
            break
    res.detail = grade(res.answer)
    res.correct = res.detail["correct"]
    res.events = cm.events
    res.notes = dict(world.notes)
    res.ledger = list(cm.ledger_items)
    res.cleared = cm.cleared
    return res


__all__ = ["run", "Result", "STRATEGIES", "Config", "msg_tokens"]
