# Building Effective AI Agents — Easy Notes

**Source:** Anthropic — Building Effective Agents  
https://www.anthropic.com/engineering/building-effective-agents

> **Core idea:** Don't start by building a complicated AI agent. Start simple → measure → add complexity only when it improves the result.

---

# 1. Workflow vs Agent

## Workflow

You decide the steps in advance.

```text
User
  |
  v
[Step 1]
  |
  v
[Step 2]
  |
  v
[Step 3]
  |
  v
Answer
```

Example:

```text
Write Article
     |
     v
Create Outline
     |
     v
Review Outline
     |
     v
Write Article
```

The **developer controls the flow**.

## Agent

The LLM decides what to do next.

```text
              +----------------+
              |      LLM       |
              |  "What next?"  |
              +-------+--------+
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Search       API        Database
          |           |           |
          +-----------+-----------+
                      |
                      v
                  Observe
                      |
                      v
                 LLM decides
                   again
```

The **LLM controls the flow**.

---

# 2. Don't Build an Agent Just Because You Can

Think like an architect:

```text
                 START
                   |
                   v
            Can one LLM call
              solve it?
             /                     YES           NO
            |             |
            v             v
       Simple LLM      Need steps?
                         |
                    +----+----+
                    |         |
                   YES        NO
                    |         |
                    v         v
                 Workflow   Agent
```

Sometimes:

```text
Prompt + RAG + One LLM
```

is better than:

```text
5 Agents
+ 12 Tools
+ Memory
+ Planner
+ Evaluator
+ Framework
```

More complexity means:

```text
Complexity ↑
    |
    +---- Cost ↑
    +---- Latency ↑
    +---- Failure points ↑
    +---- Debugging difficulty ↑
```

---

# 3. Basic Building Block: Augmented LLM

A normal LLM:

```text
User ---> LLM ---> Answer
```

An **augmented LLM** has additional capabilities:

```text
                 +-------------+
                 |     LLM     |
                 +------+------+
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
    Retrieval         Tools          Memory
        |               |               |
        +---------------+---------------+
                        |
                        v
                      Answer
```

Remember:

> **Agent = LLM + tools + feedback + decision-making loop**

---

# 4. Five Important Workflow Patterns

## Pattern 1 — Prompt Chaining

Break one big task into smaller tasks.

```text
       Input
         |
         v
   +-----------+
   | LLM #1    |
   | Generate  |
   +-----+-----+
         |
         v
   +-----------+
   | LLM #2    |
   | Review    |
   +-----+-----+
         |
         v
   +-----------+
   | LLM #3    |
   | Finalize  |
   +-----+-----+
         |
         v
       Output
```

Example:

```text
Requirement
    ↓
Create outline
    ↓
Review outline
    ↓
Write document
```

**Use when:** steps are predictable.

---

# 5. Pattern 2 — Routing

First classify the request, then send it to the right specialist.

```text
                  User
                   |
                   v
             +-----------+
             | Classifier|
             +-----+-----+
                   |
        +----------+----------+
        |          |          |
        v          v          v
      Refund     Technical   General
        |          |          |
        v          v          v
    Prompt A    Prompt B    Prompt C
```

Example:

```text
"What is my balance?"
          |
          v
       Router
          |
          v
    Account Agent


"I want to cancel my SIP"
          |
          v
       Router
          |
          v
    Investment Agent
```

**Use when:** different types of requests need different expertise.

---

# 6. Pattern 3 — Parallelization

Do multiple tasks **at the same time**.

```text
                 User
                  |
                  v
             +---------+
             |   LLM   |
             +----+----+
                  |
        +---------+---------+
        |         |         |
        v         v         v
     Agent A   Agent B   Agent C
     Search    Coding     Analysis
        |         |         |
        +---------+---------+
                  |
                  v
              Aggregator
                  |
                  v
                Answer
```

Example:

```text
Research company
      |
      +----> Financial analysis
      |
      +----> Competitor analysis
      |
      +----> Technology analysis
      |
      v
   Combine results
```

Two common forms:

### Sectioning

Different agents do different jobs.

### Voting

Several agents independently answer the same question.

```text
Question
   |
   +--> Agent 1 --> Answer A
   |
   +--> Agent 2 --> Answer B
   |
   +--> Agent 3 --> Answer C
                     |
                     v
                  Vote
                     |
                     v
                 Final answer
```

**Use when:** you want speed, multiple perspectives, or higher confidence.

---

# 7. Pattern 4 — Orchestrator + Workers

One of the most important patterns for **multi-agent systems**.

The orchestrator decides what workers are needed.

```text
                  USER
                   |
                   v
          +----------------+
          | ORCHESTRATOR   |
          | "What needs to |
          |  be done?"      |
          +-------+--------+
                  |
        +---------+---------+
        |         |         |
        v         v         v
     Worker 1  Worker 2  Worker 3
     Search    Coding     Analysis
        |         |         |
        +---------+---------+
                  |
                  v
          +---------------+
          | Orchestrator  |
          |   combines    |
          +-------+-------+
                  |
                  v
                Result
```

### Key difference

**Parallelization:**

```text
You define workers beforehand.

A ---> Task A
B ---> Task B
C ---> Task C
```

**Orchestrator:**

```text
LLM decides:

"This problem needs
A + C + D + E"
```

Workers are **dynamic**.

**Use when:** you cannot predict beforehand how many subtasks are required.

---

# 8. Pattern 5 — Evaluator + Optimizer

One LLM creates something.

Another LLM evaluates it.

Then improve it.

```text
             Task
              |
              v
        +-----------+
        | Generator |
        +-----+-----+
              |
              v
           Output
              |
              v
        +-----------+
        | Evaluator |
        +-----+-----+
              |
              v
           Feedback
              |
              v
        +-----------+
        | Generator |
        +-----+-----+
              |
              v
        Better Output
```

Or:

```text
Generate
   ↓
Evaluate
   ↓
Good enough?
 /       NO        YES
|          |
v          v
Improve   STOP
|
+-----> Evaluate
```

Example:

```text
Write code
   ↓
Run tests
   ↓
Tests fail
   ↓
Fix code
   ↓
Run tests
   ↓
Tests pass
   ↓
Done
```

**Use when:** you have clear evaluation criteria and iteration improves quality.

---

# 9. The Autonomous Agent

Now we reach the real agent.

```text
             USER
               |
               v
          +---------+
          |   LLM   |
          +----+----+
               |
          "What should
           I do next?"
               |
               v
             TOOL
               |
               v
          Tool Result
               |
               v
          +---------+
          |   LLM   |
          +----+----+
               |
          "What next?"
               |
               v
             TOOL
               |
               v
            Result
               |
              ...
               |
               v
             DONE
```

The important thing is the **loop**:

```text
       +----------------------+
       |                      |
       v                      |
     THINK                    |
       |                      |
       v                      |
     ACT                      |
       |                      |
       v                      |
   OBSERVE -------------------+
       |
       v
      DONE
```

An agent uses environmental feedback—such as tool results or code execution—to determine what to do next.

---

# 10. Agent = Loop + Tools + Guardrails

A production agent should not simply run forever.

```text
              +---------+
              |   LLM   |
              +----+----+
                   |
                   v
                 Tool
                   |
                   v
               Observe
                   |
                   v
             Continue?
             /                  YES        NO
            |          |
            +----+     v
                 |    STOP
                 |
                 +----> LLM
```

Add:

```text
Maximum iterations
        +
Human approval
        +
Sandbox
        +
Permissions
        +
Guardrails
```

Why?

Because:

```text
Autonomy ↑
   |
   +---- Capability ↑
   +---- Cost ↑
   +---- Latency ↑
   +---- Error accumulation ↑
```

---

# 11. The Hidden Superpower: Good Tools

A common mistake:

> "The LLM is smart, so give it lots of tools."

The **tool interface itself matters enormously**.

Think of:

```text
Human Developer
      |
      v
    API / UI
      |
      v
   Computer
```

For an AI:

```text
       AI Agent
          |
          v
        Tools
          |
          v
      Computer
```

This is the **Agent-Computer Interface (ACI)**.

### Good tool

```text
search_customer(
    customer_id,
    date_range
)
```

Clear.

### Bad tool

```text
do_customer_thing(
    input
)
```

Ambiguous.

A good tool should have:

```text
✓ Clear name
✓ Clear parameters
✓ Examples
✓ Edge cases
✓ Error handling
✓ Clear boundaries
✓ Hard-to-misuse inputs
```

---

# 12. Framework ≠ Architecture

Very important architect lesson.

Don't think:

```text
LangGraph
CrewAI
AutoGen
etc.
      ↓
   = Agent
```

No.

Frameworks are implementation helpers.

```text
                 YOUR ARCHITECTURE
                       |
        +--------------+--------------+
        |              |              |
      LLM            Tools          Memory
        |              |              |
        +--------------+--------------+
                       |
                    Workflow
                       |
                    Agent
```

Framework:

```text
         Framework
            |
     ----------------
     |              |
  Convenience     Abstraction
```

Understand the underlying LLM calls, prompts, tools, and responses instead of hiding everything behind framework abstractions.

---

# 13. Architect's Decision Tree

When designing an AI system, ask:

```text
                START
                  |
                  v
       Can one LLM call solve it?
              /                   YES        NO
             |          |
             v          v
           DONE      Fixed steps?
                       /                         YES     NO
                      |       |
                      v       v
                  WORKFLOW   AGENT
                      |
          +-----------+-----------+
          |           |           |
       Chain       Route      Parallel
                                  |
                                  v
                           Need dynamic
                           decomposition?
                                  |
                                 YES
                                  |
                                  v
                          Orchestrator
```

---

# 14. Most Important Lessons

## 1. Start simple

```text
Simple LLM
   ↓
RAG
   ↓
Workflow
   ↓
Agent
   ↓
Multi-agent
```

**Don't jump directly to the bottom.**

## 2. Complexity must earn its place

Ask:

> **"What problem does this additional agent solve?"**

If the answer is unclear:

```text
REMOVE IT.
```

## 3. Agents are not magic

At the core:

```text
LLM
 +
Tools
 +
Loop
 +
Feedback
 =
Agent
```

## 4. Tools are as important as prompts

```text
Good Agent
    =
Good Model
+
Good Prompt
+
Good Tools
+
Good Feedback
+
Good Guardrails
```

## 5. Measure everything

Don't say:

> "The agent seems better."

Measure:

```text
Accuracy
Cost
Latency
Tool failures
Task completion
Human intervention
Error rate
```

Then decide whether additional complexity is justified.

---

# 15. One-Minute Mental Model

If you remember **only this diagram**, remember this:

```text
                    AI SYSTEM
                       |
             +---------+---------+
             |                   |
          WORKFLOW             AGENT
             |                   |
       Fixed path          Dynamic path
             |                   |
     +-------+-------+           |
     |       |       |           v
   Chain   Route  Parallel    +-------+
                              |  LLM  |
                              +---+---+
                                  |
                                Tools
                                  |
                                  v
                               Observe
                                  |
                                  v
                              Decide
                                  |
                                  +----+
                                       |
                                       v
                                     Tool
                                       |
                                       +----> ...
```

## Ultimate Principle

> **Don't build the most sophisticated agent. Build the simplest system that reliably solves the problem.**

---

## Quick CTO / Architect Questions

1. Can this problem be solved with one LLM call?
2. If not, do I really need an agent—or is a fixed workflow enough?
3. Where should the LLM make decisions?
4. Which decisions should remain deterministic?
5. Are my tools clear and difficult to misuse?
6. What happens when a tool fails?
7. What is the maximum number of agent iterations?
8. Where is human approval required?
9. How will I measure accuracy, cost, latency, and reliability?
10. Does every additional agent actually improve the business outcome?

**Architect's mantra:**

```text
START SIMPLE
     ↓
MEASURE
     ↓
IDENTIFY THE BOTTLENECK
     ↓
ADD COMPLEXITY ONLY IF NEEDED
     ↓
MEASURE AGAIN
```
