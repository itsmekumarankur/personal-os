# 🧠 Harness Engineering for Long-Running AI Apps — Mind Map

> **Core Mental Model:**  
> **LLM alone ❌ → Harness + LLM ✅**
>
> **Remember:** `PLAN → BUILD → VERIFY → FEEDBACK → IMPROVE`

---

## 🌳 1. BIG PICTURE

```text
                    LONG-RUNNING AI
                          │
             ┌────────────┴────────────┐
             │                         │
        LLM alone ❌               HARNESS ✅
             │                         │
       Context loss              PLAN → BUILD
       Bugs                      → QA → FEEDBACK
       Missing features          → IMPROVE
       Poor decisions                  │
                                       ↓
                              Reliable Outcome
```

### Key idea

**Don't just make the AI smarter. Design the environment around the AI.**

---

# 🌿 2. WHY DO LONG-RUNNING AGENTS FAIL?

```text
Long Task
   │
   ├──→ More work
   │      ↓
   │   More context
   │      ↓
   │   Context becomes huge
   │      ↓
   │   Coherence ↓
   │
   └──→ Self-evaluation problem
          ↓
       "Looks good!"
          ↓
       But actually broken
```

### Two core problems

1. **Context degradation**
   - What is done?
   - What remains?
   - Why was a decision made?
   - What was the original goal?

2. **Self-evaluation**
   - Builder tends to believe its own output is good.
   - Code looking correct ≠ application actually working.

---

# 🌿 3. CONTEXT MANAGEMENT

```text
             HUGE CONTEXT
                  │
          ┌───────┴────────┐
          │                │
     COMPACTION        CONTEXT RESET
          │                │
      Summarize        Handoff State
          │                │
      Same Agent       Fresh Agent
          │                │
      Same mental     Clean context
       state               │
                           ↓
                     More reliable
```

### Key idea

**Don't depend only on conversation history.**

Use structured artifacts:

```text
SPEC.md
PLAN.md
TASKS.md
TESTS.md
RESULTS.md
```

These become **shared memory** between agents.

---

# 🌿 4. THE CORE HARNESS

```text
                    USER
                      │
                      ↓
                  🧠 PLANNER
                      │
                 Product Spec
                      │
                      ↓
                  🔨 BUILDER
                      │
                     Code
                      │
                      ↓
                  🧪 QA / EVALUATOR
                      │
                 Test real app
                      │
              ┌───────┴───────┐
              ↓               ↓
            PASS             FAIL
              │               │
              │           Feedback
              │               │
              │               ↓
              │            BUILDER
              │               │
              └───────────────┘
                      │
                      ↓
                BETTER PRODUCT
```

## 🔑 One-line recall

> **PLAN → BUILD → VERIFY → FEEDBACK → IMPROVE**

---

# 🌿 5. THREE AGENTS

## 🧠 Planner

**Responsibility → WHAT**

```text
User Request
     ↓
Planner
     ↓
Product Spec
     ↓
Features / Requirements
```

### Important

Planner should define **WHAT**, not prescribe every implementation detail.

---

## 🔨 Builder / Generator

**Responsibility → BUILD**

```text
Specification
     ↓
Implementation
     ↓
Application
```

Break large work into smaller sprints:

```text
Spec
 ↓
Sprint 1
 ↓
Sprint 2
 ↓
Sprint 3
 ↓
Sprint 4
```

Purpose:

> Prevent the AI from trying to solve the entire application at once.

---

## 🧪 Evaluator / QA

**Responsibility → VERIFY**

Don't ask:

> "Does the code look correct?"

Instead:

> **"Does the application actually work?"**

```text
Running Application
        │
        ├── UI
        ├── API
        └── DB State
             │
             ↓
         PASS / FAIL
```

Evaluator should behave like a **real user**.

Example:

```text
Open App
   ↓
Create Project
   ↓
Create Sprite
   ↓
Create Level
   ↓
Place Character
   ↓
Press Play
   ↓
Move Character
   ↓
Check Result
```

---

# 🌿 6. BUILDER ≠ EVALUATOR

```text
             ❌ BAD

         Builder
            │
            ↓
       Checks itself
            │
            ↓
       "Looks great!"
```

vs.

```text
             ✅ GOOD

         Builder
            │
            ↓
        Application
            │
            ↓
        Evaluator
            │
            ↓
         Feedback
            │
            ↓
         Builder
```

### Golden Rule

> **Separate creation from verification.**

---

# 🌿 7. SPRINT CONTRACT

Before coding:

```text
BUILDER
"I will build X, Y, Z"
       │
       ↓
EVALUATOR
"How will we prove X, Y, Z work?"
       │
       ↓
AGREED CONTRACT
       │
       ↓
      CODE
```

### Definition of Done

Instead of:

```text
❌ "Build a good UI"
```

Use:

```text
✅ User can create project
✅ User can edit project
✅ Primary action works
✅ API returns expected result
✅ Data persists
```

### Mental model

> **DONE = MEASURABLE**

---

# 🌿 8. WHY THE FEEDBACK LOOP MATTERS

```text
         PLAN
           ↓
         BUILD
           ↓
          TEST
           ↓
       ┌── FAIL ──┐
       │          │
       ↓          │
    FEEDBACK      │
       │          │
       └──────────┘
           ↓
         BUILD
           ↓
          TEST
           ↓
         PASS
```

### Core insight

> **The feedback loop is the real power of the harness.**

---

# 🌿 9. SOLO AGENT vs HARNESS

### Solo Agent

```text
Prompt
  ↓
One AI
  ↓
Fast / Cheap
  ↓
Looks impressive
  ↓
❌ Broken functionality
```

### Harness

```text
Prompt
  ↓
Planner
  ↓
Specification
  ↓
Builder
  ↓
Evaluator
  ↓
Bug Detection
  ↓
Fixes
  ↓
Better Product
```

### Trade-off

```text
Harness
  ↑
Quality
  ↑
Reliability
  ↑
Cost
  ↑
Complexity
```

### Important

> **Optimize for outcome quality, not only token cost.**

---

# 🌿 10. DON'T OVER-ENGINEER THE HARNESS

A harness can become:

```text
LLM
 + Planner
 + Builder
 + Evaluator
 + Memory
 + Sprint Manager
 + Orchestrator
 + Handoff System
       ↓
HUGE COMPLEX SYSTEM
```

### Rule

> **Use the simplest harness that actually improves performance.**

For every component ask:

> **"What specific model weakness does this solve?"**

If the newer model doesn't have that weakness:

```text
REMOVE IT
```

---

# 🌿 11. MODELS IMPROVE → HARNESS MUST EVOLVE

```text
OLD MODEL
   ↓
Needs:
Planner
Sprints
Evaluator
Context Reset
   ↓
NEW MODEL
   ↓
Better planning
Better coding
Longer context
Better debugging
   ↓
Remove unnecessary scaffolding
   ↓
SIMPLER HARNESS
```

### Architectural principle

> **Harness is not permanent architecture.**

It should evolve with model capability.

---

# 🌿 12. SIMPLE ARCHITECTURE

```text
             USER
               │
               ↓
           PLANNER
               │
               ↓
           BUILDER
               │
               ↓
          APPLICATION
               │
               ↓
              QA
               │
           Feedback
               │
               ↓
           BUILDER
               │
               ↓
        BETTER PRODUCT
```

### Key change

**Planner + Builder + QA**

with fewer rigid constraints.

---

# 🌿 13. WHAT IS A HARNESS?

### Simple definition

> **Harness = the surrounding system that gives an AI agent structure, tools, memory, feedback and verification so it can complete complex tasks reliably.**

### Easy analogy

```text
LLM        = 🧠 Brain
Planner    = 🎯 Strategist
Tools      = 🖐️ Hands
Evaluator  = 🧐 Critic
Artifacts  = 🧠 Memory
Harness    = 🌍 Operating Environment
```

---

# 🌿 14. ARCHITECT'S VIEW

```text
                 AI SYSTEM
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     Planner       Builder      Evaluator
        │            │            │
        └────────────┼────────────┘
                     ↓
                  Feedback
                     ↓
               Better Outcome
```

### Ask as an Architect

Instead of:

> ❌ "How do I make the AI smarter?"

Ask:

> ✅ **"What environment does the AI need to reliably finish the job?"**

---

# 🌿 15. CTO / ARCHITECT TAKEAWAYS

```text
1️⃣ DON'T BUILD ONE GIANT AGENT
      ↓
   Plan → Build → Verify


2️⃣ MAKE "DONE" MEASURABLE
      ↓
   Definition of Done


3️⃣ BUILDER ≠ EVALUATOR
      ↓
   External evaluation


4️⃣ BREAK COMPLEX WORK
      ↓
   Smaller deliverables
      ↓
   Build → Verify


5️⃣ PRESERVE STATE
      ↓
   SPEC / PLAN / TASKS / TESTS / RESULTS


6️⃣ DON'T OVER-ENGINEER
      ↓
   Every component must solve
   a specific model weakness
```

---

# 🧠 16. THE 30-SECOND RECALL

```text
                 LONG-RUNNING AI
                        │
                 LLM ALONE ❌
                        │
              Context + Bugs
                        │
                        ↓
                    HARNESS
                        │
            ┌───────────┼───────────┐
            ↓           ↓           ↓
         PLAN         BUILD       VERIFY
            │           │           │
            └───────────┼───────────┘
                        ↓
                    FEEDBACK
                        ↓
                     IMPROVE
                        ↓
                 BETTER OUTCOME
```

### 5 Things to Memorize

> **1. LLM alone is not enough.**  
> **2. PLAN → BUILD → EVALUATE → IMPROVE.**  
> **3. Builder ≠ Evaluator.**  
> **4. "DONE" must be measurable.**  
> **5. Better models → simpler harness.**

---

# 🎯 ONE QUESTION FOR ARCHITECT REVISION

> **"If I give an AI a 6-hour task, what system do I need around it so that it can PLAN, BUILD, VERIFY, REMEMBER and RECOVER reliably?"**

If you can answer this question, you remember the essence of **Harness Engineering**.
