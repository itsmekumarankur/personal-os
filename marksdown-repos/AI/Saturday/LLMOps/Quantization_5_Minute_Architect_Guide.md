# Quantization — A 5-Minute AI Architect Guide

> **Goal:** Understand how quantization reduces LLM memory and serving cost, what FP16/BF16/INT8/INT4 mean, the quality trade-offs, and how quantization affects production architecture.

---

## 1. What Is Quantization?

Quantization represents model values using fewer bits.

Instead of:

```text
32-bit floating point
```

we may use:

```text
16-bit
8-bit
4-bit
```

Conceptually:

```text
High precision
     |
     v
More bits
     |
     v
More memory

Quantization
     |
     v
Fewer bits
     |
     v
Less memory
```

---

# 2. Why Quantize an LLM?

Suppose a model has:

```text
70 billion parameters
```

Very roughly:

```text
FP32 -> 70B × 4 bytes  ≈ 280 GB

FP16 -> 70B × 2 bytes  ≈ 140 GB

INT8 -> 70B × 1 byte   ≈ 70 GB

INT4 -> 70B × 0.5 byte ≈ 35 GB
```

These are approximate weight-storage numbers only.

Actual serving memory is higher because you also need:

```text
Weights
+
KV Cache
+
Activations
+
Runtime overhead
```

---

# 3. Quantization Mental Model

Think of a number:

```text
Original:

0.123456789
```

A lower-precision representation stores it approximately:

```text
0.12
```

You are trading numerical precision for efficiency.

```text
Precision
    |
    v
Higher --------------------> Lower
    |                         |
 Quality                    Efficiency
 potentially ↑              potentially ↑
 Memory ↑                    Memory ↓
```

The exact quality impact depends heavily on the model, quantization method, calibration data, and workload.

---

# 4. Common Numerical Formats

```text
FP32
  |
  +--> 32 bits

FP16
  |
  +--> 16 bits

BF16
  |
  +--> 16 bits

INT8
  |
  +--> 8 bits

INT4
  |
  +--> 4 bits
```

Important:

> **BF16 and FP16 both use 16 bits, but they have different numerical formats and ranges.**

---

# 5. Weight Quantization

A common approach is to quantize model weights.

```text
Original Model
      |
      v
FP16 Weights
      |
      v
Quantization
      |
      v
INT8 / INT4 Weights
      |
      v
Smaller Model Representation
```

Example:

```text
FP16 Model
+------------------------+
| 2 bytes / parameter    |
+------------------------+

        Quantize

INT4 Model
+------------------------+
| 0.5 bytes / parameter  |
+------------------------+
```

This can substantially reduce model memory.

---

# 6. Why Quantization Helps Serving

Suppose:

```text
Original model = 140 GB
```

A single GPU may not fit it.

After quantization:

```text
Quantized model = ~40 GB
```

Now a smaller number of GPUs may be sufficient.

```text
Before

Model
 |
 +--> GPU 0
 +--> GPU 1
 +--> GPU 2
 +--> GPU 3


After quantization

Model
 |
 +--> GPU 0
 +--> GPU 1
```

This can affect:

- infrastructure cost
- latency
- deployment complexity
- capacity
- concurrency

---

# 7. Quantization Is Not Free

Lower precision can introduce error.

```text
Original weights
       |
       v
Quantization
       |
       v
Approximation
       |
       v
Potential quality loss
```

Potential impact:

- reasoning quality
- factual accuracy
- numerical precision
- task-specific accuracy
- output stability

But the impact varies greatly.

A good quantization workflow therefore includes benchmarking.

---

# 8. Post-Training Quantization

A model is trained first.

Then:

```text
Trained Model
     |
     v
Quantization
     |
     v
Quantized Model
     |
     v
Evaluation
```

This is often called **post-training quantization**.

The model weights are converted after training.

---

# 9. Quantization-Aware Training

Another approach is to account for quantization effects during training.

Conceptually:

```text
Training
   |
   +--> Simulate / account for quantization
   |
   v
Model optimized for lower precision
   |
   v
Quantized deployment
```

This can sometimes preserve quality better, but adds training complexity.

---

# 10. Weight-Only Quantization

A common LLM optimization is:

```text
Weights -> INT4
Activations -> higher precision
```

Conceptually:

```text
        Weights
          |
        INT4
          |
          v
Matrix operation <--- Activations
                          |
                       FP16/BF16
```

This can significantly reduce weight memory while maintaining useful numerical behavior.

---

# 11. Quantization and KV Cache

Do not confuse:

```text
Weight quantization
```

with:

```text
KV-cache quantization
```

They are separate optimization areas.

```text
GPU Memory
+---------------------------+
| Quantized model weights   |
|                           |
| KV Cache                  |
|                           |
| Activations               |
| Runtime                   |
+---------------------------+
```

You can potentially optimize both, depending on model and serving stack.

---

# 12. Quantization and GPU Architecture

Suppose:

```text
FP16 model
     |
     v
Requires 2 GPUs
```

Quantization might enable:

```text
INT4 model
     |
     v
Fits on 1 GPU
```

That can change:

```text
GPU count
   |
   v
Infrastructure cost
   |
   v
Power consumption
   |
   v
Operational complexity
```

This is why quantization is an architecture decision, not merely a model-format decision.

---

# 13. Quantization and Throughput

Smaller weights can reduce memory pressure and memory movement.

Conceptually:

```text
Quantization
     |
     v
Smaller weights
     |
     v
Less memory traffic
     |
     v
Potentially better serving efficiency
```

However, actual throughput depends on:

- GPU architecture
- kernels
- inference engine
- quantization format
- batch size
- workload
- model architecture

Therefore:

> **Always benchmark rather than assuming INT4 is automatically faster.**

---

# 14. Quantization Workflow

```text
Base Model
    |
    v
Choose precision
    |
    v
Quantize
    |
    v
Load on target GPU
    |
    v
Benchmark
    |
    +--> Quality
    +--> Latency
    +--> Throughput
    +--> Memory
    +--> Cost
    |
    v
Production
```

---

# 15. Quality vs Cost Trade-off

Think of quantization as an optimization problem:

```text
                 Quality
                   ^
                   |
          FP16     | *
                   |
          INT8     |    *
                   |
          INT4     |       *
                   |
                   +------------------> Cost
```

The exact curve varies by model and task.

The objective is not:

> "Use the lowest precision possible."

Instead:

> **Use the lowest precision that meets your quality and production SLOs.**

---

# 16. Architect's Cheat Sheet

| Concept | Meaning |
|---|---|
| Quantization | Represent values with fewer bits |
| FP16 | 16-bit floating-point format |
| BF16 | 16-bit brain floating-point format |
| INT8 | 8-bit integer representation |
| INT4 | 4-bit integer representation |
| Weight Quantization | Compress model weights |
| KV Quantization | Reduce KV-cache precision |
| PTQ | Quantize after training |
| QAT | Train with quantization effects considered |
| Weight-only Quantization | Quantize weights while keeping activations at higher precision |

---

## Final Mental Model

```text
                 LLM
                  |
            Model Weights
                  |
                  v
             Quantization
                  |
       +----------+----------+
       |          |          |
      INT8       INT4      FP16
       |          |          |
       +----------+----------+
                  |
                  v
          Smaller memory
                  |
                  v
          Better deployment
          economics/fit
                  |
                  v
              Benchmark
             /    |    \
        Quality Latency Cost
```

> **Quantization is fundamentally a memory–compute–quality trade-off. The architect's job is to find the lowest-cost precision that still satisfies the application's quality, latency, and reliability requirements.**
