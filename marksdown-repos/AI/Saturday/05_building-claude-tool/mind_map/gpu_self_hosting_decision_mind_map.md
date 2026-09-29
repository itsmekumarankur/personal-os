# 🧠 GPU & Self-Hosting Cost Decision — Mind Map

> **Recall:** `WORKLOAD → VRAM → GPU → TCO → RISK → DECISION`

## 1. Start With Workload

```text
❌ Which GPU should I buy?

✅ What workload am I trying to serve?
```

Self-hosting cost is:

```text
GPU
+ Infrastructure
+ Engineering
+ Operations
+ Networking
+ Storage
+ Monitoring
+ Security
+ Opportunity Cost
```

> **GPU invoice = tip of the iceberg.**

## 2. SaaS vs Self-Host

```text
SAAS
Users × Subscription × Time

SELF-HOST
Infrastructure + People + Operations + Risk
```

> Compare **Total Cost of Ownership**, not GPU price vs SaaS price.

### Risk-Adjusted Economics

```text
Raw Savings
   ↓
- Expected Risk Cost
   ↓
Risk-Adjusted Savings
```

> `Expected Risk Cost = Probability × Impact`

## 3. GPU Bottleneck

```text
AWS Instance
 ├── CPU
 ├── RAM
 ├── GPU
 │    └── VRAM ← model fit
 ├── Disk
 └── Network
```

> **GPU speed = how fast.**  
> **VRAM = whether it fits at all.**

> **You can't compute what you can't load.**

## 4. VRAM Formula

```text
Required VRAM
=
Model Weights
+ KV Cache
+ Activations
+ Runtime
+ Headroom
```

### 33B Model Weight Memory

```text
FP32 → ~132 GB
FP16 →  ~66 GB
INT8 →  ~33 GB
INT4 → ~16.5 GB
```

Example from the note:

```text
INT4 weights       ~17 GB
KV cache            ~2 GB
Activations         ~1 GB
Runtime             ~2 GB
Headroom            ~1 GB
                    ─────
Total              ~23 GB
```

> **24 GB GPU can fit; 16 GB cannot.**

## 5. KV Cache

```text
KV Cache
  ∝
Layers × Head Dim × Context Length × Precision
```

```text
Context ↑
   ↓
KV Cache ↑
   ↓
VRAM ↑
```

> **Longer context is not free.**

## 6. Quantization

```text
FP16 → INT8 → INT4
  │      │      │
Quality  ↔   Efficiency
  │             │
Memory ↓        Cost ↓
```

### Mental Model

```text
FP16 → best quality / expensive
INT8 → middle ground
INT4 → lower memory / potentially lower quality
```

> **Quantization is an architecture lever, not just a model optimization.**

## 7. GPU Selection

```text
Workload
   ↓
Model size
   ↓
Precision
   ↓
VRAM requirement
   ↓
GPU candidates
   ↓
Throughput / latency benchmark
   ↓
Cost + availability
   ↓
GPU decision
```

### Important

> Don't choose the GPU by name first. **Calculate fit first.**

## 8. Underestimation Traps

```text
❌ Model weights only
❌ Average traffic only
❌ GPU price only
❌ Raw savings only
❌ Peak performance only
```

Instead include:

```text
Weights + KV + runtime + headroom
        +
Concurrency + latency + reliability
        +
Engineering + operations + risk
```

## ⚡ 30-Second Recall

> **1. Start with workload, not GPU name.**
>
> **2. VRAM determines whether the model fits.**
>
> **3. Total VRAM ≠ model weights.**
>
> **4. Context length drives KV-cache memory.**
>
> **5. Quantization trades quality for efficiency.**
>
> **6. Self-hosting decisions require TCO + risk, not raw savings.**

### 🎯 Architect Question
> **"Can the model fit, can it meet concurrency/latency targets, and is the risk-adjusted TCO better?"**
