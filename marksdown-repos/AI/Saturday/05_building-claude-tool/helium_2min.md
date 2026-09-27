# Helium 2 Minute


Your company wants an AI coding assistant for **100 developers**.

It works well in a small pilot. Then the team rolls it out broadly—and developers start getting **stale code suggestions**, because the codebase is changing constantly. Some teams also depend on other repositories that the assistant cannot see. ([GitHub][1])

As the Engineering Manager, you realize the real question isn't:

> **“Is the LLM good?”**

It is:

> **“Does our AI have the right, current knowledge of our engineering ecosystem?”**

Now you start asking about **code history, index freshness, multi-repo knowledge, validation, and developer feedback**—the exact architectural concerns raised in the Helium note. ([GitHub][1])

### Why I am reading this

**Because an AI coding tool is only as useful as the quality, freshness, and completeness of the engineering knowledge it can access.**

### Leadership question

> **“How do we ensure the AI is using the current and complete context of our codebase?”**

### One-line takeaway

> **AI coding is not just about the model—it is about giving the model trustworthy engineering knowledge.**

---

## ADDENDUM 1: THE TEMPORAL DIMENSION

### ❓ What happens to the knowledge layer when time moves forward?

```
               TIME
                 |
    +------------+------------+------------+
    |            |            |            |
    v            v            v            v
  TODAY      TOMORROW    NEXT WEEK    NEXT YEAR
    |            |            |            |
    v            v            v            v
 CODE        CODE         CODE         CODE
  V1           V2           V3           V4
```

### Scenario: Breaking Change

```
MONDAY:
CustomerService.java
    |
    +-- getCustomerCategory()
    |       |
    |       +-- returns String
    |
    +-- setCustomerCategory(String)

TUESDAY:
CustomerService.java
    |
    +-- getCustomerCategory()
    |       |
    |       +-- returns CustomerCategory enum
    |
    +-- setCustomerCategory(CustomerCategory)
```

### The Architect's Question:

> **Does Helium know the old version existed?**

<details>
<summary>Reveal</summary>

If Helium only indexes HEAD:

```
          PROBLEM
             |
             v
    LLM sees only enum
             |
             v
    Generated code uses enum
             |
             v
    But deployment fails because
    customer_category in DB is
    still VARCHAR
```

</details>

### Deep Architecture Must Track:

```
                  TIME CAPSULES
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
    CODE VERSION   API VERSION    DB VERSION
        |              |              |
        +--------------+--------------+
                       |
                       v
            "What was true at
             the time of this
             JIRA ticket?"
```

### Helium Retrieval Modes:

```
                 HELIUM RETRIEVAL
                       |
          +------------+------------+
          |            |            |
          v            v            v
    CURRENT        HISTORICAL    MIGRATION
    CONTEXT        CONTEXT       PATHS
```

### Architectural Implication:

Helium isn't just a snapshot of code. It's a **temporal index** of:
- What existed
- When it existed
- What changed
- Why it changed (via git/Jira)

This makes the system aware of:

```
CODE HISTORY
      |
      +-- Breaking changes
      |
      +-- Deprecations
      |
      +-- Migration patterns
      |
      +-- When a fix is actually
           reverting an earlier change
```

### 💭 Thought-Provoking Question:

> **If Helium tracks time, can it predict where code is heading?**

<details>
<summary>Reveal</summary>

Not with certainty. But it can identify:

```
               PATTERNS
                  |
    +-------------+-------------+
    |             |             |
    v             v             v
CONSISTENT    EVOLVING       UNSTABLE
   AREA         AREA           AREA
```

The LLM could then be told:

> "This file changes frequently. Consider writing defensive code with proper abstraction."

</details>

---

## ADDENDUM 2: THE SCALE PROBLEM

### ❓ What happens when 100 developers are all using idfc-coder simultaneously?

```
              SCALE
                |
    +-----------+-----------+
    |           |           |
    v           v           v
 1 DEV      10 DEVS    100 DEVS
    |           |           |
    v           v           v
 1 QUERY    10 QUERIES 100 QUERIES
```

### The Hidden Question:

> **Does Helium's index get invalidated every time someone commits?**

<details>
<summary>Reveal</summary>

```
DEVELOPER A
     |
     v
  changes UpiService.java
     |
     v
  commits
     |
     v
  PR merged
     |
     v
  Helium index is now STALE
     |
     v
  DEVELOPER B asks about UpiService
     |
     v
  Helium returns OLD version
     |
     v
  DEVELOPER B generates code against OLD
     |
     v
  💥 CONFLICT
```

</details>

### Architecture Needs:

```
               EVENT STREAM
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
    GIT PUSH   PR MERGE   DEPLOYMENT
        |           |           |
        +-----------+-----------+
                    |
                    v
          INDEX UPDATE QUEUE
                    |
                    v
             HELIUM REFRESH
```

### 💭 Deeper Question:

> **Should Helium be eventually consistent or strongly consistent?**

<details>
<summary>Reveal</summary>

```
EVENTUALLY CONSISTENT
        |
        +-- Index updated minutes after commit
        +-- Developers may get stale context
        +-- Simpler, less resource-intensive

STRONGLY CONSISTENT
        |
        +-- Index updated instantly
        +-- Developers always get current context
        +-- Complex, expensive
```

**Architectural insight:** The answer depends on:

```
         COST OF STALE CONTEXT
                |
      +---------+---------+
      |                   |
      v                   v
   HIGH RISK          LOW RISK
      |                   |
      +---------+---------+
                |
                v
      Appropriate consistency model
```

**If stale context causes:**
- Security issues
- Data corruption
- Production outages

→ **Strongly consistent** is worth the cost.

**If stale context causes:**
- Minor bugs
- Developer rework
- Slight inefficiency

→ **Eventually consistent** is acceptable.

</details>

---

## ADDENDUM 3: THE MULTI-REPO REALITY

### ❓ What if IDFC code isn't in one repository?

```
                    IDFC ECOSYSTEM
                          |
        +-----------------+-----------------+
        |                 |                 |
        v                 v                 v
   WEALTH            RETAIL           CORPORATE
   REPO              REPO              REPO
        |                 |                 |
        +-----------------+-----------------+
                          |
                    +-----+-----+
                    |           |
                    v           v
                 SHARED      THIRD-PARTY
                 LIBS        DEPENDENCIES
```

### The Question:

> **Can Helium see across repo boundaries?**

<details>
<summary>Reveal</summary>

```
      SERVICE A
          |
          | depends on
          v
      SERVICE B
          |
          | depends on
          v
      SHARED LIB
```

If Helium only indexes one repository:

```
     SERVICE A REPO
          |
          X
          |
     SERVICE B REPO  ← Helium doesn't know this exists
          |
          X
          |
     SHARED LIB      ← Helium doesn't know this exists
```

Then:

```
LLM generates code that calls:
  SharedLib.doSomething()
  
But Helium doesn't know SharedLib exists
  |
  v
Validation fails
  |
  v
But the code is actually correct!
```

</details>

### Architectural Solution:

```
                HELIUM FEDERATION
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
   WEALTH         RETAIL       CORPORATE
   INDEX          INDEX         INDEX
        |             |             |
        +-------------+-------------+
                      |
                      v
            UNIFIED QUERY PLAN
```

### 💭 Deeper Architectural Insight:

> **The system needs to know what it doesn't know.**

<details>
<summary>Reveal</summary>

```
              KNOWLEDGE BOUNDARY
                    |
       +------------+------------+
       |            |            |
       v            v            v
    KNOWN        UNKNOWN      ASSUMED
   CONTEXT      CONTEXT      CONTEXT
       |            |            |
       +------------+------------+
                    |
                    v
         "I don't know SharedLib.
          Let me search all repos."
                    |
                    v
         Found SharedLib
                    |
                    v
         Including it in context
```

</details>

---

## ADDENDUM 4: THE TESTING PARADOX

### ❓ How does the system know if generated code actually works?

```
                      GENERATED CODE
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
        COMPILES       WORKS FOR       WORKS FOR
                     HAPPY PATH      EDGE CASES
             |              |              |
             +--------------+--------------+
                            |
                            v
                   IS THIS ENOUGH?
```

### Think About:

```
    LLM generates code
            |
            v
    Compiles ✅
            |
            v
    Helium validates structure ✅
            |
            v
    But does it actually WORK?
```

### Validation Spectrum:

```
             VALIDATION SPECTRUM
                    |
    +---------------+---------------+
    |               |               |
    v               v               v
STATIC          SEMANTIC        DYNAMIC
VALIDATION      VALIDATION     VALIDATION
    |               |               |
    v               v               v
Compiles       Helium          Tests pass?
Type checks    Reality         Integration?
Syntax         Architecture    Performance?
```

### The Architectural Question:

> **Is there a testing environment where generated code is automatically run?**

<details>
<summary>Reveal</summary>

```
      GENERATED CODE
            |
            v
      STATIC VALIDATION
            |
            v
      SEMANTIC VALIDATION
            |
            v
      +------------------+
      |  TEST SANDBOX    |
      |                  |
      |  Does it pass?   |
      +------------------+
            |
    +-------+-------+
    |               |
  PASS             FAIL
    |               |
    v               v
   PR          Regenerate
```

</details>

### 💭 Deeper Question:

> **Can Helium itself generate tests to verify the generated code?**

<details>
<summary>Reveal</summary>

```
     GENERATED CODE
          |
          v
     HELIUM
          |
          +-- "What should this do?"
          |
          +-- "What are the edge cases?"
          |
          +-- "What are the constraints?"
          |
          v
     GENERATED TESTS
          |
          v
     RUN TESTS
          |
    +-------+-------+
    |               |
  PASS             FAIL
    |               |
    v               v
   PR       Analyze failure
            |
            v
        Regenerate with
        learned context
```

This becomes a **closed loop**:

```
        GENERATE → TEST → LEARN → GENERATE
```

</details>

---

## ADDENDUM 5: THE USER FEEDBACK LOOP

### ❓ What happens when developers reject or modify generated PRs?

**Current one-way flow:**

```
    TICKET → HELIUM → LLM → GENERATE → PR
```

**Reality:**

```
    TICKET → HELIUM → LLM → GENERATE → PR → DEVELOPER
                                                    |
                                                    v
                                                MODIFIES
                                                    |
                                                    v
                                                COMMITS
```

### The Architectural Question:

> **Does Helium learn from this feedback?**

<details>
<summary>Reveal</summary>

Consider:

```
DEVELOPER REJECTION:
    Generated code used CustomerCategory enum
    Developer changed it back to String
    |
    v
Should Helium remember this?
```

</details>

### Two Philosophies:

**Philosophy A: Helium is read-only truth**

```
Helium reflects codebase truth
    |
    v
Developers modify PRs
    |
    v
Helium eventually indexes the changes
    |
    v
But doesn't learn "preferences"
```

**Philosophy B: Helium is a learning system**

```
Helium reflects codebase truth
    |
    +-- Developer rejected enum
    |
    +-- Developer used String
    |
    +-- Helium records this pattern
    |
    +-- Next time, suggests String
```

### 💭 The Deeper Architectural Insight:

```
              KNOWLEDGE TYPES
                    |
    +---------------+---------------+
    |               |               |
    v               v               v
 HARD TRUTH     SOFT PREFERENCE    EMERGENT PATTERN
    |               |               |
    v               v               v
Code actual     Style choices    Developer behavior
Schema actual   Naming patterns  Common rejections
API actual      Formatting       Most-accepted solutions
```

- **Hard truth:** Helium should never override.
- **Soft preference:** Helium can learn.
- **Emergent pattern:** Helium can suggest.

---

## Summary of Key Architectural Insights

| Addendum | Core Question | Key Takeaway |
|----------|---------------|--------------|
| 1. Temporal | Does Helium know old versions? | Helium needs a temporal index — not just HEAD |
| 2. Scale | How does index stay fresh? | Event stream + consistency model based on risk |
| 3. Multi-Repo | Can Helium see across repos? | Federation + knowledge boundary awareness |
| 4. Testing | Does generated code actually work? | Static → Semantic → Dynamic validation loop |
| 5. Feedback | Does Helium learn from rejections? | Distinguish hard truth vs soft preference vs patterns |
