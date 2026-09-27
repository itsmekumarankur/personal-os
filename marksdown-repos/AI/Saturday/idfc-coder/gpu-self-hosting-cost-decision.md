# GPU & Self-Hosting Cost Decision — Architect Notes

> **Core lesson:** Don't start with *"Which GPU should I buy?"* Start with *"What workload am I trying to serve?"*

---

## PART 1 — BUSINESS CASE

### Slide 1 — Self-Hosting vs SaaS

**Opening question:** 50 developers × $200/month — at what point does owning infrastructure become cheaper?

Don't jump to multiplying. First ask: *"What does 'owning infrastructure' actually mean?"*

```
SAAS                          SELF-HOSTED
────                          ───────────
50 developers                 50 developers
      │                             │
      ↓                            GPU
$200/dev/month                    + Software
      │                           + Engineering
      ↓                           + Networking
Predictable subscription          + Storage
                                  + Monitoring
                                  + Operations
```

**If GPU costs ₹4 lakh, does self-hosting cost ₹4 lakh?** No.

#### The Hidden Cost Layers

Name five hidden costs that don't appear on the GPU invoice.

```
HIDDEN COSTS
      │
      ├── Engineering setup time
      ├── Ongoing operations
      ├── Model updates/re-training
      ├── Monitoring/observability
      ├── Security/compliance
      ├── Networking/bandwidth
      ├── Storage for models/logs
      ├── Backup/disaster recovery
      └── Opportunity cost of engineers
```

**The iceberg model:**

```
          VISIBLE COSTS
          (GPU purchase)
              ████
              ████
              ████
              ████
          ────────────
              ████████
              ████████
              ████████
              ████████
              ████████
              ████████
              ████████
              ████████
              ████████
          HIDDEN COSTS
          (People, operations, complexity)
```

> **"The GPU invoice is the tip of the iceberg. The real cost is underwater."**

#### The TCO Equation

```
SELF-HOSTED TCO          SAAS TCO
=                        =
GPU                      Users × Subscription × Time
+ Infrastructure
+ Engineering
+ Operations
+ Networking
+ Storage
+ Monitoring
+ Opportunity Cost
```

#### Opportunity Cost Dimension

**Ask:** What's the opportunity cost of using your best engineers to build GPU infrastructure rather than customer-facing features?

```
OPPORTUNITY COST
      │
      ↓
"An hour spent on GPU ops is an hour NOT spent on..."
      │
      ├── Customer features
      ├── Product innovation
      ├── Technical debt reduction
      ├── Developer productivity
      └── Strategic initiatives
```

```
           ENGINEERING BUDGET
                  │
      ┌───────────┴───────────┐
      ↓                       ↓
  GPU OPS               PRODUCT
  (Infrastructure)      (Features)
      │                       │
      ↓                       ↓
  "Cost center"        "Value creation"
```

> **"Every rupee spent on infrastructure operations is a rupee not spent on building the business."**

#### Architect Takeaway

The first mistake: comparing `GPU price` vs `SaaS subscription`.

Instead compare:

```
              TOTAL COST OF OWNERSHIP
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
         SELF-HOSTED              SAAS
              │                     │
       all internal costs      subscription
```

---

### Slide 2 — 58% Savings

```
50 heavy users
      │
      ├── SaaS       ₹57.0 L
      │
      └── Self-host  ₹23.8 L

Savings:
₹57.0 L
  -
₹23.8 L
───────
₹33.2 L  ≈ 58%
```

**But ask:** *"Is 58% savings automatically enough to justify self-hosting?"* Probably not.

```
SAVINGS
   │
   ↓
₹33.2L
   │
   ├── Engineering risk
   ├── Operational risk
   ├── GPU availability
   ├── Model quality
   ├── Security
   └── Developer productivity
```

> **Cost saving is an input to the architecture decision, not the decision itself.**

#### Risk-Adjusted Savings

**Ask:** What's the value of NOT taking the risk?

```
RISK-ADJUSTED SAVINGS
         │
         ↓
   RAW SAVINGS
      ₹33.2L
         │
         ↓
      - RISK COSTS
         │
         ├── Operational failure: ₹10L
         ├── Security breach: ₹20L
         ├── Performance issues: ₹5L
         ├── Engineering burnout: ₹5L
         └── Project delay: ₹10L
         │
         ↓
   NET SAVINGS
      -₹16.8L
      (Self-hosting loses!)
```

```
RAW SAVINGS ≠ ACTUAL SAVINGS
       │
       ↓
   "What's the probability of each risk materializing?"
       │
       ↓
   "Expected value = Probability × Cost"
```

> **"A 58% raw saving might be a 0% risk-adjusted saving, or worse."**

#### Breakeven Concept

```
             USER COUNT
                 │
                 ↓
      ┌─────────────────────┐
      │ SaaS cost increases │
      │ almost linearly     │
      └──────────┬──────────┘
                 │
        ─────────●──────────
                 ↑
             ~21 users
                 │
        self-hosting
        starts winning
```

**Below ~21 heavy users** → SaaS is cheaper.
**Above ~21** → self-hosting begins to make economic sense under these assumptions.

#### Sensitivity Analysis

**Ask:** What assumptions could make the breakeven point 50 users or 10 users?

```
ASSUMPTION                    IMPACT ON BREAKEVEN
─────────────────────────────────────────────────────
GPU cost: ₹93/hr → ₹60/hr    Lower breakeven
Engineering cost: ₹19L → ₹9L Lower breakeven
User requests: 200 → 100/day Higher breakeven
Model size: 33B → 70B        Higher breakeven
SaaS cost: ₹1.14L → ₹0.57L   Higher breakeven
```

```
BREAKEVEN SENSITIVITY
          │
70 users ─┼─── High SaaS cost scenario
          │
50 users ─┼─── Base case
          │
30 users ─┼─── Low SaaS cost scenario
          │
10 users ─┼─── Very low cost scenario
          │
          └────────────────────────────────
```

```
BREAKEVEN IS NOT A FIXED NUMBER
        │
        ↓
  "It's a function of assumptions"
        │
        ↓
  "Test your assumptions before committing"
```

---

## PART 2 — GPU FUNDAMENTALS

### Slide 3 — Which Resource Becomes the Bottleneck?

**Ask:** An AWS instance gives me CPU, RAM, GPU, VRAM and disk. Which one can prevent a 33B model from running at all?

```
AWS INSTANCE
│
├── CPU
├── RAM
├── GPU
│    └── VRAM  ← ?
├── Disk
└── Network
```

```
33B model → needs memory → GPU VRAM
```

**If CPU is powerful but GPU VRAM is insufficient, can the model run?** No.

```
VRAM
 │
 ├── enough → model CAN run
 │
 └── insufficient → model CANNOT run
```

**Critical distinction:**

```
GPU SPEED              VRAM
   =                      =
How fast can I compute?   Can I fit the workload at all?
```

#### Capacity vs Performance Matrix

```
      CAPACITY (VRAM)
           │
    ┌──────┴──────┐
    │             │
    │     FAST    │
    │    +        │
    │  INSUFFICIENT│
    │   VRAM      │
    │             │
HIGH │             │  FAST + SUFFICIENT
PERF │             │  (The ideal)
     │             │
    └─────────────┘
               CAPACITY
```

```
FAST + INSUFFICIENT VRAM
           │
           ↓
      "It doesn't run"
           │
           ↓
     INFINITE COST/REQUEST
```

> **"You can't compute what you can't load."**

---

### Slide 4 — How Much VRAM?

**Ask:** Before looking at AWS GPU names, how would you determine the minimum GPU memory?

```
MODEL → 33 BILLION PARAMETERS
```

**How many bytes does each parameter require?**

```
FP32 → 4 bytes
FP16 → 2 bytes
INT8 → 1 byte
INT4 → ~0.5 byte
```

Therefore: `33B × bytes/parameter`

**Does model weight memory equal total GPU memory?** No.

```
TOTAL VRAM
│
├── Model weights
├── KV cache
├── Activations
├── Framework/runtime
└── Safety headroom
```

#### Complete Memory Breakdown

```
MEMORY BREAKDOWN (typical)
          │
          ↓
Model weights: 60-70%
KV cache: 15-25%
Activations: 5-10%
Runtime/overhead: 5-10%
Safety headroom: 5%
```

```
VRAM DISTRIBUTION
────────────────────────────
████████████████████ 70%  Weights
██████████ 20%            KV Cache
████ 5%                   Activations
████ 5%                   Runtime
████ 5%                   Headroom
────────────────────────────
```

**Example: 33B INT4 Model**

```
Weights: 17GB
KV cache (2K context, 8 concurrent): ~2GB
Activations (during inference): ~1GB
Runtime overhead (vLLM, PyTorch): ~2GB
Headroom (safety): ~1GB
─────────────────────────
TOTAL: ~23GB

→ L4 (24GB) fits, but just barely
→ T4 (16GB) fails
```

> **"The model weights are the main event, but the supporting cast consumes more memory than you think."**

#### Architect Rule

```
Required VRAM
=
Weights
+
KV cache
+
Activations
+
Runtime overhead
+
Headroom
```

#### KV Cache Dimension

**Ask:** What happens to VRAM when context length doubles?

```
KV CACHE FORMULA
KV Cache = 2 × Layers × Head_Dim × Seq_Length × Precision

For DeepSeek 33B:
  Layers: 60
  Head_Dim: 128
  Seq_Length: 2048 (2K)
  Precision: 2 bytes (FP16)

  KV = 2 × 60 × 128 × 2048 × 2
     = 62,914,560 bytes
     ≈ 60 MB per concurrent request

For 8 concurrent requests:  8 × 60 MB = 480 MB
For 4K context:             4 × 480 MB = 1.92 GB
For 8K context:             8 × 480 MB = 3.84 GB
For 32K context:           32 × 480 MB = 15.36 GB
```

```
CONTEXT LENGTH VS KV CACHE
          │
15GB ─────┼────●──────────────
          │
10GB ─────┼─────────●─────────
          │
 5GB ─────┼──────────────●────
          │
          └────────────────────→ Context Length
              2K   4K   8K
```

> **"Doubling context length isn't free. It consumes VRAM exponentially in practice."**

---

### Slide 5 — Why VRAM Rules

```
Developer → AI API → vLLM → GPU → LLM
```

**Resource responsibilities:**

```
CPU     → normal application logic
RAM     → system/application memory
GPU     → AI computation
VRAM    → model + working state
Disk    → model files/logs
Network → requests/responses
```

**Fundamental calculation (DeepSeek 33B):**

```
FP32:  33B × 4 bytes   ≈ 132 GB
FP16:  33B × 2 bytes   ≈ 66 GB
INT8:  33B × 1 byte    ≈ 33 GB
INT4:  33B × 0.5 byte  ≈ 16.5 GB
```

#### The Architectural Lever

```
                QUANTIZATION
                     │
         ┌───────────┼───────────┐
         ↓           ↓           ↓
       FP16        INT8         INT4
        66GB        33GB        17GB
         │           │            │
         ↓           ↓            ↓
      expensive    medium       cheap
       GPUs         GPUs         GPUs
```

> **Quantization is not merely a model optimization. It can fundamentally change the infrastructure architecture.**

#### Quantization Trade-Off Matrix

```
              QUANTIZATION TRADE-OFFS
                     │
      ┌──────────────┼──────────────┐
      ↓              ↓              ↓
    FP16           INT8           INT4
      │              │              │
  GAINS:         GAINS:         GAINS:
  Best           Good           Cheap
  quality        quality        GPUs
  No             2x memory      4x memory
  quantization   reduction      reduction
  loss
      │              │              │
  LOSSES:        LOSSES:        LOSSES:
  Expensive      Some           Quality
  GPUs           quality        loss
  2x memory      loss           May need
  requirement                    retraining
```

```
QUALITY
  ↑
  │  FP16 ────●
  │           │
  │  INT8 ────●────────
  │           │
  │  INT4 ────●────────────────
  │
  └────────────────────────────────→ COST
       Cheap      Medium     Expensive
```

**When to use each precision:**

```
FP16:
  └── Quality is paramount
       └── Can afford expensive GPUs
            └── Model accuracy is critical

INT8:
  └── Quality matters but cost is a concern
       └── Want 2x memory savings
            └── Quality loss is acceptable

INT4:
  └── Cost is the primary driver
       └── Need to fit on small GPUs
            └── Quality loss is acceptable
                 └── Model can be fine-tuned
```

> **"Quantization is a lever between cost and quality. Pull it wisely."**

---

### Slide 6 — Calculate Memory Yourself

**Given 33 billion parameters:**

```
33B
 │
 ├── × 4 bytes → 132 GB
 ├── × 2 bytes → 66 GB
 ├── × 1 byte  → 33 GB
 └── × 0.5     → 16.5 GB
```

**Ask:** Which GPU immediately becomes impossible?

```
T4 = 16GB
INT4 ≈ 16.5GB
16GB < 16.5GB
```

Already impossible **before** KV cache + runtime + batching.

#### GPU Fit Table (33B Model)

```
GPU     │ VRAM  │ FP16  │ INT8  │ INT4  │ REAL
        │       │ 66GB  │ 33GB  │ 16.5GB│ 23GB*
─────────────────────────────────────────────────
T4      │ 16GB  │  ✗   │  ✗   │  ✗   │  ✗
L4      │ 24GB  │  ✗   │  ✗   │  ✓   │  ✓
A10G    │ 24GB  │  ✗   │  ✗   │  ✓   │  ✓
A100    │ 40GB  │  ✗   │  ✓   │  ✓   │  ✓
A100    │ 80GB  │  ✓   │  ✓   │  ✓   │  ✓
H100    │ 80GB  │  ✓   │  ✓   │  ✓   │  ✓

* REAL = INT4 + KV cache + runtime + headroom
```

```
ONLY GPUS WITH 24GB+ CAN RUN THIS WORKLOAD
                │
                ↓
         ┌──────┴──────┐
         ↓             ↓
      T4 FAILS    L4 WORKS
```

> **"The GPU must fit the model before it can run the model."**

#### Headroom Principle

**Ask:** Why do we need headroom? Why can't we use 100% of VRAM?

```
HEADROOM REASONS
      │
      ├── Memory fragmentation
      ├── Unexpected allocations
      ├── Batching overhead
      ├── Model loading/unloading
      ├── Failover/reserve
      └── GPU driver overhead
```

```
NEVER USE 100% OF VRAM
        │
        ↓
  "Always leave 10-20% headroom"
        │
        ↓
   "When you're at 80%, you're at 100%"
```

```
VRAM UTILIZATION
────────────────────────────────
███████████████████████ 85%  Used
█████ 15%                    Headroom
────────────────────────────────
        ↑
     "Safe zone"
```

> **"Headroom isn't waste—it's insurance against unpredictable memory spikes."**

---

### Slide 7 — Why Not Always INT4?

**Ask:** If INT4 makes everything cheaper, why not quantize every model to INT4?

```
                    QUANTIZATION
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
            FP16       INT8       INT4
              │          │          │
           quality     balance     memory
              ↑                       ↓
           expensive                cheap
```

```
INT4
 │
 ├── ↓ memory
 ├── ↓ infrastructure cost
 ├── ↑ model fit
 │
 └── possible ↓ quality
```

```
                 QUALITY
                    ↑
               FP16 ●
                    │
               INT8 ●
                    │
               INT4 ●
                    │
                    └────────────→ COST
```

The correct question is not *"What's the cheapest precision?"* but:

> **"What's the cheapest precision that meets our quality SLA?"**

#### Quality Degradation Spectrum

```
QUANTIZATION EFFECTS
         │
   ┌─────┴─────┐
   ↓           ↓
PERPLEXITY  ACCURACY
   │           │
"Model     "Correct
 becomes    answers
 less       decrease"
 confident"
   │           │
FP16: 1.0x   FP16: 100%
INT8: 1.05x  INT8: 98-99%
INT4: 1.15x  INT4: 95-97%
```

```
ACCURACY VS QUANTIZATION
          │
100% ─────●───────────────────────
          │  ●
 98% ─────┤     ●
          │
 96% ─────┤          ●
          │
 94% ─────┤               ●
          │
          └────────────────────────→
               FP16  INT8  INT4
```

```
                     QUALITY SLA
                         │
            ┌────────────┼────────────┐
            ↓            ↓            ↓
      "95% is       "98% is        "Must
       acceptable"   acceptable"    be 99.9%"
            │            │            │
            ↓            ↓            ↓
         INT4          INT8          FP16
```

> **"Quantization choice is a quality SLA decision disguised as a memory decision."**

---

### Slide 8 — Quantization Answer

```
FP16
66GB
 │
 │ quantize
 ↓
INT8
33GB
 │
 │ quantize
 ↓
INT4
16.5GB
```

```
              33B MODEL
                  │
        ┌─────────┼─────────┐
        ↓         ↓         ↓
       FP16      INT8      INT4
        │         │         │
       66GB      33GB      17GB
        │         │         │
        ↓         ↓         ↓
     large GPU  larger    24GB GPU
```

> **Quantization is a hardware-selection decision disguised as a model-format decision.**

#### Quantization Decision Tree

```
              QUANTIZATION DECISION
                      │
            "What's your quality requirement?"
                      │
         ┌────────────┴────────────┐
         ↓                         ↓
    "High quality"            "Acceptable quality"
         │                         │
      "Use FP16"               "Can we use INT8?"
         │                         │
    "Expensive GPUs"          "What's the accuracy loss?"
         │             ┌───────────┴───────────┐
         │             ↓                       ↓
         │        "Acceptable"          "Not acceptable"
         │             │                       │
         │          "Use INT8"            "Use FP16"
         │             │
         │       "Could we use INT4?"
         │             │
         │    ┌────────┴────────┐
         │    ↓                 ↓
         │ "Yes"              "No"
         │    │                 │
         │ "Use INT4"      "Stick with INT8"
         │    │
         └────┴───────→ "Benchmark quality vs baseline"
```

```
QUALITY REQUIREMENT    →  PRECISION    →  GPU TYPE
────────────────────────────────────────────────────
99.9% (Production)     →  FP16         →  A100 80GB
98% (Good enough)      →  INT8         →  A100 40GB
95% (Acceptable)       →  INT4         →  L4 24GB
```

> **"The quantization decision cascades into GPU selection, which cascades into cost."**

---

### Slide 9 — Complete VRAM Chain

```
Parameters
    ↓
Precision
    ↓
Weight memory
    ↓
Runtime overhead
    ↓
KV cache
    ↓
Concurrency
    ↓
Required VRAM
```

**Ask:** Which part is easiest to underestimate?

```
WRONG:
Model = 17GB
GPU = 24GB
17 < 24 → DONE

CORRECT:
17GB weights
+ KV cache
+ activations
+ runtime
+ headroom
= REAL requirement
```

#### Underestimation Traps

```
UNDERESTIMATION TRAPS
         │
TRAP 1: KV CACHE
   "I forgot that KV cache grows
    with context length and concurrency"
         │
TRAP 2: RUNTIME OVERHEAD
   "I didn't account for the inference
    engine's memory usage"
         │
TRAP 3: HEADROOM
   "I thought 24GB meant 24GB usable"
```

```
VRAM REQUIREMENT
        │
  [Weights]     17GB
  + [KV Cache]  2GB   (8 concurrent, 2K context)
  + [Activations]1GB
  + [Runtime]    2GB   (vLLM, PyTorch, CUDA)
  + [Headroom]   1GB   (10% safety)
  ─────────────────
  TOTAL:        23GB
```

> **"Fit is binary; performance is continuous."**

First: *Does it fit?* Then: *How fast does it run?*

#### Performance Continuum

```
PERFORMANCE CONTINUUM
         │
    ┌────┴────┐
    ↓         ↓
LATENCY   THROUGHPUT
    │         │
"How fast   "How many
 per         per
 request?"   second?"
    │         │
  ┌────┴────┐
  ↓         ↓
BATCHING  CONCURRENCY
    │         │
"How many   "How many
 can we     in flight?"
 process
 together?"
```

```
BATCHING VS LATENCY
        │
LATENCY │        ●
  ↑     │       ●
        │      ●
        │     ●
        │    ●
        │   ●
        │  ●
        │ ●
        │●
        └──────────────────→ BATCH SIZE
        1   2   4   8   16
```

> **"Fitting is the entrance exam. Performance is the ongoing job."**

---

## PART 3 — GPU OPTIONS

### Slide 11 — T4 vs A10G vs L4

**Ask:** If T4 costs only ₹50/hour and L4 costs ₹93/hour, why not choose T4?

```
T4
16GB
₹50/hr
   │
   ↓
INT4 model ~17GB
   │
   X
Doesn't fit
```

> Cheap infrastructure that cannot run the workload has **infinite cost/request**.

```
GPU cost/hour
      ↓
   ₹50/hr

But:
capacity = 0

Therefore:
₹ / successful request = effectively infinite
```

```
L4
24GB
₹93/hr
 │
 ↓
17-19GB workload
 │
 ↓
FIT
```

#### The "Infinite Cost" Principle

```
COST PER REQUEST = GPU COST / REQUESTS SERVED

T4:
  GPU cost: ₹50/hr
  Requests served: 0 (model doesn't fit)
  Cost/request: ₹50 / 0 = ∞

L4:
  GPU cost: ₹93/hr
  Requests served: 1,000/hr
  Cost/request: ₹0.093
```

```
COST PER REQUEST
       │
₹1.00 ─┤
       │
₹0.50 ─┤
       │        ● L4 (₹0.093)
₹0.10 ─┤       ●
       │      ●
       │     ●
       │    ●
       │   ● T4 (infinite)
       └──────────────────────→ GPU
            T4    L4
```

> **"A ₹50 GPU that serves 0 requests is infinitely more expensive than a ₹93 GPU that serves 1,000 requests."**

#### Capability Comparison

```
FEATURE        │ T4 (16GB)  │ A10G (24GB) │ L4 (24GB)
───────────────────────────────────────────────────────
VRAM           │ 16GB       │ 24GB        │ 24GB
Cost/hr        │ ₹50        │ ₹115        │ ₹93
Fit 33B INT4?  │ ✗          │ ✓           │ ✓
Generation     │ Older      │ Older       │ Newer
Performance    │ Lower      │ Higher      │ Moderate
Availability   │ High       │ High        │ Growing
Suitability    │ ✗          │ ✓           │ ✓✓
```

```
L4 WINS BECAUSE:
      │
      ├── Fits the model (24GB)
      ├── Cheaper than A10G (₹93 vs ₹115)
      ├── Newer generation
      └── Lower total cost of ownership
```

> **"The winner isn't the cheapest GPU. It's the cheapest GPU that works."**

---

### Slide 12 — What Should the GPU Decision Function Be?

**Ask:** If I give you five GPUs, what number should determine the winner?

Possible answers: ₹/hour, VRAM, tokens/sec, requests/sec, latency, cost/request.

> "None of these alone."

```
                GPU VALUE
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
      FIT          SLA         COST
        │           │           │
      VRAM        latency     ₹/request
```

```
Cost / useful request
=
GPU hourly cost
────────────────────
successful requests/hour
```

But only after satisfying: `VRAM requirement + quality + latency SLA + concurrency`

```
                 SELECT GPU
                      │
                 Does it fit?
                      │
                     YES
                      │
                 Meets latency?
                      │
                     YES
                      │
                 Meets concurrency?
                      │
                     YES
                      │
               Lowest cost/request
```

#### GPU Selection Algorithm

```
    1. INPUTS:
         ├── Model size (parameters)
         ├── Precision (FP16/INT8/INT4)
         ├── Context length
         ├── Expected concurrency
         ├── Latency SLA
         └── Budget
         │
    2. CALCULATE:
         ├── Weight memory
         ├── KV cache per request
         ├── Total VRAM needed
         └── Required performance
         │
    3. FILTER:
         └── Only GPUs where VRAM >= Required VRAM
         │
    4. TEST:
         └── Only GPUs that meet latency SLA
         │
    5. OPTIMIZE:
         └── Choose cheapest GPU from remaining
```

```python
function selectGPU(workload, candidates):
    # Step 1: Calculate requirements
    required_vram = calculateVRAM(workload)
    required_perf = calculatePerformance(workload)

    # Step 2: Filter by fit
    fitting = [gpu for gpu in candidates
               if gpu.vram >= required_vram]

    # Step 3: Test performance
    performing = [gpu for gpu in fitting
                  if benchmark(gpu) >= required_perf]

    # Step 4: Minimize cost
    return min(performing, key=lambda gpu: gpu.cost_per_hour)
```

> **"The GPU selection function is a filter-then-optimize algorithm, not a popularity contest."**

---

### Slide 13 — L4 Wins

```
GPU       VRAM      ₹/hr
──────────────────────────
T4        16GB       50
A10G      24GB      115
L4        24GB       93
```

```
T4
 │
 └── cheap
      BUT
      ↓
      insufficient VRAM

A10G
 │
 └── fits
      BUT
      ↓
      more expensive than L4

L4
 │
 └── fits
      + cheaper than A10G
      + newer generation
      ↓
      WINNER
```

---

## Quick Reference — Key Principles

| Principle | Statement |
|---|---|
| Start point | "What workload am I serving?" not "Which GPU?" |
| TCO | GPU invoice is tip of the iceberg |
| Breakeven | Not fixed — function of assumptions |
| Risk adjustment | Raw savings ≠ actual savings |
| Fit vs speed | "You can't compute what you can't load" |
| VRAM rule | Weights + KV cache + activations + runtime + headroom |
| KV cache | Grows with context length & concurrency |
| Quantization | Hardware-selection decision in disguise |
| Quality SLA | Cheapest precision that meets SLA, not cheapest precision |
| Headroom | "When you're at 80%, you're at 100%" |
| Fit is binary | Performance is continuous |
| Infinite cost | ₹50 GPU serving 0 requests = ∞ cost/request |
| Winner | Cheapest GPU that works, not cheapest GPU |
| Selection | Filter-then-optimize, not popularity contest |
