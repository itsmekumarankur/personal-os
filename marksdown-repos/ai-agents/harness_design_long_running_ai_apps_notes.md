# Harness Design for Long-Running AI Apps
### Easy 10-minute notes — based on Anthropic's engineering article

Original article: https://www.anthropic.com/engineering/harness-design-long-running-apps

---

## 1. The Big Idea

The main lesson is simple:

> **A powerful AI model alone is not enough for complex, long-running tasks.**

If you ask one AI agent:

```text
"Build me a complete application."
              |
              v
        +-----------+
        | AI Agent  |
        +-----------+
              |
              v
       Build everything
              |
              v
        ❌ Bugs
        ❌ Missing features
        ❌ Poor decisions
        ❌ Loses context
```

The better approach is to build a **harness around the AI**.

Think of a harness as an **engineering system that helps the AI plan, build, test and improve.**

```text
                AI MODEL
                   |
          +--------+--------+
          |      HARNESS     |
          |                  |
          | Plan             |
          | Build            |
          | Evaluate         |
          | Feedback         |
          +------------------+
                   |
                   v
             Better software
```

---

# 2. Why Long-Running AI Agents Fail

Imagine asking an agent to work for 6 hours.

```text
Context
  |
  v
"I need to build a game"
  |
  v
Good decisions
  |
  v
More code
  |
  v
More context
  |
  v
More code
  |
  v
Context becomes huge
  |
  v
Agent starts losing coherence
```

Two major problems appeared.

### Problem 1 — Context degradation

As the conversation becomes larger, the model can lose track of:

- What has already been done
- What remains
- Why a decision was made
- What the original goal was

Sometimes the model even starts thinking:

> "I should probably finish now."

Anthropic calls this **context anxiety**.

---

# 3. Context Reset vs Compaction

There are two ways to handle a huge context.

### Compaction

Keep the same agent but summarize old information.

```text
Huge Context
     |
     v
 [Summary]
     |
     v
Same Agent continues
```

The problem:

```text
Old context
     ↓
 summarized
     ↓
 Same mental state
```

The agent never truly gets a fresh start.

### Context Reset

Instead:

```text
Agent 1
   |
   | work
   v
STATE / HANDOFF FILE
   |
   v
Agent 2
   |
   | continue
   v
Agent 3
```

A new agent starts with a **clean context**, using structured artifacts to understand previous work.

### Key lesson

```text
Long task
   |
   +--> Context becomes messy
              |
              v
       Structured handoff
              |
              v
       Fresh agent context
```

This can improve reliability, although it adds orchestration cost.

---

# 4. Another Big Problem: AI Is Bad at Judging Its Own Work

Suppose AI builds an application.

Then you ask:

> "Is your application good?"

AI tends to say:

```text
AI:
"This is excellent.
Everything looks good."
```

Even when:

```text
Human:
"Wait...
the main button doesn't work!"
```

This is the **self-evaluation problem**.

---

# 5. Separate Builder and Reviewer

Anthropic's important insight:

```text
        +-------------+
        |   PLANNER   |
        +------+------+
               |
               v
        +-------------+
        |  GENERATOR  |
        |   / BUILDER |
        +------+------+
               |
               v
          Application
               |
               v
        +-------------+
        |  EVALUATOR  |
        |    / QA     |
        +------+------+
               |
               | Feedback
               v
        +-------------+
        |  GENERATOR  |
        +-------------+
```

Instead of:

```text
AI builds
   |
   v
AI checks itself
   |
   v
"Looks great!"
```

Use:

```text
Builder  --->  Reviewer
   ^              |
   |              |
   +--- feedback--+
```

This creates an **iteration loop**.

---

# 6. Think of It Like Software Engineering

Traditional development:

```text
Requirement
    |
    v
Developer
    |
    v
Code
    |
    v
Code Review
    |
    v
QA
    |
    v
Bug fixes
```

AI development can follow the same pattern:

```text
User Prompt
     |
     v
 Planner
     |
     v
 Generator
     |
     v
 Evaluator
     |
     v
 Feedback
     |
     v
 Generator
     |
     v
 Better Product
```

**This is the core idea of the article.**

---

# 7. The Three-Agent Architecture

Anthropic initially used three specialized agents.

```text
             USER
              |
              v
       +--------------+
       |    PLANNER   |
       +------+-------+
              |
         Product Spec
              |
              v
       +--------------+
       |   GENERATOR  |
       +------+-------+
              |
            Code
              |
              v
       +--------------+
       |  EVALUATOR   |
       +------+-------+
              |
           Feedback
              |
              +----------+
                         |
                         v
                    GENERATOR
```

## Agent 1 — Planner

Input:

```text
"Build a retro game maker."
```

Planner expands it into:

```text
Product
 |
 +-- Level Editor
 +-- Sprite Editor
 +-- Entity System
 +-- Animation
 +-- Sound
 +-- AI Features
 +-- Play Mode
 +-- Export
```

Important:

**Planner should describe WHAT needs to be built, not prescribe every implementation detail.**

Why?

Because a bad technical assumption in the plan can propagate everywhere.

```text
Bad assumption
      |
      v
Planner
      |
      v
Generator
      |
      v
100s of wrong decisions
```

---

# 8. Agent 2 — Generator

The Generator actually builds the application.

Earlier architecture:

```text
Spec
 |
 v
Feature 1
 |
 v
Feature 2
 |
 v
Feature 3
 |
 v
Feature 4
```

They initially used **sprints** to keep the work manageable.

For example:

```text
Sprint 1 → Project setup
Sprint 2 → Level editor
Sprint 3 → Sprite editor
Sprint 4 → Game engine
Sprint 5 → AI features
```

This prevents the model from trying to solve the entire application at once.

---

# 9. Agent 3 — Evaluator

This is effectively an AI QA engineer.

It doesn't simply read the code.

It interacts with the running application.

```text
              APPLICATION
                   |
                   v
             +-----------+
             | Evaluator |
             +-----------+
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
     Click       API         DB
     UI          test        state
       |           |           |
       +-----------+-----------+
                   |
                   v
              PASS / FAIL
```

Anthropic used Playwright so the evaluator could behave like an actual user.

For example:

```text
Open application
      ↓
Create project
      ↓
Create sprite
      ↓
Create level
      ↓
Place character
      ↓
Press Play
      ↓
Move character
      ↓
Check expected result
```

This is much stronger than simply asking:

> "Does the code look correct?"

---

# 10. The Sprint Contract

One particularly useful concept is the **sprint contract**.

Before coding starts:

```text
Generator:
"I will implement X, Y and Z."

Evaluator:
"How will we know X, Y and Z actually work?"
```

They negotiate:

```text
        GENERATOR
            |
      proposes scope
            |
            v
        EVALUATOR
            |
       challenges it
            |
            v
      AGREED CONTRACT
            |
            v
           CODE
```

Example:

```text
Feature:
Rectangle fill tool

Definition of Done:

[ ] User selects tile
[ ] User drags rectangle
[ ] Entire rectangle fills
[ ] Undo works
[ ] Correct tile appears
```

Now "done" is measurable.

---

# 11. Why This Works

Without evaluation:

```text
Prompt
  |
  v
AI
  |
  v
Code
  |
  v
Looks impressive
  |
  v
❌ Doesn't actually work
```

With evaluation:

```text
Prompt
  |
  v
Plan
  |
  v
Build
  |
  v
Test
  |
  +---- FAIL ----+
  |              |
  |              v
  |           Feedback
  |              |
  +--------------+
         |
         v
       Build
         |
         v
       Test
         |
         v
       PASS
```

The **feedback loop** is the real power.

---

# 12. Real Example: Solo Agent vs Harness

Anthropic tested a retro game maker.

### Solo agent

```text
Prompt
  ↓
One AI
  ↓
20 minutes
  ↓
$9
```

It produced something that looked reasonable.

But when tested:

```text
UI ❌
Workflow ❌
Game runtime ❌
Entities ❌
```

The application looked impressive but important functionality was broken.

---

### Full harness

```text
Prompt
   |
   v
Planner
   |
   v
16-feature specification
   |
   v
Multiple build stages
   |
   v
Evaluator
   |
   v
Bug detection
   |
   v
Fixes
```

It ran for around:

```text
6 hours
$200
```

Much more expensive.

But the output was significantly more functional and complete.

### Important lesson

> **Don't optimize only for token cost. Optimize for outcome quality.**

---

# 13. But There Is a Catch

A sophisticated harness isn't automatically better.

It can become:

```text
Agent
 + Planner
 + Generator
 + Evaluator
 + Memory
 + Sprint Manager
 + Orchestrator
 + Handoff system
 + ...
        |
        v
 HUGE COMPLEX SYSTEM
```

Now the harness itself becomes difficult to maintain.

Anthropic therefore followed an important principle:

> **Use the simplest harness that actually improves the model's performance.**

---

# 14. Models Improve → Harness Should Change

This is one of the most important architectural lessons.

Suppose:

### Model v1

```text
Needs:
Planner
+
Sprints
+
Evaluator
+
Context reset
```

Then a stronger model arrives.

```text
Model v2
  |
  +-- better planning
  +-- better coding
  +-- longer context
  +-- better debugging
```

Some scaffolding may no longer be necessary.

So:

```text
Old Model
    ↓
Complex Harness
    ↓
New Model arrives
    ↓
REMOVE unnecessary components
    ↓
Simpler Harness
```

Anthropic removed the sprint construct when newer models became capable of handling longer continuous work.

---

# 15. The Updated Architecture

The newer approach became simpler:

```text
             USER
              |
              v
        +-----------+
        |  PLANNER  |
        +-----+-----+
              |
              v
        +-----------+
        |  BUILDER  |
        +-----+-----+
              |
              v
        Application
              |
              v
        +-----------+
        |    QA     |
        +-----+-----+
              |
          Feedback
              |
              v
        +-----------+
        |  BUILDER  |
        +-----------+
```

Notice:

**Planner + Builder + QA**

but fewer rigid constraints.

---

# 16. The DAW Experiment

Anthropic later asked the system:

```text
"Build a fully featured
Digital Audio Workstation
in the browser."
```

The run lasted roughly:

```text
~4 hours
~$125
```

The Builder worked continuously for more than two hours.

QA then found issues such as:

```text
❌ Audio recording incomplete
❌ Clip resizing missing
❌ Clip splitting missing
❌ Effects visualization incomplete
```

The Builder fixed some of these through subsequent rounds.

So:

```text
BUILD
  ↓
QA
  ↓
BUGS
  ↓
BUILD
  ↓
QA
  ↓
BUGS
  ↓
BUILD
  ↓
FINAL PRODUCT
```

This is basically **autonomous software development with an AI feedback loop**.

---

# 17. The Most Important Architectural Insight

Don't think:

```text
"How do I make
 the AI smarter?"
```

Also ask:

```text
"How do I design
 the environment
 around the AI?"
```

That environment is the **harness**.

```text
             AI capability
                  +
          Harness architecture
                  |
                  v
       -------------------------
       | Long-running Agent   |
       -------------------------
                  |
          Complex outcome
```

---

# 18. What Is a Harness?

Very simply:

> **A harness is the surrounding system that gives an AI agent structure, feedback, tools, memory and verification so it can complete complex tasks reliably.**

Think:

```text
LLM = Brain
Harness = Operating environment
Tools = Hands
Evaluator = Critic
Artifacts = Memory
Planner = Strategist
```

Together:

```text
                 AI SYSTEM
                    |
       +------------+-------------+
       |            |             |
    Planner       Builder       Evaluator
       |            |             |
       +------------+-------------+
                    |
                 Feedback
                    |
                    v
             Better outcome
```

---

# 19. CTO / Architect Takeaways

### 1. Don't build one giant agent

Prefer specialized responsibilities.

```text
Plan → Build → Verify
```

---

### 2. Make "done" measurable

Bad:

```text
"Build a good UI."
```

Better:

```text
[ ] User can create project
[ ] User can edit project
[ ] Primary action works
[ ] API returns expected result
[ ] Data persists
```

---

### 3. External evaluation beats self-evaluation

```text
Builder ≠ Evaluator
```

Separation creates a stronger feedback loop.

---

### 4. Break complex work into manageable units

```text
Huge task
   ↓
Smaller deliverables
   ↓
Build
   ↓
Verify
```

---

### 5. Use artifacts to preserve state

Instead of relying entirely on conversation:

```text
Agent
  |
  v
SPEC.md
PLAN.md
TASKS.md
TESTS.md
RESULTS.md
  |
  v
Next Agent
```

The files become **shared memory**.

---

### 6. Don't over-engineer the harness

Every component should answer:

> **"What specific model weakness does this solve?"**

If the latest model no longer has that weakness:

```text
REMOVE IT
```

---

# 20. The Entire Article in One Diagram

```text
                    USER
                     |
                     v
              "Build an App"
                     |
                     v
              +-------------+
              |   PLANNER   |
              +------+------+
                     |
               Product Spec
                     |
                     v
              +-------------+
              |   BUILDER   |
              +------+------+
                     |
                    Code
                     |
                     v
              +-------------+
              |     QA      |
              |  EVALUATOR  |
              +------+------+
                     |
              Test real app
                     |
              +------+------+
              |             |
             PASS          FAIL
              |             |
              |             v
              |        Feedback
              |             |
              |             v
              |         BUILDER
              |             |
              +-------------+
                     |
                     v
              Better Product
```

---

# 🧠 Remember This

If you remember only **5 things**, remember:

```text
1. LLM alone
      ↓
   not enough


2. PLAN
      ↓
   BUILD
      ↓
   EVALUATE
      ↓
   IMPROVE


3. Builder ≠ Evaluator


4. "Done" must be measurable.


5. As models improve,
   simplify the harness.
```

### The deepest lesson

**The future of agentic software engineering is not just about building smarter models. It is about designing better systems around those models.**

That is the essence of **harness engineering**.
