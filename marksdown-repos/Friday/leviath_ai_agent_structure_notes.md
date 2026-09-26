# Leviath: Adding Structure and Reliability to AI Agents

**Source:** https://seattle.aitinkerers.org/talks/rsvp_QI1WObTFGNU

> Notes based on the talk transcript provided with the request. The linked AI Tinkerers talk page is members-only. citeturn0view0

---

## 1. The Big Idea

The speaker, Gerald, has been experimenting with AI agents for almost a year.

He kept seeing the same problems:

- Agents don't always do what you ask.
- They hallucinate.
- They lose context during long-running tasks.
- They don't always verify their work.
- Long conversations eventually become too large for the context window.
- Developers either have to write lots of deterministic code around the agent or simply retry and hope it works.

His project, **Leviath**, explores a middle ground:

> Let the LLM do the work it is good at, while adding deterministic structure where reliability actually matters.

The project focuses on three major ideas:

```text
1. Structure
2. Stages
3. Better error handling
```

The main goal is to make agents **more reliable without turning every workflow into a large amount of traditional code**.

---

# 2. The Core Problem with AI Agents

A simple AI agent looks like:

```text
User
 ↓
LLM
 ↓
Tool
 ↓
LLM
 ↓
Tool
 ↓
Answer
```

This is powerful, but it can be unpredictable.

For example, you might ask:

> "Fix this bug, run the tests, and verify the solution."

The agent might:

```text
Read code
 ↓
Make change
 ↓
Forget to run tests
 ↓
Claim success
```

Or:

```text
Read 20 files
 ↓
Create a plan
 ↓
Continue for a long time
 ↓
Forget the original objective
```

The problem is not necessarily that the model is incapable.

The problem is that the **agent runtime doesn't provide enough structure**.

---

# 3. The Two Traditional Choices

According to the speaker, developers generally end up with one of two approaches.

### Approach 1: Write lots of deterministic code

You create explicit code for things such as:

```text
Run test
 ↓
Check exit code
 ↓
If failed → retry
 ↓
Check output
 ↓
Continue
```

This is reliable, but it can become cumbersome.

You end up writing a lot of orchestration code around the LLM.

### Approach 2: Trust the model

The other option is:

```text
Tell the agent what to do
 ↓
Hope it works
 ↓
If it fails → run again
```

This is easy but unreliable.

Leviath is trying to find the middle ground:

```text
LLM handles reasoning
        +
Runtime handles deterministic structure
```

---

# 4. Idea #1 — Structure the Context

One of the most interesting parts of Leviath is its approach to the **context window**.

Normally, we can think of the context as:

```text
Message 1
Message 2
Message 3
Message 4
...
Message 100
```

Eventually, the context becomes too large.

At that point, systems usually have to do something.

---

# 5. The Traditional Context Problem

There are two common approaches.

### Option A — Drop old messages

```text
[1][2][3][4][5][6][7][8][9][10]
 ↓
Remove [1][2][3]
```

Problem:

> Important information may disappear.

For example, the original task might have been:

> "Build a payment reconciliation service with exactly-once processing."

If that message gets removed, the agent may gradually lose the original objective.

---

### Option B — Compact the context

Another approach is summarization:

```text
100 messages
      ↓
Summary
      ↓
Smaller context
```

This saves tokens.

But summarization can also lose important details.

The summary might say:

> "User wants a payment service."

But the original conversation might have contained:

- specific constraints
- API contracts
- edge cases
- architectural decisions
- business rules

Some of those details may disappear.

---

# 6. Leviath's Context as Structured Memory

The speaker compares the idea to an old **Game Boy Advance memory structure**.

Instead of treating every piece of context equally, Leviath allows different pieces to have different retention rules.

For example:

```text
Task
 → NEVER EVICT

Plan
 → NEVER EVICT

Important files
 → NEVER EVICT

Old tool results
 → CAN COMPACT

Old conversation
 → CAN COMPACT
```

This is much more intelligent than:

```text
Everything = Same importance
```

The key idea is:

> **Context should have structure and priorities.**

---

# 7. Think of Context Like a Cache

A useful mental model is to think of the context window as a cache.

Not every piece of information deserves equal cache priority.

For example:

```text
┌───────────────────────────────┐
│ HIGH PRIORITY                 │
│                               │
│ Original task                 │
│ Current plan                  │
│ Important constraints         │
└───────────────────────────────┘

┌───────────────────────────────┐
│ LOWER PRIORITY                │
│                               │
│ Old tool outputs              │
│ Repeated conversation         │
│ Intermediate observations     │
└───────────────────────────────┘
```

When the context gets full:

```text
Keep high-value information
        +
Compact low-value information
```

This is similar to memory management in operating systems and caching systems.

---

# 8. Keep the Task Forever

One of the speaker's strongest examples is the task itself.

Imagine:

```text
User:
Build a REST API for payment reconciliation.
```

Why would the agent ever forget this?

But in a long-running conversation, context management can eventually remove or compress the original request.

Leviath allows the task to be marked as something that should **never be evicted**.

So:

```text
Task
 ↓
Permanent context
```

The agent always has access to its original objective.

---

# 9. Keep the Plan

The same concept applies to the agent's plan.

For example:

```text
Plan

[ ] Understand existing API
[ ] Identify reconciliation logic
[ ] Implement changes
[ ] Add tests
[ ] Run tests
[ ] Verify output
```

Instead of allowing this plan to disappear into old conversation history, Leviath can keep it as a structured object.

This makes the plan more like a **state machine/checklist** than ordinary chat text.

---

# 10. Compact Old Tool Calls

Now consider the opposite situation.

An agent may have executed:

```text
Tool 1
Tool 2
Tool 3
...
Tool 100
```

Keeping the full output of all 100 tools may be wasteful.

Some of those outputs may no longer matter.

Leviath can compact them:

```text
100 old tool calls
       ↓
Useful summary
       ↓
Small amount of context
```

So the context becomes:

```text
Important state → preserved
Old details     → compressed
```

---

# 11. Custom Context Rules

Leviath reportedly has built-in rules for different types of information.

But the speaker also mentioned support for custom scripting using **Rust**.

This means developers can define their own policies.

For example:

```text
IF information.type == "task"
    NEVER_EVICT

IF information.type == "tool_result"
    COMPACT_AFTER = 20 turns

IF information.type == "temporary_debug"
    EVICT_QUICKLY
```

The exact implementation can vary, but the architectural idea is powerful:

> **Context management becomes programmable.**

---

# 12. Idea #2 — Stages

Another major concept is **stages**.

Instead of treating the entire agent run as one giant loop, Leviath allows you to define different stages.

For example:

```text
Stage 1: Understand
        ↓
Stage 2: Plan
        ↓
Stage 3: Implement
        ↓
Stage 4: Test
        ↓
Stage 5: Verify
```

Each stage can run its own loop.

This provides structure around the agent.

---

# 13. Why Stages Matter

Without stages, an agent might behave like:

```text
Think
 ↓
Code
 ↓
Think
 ↓
Search
 ↓
Code
 ↓
Think
 ↓
Forget testing
 ↓
Finish
```

With stages:

```text
UNDERSTAND
    ↓
PLAN
    ↓
IMPLEMENT
    ↓
TEST
    ↓
VERIFY
```

The runtime knows what phase the agent is currently in.

This makes long-running agent workflows easier to reason about.

---

# 14. Stages Are Similar to Software Pipelines

Think about a CI/CD pipeline:

```text
Build
 ↓
Unit Test
 ↓
Integration Test
 ↓
Security Scan
 ↓
Deploy
```

You wouldn't normally allow the deployment stage to randomly skip the test stage.

Leviath applies a similar idea to agent workflows.

The LLM still makes decisions within the stage, but the overall workflow has structure.

---

# 15. Idea #3 — Better Error Handling

This is another important concept from the talk.

Imagine an agent is running tests.

The tests fail.

A basic agent might:

```text
Test failed
 ↓
Agent gets error
 ↓
Try something
 ↓
Maybe fix it
 ↓
Maybe give up
```

Leviath's stage model allows failure to become part of the workflow.

For example:

```text
Implement
   ↓
Run tests
   ↓
FAIL
   ↓
Return to implementation loop
   ↓
Fix
   ↓
Run tests again
   ↓
PASS
   ↓
Continue
```

The key idea is:

> **An error doesn't necessarily have to terminate the whole agent run.**

The runtime can decide how the workflow responds to the error.

---

# 16. Deterministic Where It Matters

This is probably the most important architectural principle behind Leviath.

LLMs are good at:

- Reasoning
- Generating code
- Explaining things
- Exploring alternatives
- Planning
- Interacting with tools

But deterministic code is better at:

- Checking exit codes
- Checking whether a file exists
- Validating schemas
- Running tests
- Enforcing limits
- Controlling workflow transitions
- Detecting success/failure

So instead of asking the LLM:

> "Did the tests pass?"

let the runtime determine it:

```text
pytest
 ↓
Exit code = 0
 ↓
PASS
```

Then the LLM can reason about what to do next.

---

# 17. LLM + Deterministic Runtime

A useful architecture is:

```text
                 ┌───────────────┐
                 │      LLM      │
                 │               │
                 │ Reasoning     │
                 │ Planning      │
                 │ Coding        │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │    Leviath    │
                 │    Runtime    │
                 │               │
                 │ Context       │
                 │ Stages        │
                 │ Errors        │
                 │ Policies      │
                 └───────┬───────┘
                         │
                         ▼
                    Tools / CLI
```

The LLM decides:

> "I think I should run the tests."

The runtime verifies:

> "The tests actually returned exit code 0."

---

# 18. Why This Is Useful for Long-Running Agents

Short tasks are relatively easy.

For example:

```text
Create a function to reverse a string.
```

An LLM can usually handle this in one interaction.

Long tasks are much harder:

```text
Understand repository
 ↓
Analyze architecture
 ↓
Modify multiple services
 ↓
Run tests
 ↓
Fix failures
 ↓
Run integration tests
 ↓
Review changes
 ↓
Deploy
```

The longer the workflow becomes, the more likely the agent is to:

- lose context
- forget requirements
- repeat work
- skip verification
- hallucinate completion

Structured state and stages help address these problems.

---

# 19. A Practical Example

Suppose you ask an agent:

> "Add authentication to this application."

A structured Leviath workflow could be:

```text
Stage 1 — Understand
    ↓
Read repository
    ↓
Identify authentication architecture

Stage 2 — Plan
    ↓
Create implementation checklist

Stage 3 — Implement
    ↓
Modify code

Stage 4 — Test
    ↓
Run unit tests
    ↓
If failure → return to Implement

Stage 5 — Verify
    ↓
Check API behavior
    ↓
Review changes

Stage 6 — Complete
```

And throughout the entire process:

```text
Original task → Never evict
Plan          → Never evict
Old tool logs → Compact
```

This is much more robust than simply giving the LLM one giant prompt.

---

# 20. Context Engineering Instead of Just Bigger Context

A common approach to solving agent memory problems is:

> "Give the model a bigger context window."

But bigger context is not always the best answer.

Consider:

```text
1 million tokens
```

containing:

- old tool outputs
- irrelevant logs
- repeated conversations
- temporary information
- important requirements

The model has more information, but not necessarily better information.

Leviath takes a different approach:

> **Organize the context instead of simply making it larger.**

So:

```text
Better context management
        >
Simply bigger context
```

at least for many long-running workflows.

---

# 21. Connection to Software Engineering

The architecture has similarities with traditional software engineering concepts.

### State management

```text
Task
Plan
Stage
Status
```

### Workflow orchestration

```text
Stage A → Stage B → Stage C
```

### Error handling

```text
Failure → Retry / Recovery / Escalation
```

### Caching

```text
Important state → Keep
Old state → Compact
```

### Deterministic validation

```text
Command exit code
Schema validation
Test results
```

The interesting part is combining these traditional engineering ideas with an LLM.

---

# 22. A Useful Mental Model

Think of a normal LLM agent as:

```text
LLM
+
Tools
+
Conversation
```

Leviath is closer to:

```text
                ┌───────────────┐
                │      LLM      │
                │   Reasoning   │
                └───────┬───────┘
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       Context        Stages       Errors
       Manager       Workflow      Recovery
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                      Tools
```

The runtime provides the **scaffolding**.

The model provides the **intelligence**.

---

# 23. Why This Approach Is Interesting

The key insight is:

> We don't necessarily need to make the LLM responsible for everything.

Instead:

```text
LLM:
"What should I do?"

Runtime:
"Here are the rules and state."

Deterministic system:
"Did it actually succeed?"

LLM:
"What should I do next?"
```

This division of responsibility can make agents more reliable.

---

# 24. Three Key Takeaways

### 1. Structure the Context

Don't treat every token or message equally.

Keep important information such as:

```text
Task
Plan
Critical constraints
```

while compacting:

```text
Old tool outputs
Old conversation
Temporary information
```

---

### 2. Use Stages for Long Workflows

Break long-running tasks into explicit phases:

```text
Understand
 ↓
Plan
 ↓
Implement
 ↓
Test
 ↓
Verify
```

This reduces the chance that the agent simply wanders through a huge conversation.

---

### 3. Use Deterministic Systems for Deterministic Questions

Don't ask an LLM to decide something that a CLI or program can verify exactly.

Instead of:

> "I think the tests passed."

Use:

```text
Run tests
 ↓
Exit code 0
 ↓
PASS
```

Let the LLM handle reasoning and let deterministic software handle verification.

---

# Final Takeaway

The biggest idea behind Leviath is:

> **Don't try to make the LLM responsible for the entire agent system.**

Give the model the part it is good at:

```text
Reason
Plan
Explore
Generate
Decide
```

Give deterministic software the parts it is good at:

```text
Track state
Manage context
Enforce workflow
Run checks
Verify results
Handle errors
```

The resulting architecture looks like:

```text
             ┌─────────────────┐
             │       LLM       │
             │                 │
             │ Reasoning       │
             │ Planning        │
             │ Coding          │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │    Leviath      │
             │                 │
             │ Context         │
             │ Stages          │
             │ State           │
             │ Error handling  │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Deterministic   │
             │ Tools / Tests   │
             └─────────────────┘
```

In one sentence:

**Leviath is an experiment in turning an LLM agent from a free-form conversation into a structured software system—where the model provides intelligence, while the runtime provides memory management, workflow structure, and deterministic verification.**
