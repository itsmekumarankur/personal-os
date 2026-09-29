# 🧠 Helium — AI Coding Knowledge Layer Mind Map

> **Recall:** `TRUSTWORTHY AI CODING = CURRENT + HISTORICAL + MULTI-REPO + VALIDATED + FEEDBACK`

## 1. Core Problem

```text
AI Coding Assistant
        ↓
Needs engineering knowledge
        ↓
Quality depends on:
 ├── Freshness
 ├── Completeness
 ├── History
 ├── Multi-repo context
 └── Validation
```

> **Question:** "Does the AI have the right, current knowledge of our engineering ecosystem?"

## 2. Temporal Knowledge

```text
CODE V1 → V2 → V3 → V4
   │       │       │
   └───────┴───────┴──→ What was true when?
```

Helium should understand:
- Code version
- API version
- DB version
- What changed
- Why it changed (Git/Jira)

### Retrieval Modes

```text
CURRENT
HISTORICAL
MIGRATION PATHS
```

> **Helium should be a temporal index, not only HEAD.**

## 3. Keeping Index Fresh

```text
Git Push
   +
PR Merge
   +
Deployment
   ↓
Event Stream
   ↓
Index Update Queue
   ↓
Helium Refresh
```

### Consistency Decision

```text
High cost of stale context
 → stronger consistency

Low cost of stale context
 → eventual consistency
```

## 4. Multi-Repo Reality

```text
          IDFC Ecosystem
                │
      ┌─────────┼─────────┐
      ↓         ↓         ↓
   Wealth     Retail   Corporate
      └─────────┼─────────┘
                ↓
        Shared Libraries
```

Solution:

```text
Repo Indexes
    ↓
Federation
    ↓
Unified Query Plan
```

> **System must know what it doesn't know.**

```text
Known → Unknown → Search → Find → Add context
```

## 5. Testing Paradox

Generated code can:

```text
Compile ✓
   ↓
Semantic check ✓
   ↓
Still fail at runtime ❌
```

### Validation Spectrum

```text
STATIC → SEMANTIC → DYNAMIC
Compile   Architecture  Tests
Types     Reality       Integration
Syntax                  Performance
```

### Closed Loop

```text
GENERATE
   ↓
TEST
   ↓
LEARN
   ↓
GENERATE AGAIN
```

## 6. Developer Feedback

```text
Ticket → Helium → LLM → Generate → PR
                                  ↓
                             Developer
                                  ↓
                              Modify
                                  ↓
                               Commit
```

Two possible approaches:

```text
READ-ONLY TRUTH
Codebase truth only

LEARNING SYSTEM
Truth + preferences + emergent patterns
```

### Knowledge Types

```text
Hard Truth       → Code/schema/API reality
Soft Preference  → Style / naming / formatting
Emergent Pattern → Developer behavior / accepted solutions
```

## ⚡ 30-Second Recall

> **1. Current context matters.**
>
> **2. History matters when code evolves.**
>
> **3. Multi-repo dependencies require federation.**
>
> **4. Generated code needs dynamic validation.**
>
> **5. Developer changes create a feedback signal.**
>
> **6. The knowledge layer must know its own boundaries.**

### 🎯 Architect Question
> **"How do we ensure the AI knows what is true, when it was true, where it lives, and whether generated code actually works?"**
