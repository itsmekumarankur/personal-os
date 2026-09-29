# IDFC Coder — Safety Guardrails Memory Map

> **Goal:** Remember the entire safety architecture without memorizing every component.

---

# 1. MASTER MEMORY MAP

```text
                         IDFC CODER
                             |
                             v
                    "Can I trust this request?"
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
       BEFORE             DURING             AFTER
        LLM                 LLM                LLM
          |                  |                  |
          v                  v                  v
   IDENTITY + ACCESS      MODEL CONTROL      OUTPUT CONTROL
          |                  |                  |
          v                  v                  v
   +---------------+   +---------------+   +----------------+
   | WAF           |   | Context       |   | Validation     |
   | Authentication|   | Queue         |   | Security Scan  |
   | RBAC          |   | Router        |   | Compliance     |
   | Prompt Policy |   | vLLM / LLM    |   | Quality        |
   | Rate Limit    |   | Resource Ctrl |   | Audit          |
   | Quota         |   +---------------+   +----------------+
   +---------------+
```

---

# 2. THE 5-WORD MEMORY HOOK

## Remember:

```text
IDENTITY
   ↓
ACCESS
   ↓
CONTEXT
   ↓
MODEL
   ↓
OUTPUT
```

### Identity
**Who are you?**

→ Authentication

### Access
**What are you allowed to do?**

→ RBAC / Authorization / Prompt Policy

### Context
**What information can the model see?**

→ Context Engine / Helium / Repository isolation

### Model
**How does the request reach the model safely?**

→ Rate Limit / Quota / Queue / Routing / Self-hosting

### Output
**Can I trust what came out?**

→ Validation / Security / Compliance / Audit

---

# 3. THE SIMPLEST STORY

```text
USER
 |
 | 1. Who are you?
 v
AUTH
 |
 | 2. Are you allowed?
 v
RBAC
 |
 | 3. Is this request allowed?
 v
PROMPT GATEWAY
 |
 | 4. What does the model need to see?
 v
CONTEXT ENGINE
 |
 | 5. Can we handle this request?
 v
QUEUE + ROUTER
 |
 | 6. Generate
 v
LLM
 |
 | 7. Is the answer safe?
 v
VALIDATION + SECURITY
 |
 | 8. Record what happened
 v
AUDIT
```

---

# 4. MEMORY TREE

```text
IDFC CODER SAFETY
│
├── 1. TRUST BOUNDARY
│   └── Self-hosting / Private VPC
│
├── 2. EDGE
│   └── WAF
│
├── 3. IDENTITY
│   └── Authentication
│
├── 4. ACCESS
│   ├── RBAC
│   ├── Authorization
│   └── Prompt Policy
│
├── 5. CONTEXT
│   ├── Helium
│   ├── Relevant Files
│   ├── Relevant Symbols
│   ├── Repository Isolation
│   └── Fresh Index
│
├── 6. RESOURCE CONTROL
│   ├── Rate Limit
│   ├── Quota
│   └── Token Control
│
├── 7. INFERENCE
│   ├── Queue
│   ├── Model Router
│   ├── vLLM
│   └── GPU
│
├── 8. MODEL GOVERNANCE
│   ├── Validation
│   ├── Benchmark
│   ├── Security Scan
│   ├── Canary
│   └── Rollback
│
├── 9. OUTPUT SAFETY
│   ├── Validation
│   ├── Quality
│   ├── Security
│   └── Compliance
│
└── 10. AUDIT
    ├── User
    ├── Repository
    ├── Model Version
    ├── Token Usage
    ├── Policy Decision
    └── Security Result
```

---

# 5. ONE QUESTION PER LAYER

Memorize these 10 questions:

| Layer | Question |
|---|---|
| Trust | **Where does my sensitive code go?** |
| WAF | **Should this request enter?** |
| Authentication | **Who are you?** |
| Authorization | **What are you allowed to access?** |
| Prompt Gateway | **Is this request allowed?** |
| Context | **What should the model see?** |
| Resource | **How much can you consume?** |
| Model | **Which model should handle it?** |
| Output | **Can I trust what came back?** |
| Audit | **Can I prove what happened?** |

---

# 6. THE GOLDEN PRINCIPLE

```text
             NEVER TRUST THE LLM ALONE
                       |
                       v
       +---------------+---------------+
       |                               |
       v                               v
DETERMINISTIC CONTROLS          PROBABILISTIC MODEL
       |                               |
       v                               v
Auth / RBAC / Policy                  LLM
Rate Limit / Quota
Context Control
Validation
Security
Compliance
```

### Remember:

> **LLM = Intelligence**
>
> **Platform = Control**

---

# 7. DEFENSE-IN-DEPTH MEMORY

Think of a bank vault.

```text
                    BANK VAULT
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
      GATE           ROOM          VAULT
        |              |              |
      WAF            RBAC          Output
      Auth           Context       Security
      Policy         Model         Audit
```

No single lock is enough.

Similarly:

> **AI safety = multiple independent controls.**

---

# 8. BEFORE / DURING / AFTER

## BEFORE LLM

```text
WAF
 ↓
Authentication
 ↓
RBAC
 ↓
Prompt Policy
 ↓
Context Control
 ↓
Rate Limit
 ↓
Quota
```

Question:

> **Can this request safely reach the model?**

---

## DURING LLM

```text
Queue
 ↓
Router
 ↓
Model
 ↓
GPU
```

Question:

> **Can we safely execute this request?**

---

## AFTER LLM

```text
Validation
 ↓
Quality
 ↓
Security
 ↓
Compliance
 ↓
Audit
```

Question:

> **Can we safely return this result?**

---

# 9. HELIUM MEMORY HOOK

Remember:

```text
HELIUM = "What should the model SEE?"
```

Not:

```text
HELIUM = "Give the model the whole repository."
```

Correct:

```text
Repository
    |
    v
Helium
    |
    v
Relevant Context
    |
    v
LLM
```

### Two Helium safety ideas

```text
1. MINIMIZE
   Give only relevant context.

2. REFRESH
   Keep context synchronized with Git changes.
```

---

# 10. STALE CONTEXT MEMORY

Remember this story:

```text
OLD CODE
   |
   v
OLD INDEX
   |
   v
LLM
   |
   v
WRONG CODE
```

Therefore:

```text
Git
 |
 v
Event
 |
 v
Index Refresh
 |
 v
Fresh Context
 |
 v
LLM
```

### Memory phrase:

> **Fresh context = safer context.**

---

# 11. GATEWAY MEMORY HOOK

Remember:

```text
PROMPT GATEWAY
      |
      +--> AUTH
      +--> ACCESS
      +--> POLICY
      +--> RATE
      +--> QUOTA
      +--> CONTEXT
```

The gateway is:

> **The policy enforcement point between the developer and the LLM.**

---

# 12. MODEL SAFETY MEMORY HOOK

Never:

```text
New Model
   |
   v
Production
```

Always:

```text
New Model
   |
   v
Validate
   |
   v
Benchmark
   |
   v
Security Scan
   |
   v
Canary
   |
   v
Production
```

Memory phrase:

> **Validate → Benchmark → Scan → Canary → Production**

---

# 13. CANARY MEMORY HOOK

```text
v1 = 95%
v2 = 5%
```

Observe:

```text
Latency
Errors
Quality
Security
Feedback
Cost
```

Then:

```text
5 → 25 → 50 → 100
```

If bad:

```text
v2 → ROLLBACK → v1
```

---

# 14. OUTPUT SAFETY MEMORY HOOK

Never:

```text
LLM
 ↓
Developer
```

Always:

```text
LLM
 ↓
Validate
 ↓
Security
 ↓
Compliance
 ↓
Developer
```

Memory phrase:

> **Generated ≠ Trusted**

---

# 15. AUDIT MEMORY HOOK

Remember:

```text
WHO?
WHAT?
WHERE?
WHICH MODEL?
HOW MUCH?
WHAT DECISION?
```

Translate:

```text
WHO          → User
WHAT         → Request
WHERE        → Repository / Branch
WHICH MODEL  → Model Version
HOW MUCH     → Tokens
DECISION     → Policy / Security Result
```

---

# 16. FAILURE MEMORY MAP

## Unauthorized

```text
User
 ↓
RBAC
 ↓
X
403
```

## Too many requests

```text
User
 ↓
Rate Limit
 ↓
X
429
```

## No quota

```text
User
 ↓
Quota
 ↓
X
Reject
```

## Sensitive context

```text
Context Engine
 ↓
Sensitive File
 ↓
X
Do Not Send
```

## Bad model output

```text
LLM
 ↓
Security Scan
 ↓
X
Block / Warn / Review
```

## Bad model version

```text
Canary
 ↓
Bad Metrics
 ↓
Rollback
```

---

# 17. INTERVIEW MEMORY MAP

If CTO asks:

> **"How did you make IDFC Coder safe?"**

Think:

```text
                SAFETY
                   |
      +------------+------------+
      |            |            |
      v            v            v
   BEFORE        DURING        AFTER
      |            |            |
      v            v            v
   CONTROL       CONTROL       CONTROL
      |            |            |
      v            v            v
 WAF/Auth/RBAC   Queue/Model   Validate/
 Policy/Quota    Routing       Security/
 Context                       Compliance
      |            |            |
      +------------+------------+
                   |
                   v
                 AUDIT
```

Then say:

> **"We designed defense in depth rather than relying on the model itself."**

---

# 18. THE 30-SECOND ANSWER

> **"We treated the LLM as a probabilistic component inside a deterministic control plane. Before inference we enforced WAF, authentication, RBAC, prompt policy, rate limits, quotas and context controls. We minimized the repository context through Helium instead of exposing everything. During inference we used queues and model routing, with self-hosting keeping sensitive code inside the trust boundary. Models went through validation, security scanning and canary deployment. After inference we validated the generated output for quality, security and compliance, and maintained auditability of the user, repository, model and request lifecycle."**

---

# 19. THE 10-SECOND ANSWER

> **"Control the identity, control the access, minimize the context, govern the model, validate the output — and audit the entire lifecycle."**

---

# 20. FINAL MEMORY CARD

```text
╔══════════════════════════════════════════════╗
║              IDFC CODER SAFETY              ║
╠══════════════════════════════════════════════╣
║                                              ║
║  1. TRUST      → Self-host / Private VPC     ║
║  2. ENTER      → WAF                         ║
║  3. IDENTITY   → Authentication              ║
║  4. ACCESS     → RBAC / Authorization        ║
║  5. POLICY     → Prompt Gateway              ║
║  6. CONTEXT    → Helium / Least Context      ║
║  7. RESOURCES  → Rate / Quota / Tokens       ║
║  8. MODEL      → Queue / Router / vLLM       ║
║  9. OUTPUT     → Validate / Security         ║
║ 10. GOVERN     → Canary / Audit / Rollback   ║
║                                              ║
╠══════════════════════════════════════════════╣
║                                              ║
║  CORE IDEA:                                  ║
║                                              ║
║  LLM = Intelligence                          ║
║  Platform = Control                          ║
║                                              ║
║  "Generated ≠ Trusted."                      ║
║                                              ║
╚══════════════════════════════════════════════╝
```

---

# 21. Final Architect Mental Model

> **CONTROL WHAT ENTERS**
>
> **CONTROL WHAT THE MODEL SEES**
>
> **CONTROL WHAT IT CONSUMES**
>
> **CONTROL WHICH MODEL RUNS**
>
> **VALIDATE WHAT COMES OUT**
>
> **AUDIT WHAT HAPPENED**

That is the entire IDFC Coder safety architecture in one mental model.
