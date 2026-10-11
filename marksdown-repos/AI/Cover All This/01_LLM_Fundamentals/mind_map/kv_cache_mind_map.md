# 🧠 KV Cache — Mind Map

> **Mental Model:** `Compute K/V once → Cache → Reuse during decoding`

## 1. Why KV Cache?

Without cache:

```text
Generate token 4 → recompute previous information
Generate token 5 → recompute previous information again
```

With cache:

```text
Previous tokens → K + V → KV Cache
Current token   → Q
                    ↓
                Attention
                    ↓
                Next token
```

> **KV Cache removes repeated K/V computation.**

## 2. What Is Cached?

```text
Input
 ├── Query (Q)
 ├── Key   (K) ──→ CACHE
 └── Value (V) ──→ CACHE
```

Previous K/V are reused during autoregressive generation.

## 3. Cache Grows

```text
Step 1 → [K1,V1]
Step 2 → [K1,V1][K2,V2]
Step 3 → [K1,V1][K2,V2][K3,V3]
```

Therefore:

```text
Context length ↑ → KV cache / request ↑
Concurrent users ↑ → Total KV cache ↑
```

## 4. Production Impact

```text
Context Length
      ↓
KV Cache / Request
      ↓
GPU Memory
      ↓
Concurrency
      ↓
Throughput
```

> GPU capacity is **not only model weights**.

## 5. Serving + Scheduling

```text
Requests
   ↓
Scheduler
   ↓
KV Cache Manager
   ↓
GPU
```

The serving engine manages active requests and available KV memory.

## 6. Continuous Batching

Users finish at different times:

```text
A ========
B ============
C ====
D   =========
```

A good serving engine can do:

```text
C exits → D enters → E enters
```

> **Continuous batching improves GPU utilization.**

## 7. Attention Architectures

```text
MHA → Many K/V heads → Higher KV memory

MQA → Shared K/V     → Lower KV memory

GQA → Grouped K/V    → Middle ground
```

## ⚡ 30-Second Recall

> **KV Cache = reuse previous K/V during autoregressive decoding.**
>
> **Longer context + more users = more KV memory.**
>
> **KV Cache connects context to GPU capacity, concurrency and cost.**

### 🎯 Architect Question
> **"At our context length and concurrency, how much KV-cache memory do we need per GPU?"**
