# Project 19 — Agent Frameworks, Explained Simply

> One line: a framework is **a manager that remembers where the work is**, so the work can stop, crash, wait for a human, and carry on without starting over.

---

## 1. The story (a refund desk)

A customer writes: *"Refund my order ORD-1002."*

Things that must happen: understand the request, find the order, get a manager's OK if the amount is large, pay the money, email the customer.

Without a framework this is one Python function. It works until something goes wrong:

```
  function refund():
      classify  ->  lookup  ->  (ask manager?)  ->  PAY  ->  EMAIL
                                      |                         |
                          manager answers tomorrow.        email service is down.
                          your program is gone.            do we pay again on retry?
```

The framework solves exactly these problems.

---

## 2. The big picture (what is in the box)

```
 +--------------------------------------------------------------+
 |                        YOUR BUSINESS CODE                    |
 |        (Shop, order lookup, refund, email - plain Python)    |
 +------------------------------+-------------------------------+
                                |  called by
 +------------------------------v-------------------------------+
 |                   THE FRAMEWORK (miniflow)                   |
 |                                                              |
 |   1. STATE         the shared notebook                       |
 |   2. GRAPH         nodes + arrows = who runs next            |
 |   3. CHECKPOINTS   save a photo after every step             |
 |   4. INTERRUPT     pause and wait for a human                |
 |   5. AGENTS        handoffs between specialists              |
 |   6. GUARDRAILS    rules the model cannot argue with         |
 |   7. TRACING       a diary of everything that ran            |
 +--------------------------------------------------------------+
```

Seven ideas. Every real framework (LangGraph, OpenAI Agents SDK, Claude Agent SDK ...) is these seven in different clothes.

---

## 3. Workflow vs Agent

```
  WORKFLOW  (you draw the road)            AGENT  (the model drives)

   A ---> B ---> C                          +-----------------+
         |                                  |  model thinks   |<----+
         +---> D                            +--------+--------+     |
                                                     |              |
   predictable, testable, cheap             picks a tool, runs it --+
                                            flexible, less predictable
```

Project 19 has both: a **graph** (workflow, Sections 4-7) and a **team of agents** (Section 8).

---

## 4. The graph: nodes and arrows

A **node** = one small job. An **arrow** (edge) = what comes next. A **router** = an arrow that picks a path by looking at the state.

```
                                    +--------------+
                              +---->| reply_error  |----> END
                              |     +--------------+
                   not found /
                   or not a refund
 +----------+    +--------+  |
 | classify |--->| lookup |--+--- amount <= 100 ---+
 +----------+    +--------+  |                    |
                             |                    v
                             |              +----------+    +--------+
                             |              |  refund  |--->| notify |--> END
                             |              +----------+    +--------+
                             |                    ^
                             +--- amount > 100    |  yes
                                      |           |
                                      v           |
                                 +----------+     |
                                 | approve  |-----+
                                 |  (PAUSE) |
                                 +----+-----+
                                      | no
                                      v
                                 +--------------+
                                 | reply_denied |--> END
                                 +--------------+
```

Important: **nodes never call each other.** The engine reads the arrows and decides.

---

## 5. State and reducers (the shared notebook)

All nodes read and write one notebook (the **state**). A node does not scribble in it. It **returns a change**, and the engine merges it.

```
   state before            node returns              state after
 +----------------+      +----------------+      +--------------------+
 | request: ...   |      | order_id:      |      | request: ...       |
 | log: [a]       |  +   |   "ORD-1002"   |  =   | order_id: ORD-1002 |
 +----------------+      | log: ["b"]     |      | log: [a, b]        |
                         +----------------+      +--------------------+
                                     \
                              the REDUCER decides how to merge
                              overwrite -> replace    append -> add to list
```

### Why reducers matter: two branches write at the same time

```
                     +--> search_web  --> findings: ["web: fees 2%"]  --+
        plan  -------+                                                   +--> synthesize
                     +--> search_docs --> findings: ["docs: fees 1.8%"]-+

   overwrite reducer:  findings = ["web: fees 2%"]               <- one source LOST, no error!
   append reducer:     findings = ["docs ...", "web ..."]        <- both kept
```

Rule: for every key that two branches may write, decide how they combine. Silent data loss is the worst kind.

---

## 6. Checkpoints (a photo after every step)

After each step the engine saves: *where are we, what is the state, what runs next.*

```
 step 0        step 1        step 2        step 3         step 4
 [classify] -> [lookup]  ->  [refund]  ->  [notify]  ->  [done]
    |             |             |             |             |
    v             v             v             v             v
  photo 0       photo 1       photo 2       photo 3       photo 4
```

### 6a. Crash recovery

The email service fails at step 3. You do not start over.

```
  first run :  classify -> lookup -> refund (money moved) -> notify  X  FAILS
                                                                |
                                          photo 3 saved: "next = notify"
  resume    :                                                   notify -> OK
               ^ only the failed step re-runs. Money was paid once.
```

### 6b. The dangerous trap (the most important lesson)

What if the **payment worked** but the reply was lost (timeout)? The photo only says "refund did not finish". So on resume it runs refund **again**.

```
  WITHOUT idempotency key              WITH idempotency key

  refund() -> money moves  (1)         refund(key="refund:ORD-1001") -> money moves (1)
  ...timeout...                        ...timeout...
  refund() -> money moves  (2) !!      refund(key="refund:ORD-1001") -> "already done, here is the old result"

  customer refunded TWICE              customer refunded ONCE
```

> Frameworks give you **"at least once"**. To get **"exactly once"** you add an **idempotency key** to every external action (payments, emails, tickets).

### 6c. Time travel (fork)

Copy an old photo into a new thread, change a value, run again. The original is untouched.

```
 original thread:  p0 --- p1 --- p2 --- p3 --- p4         (finished)
                          \
 forked thread:            p1' (order_id changed to ORD-1002) --- lookup --- PAUSE (needs approval)
```

Warning: a replay re-runs later steps, including side effects. The refund was protected by its key; the email was sent twice because `notify` has no key.

---

## 7. Human in the loop (pause for approval)

A node can call `interrupt(question)`. The whole run stops and is saved.

```
  PROCESS 1 (today)                              PROCESS 2 (tomorrow, new program)
  -----------------                              ---------------------------------
  classify                                       reads the saved photo from the database
  lookup
  approve --> "Approve 240 for ORD-1002?"        manager says YES
      |                                                |
      +--> state saved to database --------------------+
      |                                          approve (continues)
  process exits                                  refund -> notify -> done
```

### The re-run trap

When resumed, the pausing node starts **again from its first line**.

```
  BAD node                                GOOD design
  --------                                -----------
  send_email("under review")  <- runs     node 1: send_email      (saved, never repeated)
  ask_human()  <- PAUSE                   node 2: ask_human       (pauses and resumes safely)
  (on resume: email sent AGAIN)
```

Rule: **a node that can pause must be safe to run twice.**

---

## 8. Team of agents (handoffs)

Here the *model* chooses. Triage does not solve problems. It hands over.

```
                        customer: "I want my money back for ORD-1001"
                                          |
                                          v
                                  +---------------+
                                  |    TRIAGE     |   tools: none (only transfers)
                                  +-------+-------+
                          transfer_to_    |    transfer_to_
                            refunds       |      billing
                      +-------------------+-------------------+
                      v                                       v
              +---------------+                       +---------------+
              |    REFUNDS    |                       |    BILLING    |
              | lookup_order  |                       | get_invoice   |
              | issue_refund  |                       +---------------+
              +---------------+
```

A handoff is **just a tool call** that changes *which agent speaks next*. The chat history is shared.

The actual trace of one run:

```
  model:triage    ->  "transfer_to_refunds"
  handoff           triage -> refunds
  model:refunds   ->  lookup_order(ORD-1001)       tool runs
  model:refunds   ->  issue_refund(59)             tool runs
  model:refunds   ->  "Done: refund RF-1 issued."
  output guardrail    checks the final text
```

Each agent has its own **allow-list of tools**. If triage tries `admin_override`, it gets an error back.

---

## 9. Guardrails (rules in code, outside the model)

```
   user text
      |
      v
 [ INPUT GUARDRAIL ]  "ignore previous instructions"?  -> BLOCK, no model call at all
      |
      v
   model decides: issue_refund(240)
      |
      v
 [ TOOL HOOK ]  amount > 100 ?  -> DENIED, money never moves, agent told to escalate
      |
      v
   tool runs
      |
      v
   model writes answer
      |
      v
 [ OUTPUT GUARDRAIL ]  contains an email address?  -> BLOCK
      |
      v
   user sees answer
```

Put the **dangerous limit before the action** (tool hook), not after the text is written. Blocking a sentence after the money moved is too late.

Also: two agents can bounce the user forever. `max_handoffs` stops that (`handoff_loop`).

---

## 10. Tracing (the diary)

Every node, model call, tool call, guardrail and handoff is a **span** in a tree:

```
 run
  |- guardrail  injection_guard
  |- model      triage
  |- handoff    triage -> refunds
  |- model      refunds
  |- tool       lookup_order
  |- model      refunds
  |- tool       issue_refund
  `- guardrail  pii_guard
```

When something goes wrong at 3 a.m., this tree is how you find out why.

---

## 11. Do I even need a framework?

The same refund logic as a plain 11-line function and a 31-line graph gave **identical answers** on easy inputs.

```
                         plain function     graph framework
  easy, linear flow          BEST               overkill
  retry just one step        re-runs all        re-runs only the failed step
  wait a day for a human     very hard          built in
  see what ran               add logging        free
  replay from the middle     hard               fork
  parallel branches          locks + glue       reducers
```

Costs of a framework: new vocabulary, state must be JSON-friendly, upgrades can change behaviour, and you **still** need idempotency keys, re-run-safe nodes and step limits.

### Quick decision guide

```
  Short, linear, one process, no waiting ------> plain function or loop
  Need pause / resume / per-step retry --------> graph with checkpoints
  Model chooses the path ----------------------> agent loop
  Specialists with different tools ------------> handoffs (try ONE agent first)
  Long-running, many users, approvals ---------> framework earns its keep
```

Stay portable: keep business code in plain functions; make the graph a thin wiring layer.

---

## 12. Map of the project files

```
 project19-agent-frameworks/
 |
 |- miniflow/                   <- the mini framework
 |    |- state.py               reducers (overwrite, append, merge)
 |    |- graph.py               nodes, edges, routers, supersteps, interrupt, fork
 |    |- checkpoint.py          memory + sqlite savers
 |    |- agents.py              handoffs, guardrails, hooks
 |    `- trace.py               the span tree
 |
 |- scenario.py                 refund desk: Shop (ledger + outbox), graph, agents, fake model
 |
 |- experiments/
 |    |- exp1_graph.py          routing, parallel branches, reducers, loop limit
 |    |- exp2_checkpoints.py    crash recovery, duplicate payment, time travel
 |    |- exp3_human_in_loop.py  pause, new process resumes, re-run trap
 |    |- exp4_agents_...py      handoffs, guardrails, ping-pong
 |    `- exp5_framework_or_not.py  function vs graph
 |
 `- tests/                      32 tests
```

Run any experiment: `python experiments/exp2_checkpoints.py`

---

## 13. Remember these five lines

1. **Nodes return changes; reducers merge them.** Decide what happens when two branches write the same key.
2. **A checkpoint is a photo after every step.** It gives you resume, retry, pause and fork.
3. **At-least-once + idempotency key = exactly-once.** Every external action needs a key.
4. **A node that pauses runs again from its top.** Keep it free of side effects.
5. **Guardrails and tool limits live in code, before the action.** The model cannot talk its way past them.

*Honest limits: all models are scripted, no real framework (LangGraph etc.) was run, and miniflow is a teaching engine without real concurrency, retries or auth on resume.*
