# Project 13 — Context Engineering for Long-Running Agents

> **Motto:** what the model sees decides what it does.

An agent is a loop. Every turn it re-reads *everything* in its context window. On a 100-step task that window fills with old tool output, the bill grows
with the square of the task length, and — worst — the facts that matter get lost or buried. Context engineering is the craft of deciding, on every single
step, **what goes into the window, what stays out, and what is written somewhere safer.**

```
pip install -r requirements-dev.txt            # only pytest + ruff; the project has no runtime dependencies
python experiments/exp1_strategies.py          # nine strategies, one task, who remembers the step-3 fact?
python experiments/exp2_needle.py              # facts planted at shard 3 / 30 / 60 / 90 / 97, and honest-vs-confabulating models
python experiments/exp3_cache.py               # context edits vs prompt caching: why clearing a little every step is expensive
python experiments/exp4_jit_and_subagents.py   # retrieve just in time; isolate noisy work in a sub-agent
pytest -q                                      # 30 tests
```

## 1. The experiment (read this first; it is the whole project)

**World** (`world.py`): 100 log shards of boring text (~660 tokens each, 117k total). Two lines matter and are planted early:
`FACT: refund approval code is K7-ALPHA-2291` (shard 3) and `USER-CONSTRAINT: do not modify anything in region ap-south-1` (shard 7).
Decoys: a *revoked* code `K7-ALPHA-1180` and a line about the code *format*.
**Task:** read every shard, then answer "what is the current approval code and which region is frozen?"
**Window:** 30,000 tokens (small on purpose; real windows are bigger but real tasks are longer and noisier).

**Model** (`fake_model.py`): a *deterministic stand-in whose behaviour depends only on what is visible in its context.* If a fact was cleared, summarised away or never shown, it cannot
use it — exactly like a real model. It is not a language model and cannot show fuzzy failures (see §6).

### Result (from `exp1_strategies.py`)
| Strategy | What it does | Peak context | Final answer |
|---|---|---|---|
| `naive` | append forever | hits 30k at step ~25 | **overflow** — request rejected |
| `window` | keep first message + newest 8 | 21k | "cannot find" — facts fell out |
| `clear_results` | replace OLD tool results by a placeholder, keep the calls | 22k | "cannot find" — the facts lived only in cleared results |
| `clear_results+inputs` | also blank old call arguments | 22k | "cannot find" |
| `summarize_lossy` | old history → abstract summary | 21k | "cannot find" — summary said *"an approval code was encountered"* |
| `summarize_structured` | summary with required sections and **verbatim facts** | 21k | **correct** |
| `clear+ledger` | deterministic "must keep" block pinned in the system prompt | 22k | **correct** |
| `summarize_lossy+ledger` | lossy summary + verifier that re-inserts missing ledger items | 21k | **correct** |
| `clear+notes` | the agent writes notes to storage outside the window | 22k | **correct** (but ~12 extra steps) |

**The one-sentence lesson:** *managing the window is easy; not losing the thing you needed is the hard part, and it only works if something wrote the fact down in a place that is not being thrown away.*

### Result (from `exp2_needle.py`) — the "step-3 test"
```
strategy              N=3   N=30  N=60  N=90  N=97         (fact planted at shard N, question after shard 100)
window                LOST  LOST  LOST  ok    ok
clear_results         LOST  LOST  LOST  ok    ok
summarize_lossy       LOST  LOST  LOST  ok    ok
summarize_structured  ok    ok    ok    ok    ok
clear+ledger          ok    ok    ok    ok    ok
clear+notes           ok    ok    ok    ok    ok
```
Recency hides the problem. If you only test facts from the last few steps, every strategy looks fine. **Always test with an early fact.**

## 2. The anatomy of a context window
```
 ┌──────────────────────────────────────────────────────────────────────────────┐  <- the window (a budget in tokens)
 │ tools      (names, descriptions, schemas)       stable, cacheable              │
 │ system     (role, rules, pinned <must_keep>)    stable, cacheable              │
 │ ───────────── cache breakpoint ──────────────────────────────────────────────  │
 │ user task                                                                      │
 │ assistant: tool_use  read_log(1)      ┐                                        │
 │ user:      tool_result  <660 tokens>  ┘  repeated 100 times = the noise        │
 │ ...                                                                            │
 │ newest few turns                         <- what the model actually pays attention to best │
 └──────────────────────────────────────────────────────────────────────────────┘
```
Four kinds of content, four policies:
| Content | Policy |
|---|---|
| Rules and goals | pin; keep short; re-state near the end if they matter (see §6) |
| **Facts that must survive** | write them down *outside* what gets cleared: ledger, notes, structured summary |
| Bulky observations (tool results) | clear when old; keep the *call* so the agent knows what it did; keep a pointer to re-fetch |
| Raw history | audit log only (`ContextManager.transcript` is never edited; only the *view* is) |

## 3. The techniques, one by one

### 3.1 Token budgeting
Know the number before you send. `tokens.py` uses chars/4 so everything runs offline; for real work use the API's free `count_tokens` endpoint
(`client.messages.count_tokens`; rate limited; counts can differ slightly from billing; newer tokenizers produce noticeably more tokens for the same text, so count against the model you will actually use).
Set **two** thresholds: a *trigger* (start managing at 70%) and a hard *budget*. Never run at 100%: you need room for the answer and for the next tool result.

### 3.2 Tool-result clearing (`ContextManager._clear_results`)
Replace old results with `[cleared to save context: result of read_log(shard=12), ~662 tokens]`. Keep the newest N intact. Keep the **calls**: they are tiny and they are the agent's memory of *what it already did*
(that is why progress survives in this project; with `clear_results+inputs` you lose even that, which is why it is an option you should use carefully).
Anthropic's server-side version (`clear_tool_uses`, beta) exposes exactly these knobs: `trigger`, `keep`, `clear_at_least`, `exclude_tools`, `clear_tool_inputs` — see `live_context_editing.py`.

### 3.3 Sliding window (`_window`)
Cheapest and bluntest. Rules that bite: never start the window on an orphan `tool_result` (the API requires every result to follow its `tool_use`), always keep the first user message (the task).

### 3.4 Summarisation / compaction (`_summarize`)
Replace the old middle by a summary. Two summarisers in `context_manager.py`:
* **lossy** — what a casual "summarise the conversation" produces: progress and mood, no exact values.
* **structured** — required sections: Progress (with the *next step*), Facts **verbatim**, Open questions, Decisions.
Rules: (1) ask for exact values and identifiers verbatim; (2) include the next action so work can resume; (3) **verify** the summary against a must-keep list and re-insert what is missing
(`verify_summary` / the ledger); (4) summarising is a model call, so it costs tokens and time; (5) it breaks the cached prefix (§4).
Anthropic recommends server-side compaction for most uses and notes it is less suitable when precise recall of early details is needed — which is the point of this project.

### 3.5 The must-keep ledger (`ledger=True`)
Code (not a model) extracts lines matching `FACT:` / `USER-CONSTRAINT:` from every tool result as it arrives and pins them into the system prompt. It is deterministic, cheap and auditable.
The weakness is obvious: you must know in advance what "important" looks like. In real systems the ledger rules come from the domain: account numbers, user instructions, decisions, error codes, ids.
Pin changes only when a *new* fact appears, so they break the cache rarely.

### 3.6 Agent-written notes / memory (`clear+notes`)
Give the agent `write_note` / `read_notes` (a file or the memory tool). It decides what matters, and the notes live outside the window; read them back when needed.
Costs: extra steps (113 vs 101 here), and **it only works if the agent actually writes the note** — add a nudge when context nears the threshold (Anthropic's docs describe a warning to save to memory before results are cleared).
Exclude the notes tool from clearing (`exclude_tools`).

### 3.7 Just-in-time retrieval (`exp4` B)
Do not carry the corpus; carry *references* (shard numbers, file paths, ids) and fetch slices on demand. Stuffing all 100 shards = 117,370 tokens (impossible here);
two searches and one read = 1,213 tokens. Needs a good search tool: a weak one means the agent never sees what it needed. Return previews + handles, not entire files.

### 3.8 Sub-agents for context isolation (`subagent.py`, `exp4` C)
Hand the noisy sub-task to a helper with its own window; keep only its short report (42 tokens here). **This protects the parent's window; it does not reduce total tokens** —
the sub-agent still read 117k tokens and its loop billed 1.58M input tokens. Make the report structured and verbatim, with pointers to sources.

## 4. Context management vs prompt caching (Project 12 meets Project 13)
Every edit to an *earlier* part of the prompt invalidates the cached prefix from that point. `exp3_cache.py`:
```
strategy              prefix breaks   cost, no cache   cost, with cache
naive (to overflow)   0               372,168          71,351   (0.19)   append-only: perfect cache
clear_eager           64              1,926,383        1,553,767 (0.81)  edits a little every step -> rewrites the prefix every step
clear_results (70%->40%) 10           1,581,174        395,558  (0.25)
clear_batch  (70%->30%)  8            1,446,802        335,586  (0.23)
summarize_structured  6               1,271,156        295,093  (0.23)
```
Design rules: **trigger → clear a lot → append-only for a while.** Use a minimum-to-clear (`clear_at_least`) so each cache rewrite is worth it. Put pinned facts in a block that changes rarely. Do not reorder or
timestamp anything in the prefix. (Units: 1.0 per input token uncached; unchanged prefix 0.1; changed part 1.25. See Project 12.)

## 5. Decision guide
| Situation | Use |
|---|---|
| Output is bulky and mostly noise (logs, pages, search results) | tool-result clearing in batches + keep the calls |
| A few exact facts must survive (ids, user rules, decisions) | ledger and/or notes; never rely on a summary alone |
| Long chat with a human | structured summary of old turns + recent turns verbatim |
| Huge corpus | do not load it: search, handles, slices |
| Messy exploration that only needs a conclusion | sub-agent returning a structured report |
| Many parallel workers | each has its own window; merge reports, not transcripts |
| Cost matters | batch edits, stable prefix, count cache hit rate |

## 6. What this project cannot show you (be honest about it)
* Real models do **not** use a window uniformly. Facts in the **middle** of a very long context are used less reliably than facts at the start or end ("lost in the middle"),
  and instructions at the top can lose force as the window fills. The fake model here uses everything visible perfectly, so it *understates* the real problem.
  Mitigations: keep rules short; **recite** the current goals/to-do list at the *end* of the context each turn (a rolling `todo`); keep contexts small instead of full.
* The summarisers are **rule-based**. A real summariser (a model) will sometimes drop a fact even when asked not to — which is why the verifier/ledger exists.
* The "confabulating" mode (`exp2`) models a guess; real models vary in how readily they guess. Evals should include "answer is absent from context" cases (Project 15).
* Numbers (660 tokens/shard, 30k window) are chosen to make effects visible in seconds.

## 7. Architect's checklist
1. Budget measured with a real token counter; trigger at ~70%. 2. A written list of what must survive, and where each item is stored. 3. Old tool output cleared in batches, calls kept.
4. Summaries are structured, verbatim for identifiers, and verified against the list. 5. Notes tool excluded from clearing; nudge the agent to use it. 6. Prefix kept stable; cache hit rate watched.
7. A **step-3-at-step-90 test** in CI. 8. Eval for "fact absent → say so". 9. Full transcript kept for audit even when the view is trimmed. 10. Per-task token and cost ceiling with a clean abort.

## 8. Exercises
1. Add a `todo` list the agent rewrites every few steps and re-inserts at the *end* of the view; measure which strategies keep working when `clear_inputs` removes old calls.
2. Make the fake model "lose" facts in the middle (e.g. visible only if within the first 20% or last 30% of tokens). Which strategies survive now?
3. Implement `clear_at_least`: skip clearing unless it frees ≥ N tokens; show the cost curve vs N.
4. Replace `structured_summary` with a real model call (see `live_context_editing.py` for the client) and write the verifier that checks the ledger items appear verbatim.
5. Add a second fact whose *value changes* later ("code rotated to K7-BETA-5530 at shard 70"). Does the ledger keep the stale one? Design the supersede rule.
6. Add a token ceiling per task and make the agent end with a partial result and a reason instead of overflowing.
