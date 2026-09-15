# Effective Harnesses for Long-Running Agents — Easy Notes

**Source:** Anthropic — Effective Harnesses for Long-Running Agents

https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

> **Core idea:** A long-running AI agent should not try to finish everything in one context window. Instead, it works in disciplined sessions: understand → build one feature → test → save progress → hand over.

---

# 1. The Problem: AI Has Limited Context

```text
              BIG PROJECT
                  |
                  v
          +---------------+
          | Agent Session 1|
          +-------+-------+
                  |
             Context Full
                  X
                  |
          Session 2 starts
                  |
                  v
          "What happened?"
```

**Problem:** Every new session can lose context from previous work.

---

# 2. Why Context Compaction Isn't Enough

### Problem 1 — Agent tries to do too much

```text
Build everything
      |
      v
 Feature A+B+C+D
      |
 Context exhausted
```

### Problem 2 — Agent declares victory too early

```text
Project looks complete
        |
        v
       DONE ❌
```

Reality:

```text
200 Features
 |
 +-- 80 Complete
 +--120 Remaining
```

---

# 3. Anthropic's Solution

```text
          LONG TASK
              |
              v
      INITIALIZER AGENT
              |
              v
        CODING AGENT
              |
              v
 Save Progress + Git + Tests
              |
              v
        NEXT SESSION
```

**Initializer** prepares the project.

**Coding Agent** completes one feature per session.

---

# 4. Initializer Creates Project Memory

```text
           INITIALIZER
                |
    +-----------+-----------+
    |           |           |
 init.sh   progress.txt  feature_list.json
                |
                v
             Git Repo
```

Project memory includes:

- init.sh
- progress.txt
- feature_list.json
- Git history

---

# 5. Feature List = Roadmap

Instead of one huge goal:

```text
Build App
```

Create many features.

```text
1. New Chat
2. Send Message
3. AI Reply
4. Save Conversation
5. Sidebar History
6. Theme Switch
...
```

Each feature contains:

- Description
- Test steps
- Pass/Fail flag

---

# 6. Build One Feature at a Time

```text
200 FEATURES
     |
 Pick ONE
     |
 Build
     |
 Test
     |
 Commit
     |
 Next Feature
```

**Small measurable progress beats unfinished large progress.**

---

# 7. Clean State Rule

Every session ends here:

```text
Read State
    |
Implement
    |
Run Tests
    |
Fix Bugs
    |
Git Commit
    |
Update Progress
    |
 CLEAN STATE
```

Checklist:

- Code works.
- Tests pass.
- Git committed.
- Progress updated.
- Next session can continue immediately.

---

# 8. Git = Project Memory

```text
Git
 +
Progress File
 +
Feature List
 =
PROJECT MEMORY
```

Example:

```text
abc123 Add Chat UI
def456 Add API
ghi789 Save Conversations
```

Git helps understand, continue, or revert work.

---

# 9. Progress File = Shift Handover

```text
Agent 1
   |
progress.txt
   |
Agent 2
   |
progress.txt
   |
Agent 3
```

Example:

```text
Completed:
- Login
- Chat UI

Working:
- Conversation Persistence

Known Bug:
- Refresh loses conversation

Next:
- Fix persistence API
```

**Context Window ≠ Project Memory**

Use external artifacts for continuity.

---

# 10. Test End-to-End

```text
Unit Test ✓
API Test ✓
Browser Test ❌
```

Real flow:

```text
Browser
  |
Click Button
  |
 API
  |
Database
  |
 UI Update
```

E2E testing verifies the actual user experience.

---

# 11. Test Like a Human

```text
Open App
   |
Click New Chat
   |
Type Message
   |
Press Enter
   |
Verify Reply
```

Confidence comes from:

```text
Code Test
   +
API Test
   +
Browser Test
   =
Real Confidence
```

---

# 12. New Agent Startup Checklist

```text
NEW AGENT
   |
Read progress.txt
   |
git log
   |
Read feature list
   |
Start App
   |
Run Smoke Tests
   |
Pick ONE Feature
```

This minimizes wasted context.

---

# 13. Complete Harness Architecture

```text
                USER
                  |
                  v
             INITIALIZER
                  |
   +--------------+--------------+
   |              |              |
init.sh     feature_list    progress.txt
   |              |              |
   +--------------+--------------+
                  |
                Git Repo
                  |
===================================
         CODING AGENT LOOP
===================================
                  |
            Read Project State
                  |
             Pick One Feature
                  |
               Implement
                  |
                 Test
            +-----+-----+
            |           |
          FAIL        PASS
            |           |
           Fix      Git Commit
                        |
                 Update Progress
                        |
                   CLEAN STATE
                        |
                    NEXT SESSION
```

---

# 14. Failure → Solution

| Failure | Harness Solution |
|--------|-------------------|
| Builds everything | One feature at a time |
| Forgets work | Progress file + Git |
| Says Done too early | Feature checklist |
| Doesn't know startup | init.sh |
| Marks broken feature complete | Browser tests |
| Leaves messy project | Clean state + Git commit |

---

# 15. Model vs Harness

```text
            AI MODEL
               |
               v
        +--------------+
        |   HARNESS    |
        |--------------|
        | Tools        |
        | Memory       |
        | Git          |
        | Tests        |
        | Progress     |
        +------+-------+
               |
               v
          Real Project
```

| Model | Harness |
|------|---------|
| Intelligence | Continuity |
| Reasoning | Memory |
| Prompt | Project Structure |
| Output | Reliable Long-running Work |

---

# 16. One-Minute Mental Model

```text
LONG-RUNNING TASK
        |
    INITIALIZE
        |
 BREAK INTO FEATURES
        |
   AGENT LOOP
        |
 Read State
        |
 Pick Feature
        |
 Build
        |
 Test
        |
 Commit
        |
 Update Progress
        |
 CLEAN STATE
        |
 NEXT AGENT
```

Formula:

```text
Long-running Agent
    =
LLM
+ External Memory
+ Small Features
+ Git
+ Testing
+ Progress Tracking
```

---

# 17. CTO / AI Architect Cheat Sheet

Ask yourself:

```text
1. How will the next agent continue?

2. Where is project memory stored?

3. Can work be split into testable features?

4. What defines DONE?

5. How do we recover from failures?

6. Are browser tests part of the workflow?

7. Does every session end in a clean state?
```

---

# ⭐ Final Takeaway

```text
DON'T SAY:
"Finish the project."

INSTEAD SAY:

Build ONE feature
      |
      v
Test it
      |
      v
Commit it
      |
      v
Update progress
      |
      v
Leave clean state
      |
      v
Next agent continues
```

## Architect's Mantra

```text
Small Features
      +
External Memory
      +
Git History
      +
Testing
      +
Clean Handoffs
      =
Reliable Long-Running AI Agents
```
