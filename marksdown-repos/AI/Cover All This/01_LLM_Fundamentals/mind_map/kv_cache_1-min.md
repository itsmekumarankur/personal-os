# 🧠 KV Cache — Mind Map - 1 min

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

Think of an LLM reading a sentence and deciding the next word.
- Q — Query: What information am I looking for right now?
- K — Key: What information does each previous token contain?
- V — Value: What actual information should I retrieve from that token?

Example: “The cat drank milk because it was thirsty.”

When processing “thirsty”:
- Q: Find what “it” refers to.
- K: Compare tokens like cat, milk, and thirsty to find relevant information.
- V: Retrieve the useful information associated with the relevant token, such as cat.

Remember: Q = Ask, K = Match, V = Information.

Why KV Cache? 
It stores previously computed K and V so the model doesn't need to calculate them again for every new token.

Example: “Ankur eats an apple because he is hungry.”

When the LLM processes “hungry”:
- Q (Query): Who is hungry?
- K (Key): Check which word matches the question — Ankur or apple.
- V (Value): Retrieve the information associated with Ankur.

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
