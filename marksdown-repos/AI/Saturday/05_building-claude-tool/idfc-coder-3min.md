# IDFC Coder —

Your company wants to give thousands of developers an AI coding assistant.

The easy decision is:

> **“Let's buy an AI coding tool and give everyone access.”**

But as the Engineering Manager, you realize the developers may send **source code, internal APIs, architecture and business logic** to a third-party AI service. At the same time, usage can grow rapidly and become a major recurring cost. Your note frames the decision around **cost, control, security, auditability and developer productivity**. ([GitHub][1])

Now the question is no longer:

> “Which AI coding tool is better?”

It becomes:

> **“Should AI coding be a commodity tool we consume, or a capability we need to control?”**

That is the leadership decision behind IDFC Coder.

### Why I am reading this

**Because enterprise AI adoption is not just about choosing an AI tool—it is about deciding who controls the data, cost, security and developer experience.**

### Leadership question

> **“What should we own ourselves, and what should we safely consume from a vendor?”**

### One-line takeaway

> **AI adoption at enterprise scale is an architecture and business decision—not just a developer-tool decision.**


> **Central architectural idea:** The LLM is only one component. The platform around the LLM is what makes it production-grade.

---

## PART 1 — WHY SELF-HOST?

### Slide 1 — Build or Buy?

**Opening question:** *"If I have 10,000 developers in a regulated fintech, why wouldn't I simply buy GitHub Copilot / Claude / another commercial AI coding product?"*

Don't accept "because it's expensive." Push harder. Ask: **What exactly are we optimizing?**

```
        COST
         │
  ┌──────┼──────┐
  ↓      ↓      ↓
Security Control Productivity
  │      │      │
  ↓      ↓      ↓
Sovereignty Audit  Developer
                   experience
```

**BUY** → Fast, low ops, vendor dependency
**BUILD** → Control, sovereignty, cost leverage

**The real question:** *"What does the organization gain by owning the intelligence layer?"*

```
SELF-HOSTED AI
      │
      ├── Data sovereignty
      ├── Auditability
      ├── Model control
      ├── Customization
      ├── Predictable economics
      └── Infrastructure ownership
```

#### Strategic vs Tactical Decision

| STRATEGIC CAPABILITY | TACTICAL TOOL |
|---|---|
| Build | Buy |
| Long-term investment | Short-term solution |
| Core to business | Nice to have |
| Differentiates | Commoditizes |
| Control over roadmap | Vendor roadmap |
| Data as strategic asset | Data as cost |

**Bank's answer:** Banking → Technology Enabled → AI-Native Banking → Differentiation

> *"If AI becomes core to how banking works, can we afford to outsource the core?"*

#### The Vendor Lock-In Spiral

```
VENDOR LOCK-IN
      │
  ┌───┼───┐
  ↓   ↓   ↓
DATA  MODEL  API
LOCK  LOCK   LOCK
  │     │      │
  ↓     ↓      ↓
"All our   "We fine-tuned  "We built on
prompts    their model     their API
are in     on our data"    patterns"
their logs"
  │     │      │
  ↓     ↓      ↓
Can't leave without losing history / retraining / rewriting
```

**Escape cost:** Data migration 6–12 mo + Model retraining 3–6 mo + App rewrite 6–12 mo + Dev retraining 3–6 mo = **2–3 years**

> *"The cheapest vendor today might be the most expensive vendor to leave tomorrow."*

---

### Slide 2 — Executive Summary

```
10,000 developers
       │
       ↓
Self-hosted LLM
       │
       ├── 54–72% potential savings
       ├── AWS
       ├── DeepSeek Coder 33B
       └── 18-month evolution
```

**Ask:** *"If I save 70% but expose source code to a third party, have I really optimized the system?"*

```
        ARCHITECTURE VALUE
              │
     ┌────────┼────────┐
     ↓        ↓        ↓
   COST    CONTROL  PRODUCTIVITY
     │        │        │
     └────────┼────────┘
              ↓
         BUSINESS VALUE
```

#### Executive Presentation Pyramid

```
   TOP LEVEL (30 sec)
   "We can save $4.6–8.6M annually
    while keeping code secure"
              │
   MID LEVEL (5 min)
   "Here's the architecture and plan"
              │
   DETAIL LEVEL (Deep dive)
```

**The 30-second pitch:** *"We can cut AI code generation costs by 54–72%, keep all source code inside our VPC, maintain full auditability, and build a platform that scales to 10,000 developers—all while avoiding vendor lock-in."*

> *"The executive doesn't need the architecture. They need the outcome."*

**Key takeaway:** Don't pitch "a cheaper Copilot." Pitch **"a controlled enterprise AI platform where economics, security, governance and developer productivity are under our control."**

---

## PART 2 — BUSINESS CASE

### Slide 3 — 10,000 Developers × 50 Calls

**Ask:** *"10,000 developers × 50 AI calls/day. How expensive could that become?"*

First identify variables:

```
TOTAL COST
   ├── Developers
   ├── Requests / developer
   ├── Tokens / request
   ├── Model price
   ├── Context size
   └── Premium model usage
```

```
10,000 × 50 calls/day = 500,000 calls/day
500,000 × 30 ≈ 15 million calls/month
```

**Ask:** *"What happens if our average request assumption is wrong by 4×?"* → 200 calls/day → 4× traffic → 4× API spend.

#### Sensitivity Analysis

| Assumption | Impact on Cost |
|---|---|
| 50 → 200 calls/day | 4× increase |
| 2K → 8K tokens/request | 4× increase |
| $0.03 → $0.06/token | 2× increase |
| **All three combined** | **32× increase** |

> *"Cost is not a fixed number. It's a range with enormous uncertainty. We need to build flexibility into the architecture."*

**Architect lesson:** The most dangerous assumption in SaaS economics is usually **usage**, not price.

#### Usage Growth Model

```
LINEAR: grows proportionally to user base
EXPONENTIAL: adoption → word-of-mouth → more adoption

ADOPTION S-CURVE
  ↑
  │               ████████████
  │          █████
  │     █████
  │ █████
  └────────────────────────────→ Time
     Q1  Q2  Q3  Q4  Q5  Q6
```

**Lesson:** Early months low usage (easy to support) → Months 3–6 accelerate (watch capacity) → Months 6–12 stabilize (plan steady state).

> *"Architect for the S-curve, not just the starting point or the destination."*

---

### Slide 4 — What Must Self-Hosting Cost?

**Ask:** *"If SaaS costs millions per year, what exactly are we comparing against?"*

```
SAAS                    SELF-HOST
────                    ─────────
API calls               GPU + Storage + Network
  × price/call          + Management + Engineering
  × usage               + Operations + Monitoring
                        + Capacity planning
```

```
        TCO
     ┌───┴───┐
     ↓       ↓
   SaaS   Self-host
     │       │
  variable  fixed +
   cost     step cost
```

> **Never compare API price against GPU price. Compare API TCO against platform TCO.**

#### TCO Breakdown

```
CAPEX: GPU, Storage, Network
OPEX: Personnel, Power, Cooling, Monitoring, Support, Maintenance, Depreciation
OPPORTUNITY: Lost features, Delay to market, Engineering time multiplied

TCO DISTRIBUTION
████████████████ 40%  Personnel
████████████ 30%       GPU/Infrastructure
████████ 20%           Operations
████ 10%               Opportunity Cost
```

> *"The GPU is often the smallest part of the TCO at small scale."*

---

### Slide 5 — Cost Reality

**Conservative external model:**
```
10,000 dev × 50 calls/day × $0.03
= $15,000/day = $450K/month = $5.4M/year
```

**Realistic heavy usage:** longer context + premium models → **$8–12M/year**

**Self-host:**
```
GPU + Infrastructure + 3 FTE
= ~$286K/month = ~$3.4M/year
```

**Savings:** $8–12M − $3.4M = **$4.6–8.6M**

#### Realistic Worst Case

```
10,000 dev × 200 calls/day × 8,000 tokens × $0.06/token
= $9.6M/month = $115.2M/year
```

**Base case $5.4M vs Worst case $115M = 21× difference**

> *"The cost can vary by 21× based on usage assumptions. Build architecture that handles both."*

**Architectural economic difference:**

```
SAAS:        Developers ↑ → API calls ↑ → Cost ↑
SELF-HOST:   Developers ↑ → Workload ↑ → GPU utilization ↑
             → Eventually add GPU node → STEP
```

---

### Slide 6 — Provider Gets Acquired by Competitor

**Ask:** *"Tomorrow our AI provider is acquired by a competitor. What has already left our VPC?"*

```
Developer → Confidential source code → Third-party API → ???????
```

**Potential data exposed:**
```
┌───────────────────────────┐
│ Source code               │
│ Architecture              │
│ Internal APIs             │
│ Business logic            │
│ Jira context              │
│ Developer prompts         │
│ Repository structure      │
│ Proprietary terminology   │
└───────────────────────────┘
```

**Ask:** *"Which of these can you retrieve after sending them?"* → **None. You cannot "un-send" it.**

#### Data Exposure Timeline

```
DAY 1:   Prompt patterns, API usage, developer queries
DAY 30:  Code patterns, internal APIs, architecture
DAY 90:  Business logic, security patterns, competitive advantage eroded
DAY 365: Complete codebase pattern, dev methodology, proprietary processes
```

**Key principle:** Security is not only about encryption. It is also about **where the data is allowed to exist**.

#### Third-Party Risk Continuum

| Risk Type | Severity | Mitigation |
|---|---|---|
| Prompt exposure | Moderate | Anonymize |
| Code exposure | High | Self-host |
| Architecture exposure | High | Self-host |
| Business logic | Critical | Self-host |
| Strategy exposure | Critical | Self-host |

> *"Third-party AI is a risk continuum, not a binary. The most critical data should never leave."*

---

### Slide 7 — Why Would a Bank Prefer Self-Hosting?

**Ask:** *"Suppose both solutions cost the same and developers are equally productive. Which one would a regulated bank prefer?"*

→ **Data control, Auditability, Governance**

**Ask:** *"Can you prove those properties technically?"* Not "our vendor is SOC2 compliant" — instead:

```
Request → WAF → Private VPC → Wrapper → GPU
```
Every step can be logged: WHO? WHAT? WHEN? WHICH MODEL? WHICH REPOSITORY? HOW MANY TOKENS? WHAT RESPONSE?

#### Regulatory Matrix

```
GDPR: Data privacy, right to be forgotten
Basel III: Risk management, audit trails
RBI/SARB: Local laws, data residency, sovereignty
```

**Auditable AI:** Every request logged, every response logged, every decision traceable, every model version known, every cost attributable.

> *"In banking, 'trust me' is not a compliance strategy."*

#### Auditability Comparison

```
SAAS AUDIT: "I can see who called the API, but not what the model used.
             Vendor provides logs — vendor's logs are not our logs."

SELF-HOSTED AUDIT: "I control the entire pipeline.
                    Every prompt, context, response logged in our systems.
                    Every model version versioned. Every decision auditable."
```

---

### Slide 8 — Data Sovereignty Matrix

| | THIRD PARTY | SELF-HOST |
|---|---|---|
| Code leaves VPC | YES | NO |
| Provider sees code | YES | NO |
| Audit trail | Limited | Complete |
| Model customization | Limited | Full |
| Latency SLA | External | Internal |
| Regulatory control | Complex | Direct |

**Ask:** *"Which row is impossible to fully fix after choosing a third-party API?"* → **Data sovereignty**

#### Data Sovereignty Layers

```
PHYSICAL: where data physically resides
LOGICAL:  who can access data and how it's protected
BUSINESS: who owns the insights from the data
```

| Sovereignty Layer | Third Party | Self-Host |
|---|---|---|
| Physical location | Vendor DC | Our DC/Cloud |
| Data access | Vendor staff | Our staff |
| Data encryption | Vendor key | Our key |
| Data retention | Vendor policy | Our policy |
| Data deletion | Vendor process | Our process |
| Data usage | Vendor can use for training? | We control |

> *"Sovereignty isn't just about where data sits. It's about who controls it."*

**Lesson:** Self-hosting isn't merely a compute decision. It's a **trust-boundary decision**.

---

### Slide 9 — CTO Elevator Pitch

**Ask:** *"You have 30 seconds with the CTO. No spreadsheet. Convince them."*

```
        SELF-HOSTING CASE
     ┌────────┼────────┐
     ↓        ↓        ↓
 ECONOMICS SOVEREIGNTY CONTROL
     │        │        │
 $4.6–8.6M  Code stays  Audit /
  savings    internal   customize
```

**Strongest executive story:**
```
10,000 developers
       ↓
$8–12M external spend
       ↓
~$3.4M self-hosted
       ↓
54–72% reduction + code stays inside VPC + full governance
```

#### CTO Decision Framework

```
RISK: "What can go wrong?"          RETURN: "What's the potential upside?"
  ├── Price increase 20–50%           ├── Cost savings $4.6–8.6M/yr
  ├── Vendor lock-in: High            ├── Control: Complete
  ├── Data exposure: Moderate         ├── Differentiation: High
  ├── Acquisition risk: Real          ├── Talent attraction: Yes
  └── Roadmap: Not ours               └── Strategic alignment: Core
```

---

## PART 3 — LLM SELECTION

### Slide 11 — Highest Quality Model?

**Ask:** *"Eight models. One has the highest code-generation benchmark score. Do we automatically choose it?"* → **No.**

```
        MODEL SELECTION
     ┌────────┼────────┐
     ↓        ↓        ↓
  Quality   Cost   Operations
     │        │        │
  CodeGen  GPU cost  Latency
  accuracy Tokens    Memory
                    Scaling
```

A model can win CodeGen=9.5 and still lose because: VRAM enormous, cost enormous, latency poor, license problematic, fine-tuning difficult.

#### Benchmark Validity Problem

```
PUBLIC benchmark: Known problems, clean synthetic data
OUR CODEBASE: Internal APIs, legacy code, business logic, real-world mess
```

> *"Benchmarks are a filter, not a decision."*

**The test:** Benchmark scores → promising candidates → internal evaluation (internal API tests + real codebase tests) → final decision.

---

### Slide 12 — Build the Model-Selection Framework First

**Ask:** *"Before seeing any model scores, what dimensions would you evaluate?"*

```
        MODEL
     ┌────┼────┐
     ↓    ↓    ↓
  QUALITY SYSTEM BUSINESS
     │    │      │
  CodeGen Latency License
  Accuracy Memory  Cost
          Throughput Fine-tuning
```

**Weighted score example:**
```
MODEL SCORE = 40% Quality + 20% Latency + 15% Memory
            + 10% Fine-tuning + 10% License + 5% Cost
```

> **Define the decision function before looking at the candidates.**

Otherwise: See shiny model → Invent criteria → Justify model. Instead: Define criteria → Evaluate models → Select model.

#### Weighted Decision Matrix

| Criterion | Weight | DeepSeek | Mistral | Other |
|---|---|---|---|---|
| CodeGen Quality | 40% | 9 | 8 | 7 |
| Latency | 20% | 7 | 9 | 8 |
| Memory | 15% | 8 | 9 | 7 |
| Fine-tuning | 10% | 7 | 8 | 6 |
| License | 10% | 9 | 8 | 5 |
| Cost | 5% | 8 | 9 | 7 |
| **Weighted Score** | 100% | **8.2** | **8.3** | **6.9** |

> *"Model selection is a trade-off optimization, not a search for 'best'."*

---

### Slide 13 — Eight-Model Matrix

**Ask:** *"Why is model selection actually an infrastructure decision?"*

```
Model → Memory requirement → GPU type → GPU count → Latency → Cost
```

> **Choosing an LLM indirectly chooses part of your infrastructure architecture.**

#### Infrastructure Cascade

```
MODEL CHOICE
     │
  ┌──┴──┐
  ↓     ↓
QUALITY PERFORMANCE
  │     │
  └──┬──┘
     ↓
INFRASTRUCTURE
  ┌──┴──┐
  ↓     ↓
GPU TYPE  GPU COUNT
  │     │
  └──┬──┘
     ↓
   COST
```

> *"Every model choice is an infrastructure choice waiting to be discovered."*

---

## PART 4 — TARGET ARCHITECTURE

### Slide 14 — System Overview

**Ask:** *"If 10,000 developers hit one LLM endpoint directly, what goes wrong?"*

**Naive architecture:**
```
10,000 developers → LLM API → GPU
```

**Ask:** *"Where do authentication, quota, caching, audit and throttling happen?"* → They don't.

**Real architecture:**
```
Developers → WAF → ALB → Wrapper → Queue → GPU
                          │
                          ├── Auth
                          ├── RBAC
                          ├── Rate limit
                          ├── Quota
                          ├── Prompt
                          ├── Cache
                          └── Token control
```

#### Missing Layers

| Without Layers | With Layers |
|---|---|
| No auth → Anyone can call | Auth → Only authorized |
| No rate limit → Unbounded cost | Rate limit → Predictable cost |
| No cache → Duplicate work | Cache → Lower cost |
| No audit → No accountability | Audit → Full traceability |
| No routing → One model fits all | Routing → Optimized cost/quality |

> *"A model without a platform is just a toy."*

**Key lesson:** Never expose the model directly to thousands of users.

---

### Slide 15 — Why API Gateway / Wrapper?

**Ask:** *"What should be the single control point between developers and the model?"* → **Wrapper** (policy enforcement point)

Without it: Developer A → Model, Developer B → Model, Developer C → Model... You lose centralized: Authentication, Authorization, Quota, Rate limiting, Cost tracking, Prompt policy, Caching, Audit.

#### Gateway Pattern

```
           AI GATEWAY
     ┌─────────┼─────────┐
     ↓         ↓         ↓
 SECURITY  GOVERNANCE  ECONOMICS
     │         │         │
   Auth      Quota     Cost tracking
   RBAC      Audit     Budget limits
   Rate limit Policy   Token counting
   WAF       Compliance Usage reports
```

**Gateway as filter:**
```
REQUEST → AUTH CHECK ──❌──→ 401 Unauthorized
       → RBAC CHECK ──❌──→ 403 Forbidden
       → RATE LIMIT ──❌──→ 429 Too Many
       → QUOTA CHECK ─❌──→ Quota Exceeded
       → CACHE CHECK ─✓──→ Cached Response
       → TOKEN ESTIMATE → Cost projection
       → REQUEST PASSES
```

> *"The gateway is not a proxy. It's a policy enforcement layer."*

---

### Slide 16 — Request Flow

```
Developer → Generate Code → WAF → ALB → Wrapper
                                        ├── Who are you?
                                        ├── Are you allowed?
                                        ├── Is your team within quota?
                                        ├── Can we serve from cache?
                                        ├── How many tokens?
                                        └── Which model?
                                          ↓
                                        Queue → Batching → GPU
                                          ↓
                                        Validation → Response
```

#### Request Lifecycle

```
PRE-PROCESS: Auth, RBAC, Rate limit, Quota, Cache, Prompt
INFERENCE:   Queue, Batching, Model, GPU
POST-PROCESS: Validation, Quality check, Security scan, Compliance, Formatting, Response
```

**Timing:** ~50ms pre-process → ~2.5s inference → ~50ms post-process

> *"The request lifecycle is a chain. Optimize the right link."*

---

## PART 5 — LLM SELECTION: KILL THE "BIGGEST MODEL = BEST MODEL" ASSUMPTION

**Opening question:** *"You have eight models. One has the highest code-generation score. Should you automatically choose it?"*

```
        MODEL SELECTION
     ┌────────┼────────┐
     ↓        ↓        ↓
  QUALITY  LATENCY   COST
     │        │        │
  Accuracy  Response  GPU/hour
             time
```

> **"BEST MODEL" ≠ "BEST SYSTEM"**

**Ask:** *"What happens if your best model is 2× slower?"*

```
Model A: Quality 9, Latency 2s → Developer frustrated
Model B: Quality 8, Latency 300ms → Developer happy
```

#### Productivity Equation

```
DEVELOPER PRODUCTIVITY = Time Saved = (Model Quality × Response Speed)

Model A: Quality 9/10, Latency 2s   → Productivity 1.8
Model B: Quality 8/10, Latency 0.3s → Productivity 6.4
Model C: Quality 6/10, Latency 0.1s → Productivity 3.6
Winner: Model B (faster adoption beats perfect quality)
```

**Hidden dimension:**
```
MODEL SELECTION
     ┌────────┼────────┐
     ↓        ↓        ↓
  QUALITY  LATENCY  ADOPTION
     │        │        │
  "Correct" "Fast"  "Used"
```

> *"A perfect model that nobody uses is worth less than an imperfect model everyone uses."*

**Architect principle:** Optimize BUSINESS VALUE = Quality + Latency + Cost — not benchmark score alone.

#### Benchmark Fallacy

```
BENCHMARK: Known problems, clean code, synthetic, perfect docs
REAL CODE: Internal APIs, legacy code, business logic, edge cases, ugly real code
```

> *"Benchmarks measure potential. Production measures reality."*

**CTO's Rule:** *"Optimize for adoption, not benchmarks. An unused model is a waste of money."*

#### Genuine Advice

| Role | Advice |
|---|---|
| **CTO** | "Your primary KPI is *adoption*, not *accuracy*. Measure how many developers use the tool." |
| **Architect** | "Run your actual codebase through the model before trusting the benchmark." |
| **ML Engineer** | "Test for the 95th percentile, not the 50th. The slowest 5% create the most frustration." |

---

## PART 6 — MULTI-MODEL STRATEGY

**Opening question:** *"Would you send every request from 10,000 developers to your most powerful model?"*

```
        REQUEST
           │
      ┌────┴────┐
      │ ROUTER  │
      └────┬────┘
    ┌──────┼──────┐
    ↓      ↓      ↓
  SIMPLE NORMAL COMPLEX
    │      │      │
  7B model 33B   34B
```

**Ask:** *"Why waste a 33B model answering something a 7B model can solve?"*

**Deck's answer:**
- 95% simple requests → Mistral 7B
- Complex generation → DeepSeek 33B
- Specialized work → WizardCoder 34B

#### Classification Problem

```
REQUEST → CLASSIFIER (Complexity? Domain? Urgency? User?) → ROUTING

Classifier inputs: Prompt length, Token count, User role,
                   Team history, Query type, Time of day

Routing outputs: Simple → Mistral 7B
                 Normal → DeepSeek 33B
                 Complex → WizardCoder 34B
                 Unknown → DeepSeek 33B (default)

Feedback loop: REQUEST → CLASSIFY → ROUTE → MODEL → RESPONSE
               → EVALUATE ("Was routing correct?") → UPDATE ROUTER
```

> *"A routing system is a learning system. Start simple, then improve."*

**Deep architectural lesson:** Model routing is equivalent to **compute scheduling**.

```
        AI COMPUTE POOL
              │
     intelligent router
              │
    ┌─────────┼─────────┐
    ↓         ↓         ↓
  cheap    normal   expensive
```

#### Economic Optimization

```
REQUEST DISTRIBUTION
95% simple  → 7B model  ($0.0001)
 4% normal  → 33B model ($0.001)
 1% complex → 34B model ($0.01)

100,000 requests/day:
Simple:  95,000 × $0.0001 = $9.50
Normal:   4,000 × $0.001  = $4.00
Complex:  1,000 × $0.01   = $10.00
Total:                      $23.50/day

If we used 34B for everything: 100,000 × $0.01 = $1,000/day
Savings: $976.50/day = ~$356,000/year
```

> *"Model routing isn't just clever—it's economically essential."*

**The 80/20 Rule in AI:**

> *"80% of requests can be handled by 20% of the compute."*

```
80% Simple (autocomplete, formatting) → Cheap model (7B)
15% Normal (function generation)      → Medium model (33B)
 5% Complex (architectural changes)   → Expensive model (70B+)
```

**CTO's Question:** *"What's the cost of using the wrong model 100% of the time?"*

**Design Principle:**

> *"Use the cheapest adequate model. Not the cheapest model. Not the best model. The cheapest adequate model."*

#### Genuine Advice

| Role | Advice |
|---|---|
| **CTO** | "The routing system is where you'll get the biggest ROI. Invest heavily in getting this right." |
| **Architect** | "Build the routing system as a learning system. Start with simple rules, then evolve based on feedback." |
| **Product** | "Different users have different needs. A junior dev's 'complex' is a senior's 'simple.'" |

---

## KEY TAKEAWAYS SUMMARY

1. **The LLM is one component.** The platform around it makes it production-grade.
2. **Strategic vs tactical:** If AI is core to banking, you can't outsource the core.
3. **Cost varies 21×** based on usage assumptions. Architect for the S-curve.
4. **Never compare API price to GPU price.** Compare API TCO to platform TCO.
5. **Security = where data is allowed to exist.** You can't "un-send" data.
6. **Self-hosting is a trust-boundary decision,** not just a compute decision.
7. **Benchmarks are a filter, not a decision.** Test on your real codebase.
8. **Adoption > Quality.** A perfect model nobody uses is worthless.
9. **Model selection = infrastructure selection.** Every choice cascades.
10. **Never expose the model directly.** The wrapper is the policy enforcement point.
11. **Model routing is compute scheduling.** Use the cheapest adequate model.
12. **Optimize for business value:** Quality + Latency + Cost — not benchmark score.
