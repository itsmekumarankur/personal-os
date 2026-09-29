# 🧠 Quantization — Mind Map

> **Mental Model:** `Fewer bits → Less memory → Lower infrastructure cost → Possible quality loss`

## 1. What Is Quantization?

```text
FP32 → 32 bits
FP16 → 16 bits
BF16 → 16 bits
INT8 →  8 bits
INT4 →  4 bits
```

```text
Precision ↓
   ↓
Memory ↓
   ↓
Infrastructure requirement ↓
```

## 2. Why Quantize?

Approximate weight storage for 70B parameters:

```text
FP32 ≈ 280 GB
FP16 ≈ 140 GB
INT8 ≈  70 GB
INT4 ≈  35 GB
```

Real serving memory also includes:

```text
Weights + KV Cache + Activations + Runtime overhead
```

## 3. Core Trade-off

```text
Higher Precision
 ├── Quality potentially ↑
 └── Memory ↑

Lower Precision
 ├── Efficiency ↑
 ├── Memory ↓
 └── Quality may ↓
```

Impact depends on model, method, calibration data and workload.

## 4. Weight Quantization

```text
FP16 Weights
     ↓
 Quantization
     ↓
 INT8 / INT4
     ↓
Smaller representation
```

## 5. Production Benefit

```text
Large Model
    ↓
Quantize
    ↓
Smaller Model
    ↓
Fewer GPUs potentially needed
    ↓
Cost / complexity ↓
```

Can affect:
- Infrastructure cost
- Latency
- Deployment complexity
- Capacity
- Concurrency

## 6. Quantization Is Not Free

```text
Original weights
      ↓
Quantization
      ↓
Approximation
      ↓
Potential quality loss
```

Possible impact:
- Reasoning quality
- Factual accuracy
- Numerical precision
- Task accuracy
- Output stability

> **Always benchmark.**

## 7. PTQ vs QAT

### Post-Training Quantization
```text
Train → Quantize → Evaluate
```

### Quantization-Aware Training
```text
Training
   ↓
Account for quantization
   ↓
Optimize model
   ↓
Quantized deployment
```

QAT may preserve quality better in some cases, but adds training complexity.

## 8. Weight-Only Quantization

```text
Weights     → INT4
Activations → FP16 / BF16
```

## ⚡ 30-Second Recall

> **Quantization = trade precision for efficiency.**
>
> **Memory ↓, GPU requirement ↓, cost ↓ — but quality can ↓.**
>
> **Benchmark before production.**

### 🎯 Architect Question
> **"What quality are we sacrificing, and how much infrastructure cost are we actually saving?"**
