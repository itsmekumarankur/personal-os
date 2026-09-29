https://www.anthropic.com/engineering/building-effective-agents


## 🧠 3-Minute Summary — Building Effective Agents

### 1. First understand: Workflow vs Agent

**Workflow = predefined path**

```text
User
 ↓
LLM → Tool A → LLM → Tool B → Result
       predefined flow
```

**Agent = dynamic decision-making**

```text
User
 ↓
   LLM / Agent
    ↙   ↓   ↘
 Tool A Tool B Tool C
    ↑     ↓
    └─ observe ─┘
        ↓
      decide
        ↓
      repeat
```

A workflow follows **your code**.

An agent decides **its own next step** based on what it observes. ([Anthropic][1])

---

## 2. Don't use an Agent unless you need one

Anthropic's recommended progression is:

```text
Simple Prompt
     ↓
Prompt + RAG / Examples
     ↓
Workflow
     ↓
Agent
```

Every step adds **complexity, latency, cost and potential failure modes**.

So ask:

> **"Can I solve this reliably with a simpler architecture?"**

If yes → don't build an agent. ([Anthropic][1])

---

# 3. The 5 important workflow patterns

### Pattern 1 — Prompt Chaining

Break one difficult task into sequential steps.

```text
Input
 ↓
Generate
 ↓
Validate
 ↓
Improve
 ↓
Final Output
```

**Use when:** the steps are known beforehand.

Example:

```text
Generate outline
      ↓
Check outline
      ↓
Write document
```

---

### Pattern 2 — Routing

First classify the request, then send it to the appropriate specialist.

```text
             ┌→ Billing Agent
User → Router├→ Technical Agent
             └→ Support Agent
```

**Use when:** different categories need different prompts, tools or models.

---

### Pattern 3 — Parallelization

Do multiple LLM tasks simultaneously.

```text
             ┌→ Security review
Input ───────┼→ Performance review
             └→ Code quality review
                    ↓
                 Aggregate
```

Two forms:

* **Sectioning** → different subtasks in parallel
* **Voting** → multiple independent attempts, then combine results

Useful when you need **speed, multiple perspectives or higher confidence**. ([Anthropic][1])

---

### Pattern 4 — Orchestrator → Workers

This is more dynamic.

```text
             Orchestrator
                  ↓
       ┌──────────┼──────────┐
       ↓          ↓          ↓
    Worker 1   Worker 2   Worker 3
       └──────────┼──────────┘
                  ↓
              Synthesis
```

The key difference from parallelization:

**Workers are not predetermined.**

The orchestrator decides:

> "What subtasks do I need for this particular request?"

Great for **complex coding and research tasks**. ([Anthropic][1])

---

### Pattern 5 — Evaluator → Optimizer

One LLM produces the answer; another evaluates it.

```text
Generator
    ↓
  Answer
    ↓
Evaluator
    ↓
Feedback
    ↓
Generator
    ↓
Improved Answer
```

Use this when you have **clear evaluation criteria** and iteration actually improves quality.

Think:

> **Generate → Critique → Improve → Repeat**

---

# 4. What is an actual Agent?

An agent is basically:

```text
        ┌───────────────┐
        │      LLM      │
        └───────┬───────┘
                ↓
             Decide
                ↓
           Choose Tool
                ↓
         Execute Action
                ↓
        Observe Result
                ↓
        "What next?"
                ↓
             Decide
                ↺
```

The important word is **feedback**.

The agent should continuously get **ground truth from the environment**:

* tool results
* API responses
* code execution
* test results
* database state
* user feedback

It uses that feedback to decide its next action. ([Anthropic][1])

---

# 5. Agents have a cost

Agents provide flexibility, but introduce:

```text
More autonomy
     ↓
More tool calls
     ↓
More tokens
     ↓
Higher latency + cost
     ↓
More opportunities for errors
```

Errors can also **compound across multiple steps**.

Therefore use:

* sandboxing
* guardrails
* iteration limits
* human checkpoints
* extensive testing

especially for autonomous systems. ([Anthropic][1])

---

# 6. The hidden superpower: Tool / ACI design

One of Anthropic's strongest points is:

> **An agent is only as good as the tools you give it.**

Don't think only about **API design**.

Think about:

### ACI — Agent-Computer Interface

```text
Agent
  ↓
Tool description
  ↓
Parameters
  ↓
Tool execution
  ↓
Meaningful result
  ↓
Agent understands what happened
```

Tool descriptions should clearly explain:

* what the tool does
* parameters
* examples
* edge cases
* limitations
* boundaries
* expected outputs

Anthropic recommends treating tool design almost like designing a good interface for a junior engineer. ([Anthropic][1])

---

# 🎯 The 3 principles to remember

If you remember only **three things from the entire article**, remember these:

### 1. **Simplicity**

> Don't build an agent when a prompt or workflow can solve the problem.

### 2. **Transparency**

> Make the agent's planning and actions understandable.

### 3. **Excellent ACI**

> Invest heavily in designing, documenting and testing tools.

([Anthropic][1])

---

## 🧩 Architect's mental model

For your AI-architecture learning, I would remember the article as this ladder:

```text
                 COMPLEXITY
                     ↑
                     │
             ┌──────────────┐
             │    AGENT     │ ← Dynamic planning
             └──────────────┘
                     │
          ┌────────────────────┐
          │ ORCHESTRATOR/WORKER│ ← Dynamic delegation
          └────────────────────┘
                     │
          ┌────────────────────┐
          │ EVALUATOR/OPTIMIZER│ ← Generate → Critique
          └────────────────────┘
                     │
          ┌────────────────────┐
          │   PARALLELIZATION │
          └────────────────────┘
                     │
          ┌────────────────────┐
          │      ROUTING       │
          └────────────────────┘
                     │
          ┌────────────────────┐
          │  PROMPT CHAINING   │
          └────────────────────┘
                     │
          ┌────────────────────┐
          │    LLM + RAG       │
          └────────────────────┘
                     │
          ┌────────────────────┐
          │    SIMPLE PROMPT   │
          └────────────────────┘
                     │
                 SIMPLICITY
```

**The architect's question is not *"How do I build an agent?"***

It is:

> **"What is the simplest architecture that reliably achieves the required outcome?"**

That is essentially the core lesson of Anthropic's article. ([Anthropic][1])

[Read the original Anthropic article](https://www.anthropic.com/engineering/building-effective-agents?utm_source=chatgpt.com)

[1]: https://www.anthropic.com/engineering/building-effective-agents?utm_source=chatgpt.com "Building Effective AI Agents \ Anthropic"
