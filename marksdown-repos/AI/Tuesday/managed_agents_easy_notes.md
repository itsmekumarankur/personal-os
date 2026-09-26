https://www.anthropic.com/engineering/managed-agents

# Managed Agents — Very Easy Notes

**Source:** Anthropic — *Scaling Managed Agents: Decoupling the brain from the hands*

> **Core idea:** Don't tightly connect the AI, its tools, its execution environment, and its memory. **Separate them using stable interfaces.** This makes agents easier to scale, recover, secure, and evolve as models become smarter.

---

# 1. What Problem Is Anthropic Solving?

```text
             AI AGENT
                |
       +--------+--------+
       |        |        |
      Brain    Tools    Memory
       |        |        |
      LLM     Sandbox   History
```

Naive design:

```text
+--------------------------------+
|          ONE CONTAINER         |
|                                |
|  Claude + Harness + Sandbox   |
|  + Session + User Data         |
|                                |
+--------------------------------+
```

If the container dies:

```text
Container dies
     |
     v
Everything dies
     |
     +--> Agent state
     +--> Session
     +--> Tools
     +--> Work
```

**Problem:** tightly coupled systems are harder to debug, recover, connect to customer infrastructure, and scale.

---

# 2. The Big Idea: Decouple Everything

```text
             BRAIN
        +-------------+
        | Claude      |
        | Harness     |
        +------+------+
               |
          Interfaces
               |
       +-------+-------+
       |               |
       v               v
    SESSION          HANDS
    (Memory)      (Tools/Sandbox)
```

Think:

```text
BRAIN
  |
  +---- SESSION = What happened?
  |
  +---- HANDS   = Do something
  |
  +---- HARNESS = How should the brain operate?
```

Each part can fail, restart, or change independently.

---

# 3. Brain vs Hands

This is the **most important mental model**.

## Brain

```text
       BRAIN
         |
         v
      Claude
         |
         v
"What should I do?"
```

## Hands

```text
       HANDS
         |
   +-----+-----+
   |     |     |
 Shell  Git   API
   |     |     |
   +-----+-----+
         |
         v
    Real World
```

The brain **decides**.

The hands **execute**.

```text
          BRAIN
            |
       "Run this code"
            |
            v
          HAND
            |
       Execute code
            |
            v
         Result
            |
            v
          BRAIN
```

---

# 4. The Harness

The harness is the control loop around Claude.

```text
             +---------+
             | Claude  |
             +----+----+
                  |
               Harness
                  |
       +----------+----------+
       |          |          |
       v          v          v
    Session     Tool      Sandbox
```

Example:

```text
Claude wants to use a tool
          |
          v
       Harness
          |
          v
    Find the right tool
          |
          v
       Execute
          |
          v
      Return result
```

**Key idea:** The harness should not assume too much about what Claude needs today, because model capabilities change.

---

# 5. Why Interfaces Matter

Think about an operating system.

Applications use stable abstractions rather than depending on the exact hardware.

```text
Agent
  |
  v
execute(name, input)
  |
  +---- Container
  +---- MCP server
  +---- Custom tool
  +---- Phone
  +---- Other environment
```

The interface stays stable.

The implementation can change.

> **Stable interfaces allow the underlying implementation to evolve.**

---

# 6. Don't Build a "Pet"

Classic infrastructure concept:

```text
PETS vs CATTLE
```

## Pet

```text
One special server

"Please don't die!"

    |
    v
Manual fixing
Manual debugging
Manual recovery
```

## Cattle

```text
Server 1
Server 2
Server 3
Server 4

Any one can disappear.
Create another.
```

For agents:

```text
BAD

Agent
 |
 +--> Special Container
       |
       X
     Failure
       |
       X
    Lost work
```

Better:

```text
Agent
 |
 +--> Container
       |
       X
    Failure
       |
       v
Tool error
       |
       v
Create NEW container
       |
       v
Continue
```

**Container = replaceable infrastructure, not permanent state.**

---

# 7. Session = Durable Memory

Important distinction:

```text
Session
   ≠
Claude's Context Window
```

Think:

```text
       SESSION
          |
          v
+------------------------+
| Event 1                |
| Event 2                |
| Tool call              |
| Tool result            |
| Event 3                |
| Event 4                |
| ...                    |
+------------------------+
```

Claude only sees the portion it currently needs.

```text
             FULL SESSION
                  |
       +----------+----------+
       |          |          |
       v          v          v
    Events     Events      Events
       \          |          /
        \         |         /
         +--------+--------+
                  |
              HARNESS
                  |
                  v
          Claude Context
```

So:

```text
Context Window
      ≠
Project Memory
```

The session provides durable history.

---

# 8. Why This Is Better Than Just Compaction

Traditional approach:

```text
Huge Context
     |
     v
Compaction
     |
     v
Summary
```

Problem:

```text
What if the summary
removed something important?
```

Better:

```text
FULL EVENT LOG
      |
      v
   Durable
      |
      v
Harness asks:
"What context do I need?"
      |
      v
Selected events
      |
      v
Claude
```

The architecture separates:

```text
Storage of history
        from
Management of context
```

This lets future harnesses use different context strategies without changing durable session storage.

---

# 9. Security: Never Give the Sandbox the Keys

Bad architecture:

```text
+----------------------------------+
| Sandbox                          |
|                                  |
| AI-generated code                |
|        +                         |
|        |                         |
|        v                         |
|   SECRET TOKENS                  |
+----------------------------------+
```

If malicious code gets access:

```text
Prompt Injection
      |
      v
AI executes malicious action
      |
      v
Reads credentials
      |
      v
Attacker gets access
```

Better:

```text
             Claude
                |
                v
             Harness
                |
                v
          Secure Vault
                |
                v
        External Service
```

The sandbox should not directly receive credentials.

```text
Git Token
   |
   v
Securely provision Git access
   |
   v
Sandbox

Claude never needs to see the token.
```

**Security principle: isolate secrets from generated code.**

---

# 10. Many Brains, Many Hands

Once everything is decoupled, scaling becomes easier.

## Many brains

```text
       Brain 1
          |
       Brain 2
          |
       Brain 3
          |
       Brain 4
```

## Many hands

```text
                BRAIN
                  |
        +---------+---------+
        |         |         |
        v         v         v
     Sandbox    Git       MCP
        |         |         |
        +---------+---------+
```

Potentially:

```text
Brain A ----+
            |
Brain B ----+----> Hands
            |
Brain C ----+
```

Because brains and hands are no longer tightly coupled.

---

# 11. Big Performance Benefit

Previously:

```text
New Agent
    |
    v
Provision Container
    |
    v
Clone Repo
    |
    v
Boot Process
    |
    v
Load Events
    |
    v
First Token
```

This creates startup latency.

With decoupling:

```text
New Agent
    |
    v
Read Session
    |
    v
START INFERENCE
    |
    v
Need Sandbox?
    |
   YES
    |
    v
Provision Sandbox
```

The sandbox is created **only when required**.

Anthropic reports that this architecture reduced median time-to-first-token by roughly **60%**, and p95 by **more than 90%** in their system.

---

# 12. Complete Architecture

```text
                         USER
                           |
                           v
                  +----------------+
                  |     BRAIN      |
                  |    Claude      |
                  +-------+--------+
                          |
                       HARNESS
                          |
             +------------+------------+
             |                         |
             v                         v
        +----------+             +-----------+
        | SESSION  |             |   HANDS   |
        |          |             |           |
        | Event Log|             | Tools     |
        | History  |             | Sandbox   |
        +----------+             | MCP       |
                                 | Git       |
                                 +-----------+
```

Interaction loop:

```text
        THINK
          |
          v
       DECIDE
          |
          v
     Call Tool
          |
          v
        HAND
          |
          v
       RESULT
          |
          v
        SESSION
          |
          v
        THINK
          |
          +-------> ...
```

---

# 13. The Most Important Architecture Principle

Traditional thinking:

```text
Agent
  =
LLM + Everything
```

Better:

```text
Agent System
     |
     +---- Brain
     |
     +---- Harness
     |
     +---- Session
     |
     +---- Hands
     |
     +---- Security
```

Responsibilities:

```text
Brain       → Reason
Harness     → Orchestrate
Session     → Remember
Hands       → Execute
Vault       → Protect secrets
```

---

# 14. Why This Matters for Future AI

Today's model:

```text
Model A
   |
Harness A
   |
Sandbox A
```

Tomorrow:

```text
Better Model
   |
Different Harness
   |
Different Tools
   |
Different Sandbox
```

If everything is tightly coupled:

```text
New Model
   |
   v
Rewrite EVERYTHING ❌
```

With stable interfaces:

```text
New Model
    |
    v
Same Interfaces
    |
 +--+--+--+
 |  |  |  |
 v  v  v  v
New harness / tools / sandbox
```

**Build stable interfaces around the AI, not a rigid implementation around today's AI.**

---

# 15. One-Minute Mental Model

Remember this:

```text
                 AI AGENT
                    |
          +---------+---------+
          |                   |
        BRAIN                HANDS
      "Think"             "Execute"
          |                   |
       Claude          Tools / Sandbox
          |
       HARNESS
          |
          v
       SESSION
     "Remember"
```

Or even simpler:

```text
        THINK
          |
          v
       HARNESS
          |
          +------> HANDS
          |
          +------> SESSION
          |
          v
       THINK AGAIN
```

---

# 16. CTO / AI Architect Questions

When designing an agent platform, ask:

1. Can the brain survive if the sandbox dies?
2. Can the sandbox be replaced without losing the session?
3. Where is durable agent memory stored?
4. Can the harness restart from the last event?
5. Can different models use the same infrastructure?
6. Can one brain use multiple execution environments?
7. Are credentials completely isolated from generated code?
8. Can tools be added without changing the core agent?
9. Are we coupling today's model limitations into our architecture?
10. What interfaces will still make sense when models become much smarter?

---

# Final Takeaway

Don't build this:

```text
       +----------------+
       | EVERYTHING     |
       | IN ONE BOX     |
       +----------------+
```

Instead:

```text
              BRAIN
                |
             INTERFACE
                |
      +---------+---------+
      |                   |
   SESSION              HANDS
   Memory           Tools/Sandbox
      |                   |
      +---------+---------+
                |
             Security
```

> **Build stable interfaces around the AI, not a rigid implementation around today's AI.**

This allows:

```text
Better Models
     +
New Harnesses
     +
New Tools
     +
New Sandboxes
     +
Durable Sessions
     =
Scalable Long-Running Agents
```

## Architect's Mantra

```text
DECOUPLE
   ↓
ISOLATE
   ↓
PERSIST
   ↓
RECOVER
   ↓
SCALE
   ↓
EVOLVE
```

**The model gives intelligence.  
The harness turns that intelligence into reliable long-running engineering work.**
