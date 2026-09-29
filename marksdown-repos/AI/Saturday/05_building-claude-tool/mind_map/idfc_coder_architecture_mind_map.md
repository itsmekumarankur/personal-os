# 🧠 IDFC Coder — Architecture Mind Map

> **Recall:** `USER → EDGE → GATEWAY → QUEUE → GPU → STREAM`

## 1. Core Architecture

```text
Developer
   ↓
IDE / Web UI
   ↓
Route 53 → CloudFront → WAF → ALB
   ↓
API + Auth
   ↓
Prompt Gateway
   ├── Auth / RBAC
   ├── Rate Limit / Quota
   ├── Prompt Policy
   ├── Context Build
   └── Model / GPU Routing
   ↓
Redis → Kafka/SQS
   ↓
GPU Inference Cluster
   ↓
vLLM → 33B INT4
   ↓
Streaming Response
```

## 2. Context Engine

```text
Repository
   ↓
Context Engine
   ├── Relevant files
   ├── Symbols
   ├── Imports
   ├── Recent changes
   └── Developer prompt
   ↓
Context Window
```

> **Never blindly send the entire repository.**

## 3. Why Each Layer?

| Layer | Purpose |
|---|---|
| WAF | Protect web/API traffic |
| ALB | Distribute + health-aware routing |
| Gateway | Policy/control point |
| Redis | Rate limits, sessions, cache |
| Queue | Absorb bursts / decouple GPU |
| vLLM | Scheduling, batching, KV cache, streaming |

## 4. GPU Mental Model

```text
33B INT4
   ↓
~16.5 GB weights
   ↓
+ KV Cache
+ Activations
+ Runtime
+ Headroom
   ↓
~23 GB example footprint
```

> **GPU count ≠ user count.**

```text
Users
 ↓
DAU / concurrency
 ↓
Peak RPS
 ↓
Benchmark: RPS/GPU
 ↓
Required GPUs + HA headroom
```

## 5. vLLM

```text
Requests
   ↓
Scheduler
   ↓
Continuous Batching
   ↓
GPU
   ↓
Token Streams
```

## 6. Scaling & Failure

```text
Metrics
 ├── Queue depth
 ├── GPU utilization
 ├── TTFT
 ├── Tokens/sec
 ├── Active generations
 └── KV-cache utilization
        ↓
   Autoscaler
        ↓
 GPU scale out/in
```

```text
GPU fails → remove from router → serve from healthy GPUs → replace
AZ fails  → shift traffic → survive with spare capacity
```

## 7. Observability

```text
API     → RPS, latency, errors
GPU     → utilization, VRAM, temperature
LLM     → TTFT, tokens/sec, queue time, KV cache
```

## ⚡ 30-Second Recall

> **1. Context Engine sends relevant context.**
>
> **2. Gateway is the policy brain.**
>
> **3. Queue protects GPU capacity from bursts.**
>
> **4. vLLM drives efficient inference.**
>
> **5. GPU sizing comes from workload + benchmark, not user count.**
>
> **6. Design for GPU + AZ failure.**

### 🎯 Architect Question
> **"Where is the bottleneck: context, gateway, queue, GPU VRAM, inference throughput, or concurrency?"**
