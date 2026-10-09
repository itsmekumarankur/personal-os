# Project 19 — Agent frameworks: what they actually do for you (and what they cost)

LangGraph, the OpenAI Agents SDK, the Claude Agent SDK, CrewAI, AutoGen, Strands ... they look different, but underneath
they sell the same handful of ideas. Instead of learning one library's API (which will change), this project **builds the ideas in ~450 lines**
(`miniflow/`), so you can see each one work, break, and recover. Then you can read any framework's docs and recognise the parts.

Nothing here calls a real model or installs a framework. The scenario is a customer-support refund desk with **real side effects**
(a money ledger and an outbox), so duplicates and double-sends are visible, not theoretical. Stdlib only.

```
python experiments/exp1_graph.py                       # state, reducers, routing, parallel branches, loop brakes
python experiments/exp2_checkpoints.py                 # crash recovery, the duplicate-payment trap, time travel
python experiments/exp3_human_in_loop.py               # pause, exit the process, resume in ANOTHER process; code-before-interrupt trap
python experiments/exp4_agents_handoffs_guardrails.py  # handoffs, per-agent tools, guardrails, hooks, ping-pong
python experiments/exp5_framework_or_not.py            # same logic as a plain function vs a graph; the decision guide
python -m pytest -q                                    # 32 tests
```

---
## 1. First, the vocabulary that sorts every framework

Anthropic's "Building effective agents" draws the line this project follows:

* **Workflow** — the PATH is decided by your code (A, then B, then C, with branches). The model fills in steps. Predictable, testable, cheap. → *graph runtimes*.
* **Agent** — the MODEL decides the next step in a loop with tools. Flexible, less predictable. → *agent loops* (Project 17), *handoff* teams.
* Real systems mix them: a workflow whose one step is an agent, or an agent that calls a workflow as a tool.

A framework is mostly **infrastructure around that loop or graph**: state, persistence, pausing, tracing, guardrails, retries. Ask of any framework:
"which of these seven things does it give me, and do I need them yet?"

| # | Capability | Plain code needs | miniflow shows it in |
|---|---|---|---|
| 1 | **State** with defined merge rules | dicts + discipline | `state.py`, exp1-C |
| 2 | **Control flow** the engine owns (nodes, edges, routers, cycles + brakes) | if/else/while | `graph.py`, exp1 |
| 3 | **Checkpoints**: save after each step → resume, retry one step, fork | your own DB tables | `checkpoint.py`, exp2 |
| 4 | **Human in the loop**: pause, wait for days, resume anywhere | queue + state table + auth | `Ctx.interrupt`, exp3 |
| 5 | **Multi-agent**: handoffs, per-agent tools | message plumbing | `agents.py`, exp4 |
| 6 | **Guardrails + hooks**: checks outside the model | wrappers around tools | exp4 |
| 7 | **Tracing**: a span tree of everything that ran | logging in every function | `trace.py`, exp1-A, exp4-A |

---
## 2. Graph workflows (`miniflow/graph.py`)

```
classify ─> lookup ─(order not found / not a refund)─> reply_error ─> END
                   ├─(amount <= 100)─> refund ─> notify ─> END
                   └─(amount  > 100)─> approve ⏸ (human) ─(yes)─> refund ─> notify ─> END
                                                           └(no)─> reply_denied ─> END
```
* A **node** is `state -> update`. It never edits the state; it returns the *change*. The engine merges it.
* A **router** is a function of the state that names the next node(s). The nodes never call each other.
* **Supersteps**: every node that is due runs against the *same* input state, then all updates are merged. Two edges into one node is a **join**:
  it runs once, after both branches. (exp1-C)
* **Reducers** decide how two writes to one key combine. Default overwrite = "last one wins" = **silent data loss** in parallel branches
  (exp1-C: the answer is built on 1 of 2 sources, no error). `append` keeps both. In real frameworks the winner of an overwrite may also depend on timing, so treat it as a bug.
* **Brakes**: any cycle needs a step limit (LangGraph calls it the recursion limit). Exp1-D: a loop that never converges ends `step_limit`, not a bill.
* `compile()` validates the graph: dangling nodes and edges to unknown nodes fail at build time, not at 3 a.m.

## 3. Checkpoints and what they do NOT promise (`checkpoint.py`, exp2)

After every superstep the engine stores `(thread, step, state, next nodes, status)`. Consequences you can see:

* **Resume after failure (exp2-A)**: the email step timed out; `invoke(None, thread)` re-ran *only* `notify`. The payment (one refund attempt) was not repeated.
* **THE trap (exp2-B)**: the payment provider *did* take the money, then the call timed out. The checkpoint only knows "refund did not finish", so on resume it runs again:
  ```
  no idempotency key    2 refund(s) in the ledger     <- customer refunded twice
  with idempotency key  1 refund(s) in the ledger     <- 2 calls made, 1 payment
  ```
  Frameworks give you **at-least-once** execution of a node. **Exactly-once effects = at-least-once + idempotency key.** Every external side effect (payments, emails, tickets, deploys) needs one. This is the most important sentence in the project.
* **Time travel (exp2-C)**: `history()` lists every checkpoint; `fork(thread, step, new_thread, patch)` copies one into a new thread. "What if classify had picked ORD-1002?" ran
  from step 1 without re-running classify, ended at the approval pause, and the original thread was untouched. Caveat shown in the same experiment: **a replay re-executes later side effects** — payment was protected by its key, the email was sent twice because `notify` has no key.
* **Memory = same thread id**. A new input on an existing thread continues its state (tested).
* **Durable store** (`SqliteCheckpointer`): state must be JSON-serialisable — no live clients, no lambdas, no file handles in state. This is a real design constraint of all such frameworks.
* A sibling node that already finished in a superstep is stored as a *pending write* and is not re-run when another sibling fails (tested).

## 4. Human in the loop (`Ctx.interrupt`, exp3)

`ctx.interrupt(question)` stops the whole run and saves it. `invoke(resume=answer)` later continues; `interrupt()` now *returns* the answer.

* Exp3-A: process 1 pauses at "Approve refund of 240.0 for ORD-1002?"; money moved: 0. Then a **brand-new Python process** with new objects and only the sqlite file resumes, the manager approves, the refund happens in process 2.
* **Trap (exp3-C)**: on resume the interrupting node runs **again from its first line**. A side effect before `interrupt()` fires twice (2 emails); put it in its own earlier node and it fires once (checkpointed). Rule: *a node that can pause must be safe to re-run.*
* Production questions this toy skips on purpose: Who may answer? (the resume endpoint needs authentication/authorisation) What if nobody answers? (timeout → deny by default) Where is the decision recorded? (`state["approver"]`) Can the same approval be replayed?

## 5. Teams of agents (`miniflow/agents.py`, exp4)

Two patterns, easy to confuse:
* **Handoff** — control *transfers*. Triage calls `transfer_to_refunds`; now the refunds agent (own instructions, own tools) answers the user.
* **Agent-as-tool** — control *stays*; a manager calls a specialist like a function and gets a result back (Projects 6, 13).

A handoff is **just a tool call** whose effect is "change which agent the next model call uses". The trace (exp4-A) shows it:
`model:triage → handoff triage→refunds → model:refunds → tool lookup_order → model:refunds → tool issue_refund → model:refunds → guardrail`.
Message history is shared, so the specialist sees the original request. (Real SDKs can filter/trim the history on handoff; here it is passed whole.)

Eight situations (exp4-B):
| situation | what happens |
|---|---|
| small refund | triage → refunds, paid 1 |
| large refund | the model *did* call `issue_refund(240)`; the **tool hook** denied it, nothing paid, agent escalates |
| prompt injection | **input guardrail** blocks before any model call |
| billing leaks an email | **output guardrail** blocks the answer |
| triage calls a tool it doesn't own | error returned to the model (per-agent allow-list) |
| agents bounce the user | `handoff_loop` after `max_handoffs` |
| unknown order | agent says it can't find it |

Where guardrails belong: the **limit on refunds is a tool hook (before the action)**, not an output filter (after the damage). Guardrails are code outside the model, so a prompt cannot argue with them. They are also *incomplete* (regex here; a small classifier model in real systems), so they sit **on top of** least-privilege tools and sandboxes (Project 17), not instead.

**Do you need several agents at all?** Each agent adds a model call, a prompt to maintain, and a place to lose context. First try one agent with a good tool set. Split when instructions or tool lists genuinely conflict, when a specialist needs a different model or permission level, or when you want to isolate context (Project 13).

## 6. Tracing and hooks
`Tracer.span()` wraps every node, model call, tool call, guardrail and handoff into a tree with durations and attributes. `hooks={"before_node": ..., "after_node": ...}` and `before_tool` / `on_handoff` are the extension points for audit logs, metrics, cost tracking and policy. Frameworks standardise this so any tracing backend can read it (Project 15 covers the backend side).

## 7. Do you need a framework? (exp5)
The same business logic as an 11-line function and a 31-line graph give **identical answers** on easy inputs. The graph wins only when you ask for: retry of one step (measured: function re-ran the payment call, graph did not), waiting a day for a person, step-level visibility, replay from the middle, safe parallel merge. It costs: vocabulary, serialisable state, abstraction leaks (you still need idempotency, re-run-safe nodes, step limits), upgrade churn, and framework-shaped stack traces.

**Decision guide**
* linear, short, one process, no pauses → a function or a simple loop. No framework.
* pause/resume, per-step retry, audit trail → graph runtime with durable checkpoints.
* model chooses the path → agent loop; add a framework only for the pieces you don't want to write (tracing, sessions, guardrails).
* specialists with different tools/permissions → handoffs, after trying one agent.
* long-running, many users, approvals → durable checkpoints + queue + authenticated resume. Here frameworks pay for themselves.

**Staying portable**: keep business logic (`Shop`, order lookup) in plain functions with no framework imports; make the graph/agent definition a thin wiring layer; keep state small and JSON; wrap framework calls behind your own `run(request)` function; pin versions and re-run your experiments/tests on upgrade.

## 8. Mapping to real frameworks (concepts only — verify names and APIs in current docs; I did not run any of them here)
| miniflow | LangGraph | OpenAI Agents SDK | Claude Agent SDK / Claude Code |
|---|---|---|---|
| `Graph`, nodes, edges, routers | `StateGraph`, nodes, conditional edges | (agent loop; not graph-first) | (agent loop) |
| reducers | state schema with reducer annotations | — | — |
| `MemoryCheckpointer` / `Sqlite…` | checkpointers (memory, sqlite, postgres …) | sessions | session resume |
| `thread` | `thread_id` | session id | session id |
| `ctx.interrupt` / `invoke(resume=)` | `interrupt()` / resume with a command | — | permission prompts, hooks |
| `fork` | time travel / update state | — | — |
| `Agent`, `handoffs` | (multi-agent patterns built from graphs) | `Agent`, handoffs | subagents |
| guardrails | (your nodes/conditions) | input/output guardrails | permissions, hooks |
| `Tracer` | LangSmith / OpenTelemetry integration | built-in tracing | hooks / transcripts |
Others (CrewAI, AutoGen, Strands, Google ADK ...) emphasise roles/conversations/model-driven loops; the same seven capabilities apply. Use the table in section 1 as a checklist when evaluating one.

## 9. Production checklist
* Idempotency key on every external write. Test by killing the process *after* the write.
* Nodes safe to re-run; side effects in their own nodes; nothing before `interrupt()`.
* Step limit on every cycle; `max_handoffs`; per-job cost/time budget (Project 14/17 ideas).
* Durable checkpointer (Postgres/SQLite file), migration plan for state-schema changes (old checkpoints must still load!), retention/PII policy for stored state.
* Authenticated resume endpoint; approval timeout; audit of who approved what.
* Tool allow-list per agent; policy hooks in code; sandbox for code execution (Project 17).
* Trace every run; alert on `error`, `step_limit`, `handoff_loop`, guardrail trips.
* Pin framework versions; keep the business logic framework-free.

## 10. Exercises
1. In exp1-C, make a third branch write the same key. Add a reducer that dedupes. 
2. Add a `retry(n, backoff)` wrapper for nodes. Which failures should NOT be retried (hint: non-idempotent, or deterministic bugs)?
3. Add an approval **timeout**: after N seconds a paused thread is auto-denied. Where does the timer live if the process is not running?
4. Change the state shape (rename `order_id`) and try to resume an old checkpoint. What breaks? Design a migration.
5. Make `notify` idempotent and re-run exp2-C. 
6. Implement agent-as-tool next to handoff: a `policy_checker` agent the refunds agent calls and gets an answer back from.
7. Add streaming of node events (`yield` per superstep) like Project 12.
8. Port the refund graph to a real framework of your choice and compare against exp1-3: which behaviours match, which surprise you?

## Honest limits
* Models are scripted; no real LLM calls and no real framework was installed or run. Section 8 is conceptual and from memory — check current docs.
* miniflow is a teaching engine: nodes run sequentially within a superstep (no real concurrency), no streaming, no retries, no schema migration, no auth on resume.
* Only the first row of exp5-B is measured; the other rows describe capabilities demonstrated elsewhere in the project.
* Guardrails are regexes. Idempotency here is an in-memory dict standing in for a payment provider's feature.
