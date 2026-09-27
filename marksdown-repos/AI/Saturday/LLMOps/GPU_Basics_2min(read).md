# GPU Basics for LLMs — A 5-Minute AI Architect Guide

> **Goal:** Understand why LLMs need GPUs, what GPU memory and compute mean, and how GPU architecture affects model size, latency, throughput, and cost.

---

## 1. Why Do LLMs Need GPUs?

LLMs perform enormous numbers of mathematical operations, especially matrix multiplications.

A neural network is largely:

```text
Input vectors
     |
     v
Matrix Multiplication
     |
     v
Activation
     |
     v
Matrix Multiplication
     |
     v
...
```

GPUs are designed to perform many similar mathematical operations in parallel.

```text
CPU
+----------------------+
| Few powerful cores   |
|  O  O  O  O          |
+----------------------+

GPU
+--------------------------------+
| O O O O O O O O O O O O O O  |
| O O O O O O O O O O O O O O  |
| O O O O O O O O O O O O O O  |
| O O O O O O O O O O O O O O  |
| O O O O O O O O O O O O O O  |
+--------------------------------+
     Many parallel operations
```

A useful mental model:

> **CPU = general-purpose problem solver. GPU = massively parallel numerical engine.**

---

# 2. GPU vs CPU for LLMs

| CPU | GPU |
|---|---|
| Fewer powerful cores | Many parallel compute units |
| Great for general logic | Great for matrix operations |
| Large system memory | High-bandwidth GPU memory |
| Lower parallel throughput | Very high parallel throughput |
| Common for orchestration | Common for model inference/training |

A production LLM system often uses both:

```text
                    User
                      |
                      v
              +---------------+
              | CPU Services  |
              | API / Router  |
              +---------------+
                      |
                      v
              +---------------+
              | GPU Inference |
              |    Server     |
              +---------------+
                      |
                      v
                    LLM
```

---

# 3. GPU Memory Is Critical

For LLMs, GPU memory is often the first constraint architects encounter.

A model has billions of parameters.

For example:

```text
7B model
= approximately 7 billion parameters
```

If each parameter uses 16 bits:

```text
7 billion × 2 bytes
≈ 14 GB
```

That is only the parameter storage.

You also need memory for:

- KV cache
- activations
- temporary tensors
- runtime/framework overhead
- batching
- CUDA/workspace allocations

So:

```text
GPU Memory
+---------------------------+
| Model weights             |
| KV Cache                  |
| Activations               |
| Temporary tensors         |
| Runtime overhead          |
+---------------------------+
```

**Important:** Model size alone does not tell you the GPU requirement.

---

# 4. Precision and Quantization

The same model can use different numerical formats.

Common examples:

```text
FP32  = 32 bits
FP16  = 16 bits
BF16  = 16 bits
INT8  = 8 bits
INT4  = 4 bits
```

Approximate weight memory:

```text
7B parameters

FP32  -> ~28 GB
FP16  -> ~14 GB
INT8  -> ~7 GB
INT4  -> ~3.5 GB
```

These are rough calculations and exclude runtime overhead.

The architectural trade-off is:

```text
Lower precision
      |
      +----> Lower memory
      |
      +----> Often higher serving efficiency
      |
      +----> Potential quality loss
```

Quantization is therefore a major LLM serving optimization.

---

# 5. GPU Memory vs GPU Compute

Do not confuse these two.

### Memory

Answers:

> "Can I fit the model and workload?"

### Compute

Answers:

> "How quickly can I perform the operations?"

```text
GPU
 |
 +---- Memory Capacity
 |        |
 |        +--> Can model fit?
 |
 +---- Memory Bandwidth
 |        |
 |        +--> How quickly can data move?
 |
 +---- Compute
          |
          +--> How quickly can operations execute?
```

A GPU can have enough memory to load a model but still provide insufficient throughput for your workload.

---

# 6. Why Memory Bandwidth Matters

LLM inference frequently involves moving large amounts of model data.

Conceptually:

```text
GPU Memory
    |
    |  weights / tensors
    v
Compute Units
    |
    v
Matrix Operations
```

If computation is waiting for data:

```text
Compute
   ^
   |
   | waiting
   |
Memory bandwidth becomes bottleneck
```

Therefore GPU selection is not simply:

> "How many GPU cores does it have?"

You should consider:

- GPU memory capacity
- memory bandwidth
- compute capability
- supported precision
- interconnect
- power/cost
- software ecosystem

---

# 7. What Happens During LLM Inference?

LLM generation has two important phases.

## Prefill

The prompt is processed.

```text
Long Prompt
    |
    v
Tokenization
    |
    v
Transformer
    |
    v
KV Cache created
```

Prefill can be compute-intensive.

## Decode

The model generates tokens one by one.

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
...
```

The KV cache is reused.

```text
             +----------------+
             |   KV Cache     |
             +----------------+
                    |
                    v
Current token --> Attention --> Next token
```

This distinction is important when analyzing latency.

---

# 8. Latency Metrics

For production LLM systems, track:

```text
TTFT
Time To First Token

+
TPOT
Time Per Output Token

+
Total latency
```

Example:

```text
Request
  |
  |------ 800 ms ------|
  |                    |
  v                    v
First token          More tokens
  ^                      ^
  |                      |
 TTFT                  Decode
```

A system can have excellent TTFT but poor token generation speed, or the opposite.

---

# 9. KV Cache and GPU Memory

Suppose many users are generating responses simultaneously.

Each request may require KV cache memory.

```text
GPU Memory
+-----------------------------+
| Model weights               |
|                             |
| Request A -> KV cache       |
| Request B -> KV cache       |
| Request C -> KV cache       |
| Request D -> KV cache       |
| ...                         |
+-----------------------------+
```

As:

```text
Context length ↑
+
Concurrent requests ↑
```

then:

```text
KV cache memory ↑
```

This can become a major production bottleneck.

---

# 10. Multi-GPU Architecture

A model may be too large for one GPU.

Then the model can be distributed across GPUs.

```text
             Large LLM
                 |
        +--------+--------+
        |        |        |
        v        v        v
      GPU 0    GPU 1    GPU 2
        |        |        |
        +--------+--------+
             Interconnect
```

Common concepts include:

- Tensor Parallelism
- Pipeline Parallelism
- Data Parallelism

### Tensor Parallelism

A layer's computation is split across GPUs.

```text
Large Matrix
     |
     +----------+----------+
     |          |          |
    GPU 0      GPU 1      GPU 2
     |          |          |
     +----------+----------+
              |
              v
            Result
```

### Data Parallelism

Different replicas process different requests/batches.

```text
                Traffic
                   |
        +----------+----------+
        |          |          |
        v          v          v
      GPU 0      GPU 1      GPU 2
      Model      Model      Model
       copy       copy       copy
```

---

# 11. GPU Architecture Mental Model

For an AI Architect:

```text
                GPU
                 |
       +---------+---------+
       |                   |
   Memory System       Compute
       |                   |
       |             Matrix operations
       |
   Weights
   KV Cache
   Activations
       |
       v
 Memory bandwidth
       |
       v
   Performance
```

Always ask:

1. How much model memory is required?
2. How much KV cache memory is required?
3. What precision are we using?
4. What is the expected concurrency?
5. What is the context length?
6. What latency/throughput is required?
7. Can one GPU handle the model?
8. If not, what parallelism strategy is needed?

---

# 12. Architect's Cheat Sheet

```text
Model size
    |
    v
Weight memory
    |
    +--> Precision / Quantization
    |
    v
GPU memory requirement
    |
    +--> KV Cache
    +--> Runtime overhead
    |
    v
Can model fit?
    |
    +---- NO ----> Multi-GPU / smaller model / quantization
    |
   YES
    |
    v
Benchmark
    |
    +--> TTFT
    +--> Tokens/sec
    +--> P95/P99 latency
    +--> GPU utilization
    +--> Cost/request
```

> **Key takeaway:** For LLMs, GPU architecture is not just about "which GPU is fastest." It is about balancing **memory capacity, memory bandwidth, compute, concurrency, latency, throughput, and cost**.
