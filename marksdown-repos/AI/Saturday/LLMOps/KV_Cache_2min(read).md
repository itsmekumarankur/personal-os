# KV Cache — A 5-Minute AI Architect Guide

> **Goal:** Understand what the KV cache stores, why it is critical for LLM inference, how it affects GPU memory and concurrency, and why serving systems care about KV-cache management.

---

## 1. Why Do We Need a KV Cache?

LLMs generate text one token at a time.

Example:

```text
Prompt
  |
  v
Token 1
  |
  v
Token 2
  |
  v
Token 3
  |
  v
Token 4
```

At each step, attention needs information from previous tokens.

Recomputing everything from scratch would be wasteful.

The KV cache stores previously calculated **Keys (K)** and **Values (V)**.

```text
Previous tokens
      |
      v
+----------------+
|    KV Cache    |
| K1 K2 K3 ...   |
| V1 V2 V3 ...   |
+----------------+
      |
      v
Current Query
      |
      v
Attention
      |
      v
Next token
```

---

# 2. Query, Key, Value

Recall:

```text
Input
 |
 +----> Query
 |
 +----> Key
 |
 +----> Value
```

During autoregressive generation:

```text
Old tokens
    |
    +--> Keys + Values --> CACHE

New token
    |
    +--> Query
    |
    v
Attention with cached K/V
    |
    v
Next token
```

The important optimization:

> **Previously computed K/V representations are reused instead of recomputed.**

---

# 3. Without KV Cache

Conceptually:

```text
Generate token 4

Token 1
Token 2
Token 3
Token 4
   |
   v
Recalculate attention information
for previous tokens again
```

Then:

```text
Generate token 5

Token 1
Token 2
Token 3
Token 4
Token 5
   |
   v
Recalculate again
```

A lot of repeated work occurs.

---

# 4. With KV Cache

```text
Token 1 ---> K1,V1 --+
Token 2 ---> K2,V2 --+
Token 3 ---> K3,V3 --+--> KV Cache
                      |
Current token ------> Q
                      |
                      v
                  Attention
                      |
                      v
                  Next token
```

The cache grows as generation continues.

```text
Step 1: [K1,V1]

Step 2: [K1,V1][K2,V2]

Step 3: [K1,V1][K2,V2][K3,V3]

Step 4: [K1,V1][K2,V2][K3,V3][K4,V4]
```

---

# 5. Why KV Cache Consumes GPU Memory

For every active request, the system may store:

```text
KV cache
  |
  +--> Layers
  +--> Attention heads
  +--> Sequence positions
  +--> K and V tensors
```

Therefore:

```text
Context length ↑
      |
      v
KV cache per request ↑
```

And:

```text
Concurrent requests ↑
      |
      v
Total KV cache ↑
```

This is why long-context, high-concurrency workloads can become memory-bound.

---

# 6. A Simple Production Example

Suppose:

```text
100 concurrent users
```

and every request has a large context.

Conceptually:

```text
GPU Memory
+----------------------------------+
| Model weights                    |
|                                  |
| User 1 KV cache                  |
| User 2 KV cache                  |
| User 3 KV cache                  |
| ...                              |
| User 100 KV cache                |
+----------------------------------+
```

Even if the model weights fit comfortably, the workload may still run out of GPU memory because of KV cache.

---

# 7. KV Cache and Batch Scheduling

A serving engine needs to decide:

```text
Which requests should run?
How much GPU memory is available?
How many tokens can be generated?
When should a request enter/leave the batch?
```

This is one reason modern LLM inference engines use advanced scheduling and memory management.

Conceptually:

```text
Requests
  |
  v
Scheduler
  |
  +---- Request A
  +---- Request B
  +---- Request C
  |
  v
KV Cache Manager
  |
  v
GPU
```

---

# 8. KV Cache and Continuous Batching

Different users finish at different times.

```text
Request A: ========
Request B: ============
Request C: ====
Request D:   =========
```

A good serving system can continuously manage active requests instead of waiting for the entire batch to finish.

```text
GPU
 |
 +--> A
 +--> B
 +--> C exits
 +--> D enters
 +--> E enters
```

This improves utilization.

---

# 9. Important Trade-off

KV cache creates a three-way relationship:

```text
Context Length
       |
       v
KV Cache Memory
       |
       v
Concurrency
       |
       v
Throughput
```

If context length increases dramatically:

```text
Longer context
      |
      v
More KV memory/request
      |
      v
Fewer concurrent requests/GPU
      |
      v
Potential capacity reduction
```

The exact relationship depends on model architecture and implementation.

---

# 10. MHA, MQA and GQA

Attention architectures can change KV-cache requirements.

### MHA — Multi-Head Attention

Many attention heads have separate K/V heads.

```text
Q1 -> K1,V1
Q2 -> K2,V2
Q3 -> K3,V3
...
```

### MQA — Multi-Query Attention

Multiple query heads share K/V.

```text
Q1 \
Q2  +--> Shared K,V
Q3 /
```

This reduces KV-cache memory.

### GQA — Grouped-Query Attention

A middle ground:

```text
Q1 Q2 --> K/V group 1
Q3 Q4 --> K/V group 2
Q5 Q6 --> K/V group 3
```

Modern LLM architectures commonly use variants such as GQA because it can reduce memory bandwidth and KV-cache requirements while preserving multiple query heads.

---

# 11. Prefix / Prompt Caching

Some applications repeatedly use the same prefix.

Example:

```text
Large system prompt
+
Same policy document
+
Different user question
```

Instead of recomputing the same prefix repeatedly, systems can sometimes reuse cached computation.

```text
Shared Prefix
     |
     v
Cached KV
     |
 +---+---+
 |       |
User A  User B
 |       |
 v       v
Answer  Answer
```

This can improve efficiency for repeated prefixes.

---

# 12. Architect's Cheat Sheet

| Concept | Meaning |
|---|---|
| KV Cache | Stores attention Keys and Values from prior tokens |
| Purpose | Avoid repeated computation during generation |
| Main cost | GPU memory |
| Context ↑ | KV cache generally ↑ |
| Concurrency ↑ | Total KV cache generally ↑ |
| MHA | Separate K/V per attention head |
| MQA | Shared K/V across query heads |
| GQA | Groups of query heads share K/V |
| Prefix caching | Reuses cached computation for repeated prefixes |

---

## Final Mental Model

```text
                 LLM Decode
                     |
                     v
             Current Query (Q)
                     |
                     v
          +-------------------+
          |     KV Cache      |
          | Previous K + V     |
          +-------------------+
                     |
                     v
                Attention
                     |
                     v
                Next Token
```

> **KV cache is one of the most important bridges between Transformer theory and production LLM infrastructure. It improves generation efficiency, but turns context length and concurrency directly into GPU-memory concerns.**
