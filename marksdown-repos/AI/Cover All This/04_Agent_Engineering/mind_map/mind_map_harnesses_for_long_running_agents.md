# 🧠 Effective Harnesses for Long-Running Agents — Mind Map

> **Core Mental Model:**  
> **INITIALIZE → BREAK INTO FEATURES → BUILD → TEST → COMMIT → UPDATE → CLEAN STATE → NEXT AGENT**

---

# 🌳 1. THE BIG PROBLEM

```text
                 LONG-RUNNING TASK
                        │
                        ↓
                LIMITED CONTEXT
                        │
          ┌─────────────┴─────────────┐
          ↓                           ↓
    Context gets full          Agent forgets
          │                           │
          ↓                           ↓
   Session ends              "What happened?"
          │
          ↓
      NEW AGENT
```

### Two major failures

```text
1️⃣ Agent tries to build EVERYTHING
        ↓
   Context exhausted

2️⃣ Agent thinks it is DONE
        ↓
   Many features still broken/missing
```

### Key insight

> **A long-running agent should NOT try to finish everything in one context window.**

---

# 🌿 2. THE SOLUTION — HARNESS

```text
                    LONG TASK
                       │
                       ↓
                 INITIALIZER
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       init.sh    feature_list   progress.txt
          │            │            │
          └────────────┼────────────┘
                       ↓
                    GIT REPO
                       │
                       ↓
                 CODING AGENT
                       │
                       ↓
                ONE FEATURE
                       │
                       ↓
                    TEST
                       │
              ┌────────┴────────┐
              ↓                 ↓
            FAIL               PASS
              ↓                 ↓
             FIX              COMMIT
                                │
                                ↓
                         UPDATE PROGRESS
                                │
                                ↓
                           CLEAN STATE
                                │
                                ↓
                           NEXT AGENT
```

---

# 🌿 3. INITIALIZER AGENT

## Responsibility → **PREPARE THE WORLD**

```text
                 INITIALIZER
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
    init.sh      progress.txt   feature_list.json
       │              │              │
       └──────────────┼──────────────┘
                      ↓
                   Git Repo
```

### Creates

- `init.sh` → how to start the project
- `progress.txt` → what has happened
- `feature_list.json` → what needs to be built
- Git history → what changed

### Mental model

> **Initializer = Set up the memory + roadmap + startup process**

---

# 🌿 4. FEATURE LIST = ROADMAP

Instead of:

```text
❌ "Build the entire application"
```

Create:

```text
✅ Feature 1
✅ Feature 2
✅ Feature 3
✅ Feature 4
...
```

Example:

```text
1. New Chat
2. Send Message
3. AI Reply
4. Save Conversation
5. Sidebar History
6. Theme Switch
```

Each feature should have:

```text
Feature
  ├── Description
  ├── Test Steps
  └── Pass / Fail
```

### Key principle

> **Big goal → Small measurable features**

---

# 🌿 5. BUILD ONE FEATURE AT A TIME

```text
              200 FEATURES
                    │
                    ↓
               PICK ONE
                    │
                    ↓
                  BUILD
                    │
                    ↓
                  TEST
                    │
                    ↓
                 COMMIT
                    │
                    ↓
              NEXT FEATURE
```

### Why?

```text
BIG WORK
   ↓
Hard to track
Hard to test
Hard to recover
Hard to handoff

SMALL FEATURES
   ↓
Measurable
Testable
Recoverable
Easy to handoff
```

> **Small measurable progress > unfinished large progress**

---

# 🌿 6. CLEAN STATE RULE ⭐

Every agent session should finish here:

```text
READ STATE
    ↓
IMPLEMENT
    ↓
RUN TESTS
    ↓
FIX BUGS
    ↓
GIT COMMIT
    ↓
UPDATE PROGRESS
    ↓
CLEAN STATE
```

### Clean State means

```text
✅ Code works
✅ Tests pass
✅ Git committed
✅ Progress updated
✅ Next agent can continue immediately
```

### Golden Rule

> **Never leave the project half-understood or half-broken for the next agent.**

---

# 🌿 7. GIT = PROJECT MEMORY

```text
       Git
        +
 Progress File
        +
 Feature List
        ↓
 PROJECT MEMORY
```

Example:

```text
abc123 → Add Chat UI
def456 → Add API
ghi789 → Save Conversations
```

Git allows the next agent to:

```text
Understand
   ↓
Continue
   ↓
Revert if needed
```

### Mental model

> **Conversation memory is temporary. Git is durable project memory.**

---

# 🌿 8. PROGRESS.TXT = SHIFT HANDOVER

Think of agents like engineers working in shifts:

```text
Agent 1
   ↓
progress.txt
   ↓
Agent 2
   ↓
progress.txt
   ↓
Agent 3
```

Example:

```text
COMPLETED
- Login
- Chat UI

WORKING
- Conversation Persistence

KNOWN BUG
- Refresh loses conversation

NEXT
- Fix persistence API
```

### Critical insight

> **Context Window ≠ Project Memory**

Use external artifacts for continuity.

---

# 🌿 9. END-TO-END TESTING

Unit tests alone are not enough.

```text
Unit Test       ✓
API Test        ✓
Browser Test    ❌
                 ↓
              REAL BUG
```

Real user flow:

```text
Browser
   ↓
Click Button
   ↓
API
   ↓
Database
   ↓
UI Update
```

### Confidence formula

```text
Code Test
    +
API Test
    +
Browser Test
    =
REAL CONFIDENCE
```

---

# 🌿 10. TEST LIKE A HUMAN

Don't only test:

```text
"Does the function return 200?"
```

Test the actual journey:

```text
Open App
   ↓
Click New Chat
   ↓
Type Message
   ↓
Press Enter
   ↓
Verify Reply
```

### Key idea

> **The agent should verify the product from the user's perspective.**

---

# 🌿 11. NEW AGENT STARTUP CHECKLIST

When a fresh agent starts:

```text
             NEW AGENT
                 │
                 ↓
          Read progress.txt
                 │
                 ↓
              git log
                 │
                 ↓
         Read feature list
                 │
                 ↓
             Start App
                 │
                 ↓
           Smoke Tests
                 │
                 ↓
          Pick ONE Feature
```

### Purpose

> **Minimize wasted context.**

---

# 🌿 12. COMPLETE AGENT LOOP

```text
             ┌─────────────────────┐
             │   READ PROJECT STATE │
             └──────────┬──────────┘
                        ↓
                 PICK ONE FEATURE
                        ↓
                     BUILD
                        ↓
                     TEST
                        ↓
                ┌───────┴───────┐
                ↓               ↓
              FAIL             PASS
                ↓               ↓
               FIX            COMMIT
                │               │
                └───────┐       ↓
                        │   UPDATE PROGRESS
                        │       │
                        └───────┘
                                ↓
                          CLEAN STATE
                                ↓
                         NEXT SESSION
```

---

# 🌿 13. FAILURE → HARNESS SOLUTION

| Failure | Harness Solution |
|---|---|
| Builds everything | One feature at a time |
| Forgets previous work | Progress file + Git |
| Says "Done" too early | Feature checklist |
| Doesn't know how to start | `init.sh` |
| Marks broken feature complete | Browser/E2E tests |
| Leaves messy project | Clean state + Git commit |

### Mental shortcut

> **Every harness component should solve a specific agent failure.**

---

# 🌿 14. MODEL vs HARNESS

```text
                 AI MODEL
                    │
                    ↓
              ┌─────────────┐
              │   HARNESS   │
              ├─────────────┤
              │ Tools       │
              │ Memory      │
              │ Git         │
              │ Tests       │
              │ Progress    │
              └──────┬──────┘
                     ↓
                REAL PROJECT
```

| AI Model | Harness |
|---|---|
| Intelligence | Continuity |
| Reasoning | Memory |
| Prompt | Project structure |
| Output | Reliable long-running work |

### Key idea

> **Model provides intelligence. Harness provides continuity.**

---

# 🌿 15. ONE-MINUTE MENTAL MODEL ⭐⭐⭐

```text
             LONG-RUNNING TASK
                     │
                     ↓
                INITIALIZE
                     │
                     ↓
             BREAK INTO FEATURES
                     │
                     ↓
                 AGENT LOOP
                     │
              ┌──────┴──────┐
              ↓             ↓
          READ STATE    PICK FEATURE
              │             │
              └──────┬──────┘
                     ↓
                   BUILD
                     ↓
                   TEST
                     ↓
              ┌──────┴──────┐
              ↓             ↓
            FAIL           PASS
              ↓             ↓
             FIX          COMMIT
                            ↓
                     UPDATE PROGRESS
                            ↓
                       CLEAN STATE
                            ↓
                       NEXT AGENT
```

---

# 🧠 16. THE FORMULA

```text
Long-Running Agent
        =
      LLM
       +
 External Memory
       +
 Small Features
       +
      Git
       +
    Testing
       +
 Progress Tracking
```

### Short version

> **LLM + Memory + Small Work + Tests + Git + Handoff**

---

# 🎯 17. CTO / AI ARCHITECT CHEAT SHEET

When designing a long-running agent, ask:

```text
1. How will the NEXT agent continue?

2. Where is PROJECT MEMORY stored?

3. Can the work be split into TESTABLE FEATURES?

4. What exactly defines DONE?

5. How does the agent RECOVER from failures?

6. Are BROWSER / E2E TESTS part of the workflow?

7. Does EVERY SESSION end in a CLEAN STATE?
```

---

# ⭐ 18. ARCHITECT'S MANTRA

```text
       SMALL FEATURES
              +
       EXTERNAL MEMORY
              +
         GIT HISTORY
              +
           TESTING
              +
        CLEAN HANDOFFS
              │
              ↓
   RELIABLE LONG-RUNNING
        AI AGENTS
```

---

# ⚡ 30-SECOND REVISION

If you remember only this:

```text
LONG TASK
   ↓
INITIALIZE
   ↓
BREAK INTO SMALL FEATURES
   ↓
READ STATE
   ↓
BUILD ONE FEATURE
   ↓
TEST LIKE A USER
   ↓
FIX
   ↓
GIT COMMIT
   ↓
UPDATE PROGRESS
   ↓
CLEAN STATE
   ↓
NEXT AGENT
```

### 🔥 Final 5 Things to Remember

> **1. Don't build everything in one context.**  
> **2. Break the project into small, testable features.**  
> **3. Git + progress files = external project memory.**  
> **4. Test end-to-end, like a real user.**  
> **5. Every session must end in a clean state.**

---

# 🧩 THE ONE QUESTION

> **"If the current AI agent disappears right now, can another agent open the project and continue immediately without asking me what happened?"**

If the answer is **YES**, the harness is doing its job.
