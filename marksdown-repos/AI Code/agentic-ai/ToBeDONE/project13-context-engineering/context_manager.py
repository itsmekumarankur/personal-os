"""Context management: decides what the model SEES on each step. The full history is never lost (self.transcript); only the VIEW changes.

Tools in the toolbox (each is a real technique, each fails in a different way):

  naive              append forever.                       fails: overflows the window
  window             keep the first message + newest N.    fails: forgets everything old, including the facts
  clear_results      replace OLD tool results by a one-line placeholder (keep the tool CALLS so the agent still knows what it did).
                     fails: facts that lived only in a cleared result are gone
  summarize_lossy    replace old history by an abstract summary.      fails: summaries love to drop exact values ("a code was found")
  summarize_struct   summary with REQUIRED sections + verbatim facts.  fails less; still a model call that can drop things in real life
  ledger             deterministic 'must keep' extraction from every tool result into a pinned block. Works with any strategy above.
  notes              the AGENT writes notes to storage outside the window (memory tool). Fails if the agent does not write them.

Cache note (Project 12): every edit to an EARLIER part of the view breaks the cached prefix. 'eager' clearing edits a little every step
(many breaks); 'batch' clearing waits for the trigger and clears a lot at once (few breaks). See experiments/exp3_cache.py.
"""
import re
from dataclasses import dataclass, field

from fake_model import dumps
from tokens import count_text

FACT_LINE = re.compile(r"^(FACT: .*|USER-CONSTRAINT: .*)$", re.M)


class ContextOverflow(Exception):
    pass


def msg_tokens(m: dict) -> int:
    return count_text(dumps(m["content"]))


def view_tokens(system: str, view: list) -> int:
    return count_text(system) + sum(msg_tokens(m) for m in view)


@dataclass
class Config:
    name: str = "naive"
    budget: int = 30_000                  # the hard window we pretend to have (small on purpose, so the effects show quickly)
    trigger: float = 0.70                 # start managing at this fraction of the budget
    keep_results: int = 4                 # newest tool results always kept intact
    keep_messages: int = 8                # newest messages kept by window / summarise
    clear_inputs: bool = False            # also blank the tool CALL arguments (loses 'what did I already do')
    clear_mode: str = "batch"             # batch: clear down to 'target' once triggered | eager: clear just enough, every step
    target: float = 0.40                  # batch clearing aims for this fraction of the budget
    summarizer: str | None = None         # None | lossy | structured
    ledger: bool = False
    verify_summary: bool = False          # re-insert any ledger item the summary dropped


STRATEGIES = {
    "naive": Config("naive"),
    "window": Config("window"),
    "clear_results": Config("clear_results"),
    "clear_results+inputs": Config("clear_results+inputs", clear_inputs=True),
    "summarize_lossy": Config("summarize_lossy", summarizer="lossy"),
    "summarize_structured": Config("summarize_structured", summarizer="structured"),
    "clear+ledger": Config("clear+ledger", ledger=True),
    "summarize_lossy+ledger": Config("summarize_lossy+ledger", summarizer="lossy", ledger=True),
    "clear_eager": Config("clear_eager", clear_mode="eager"),
    "clear_batch": Config("clear_batch", clear_mode="batch", target=0.30),
    "clear+notes": Config("clear+notes"),                  # needs a notetaker model; notes live in world.notes
}


@dataclass
class ContextManager:
    cfg: Config
    system_base: str = "You are an investigation agent. Read every log shard, keep track of what matters, then answer the final question."
    transcript: list = field(default_factory=list)       # everything, forever (audit)
    view: list = field(default_factory=list)             # what the model sees
    ledger_items: list = field(default_factory=list)
    events: list = field(default_factory=list)
    cleared: int = 0

    # ---- pinned text that goes into the system prompt
    @property
    def system(self) -> str:
        if self.cfg.ledger and self.ledger_items:
            return self.system_base + "\n\n<must_keep>\n" + "\n".join(self.ledger_items) + "\n</must_keep>"
        return self.system_base

    def add(self, msg: dict):
        self.transcript.append(msg)
        self.view.append(msg)
        if self.cfg.ledger and msg["role"] == "user" and isinstance(msg["content"], list):
            for b in msg["content"]:
                if b.get("type") == "tool_result":
                    for line in FACT_LINE.findall(str(b["content"])):
                        if line not in self.ledger_items:
                            self.ledger_items.append(line)

    def tokens(self) -> int:
        return view_tokens(self.system, self.view)

    # ---- the one entry point: called before every model call
    def prepare(self) -> tuple:
        c = self.cfg
        limit = c.budget * c.trigger
        if c.name == "naive":
            pass
        elif c.name == "window":
            if self.tokens() > limit:
                self._window()
        elif c.summarizer:
            if self.tokens() > limit:
                self._summarize()
        elif self.tokens() > limit or (c.clear_mode == "eager" and self.tokens() > limit * 0.999):
            self._clear_results()
        if self.tokens() > c.budget:
            raise ContextOverflow(f"{self.tokens()} tokens > budget {c.budget}")
        return self.system, self.view

    # ---- strategy 1: clear old tool results, keep the calls
    def _results(self):
        out = []
        for i, m in enumerate(self.view):
            if m["role"] == "user" and isinstance(m["content"], list):
                for j, b in enumerate(m["content"]):
                    if b.get("type") == "tool_result" and not str(b["content"]).startswith("[cleared"):
                        out.append((i, j))
        return out

    def _call_label(self, tool_use_id: str) -> str:
        for m in self.view:
            if m["role"] == "assistant":
                for b in m["content"]:
                    if b.get("type") == "tool_use" and b["id"] == tool_use_id:
                        return f"{b['name']}({', '.join(f'{k}={v}' for k, v in b['input'].items())})"
        return "tool call"

    def _clear_results(self):
        c = self.cfg
        goal = c.budget * (c.target if c.clear_mode == "batch" else c.trigger * 0.97)
        candidates = self._results()[:-c.keep_results] if c.keep_results else self._results()
        freed = 0
        for i, j in candidates:
            if self.tokens() <= goal:
                break
            b = self.view[i]["content"][j]
            label = self._call_label(b["tool_use_id"])
            before = count_text(str(b["content"]))
            b["content"] = f"[cleared to save context: result of {label}, ~{before} tokens]"
            freed += before
            self.cleared += 1
        if c.clear_inputs:
            for m in self.view[:-c.keep_messages]:
                if m["role"] == "assistant":
                    for b in m["content"]:
                        if b.get("type") == "tool_use":
                            b["input"] = {}
        if freed:
            self.events.append(("clear", freed))

    # ---- strategy 2: sliding window (drop oldest whole exchanges, keep tool_use/tool_result pairs together)
    def _window(self):
        first, rest = self.view[0], self.view[1:]
        k = self.cfg.keep_messages
        rest = rest[-k:]
        while rest and rest[0]["role"] == "user" and isinstance(rest[0]["content"], list):      # never start on an orphan tool_result
            rest = rest[1:]
        self.events.append(("window", len(self.view) - 1 - len(rest)))
        self.view = [first] + rest

    # ---- strategy 3: summarise
    def _summarize(self):
        k = self.cfg.keep_messages
        old, recent = self.view[1:-k], self.view[-k:]
        while recent and recent[0]["role"] == "user" and isinstance(recent[0]["content"], list):
            old, recent = old + [recent[0]], recent[1:]
        text = (lossy_summary if self.cfg.summarizer == "lossy" else structured_summary)(old, self.transcript)
        if self.cfg.verify_summary or self.cfg.ledger:
            missing = [x for x in self.ledger_items if x not in text]
            if missing:
                text += "\nVERBATIM (re-inserted by the verifier):\n" + "\n".join(missing)
        summary_msg = {"role": "user", "content": [{"type": "text", "text": f"<summary of earlier work>\n{text}\n</summary>"}]}
        self.events.append(("summarize", count_text(text)))
        self.view = [self.view[0], summary_msg] + recent


def _shards_read(messages: list) -> list:
    return sorted({b["input"]["shard"] for m in messages if m["role"] == "assistant" for b in m["content"]
                   if b.get("type") == "tool_use" and b["name"] == "read_log"})


def lossy_summary(old: list, transcript: list) -> str:
    done = _shards_read(transcript)
    return (f"Progress: reviewed log shards 1 to {max(done)}. NEXT_SHARD={max(done) + 1}.\n"
            "Findings so far: the logs are mostly routine request lines with occasional warnings and a few 503 errors. "
            "An approval code and a compliance instruction were encountered and should be kept in mind.")


def structured_summary(old: list, transcript: list) -> str:
    done = _shards_read(transcript)
    facts = []
    for m in transcript:                                       # a real summarizer is a model reading this; here: rule-based, VERBATIM
        if m["role"] == "user" and isinstance(m["content"], list):
            for b in m["content"]:
                if b.get("type") == "tool_result":
                    for line in FACT_LINE.findall(str(b["content"])):
                        if line not in facts:
                            facts.append(line)
    return (f"## Progress\nreviewed shards 1..{max(done)}; NEXT_SHARD={max(done) + 1}\n"
            "## Facts (verbatim)\n" + ("\n".join(facts) or "(none yet)") + "\n## Open questions\nfinal question not yet answered\n## Decisions\nnone")
