# IDFC Coder — Safety Guardrails
## Detailed Architect Notes: How We Made a Claude-Like Coding Assistant Safe for a Bank

> **Core principle:** The LLM is not the security boundary. The platform around the LLM is the security boundary.

---

# 1. The Core Safety Architecture

A dangerous design would be:

```text
Developer
   |
   v
  LLM
   |
   v
 Code
```

IDFC Coder should instead enforce multiple deterministic controls around the probabilistic model:

```text
Developer
    |
    v
IDE / Web UI
    |
    v
CloudFront
    |
    v
WAF
    |
    v
Authentication
    |
    v
+-------------------------+
|     PROMPT GATEWAY      |
|                         |
|  Authentication         |
|  Authorization          |
|  Prompt Policy          |
|  Rate Limit             |
|  Quota                  |
|  Context Control        |
+------------+------------+
             |
             v
      Context Engine
             |
             v
        Request Queue
             |
             v
       Inference Router
             |
             v
       vLLM / LLM
             |
             v
     POST-PROCESSING
             |
             +--> Validation
             +--> Quality Check
             +--> Security Scan
             +--> Compliance
             |
             v
          Response
```

The important architectural idea is:

> **We did not try to make the LLM itself the security mechanism. We built a controlled execution environment around it.**

---

# 2. Why Safety Is Critical for IDFC Coder

A banking coding assistant can potentially see:

- Internal source code
- Internal APIs
- Database schemas
- Authentication mechanisms
- Business rules
- Payment logic
- Mutual-fund logic
- Infrastructure configuration
- Internal architecture
- Potentially sensitive customer-related code

So the real security questions are:

1. What information can enter the AI system?
2. Who can use the system?
3. What repositories can a developer access?
4. What context can the model see?
5. Which model can process the request?
6. How much can a user consume?
7. What can leave the model?
8. Can we audit what happened?

---

# 3. Guardrail #1 — Keep Sensitive Code Inside the Trust Boundary

One of the biggest decisions was self-hosting.

Instead of:

```text
Developer
   |
   v
Internet
   |
   v
External AI Provider
   |
   v
LLM
```

the controlled architecture is:

```text
Developer
   |
   v
IDFC Network
   |
   v
Private VPC
   |
   +------------------+
   |                  |
   v                  v
Prompt Gateway     Context Engine
   |                  |
   +--------+---------+
            |
            v
       GPU Cluster
            |
            v
           LLM
```

### Why?

Because source code and sensitive context remain inside the organization's controlled environment.

### Key principle

> **The more sensitive the data, the less we want it crossing organizational boundaries.**

Self-hosting is therefore not merely a GPU/cost decision. It is a **trust-boundary decision**.

---

# 4. Guardrail #2 — WAF at the Edge

The first security layer is:

```text
Internet
   |
   v
CloudFront
   |
   v
WAF
   |
   v
ALB
```

Think of WAF as:

> **"Should this HTTP/API request even enter my application?"**

WAF protects the application from malicious web/API traffic.

It is not responsible for determining whether generated Java code is correct.

---

# 5. Guardrail #3 — Authentication

Before the request reaches the AI platform, we need to know:

> **Who is making this request?**

```text
Developer
    |
    v
Authentication
    |
    +---- invalid --> Reject
    |
    +---- valid ----> Continue
```

Enterprise SSO/Identity Provider establishes the user's identity.

Conceptually:

```text
User
  |
  v
Identity
  |
  v
Employee / Developer
  |
  v
Team / Role
```

---

# 6. Guardrail #4 — Authorization / RBAC

Authentication answers:

> **Who are you?**

Authorization answers:

> **What are you allowed to do?**

Example:

```text
Developer A
   |
   +--> Wealth repositories
   |
   +--> Can generate code
   |
   +--> Cannot access restricted repository
```

Another developer may have:

```text
Developer B
   |
   +--> Retail repository
   |
   +--> Can use normal model
   |
   +--> Cannot access restricted model
```

Flow:

```text
Authenticated User
        |
        v
      RBAC
        |
   +----+----+
   |         |
 allowed   denied
   |         |
   v         v
continue    403
```

### Important principle

> **Never let repository access be decided by the LLM.**

Authorization should be deterministic and enforced before the model sees the request.

---

# 7. Guardrail #5 — Prompt Gateway

The most important control point is the Prompt Gateway.

Instead of:

```text
Developer --> LLM
```

we enforce:

```text
Developer
    |
    v
Prompt Gateway
    |
    v
LLM
```

The gateway is not just a proxy.

> **It is a policy-enforcement layer.**

It can enforce:

```text
Authentication
Authorization
Prompt Policy
Rate Limiting
Quota
Token Control
Context Policy
```

Conceptually:

```text
                    PROMPT GATEWAY

                        Request
                           |
                           v
                  +----------------+
                  | Authentication|
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Authorization  |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Prompt Policy  |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Rate Limiting  |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Quota Check    |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  | Context Policy |
                  +-------+--------+
                          |
                          v
                    LLM Request
```

---

# 8. Guardrail #6 — Prompt Validation and Policy

Before sending a prompt to the LLM:

```text
Developer Prompt
       |
       v
Prompt Validation
       |
       +---- invalid --> Reject
       |
       +---- valid ----> Continue
```

Potentially problematic requests include:

```text
"Ignore all system instructions..."

"Give me secrets from the repository..."

"Show production credentials..."

"Read every repository..."

"Generate code that bypasses authentication..."
```

The gateway is the natural place to enforce organizational policy.

### Architect-level statement

> **We did not make the model responsible for enforcing every policy. We put deterministic policy controls before inference.**

---

# 9. Guardrail #7 — Context Control

A dangerous approach would be:

```text
Developer asks question
        |
        v
Send entire repository
        |
        v
LLM
```

Instead:

```text
Repository
    |
    v
Context Engine
    |
    +--> Relevant files
    +--> Relevant symbols
    +--> Imports
    +--> Recent changes
    +--> Developer prompt
    |
    v
Small relevant context
    |
    v
LLM
```

The Context Engine should identify only the context required for the task.

### Example

Developer asks:

> "Create an API for Mutual Fund holdings."

Potentially useful:

```text
HoldingController.java
HoldingService.java
HoldingRepository.java
Relevant interfaces
Relevant configuration
```

Unnecessary:

```text
PaymentSecrets.java
ProductionDeploymentConfig.java
InternalAdminService.java
Unrelated authentication code
```

### Key principle

> **Give the model the minimum information required to perform the task.**

This is both:

- a security control
- a performance optimization
- a token/cost optimization

---

# 10. Guardrail #8 — Repository and Context Isolation

Helium / Context Engine introduces an important question:

> **How much repository visibility should the developer and model receive?**

The safe conceptual flow is:

```text
User
  |
  v
Authorized Repositories
  |
  v
Authorized Branches
  |
  v
Relevant Files
  |
  v
Relevant Symbols
  |
  v
LLM
```

Do not simply:

```text
Index Everything
      |
      v
Give Everything to LLM
```

Repository visibility should follow access-control rules.

---

# 11. Guardrail #9 — Prevent Stale Context

AI context can become stale.

Example:

```text
Developer A
   |
changes UpiService.java
   |
commit
   |
merge
   |
Helium index still contains OLD code
   |
Developer B asks question
   |
LLM receives OLD context
   |
Wrong recommendation
```

A better flow is:

```text
Git Push
   |
PR Merge
   |
Deployment
   |
   v
Event Stream
   |
   v
Index Update Queue
   |
   v
Helium Refresh
```

### Why does this matter for safety?

Stale context can cause:

- obsolete authentication recommendations
- outdated authorization logic
- incorrect business rules
- data corruption
- production incidents
- security vulnerabilities

Therefore:

> **Context freshness is part of AI reliability and safety.**

---

# 12. Guardrail #10 — Rate Limiting

Without rate limiting:

```text
10,000 developers
       |
       v
1000 requests/sec
       |
       v
GPU Cluster
```

Possible consequences:

```text
GPU overload
Latency increase
Queue explosion
Cost increase
Service outage
```

Therefore:

```text
Developer
   |
   v
Rate Limiter
   |
   +---- within limit --> Continue
   |
   +---- exceeded ------> 429
```

Example:

```text
user:12345
50 requests / minute
```

Rate limiting protects:

- availability
- cost
- GPU resources
- fair usage

---

# 13. Guardrail #11 — Quotas

Rate limiting answers:

> **How fast can you call the system?**

Quota answers:

> **How much can you consume?**

Example:

```text
Developer
   |
   +--> 100 requests/day
   +--> 500K tokens/day
```

Team:

```text
Wealth Team
   |
   +--> 50M tokens/month
```

Organization:

```text
IDFC Coder
   |
   +--> Controlled monthly AI budget
```

Flow:

```text
Request
   |
   v
Quota Check
   |
   +---- exceeded --> Reject
   |
   +---- available --> Continue
```

---

# 14. Guardrail #12 — Token Control

Tokens are the unit of LLM consumption.

Example:

```text
Request A = 1K tokens
Request B = 10K tokens
Request C = 100K tokens
```

Treating all requests equally is inefficient and potentially dangerous.

Therefore:

```text
Request
   |
   v
Token Estimation
   |
   +--> Cost Estimate
   +--> Quota Consumption
   +--> Model Selection
   +--> Context Control
```

This prevents a single request from consuming disproportionate resources.

---

# 15. Guardrail #13 — Model Routing

Do not send every request to the biggest model.

Conceptually:

```text
                  REQUEST
                     |
                     v
                  ROUTER
                     |
          +----------+----------+
          |          |          |
          v          v          v
       SIMPLE      NORMAL     COMPLEX
          |          |          |
          v          v          v
        Small       Medium      Large
        Model       Model       Model
```

Benefits:

- Cost control
- Resource control
- Predictable capacity
- Model-specific policy
- Better utilization

This is not purely a security control, but it is an important governance control.

---

# 16. Guardrail #14 — Queue Before GPU

Do not expose GPUs directly to hundreds of concurrent users.

Instead:

```text
500 Requests
      |
      v
Request Queue
      |
      v
Inference Router
      |
      v
GPU Cluster
```

Think of the queue as:

> **A shock absorber for the inference layer.**

It protects the model-serving layer from sudden traffic spikes.

---

# 17. Guardrail #15 — Model Validation Before Production

A new model should not go directly into production.

Instead:

```text
New Model
    |
    v
Validation
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

Conceptually:

```text
New Model
   |
   v
Model Artifact
   |
   v
Validation
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

### Key principle

> **A model is a production artifact. Treat it with the same discipline as production software.**

---

# 18. Guardrail #16 — CI/CD Security Checks

Model and infrastructure deployment should go through controlled pipelines.

```text
Developer
    |
    v
Git
    |
    v
CI/CD
    |
    +--> Unit Tests
    +--> Security Scan
    +--> Container Scan
    +--> Model Validation
    +--> Performance Benchmark
    +--> Integration Tests
    |
    v
Container
    |
    v
Registry
```

This gives:

> **AI infrastructure should follow the same engineering discipline as production software.**

---

# 19. Guardrail #17 — Canary Deployment

Suppose:

```text
Model v1 --> Production
```

We create:

```text
Model v2
```

Do not immediately replace v1.

Instead:

```text
                 Traffic
                    |
              +-----+-----+
              |           |
              v           v
           Model v1     Model v2
            95%          5%
                         ^
                       Canary
```

Observe:

```text
Latency
Error Rate
Code Quality
Security Findings
Developer Feedback
Token Consumption
```

If healthy:

```text
5%
 |
 v
25%
 |
 v
50%
 |
 v
100%
```

If unhealthy:

```text
Model v2
   |
   v
Rollback
   |
   v
Model v1
```

---

# 20. Guardrail #18 — Post-Processing

Safety does not stop when the LLM finishes.

The lifecycle is:

```text
PRE-PROCESS
    |
    +--> Auth
    +--> RBAC
    +--> Rate Limit
    +--> Quota
    +--> Prompt Policy
    +--> Context Control
    |
    v
INFERENCE
    |
    +--> Queue
    +--> Routing
    +--> Model
    +--> GPU
    |
    v
POST-PROCESS
    |
    +--> Validation
    +--> Quality Check
    +--> Security Scan
    +--> Compliance
    |
    v
RESPONSE
```

This is one of the most important ideas to remember:

> **Safety exists before, during and after inference.**

---

# 21. Guardrail #19 — Generated Code Security

Example generated code:

```java
db.execute(
    "SELECT * FROM customers WHERE id = " + userInput
);
```

The code may compile.

The model may confidently return it.

But compilation does not mean security.

Therefore:

```text
LLM
 |
 v
Generated Code
 |
 v
Security Scanner
 |
 +---- safe ------> Response
 |
 +---- suspicious -> Block / Warn / Review
```

The AI-generated output should not automatically be treated as trusted code.

---

# 22. Guardrail #20 — Auditability

For a banking AI platform, we should be able to answer:

- Who asked?
- What repository?
- Which branch?
- Which model?
- When?
- How many tokens?
- Which policy was applied?
- What security checks happened?

Conceptually:

```text
Request
   |
   +--> User ID
   +--> Team
   +--> Repository
   +--> Branch
   +--> Model Version
   +--> Token Count
   +--> Policy Decision
   +--> Security Result
   +--> Timestamp
   |
   v
Audit Store
```

### Important

Auditability does **not** mean:

> Store every raw prompt and source-code fragment forever.

Audit data itself must be protected through:

- Encryption
- Access control
- Retention policies
- Data masking
- Appropriate deletion

---

# 23. Guardrail #21 — Model Version Control

If production changes from:

```text
Monday:
Model v1

Friday:
Model v2
```

and something goes wrong, we must know:

> **Which model generated this response?**

Therefore each request should be traceable to:

```text
Request
   |
   +--> Model Version
   +--> Prompt Policy Version
   +--> Context Index Version
   +--> Gateway Policy Version
```

This gives:

- Reproducibility
- Traceability
- Easier debugging
- Safer rollback

---

# 24. Guardrail #22 — Learn From Traditional ML/Fraud Systems

Traditional fraud systems use:

```text
Rules
  +
ML
```

rather than trusting ML alone.

Why?

Rules provide:

- Deterministic control
- Explainability
- Immediate policy changes
- Regulatory control
- Known-pattern detection

The same philosophy applies to AI coding systems:

```text
                 AI SAFETY

              +------------+
              |    Rules   |
              +------+-----+
                     |
              +------+------+
              |             |
              v             v
       Deterministic      Model
          Controls      Intelligence
```

### Key principle

> **Do not ask the LLM to enforce every security rule. Use deterministic platform controls wherever possible.**

---

# 25. Defense in Depth — Complete Safety Architecture

```text
                 IDFC CODER
                     |
                     v
              +-------------+
              |     WAF     |
              +------+------+ 
                     |
              +------v------+
              |    AUTH     |
              +------+------+ 
                     |
              +------v------+
              |    RBAC     |
              +------+------+ 
                     |
              +------v-----------+
              |  PROMPT GATEWAY |
              |                 |
              | Prompt Policy   |
              | Rate Limit      |
              | Quota           |
              | Token Control   |
              +------+----------+
                     |
              +------v------+
              |   CONTEXT   |
              |   CONTROL   |
              +------+------+ 
                     |
              +------v------+
              |    QUEUE    |
              +------+------+ 
                     |
              +------v------+
              |MODEL ROUTER |
              +------+------+ 
                     |
              +------v------+
              |     LLM     |
              +------+------+ 
                     |
              +------v-----------+
              | OUTPUT CONTROLS |
              |                 |
              | Validation      |
              | Security Scan   |
              | Compliance      |
              +------+----------+
                     |
              +------v------+
              |    AUDIT    |
              +-------------+
```

This is **defense in depth**.

If one layer fails, another layer still exists.

---

# 26. End-to-End Example

Developer asks:

> "Create an API to fetch mutual-fund holdings using Redis and MongoDB."

## Step 1 — Identity

SSO authenticates the developer.

```text
Developer
   |
   v
Authentication
```

---

## Step 2 — Authorization

Check:

```text
Can this developer access the Wealth repository?
```

If not:

```text
403
```

---

## Step 3 — WAF

Check whether the HTTP/API request is legitimate.

---

## Step 4 — Prompt Policy

Check whether the request is permitted.

---

## Step 5 — Context Selection

Context Engine finds:

```text
HoldingController
HoldingService
HoldingRepository
Relevant Interfaces
Relevant Configuration
```

Instead of the entire repository.

---

## Step 6 — Quota

Check:

```text
Does this developer/team have remaining AI quota?
```

If not:

```text
Reject
```

---

## Step 7 — Model Routing

Determine complexity.

```text
Medium complexity
      |
      v
Medium/Large coding model
```

---

## Step 8 — Queue

Request enters the inference queue.

```text
Request
   |
   v
Queue
```

---

## Step 9 — LLM

The model receives:

```text
Developer Request
        +
Relevant Context
```

and generates code.

---

## Step 10 — Output Validation

Generated code goes through:

```text
Syntax Validation
Quality Check
Security Scan
Compliance Check
```

---

## Step 11 — Audit

Record appropriate metadata:

```text
User
Repository
Model Version
Request ID
Token Usage
Policy Decision
Security Result
Timestamp
```

---

## Step 12 — Response

Only now:

```text
Developer
    ^
    |
Validated Response
```

---

# 27. What Happens When Something Goes Wrong?

### Unauthorized repository

```text
Developer
   |
   v
RBAC
   |
   X
  403
```

LLM is never called.

### Too many requests

```text
Developer
   |
   v
Rate Limit
   |
   X
  429
```

### Quota exhausted

```text
Developer
   |
   v
Quota
   |
   X
Quota Exceeded
```

### Sensitive context

```text
Context Engine
      |
      v
Sensitive File
      |
      X
Do Not Include
```

### Security issue in generated code

```text
LLM
 |
 v
Generated Code
 |
 v
Security Scan
 |
 X
Reject / Warn / Review
```

### New model behaves badly

```text
Model v2
   |
   v
Canary
   |
   v
Metrics Degrade
   |
   v
Rollback
   |
   v
Model v1
```

---

# 28. The Most Important Mental Model

Do not think:

```text
Safety = One AI Safety Filter
```

Think:

```text
             AI SAFETY
                 |
       +---------+---------+
       |         |         |
       v         v         v
    BEFORE    DURING     AFTER
      AI        AI         AI
       |         |         |
       v         v         v
   Identity   Model      Output
   Policy     Isolation  Validation
   Context    Resource   Security
   RBAC       Control    Compliance
   Quota      Queue      Quality
```

Or remember:

> **CONTROL WHAT ENTERS → CONTROL WHAT THE MODEL SEES → CONTROL WHAT IT CONSUMES → VALIDATE WHAT COMES OUT**

---

# 29. What Is Explicitly in the Notes vs. Recommended Extensions

## Explicitly present in the notes

| Guardrail | Status |
|---|---|
| WAF | Implemented/architected |
| Authentication | Implemented/architected |
| Authorization / RBAC | Implemented/architected |
| Prompt Gateway | Implemented/architected |
| Prompt Policy | Implemented/architected |
| Rate Limiting | Implemented/architected |
| Quota | Implemented/architected |
| Token Control | Implemented/architected |
| Context Minimization | Implemented/architected |
| Repository/Context Control | Implemented/architected |
| Request Queue | Implemented/architected |
| Model Routing | Implemented/architected |
| Model Validation | Implemented/architected |
| Security Scan | Implemented/architected |
| Container Scan | Implemented/architected |
| Performance Benchmark | Implemented/architected |
| Canary Deployment | Implemented/architected |
| Output Validation | Implemented/architected |
| Compliance Check | Implemented/architected |
| Auditability | Implemented/architected |
| Model Versioning | Implemented/architected |
| Self-hosting / VPC isolation | Implemented/architected |
| Helium Index Refresh | Implemented/architected |

## Recommended extensions — do not claim these as already implemented unless separately verified

```text
Prompt Injection Classifier
DLP Scanner
Secret Detection
PII Redaction
Code-Level SAST
Dependency Vulnerability Scanning
Human Approval for High-Risk Operations
Tool/MCP Permission Sandbox
Output Toxicity Classifier
Formal Policy Engine
Automated Security-Based Rollback
```

This distinction is important in a CTO/VP interview.

---

# 30. Strong CTO/VP Interview Answer

If asked:

> **"How did you introduce safety guardrails into IDFC Coder?"**

Use this:

> **"We didn't treat safety as a single filter around the LLM. We designed it as defense in depth. At the edge we had WAF and authentication. At the gateway we enforced authorization, RBAC, prompt policy, rate limits, quotas and token controls. We controlled the context going into the model through the context engine rather than sending the entire repository. Requests were queued and routed to appropriate models instead of exposing GPUs directly. Models went through validation, security scanning, benchmarking and canary deployment before production. After inference, generated output went through validation, security and compliance checks. Finally, we maintained auditability around the user, repository, model version, token usage and request lifecycle. The key principle was that the LLM remained a probabilistic component, while deterministic platform controls enforced the organization's security and governance policies."**

---

# 31. The One-Line Architect Summary

> **"We built a controlled execution environment around a probabilistic model."**

And the five-word memory hook:

> **IDENTITY → ACCESS → CONTEXT → MODEL → OUTPUT**

