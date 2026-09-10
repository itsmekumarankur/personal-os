# IDFC Coder GPU Decision — Architect & CTO Questioning Muscle

## Purpose

The goal is to build the **questioning muscle itself**.

Act as an architect and CTO interviewer. Do not merely explain the topic. Use questions that force critical thinking across:

- Failure
- Trade-offs
- Scale
- Cost
- Security
- Customer
- Product
- Operations
- Business value
- Strategic risk

The questioning should be **linked**: each answer should naturally lead to a deeper follow-up question.

The progression is:

```text
Architect
   ↓
Senior Architect
   ↓
CTO
   ↓
Board / Strategic Decision
```

The purpose is revision, but more importantly, to train the instinct:

> **"What is the right question I should ask before making this decision?"**

---

# SET 1 OF 5 — Business → Workload → GPU

## Question 1 — Architect Level

Your CTO tells you:

> "We have 50 developers using IDFC Coder. SaaS costs us roughly ₹57L/year, while an initial self-hosting estimate is ₹23.8L/year. That's almost 58% savings. Let's buy GPUs and self-host."

You are the architect responsible for this decision.

### Challenge

Do you approve the decision?

Don't immediately calculate the savings.

Instead, tell me:

**What are the first 5–7 questions you would ask the CTO/business/product/engineering teams before you even start selecting a GPU?**

Think across:

- Workload
- Users
- Usage pattern
- Model
- Quality
- Latency
- Concurrency
- Infrastructure
- Engineering effort
- Security/compliance
- Operational risk
- Future growth

And importantly:

> **Which question would you ask FIRST, and why?**

Your answer should demonstrate how you would **decompose the problem**, not just list technical questions.

---

# SET 2 OF 5 — Workload → Capacity → GPU Architecture

Now raise the bar.

This set focuses on whether you can move from:

> "We need a GPU"

to:

> "What capacity do we actually need?"

Your questioning chain should start looking like:

```text
33B parameters
      ↓
Model memory?
      ↓
What else consumes VRAM?
      ↓
Concurrent requests?
      ↓
KV cache?
      ↓
Context length?
      ↓
Batching?
      ↓
Latency?
      ↓
Throughput?
      ↓
GPU utilization?
      ↓
How many GPUs?
```

## Question 1 — Senior Architect / CTO

You discover:

- 50 developers
- 50% use the coding assistant daily
- Average active users during peak = 15
- Each active developer can generate multiple requests
- Some requests are small code completions
- Some are large-context codebase questions
- The model being considered is a **33B parameter model**
- The model can be quantized
- The business wants **low latency**
- The CTO wants enough capacity for future growth

The infrastructure team says:

> "A 33B model needs around 66 GB in FP16, so let's buy an 80 GB GPU. That should be enough."

### Challenge

Would you accept this reasoning?

Don't answer simply yes/no.

### 1. Model Memory

Is parameter count × bytes/parameter sufficient to determine GPU memory requirements?

Why or why not?

### 2. VRAM Budget

What other components would you include in the **VRAM budget**?

### 3. Context Length

How would **context length** change your calculation?

### 4. KV Cache

Why does **KV cache** become important when concurrency increases?

### 5. Latency Problem

Suppose one GPU can technically load the model but gives poor latency when 10 developers generate requests simultaneously.

**What question would you ask next?**

### 6. Capacity Metric

Would you optimize for:

- Maximum concurrent users
- Requests/sec
- Tokens/sec
- p95 latency

What would determine your choice?

### 7. CTO Trade-off

As CTO, what would worry you more:

> A GPU that is too small and cannot handle peak load

or

> A GPU that is oversized and sits at 20% utilization most of the time?

Defend the **decision framework**, not just the answer.

---

# SET 3 OF 5 — Performance → Capacity → Cost → Trade-offs

Now move from:

> "Can we run the model?"

to:

> **"Can we run it economically and provide a good developer experience?"**

Questioning chain:

```text
User demand
    ↓
Concurrency
    ↓
Tokens / request
    ↓
Throughput
    ↓
Latency
    ↓
GPU utilization
    ↓
Number of GPUs
    ↓
Cost
    ↓
Business ROI
```

## Question 1 — Architect → CTO

You run a benchmark for the proposed self-hosted IDFC Coder platform.

| Metric | Result |
|---|---:|
| Developers | 50 |
| Peak concurrent users | 15 |
| Average request | 1,500 tokens |
| Peak request rate | 10 requests/sec |
| GPU | 80 GB |
| Average GPU utilization | 45% |
| p50 latency | 1.2 sec |
| p95 latency | 7.5 sec |
| Monthly GPU + infra cost | ₹1.8L |
| SaaS equivalent monthly cost | ₹4.75L |

The CFO says:

> "Excellent. We're saving almost ₹3L every month. Let's move to production."

You are the CTO.

### Build your questioning chain

Don't give a random list.

Link the questions:

```text
p95 = 7.5 sec
      ↓
Why is p95 high?
      ↓
Queueing or inference?
      ↓
Why is GPU utilization only 45%?
      ↓
Are we under-utilizing GPU?
      ↓
Can batching improve throughput?
      ↓
Does batching hurt latency?
      ↓
What happens at 2× traffic?
      ↓
What happens when context length increases?
      ↓
How does this change GPU count?
      ↓
Does the ₹1.8L/month assumption still hold?
```

### A. Performance

p50 is 1.2 sec but p95 is 7.5 sec.

What are the **first 3 hypotheses** you would investigate?

### B. Concurrency

You have 15 concurrent users but 10 requests/sec.

What additional information do you need before deciding whether this GPU has sufficient capacity?

### C. Batching

The inference team proposes:

> "Increase batching to improve GPU utilization."

What questions would you ask before accepting this?

Think about:

**throughput ↔ latency ↔ user experience**

### D. Cost

The CFO calculates:

```text
SaaS      = ₹4.75L/month
Self-host = ₹1.8L/month

Savings = ₹2.95L/month
```

What costs might be missing from the self-hosted number?

Think beyond simply **GPU purchase/rental cost**.

### E. Failure

Now assume traffic unexpectedly becomes **3× higher**.

Your GPU becomes saturated.

Requests start queueing and developers experience 20–30 second latency.

As architect, what would you ask **before simply adding another GPU?**

### F. CTO Question

Imagine you discover:

```text
Self-hosting:
₹35L/year total cost
+
2 engineers permanently operating the platform

SaaS:
₹57L/year
+
almost zero infrastructure operations
```

The CFO says:

> "Self-hosting still saves ₹22L. Do it."

As CTO:

**What is the single most important question you would ask before making the final decision?**

Don't answer with:

> "What is the ROI?"

I want the **question behind the ROI question**.

---

# SET 4 OF 5 — Architecture → Reliability → Security → Strategic Trade-offs

Now move closer to **CTO-level questioning**.

The focus is no longer just:

> "Can we run the model?"

It becomes:

> **"Should we own this capability, and what happens when reality is different from our benchmark?"**

Questioning chain:

```text
                    ┌── Performance
                    ├── Reliability
                    ├── Security
Request → Inference ├── Cost
                    ├── Operations
                    └── Business Risk
                           ↓
                    CTO Decision
```

## Question 1 — CTO Level

You decide to self-host the coding model.

The architecture team proposes:

```text
Developer IDE
     |
     v
API Gateway
     |
     v
Inference Service
     |
     v
GPU Server
     |
     v
33B Quantized Model
```

The team tells you:

> "The model fits comfortably in GPU memory. Benchmark latency is acceptable. Infrastructure cost is 40% lower than SaaS. We can go live."

You are **not convinced**.

### Challenge

Start questioning the architecture.

Build a **question chain**, where every question naturally leads to the next:

```text
Architecture
   ↓
What can fail?
   ↓
What happens when it fails?
   ↓
How do we detect it?
   ↓
How do we recover?
   ↓
What happens during GPU overload?
   ↓
What happens during model failure?
   ↓
What happens during deployment?
   ↓
What happens to developer productivity?
   ↓
What is the business impact?
```

### 1. Failure

What are the major failure domains in this architecture?

Don't just say:

> "GPU can fail."

Break the system into **failure boundaries** and ask what happens when each boundary fails.

### 2. Capacity Failure

Suppose:

```text
Normal:
10 concurrent users
p95 = 4 sec

Peak:
30 concurrent users
p95 = 25 sec
```

What questions would you ask to determine whether the problem is:

- GPU compute
- VRAM
- KV cache
- Batching
- Queueing
- Network
- Inference engine
- Model/context size

### 3. Reliability

Your CTO asks:

> "What is our SLA for IDFC Coder?"

What questions must you ask **before agreeing to an SLA**?

Think about:

```text
Availability
Latency
Throughput
Capacity
Failure recovery
Maintenance
Degradation
```

### 4. Security

The model processes:

- Proprietary source code
- Architecture documents
- Internal APIs
- Potentially sensitive financial-domain code

The security team says:

> "Self-hosting is automatically more secure because the data doesn't leave our infrastructure."

Would you accept that statement?

What **questions** would you ask to validate it?

Think across:

```text
Data
   ↓
IDE
   ↓
Network
   ↓
Gateway
   ↓
Inference service
   ↓
GPU memory
   ↓
Logs
   ↓
Telemetry
   ↓
Model / third-party dependencies
```

### 5. Disaster Recovery

Imagine your only GPU server dies during a critical production period.

You have:

```text
No second GPU
No warm standby
Model image backed up
Model weights available
SaaS alternative available
```

As CTO, what questions would you ask before deciding whether a **second GPU** is worth the additional cost?

### 6. Strategic Question

Now SaaS announces:

> "Our coding model has improved significantly. The new model is 2× better at code generation, but SaaS pricing increases by 30%."

Your self-hosted model is cheaper but requires engineering ownership.

What questions would you ask to determine whether you should:

**A. Continue self-hosting**

**B. Move back to SaaS**

**C. Run a hybrid model**

Don't choose A/B/C immediately.

Instead, construct the **decision questions** that would allow you to make that decision.

### Final CTO Challenge

Imagine you're presenting to the board.

You have only **60 seconds**.

The board asks:

> "Why should IDFC own GPU infrastructure for an AI coding platform instead of simply buying the capability from a SaaS provider?"

What **5 questions** would you want your architecture team to have answered before you make that recommendation?

The key exercise:

> **Don't defend self-hosting. Don't defend SaaS. Build the questions that allow you to make the decision objectively.**

---

# SET 5 OF 5 — Final CTO Challenge: Make the Investment Decision

This is the final set.

Now combine everything:

```text
Business
   ↓
Workload
   ↓
Model
   ↓
VRAM / Quantization
   ↓
KV Cache
   ↓
Concurrency
   ↓
Latency / Throughput
   ↓
GPU Capacity
   ↓
Reliability
   ↓
Security
   ↓
TCO
   ↓
ROI
   ↓
Strategic Decision
```

The objective is to train yourself to think:

> **"What question am I missing?"**

rather than simply finding the answer.

---

## Question 1 — Board / CTO Simulation

You are the CTO of the bank.

Your team presents this final proposal.

### Current situation

```text
Developers                  50
Peak concurrent users       20
Annual SaaS cost            ₹57L
```

### Proposed self-hosted platform

```text
33B coding model
Quantized model
80 GB GPU
Self-hosted inference
Annual infrastructure     ₹24L
Engineering/operations    ₹12L
Total annual TCO          ₹36L
```

Expected saving:

```text
₹57L - ₹36L = ₹21L/year
```

The architecture team says:

> "Self-hosting saves ₹21L annually, keeps source code inside the bank, and gives us control over the model and infrastructure. We recommend proceeding."

You have **one concern**:

### The model landscape is changing extremely quickly.

A significantly better coding model may become available within 6–12 months.

---

## Your Task

Don't tell me whether you approve the proposal.

Instead, **interrogate the proposal.**

Construct a chain of questions.

Start here:

> **"What assumptions must be true for this ₹21L saving to actually exist?"**

Then progressively go deeper.

Example:

```text
₹21L saving
     ↓
What assumptions create this number?
     ↓
Are GPU utilization assumptions realistic?
     ↓
Are request volumes accurate?
     ↓
Are token/context assumptions accurate?
     ↓
What happens at 2× developers?
     ↓
What happens when model changes?
     ↓
Can our GPU run the next model?
     ↓
What is migration cost?
     ↓
What is engineering opportunity cost?
     ↓
What is developer productivity impact?
     ↓
What is the cost of being wrong?
```

### 1. Business

What are the **5 assumptions** behind the ₹21L annual saving that you would validate first?

### 2. Workload

The team says:

> "20 concurrent users is our peak."

What questions would you ask to determine whether **20 is actually the right capacity-planning number**?

### 3. Model

Suppose six months later the preferred model changes from:

```text
33B → 70B
```

What architectural questions determine whether your investment in the current GPU infrastructure remains useful?

### 4. Quantization

The team proposes moving from FP16 to a lower-bit quantized model to fit the larger model.

What questions would you ask before accepting the trade-off?

Think:

```text
Memory
   ↕
Quality
   ↕
Latency
   ↕
Throughput
   ↕
Accuracy
   ↕
Developer productivity
```

### 5. Cost

The finance team says:

> "₹36L TCO is already conservative."

What questions would you ask to determine whether this is **TCO or merely infrastructure spend disguised as TCO?**

### 6. Optionality

As CTO, ask yourself:

> **"What happens if I am wrong?"**

If self-hosting turns out to be the wrong decision after 12 months, what questions would you ask about:

- Exit cost
- Migration
- SaaS fallback
- Stranded GPU investment
- Engineering capacity
- Vendor lock-in
- Developer disruption

---

# Final Question — The CTO Questioning Muscle

You walk into the boardroom.

The board gives you only this:

> "Should we spend ₹36L/year to self-host IDFC Coder, or pay ₹57L/year for SaaS?"

You are **not allowed to answer immediately**.

You get **5 questions only**.

Those five questions must uncover enough information for you to make the decision.

Your five questions should collectively cover:

```text
1. Business value
2. Workload / scale
3. Technical feasibility
4. Risk / security / reliability
5. Economics + strategic optionality
```

### Your challenge

**What are your 5 questions?**

And for each question, tell me:

> **"Why does this question matter to a CTO?"**

This is the final exercise for the five-set series.

The goal is to move from:

```text
Answering architecture questions
            ↓
Understanding architecture
            ↓
Identifying assumptions
            ↓
Challenging assumptions
            ↓
Discovering missing questions
            ↓
Making CTO-level decisions
```

---

# Core Questioning Framework

Use this mental model whenever you face a new architecture decision:

```text
                    ┌──────────────┐
                    │  BUSINESS    │
                    │  Why?        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  WORKLOAD    │
                    │  How much?   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  TECHNICAL   │
                    │  Can we?     │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  CAPACITY    │
                    │  How much?   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  FAILURE     │
                    │  What if?    │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  SECURITY    │
                    │  Safe?       │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  ECONOMICS   │
                    │  Worth it?   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │  OPTIONALITY │
                    │  What next?  │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ CTO DECISION │
                    └──────────────┘
```

## The Most Important Habit

Before answering any architecture question, ask:

1. **What am I assuming?**
2. **What data would prove or disprove that assumption?**
3. **What happens at 2× or 10× scale?**
4. **What happens when the system fails?**
5. **What is the cost of being wrong?**
6. **What is the business/customer impact?**
7. **What alternative am I implicitly rejecting?**
8. **How reversible is this decision?**
9. **What question have I not asked yet?**

> **The strongest architect is not the person who knows every answer. It is the person who knows which questions must be answered before the decision is made.**
