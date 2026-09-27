# IDFC Coder — Architecture Interview Notes

**Assumed workload:**
- 10,000 registered developers
- ~2,000 daily active users
- ~500 peak concurrent users
- ~100 AI requests/sec peak
- Average generation: 300–800 output tokens
- Context: 2K–8K tokens
- 33B coding model, INT4 quantization

---

## 1. The Architecture I Would Present

```
                         AWS CLOUD
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  Developer                                                    │
│      │ Prompt                                                 │
│      ▼                                                        │
│  ┌───────────────┐                                            │
│  │ IDE / Web UI  │                                            │
│  │ IDFC Coder    │                                            │
│  └───────┬───────┘                                            │
│          │ HTTPS                                              │
│          ▼                                                    │
│  ┌─────────────────┐                                          │
│  │ Route 53        │                                          │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ CloudFront      │                                          │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ AWS WAF         │                                          │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ ALB             │                                          │
│  └────────┬────────┘                                          │
│           │                                                   │
│      ┌────┴─────────────────────────────┐                     │
│      ▼                                  ▼                     │
│ ┌──────────────┐                  ┌───────────────┐           │
│ │ API Service  │                  │ Auth Service  │           │
│ │ ECS / EC2    │                  │ SSO / IdP     │           │
│ └──────┬───────┘                  └───────────────┘           │
│        ▼                                                      │
│ ┌──────────────────┐                                          │
│ │ Prompt Gateway   │                                          │
│ │ - validation     │                                          │
│ │ - authorization  │                                          │
│ │ - rate limit     │                                          │
│ │ - prompt policy  │                                          │
│ │ - context build  │                                          │
│ └────────┬─────────┘                                          │
│          ▼                                                    │
│ ┌──────────────────┐                                          │
│ │ Redis            │                                          │
│ │ cache / limits   │                                          │
│ └──────────────────┘                                          │
│          ▼                                                    │
│ ┌──────────────────┐                                          │
│ │ Kafka / SQS      │                                          │
│ │ Request Queue    │                                          │
│ └────────┬─────────┘                                          │
│          ▼                                                    │
│ ┌──────────────────────────────────────────┐                  │
│ │          GPU INFERENCE CLUSTER           │                  │
│ │  ┌────────────┐ ┌────────────┐           │                  │
│ │  │ GPU Node 1 │ │ GPU Node 2 │           │                  │
│ │  │ L4 24GB    │ │ L4 24GB    │           │                  │
│ │  │ vLLM       │ │ vLLM       │           │                  │
│ │  │ 33B INT4   │ │ 33B INT4   │           │                  │
│ │  └────────────┘ └────────────┘           │                  │
│ │  ┌────────────┐ ┌────────────┐           │                  │
│ │  │ GPU Node 3 │ │ GPU Node 4 │           │                  │
│ │  │ L4 24GB    │ │ L4 24GB    │           │                  │
│ │  │ vLLM       │ │ vLLM       │           │                  │
│ │  └────────────┘ └────────────┘           │                  │
│ └──────────────────────┬───────────────────┘                  │
│                        ▼                                      │
│                Streaming response                             │
│                        ▼                                      │
│                    Developer                                  │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Request Flow Walkthrough

### Step 1 — Developer Sends Prompt

Example prompt: *"Create a REST API in Go for fetching mutual fund holdings. Use Redis caching and MongoDB."*

```json
{
  "user_id": "12345",
  "repository": "wealth-api",
  "language": "go",
  "prompt": "Create a REST API...",
  "files": ["holding.go", "repository.go", "handler.go"],
  "context": { "branch": "feature/mf-holdings" }
}
```

**Don't send the entire repository blindly.** Instead:

```
Repository
     │
     ▼
Context Engine
     │
     ├── relevant files
     ├── symbols
     ├── imports
     ├── recent changes
     └── developer prompt
             │
             ▼
       Context Window
```

### Step 2 — Authentication (Edge)

```
Developer → Route 53 → CloudFront → WAF → ALB → Auth
```

### Step 3 — WAF

WAF = security guard for web/API traffic. Decides: *"Is this request safe enough to enter the application?"*

```
INTERNET → CloudFront → WAF → Application
                          🛡️
```

### Step 4 — ALB

ALB = traffic manager. Distributes traffic across servers, checks health, routes by URL/path.

```
                     ALB
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       API-01      API-02      API-03
       EC2/ECS     EC2/ECS     EC2/ECS
```

**Don't size EC2 based on 10,000 users.** Size based on:
```
Peak requests/sec + CPU utilization + memory + network + availability requirement
```

Reasonable starting topology:
```
ALB → AZ-A (4 API nodes) / AZ-B (4) / AZ-C (4) = 12 API instances
Autoscaling: Min=6, Desired=12, Max=30
```
Exact number must come from load testing.

### Step 5 — Prompt Gateway

One of the most important components.

```
                 API
                  │
                  ▼
          ┌───────────────┐
          │ Prompt Gateway│
          └───────┬───────┘
       ┌──────────┼───────────┐
       ▼          ▼           ▼
 Authentication  Policy     Rate Limit
       └──────────┼───────────┘
                  ▼
            Context Engine
```

Decides:
```
Can this user make the request?
       ▼
Is the request allowed?
       ▼
How much context should we send?
       ▼
Which model should process it?
       ▼
Which GPU pool?
```

### Step 6 — Redis

```
                  Redis
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   Rate Limits   Sessions      Cache
```
Example: `user:12345:requests → 50 requests/minute`. Cache `Prompt → response` for deterministic/common requests.

### Step 7 — Queue

Where the architecture becomes resilient.

```
API Servers → Request Queue (Kafka / SQS) → Inference Router
```

Why? Because 500 simultaneous requests can't all hit GPU capacity at once.

---

## 3. GPU Capacity & Inference Engine

### The GPU Architecture

For the 33B model:
```
FP16:  33B × 2 bytes   ≈ 66 GB
INT8:  33B × 1 byte    ≈ 33 GB
INT4:  33B × 0.5 byte  ≈ 16.5 GB
```

**16.5 GB is NOT the actual production requirement** — you also need KV cache, activations, runtime and headroom:

```
Weights             ~17 GB
KV cache             ~2 GB
Activations          ~1 GB
Runtime              ~2 GB
Headroom             ~1 GB
                     -------
Total                ~23 GB
```

### GPU Cluster

```
                  GPU INFERENCE CLUSTER
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          AZ-A           AZ-B          AZ-C
       ┌─────────┐     ┌─────────┐    ┌─────────┐
       │ L4 #01  │     │ L4 #03  │    │ L4 #05  │
       │ 24 GB   │     │ 24 GB   │    │ 24 GB   │
       │ vLLM    │     │ vLLM    │    │ vLLM    │
       └─────────┘     └─────────┘    └─────────┘
       ┌─────────┐     ┌─────────┐    ┌─────────┐
       │ L4 #02  │     │ L4 #04  │    │ L4 #06  │
       │ 24 GB   │     │ 24 GB   │    │ 24 GB   │
       │ vLLM    │     │ vLLM    │    │ vLLM    │
       └─────────┘     └─────────┘    └─────────┘
```

Initial production sizing could be: 6 GPU nodes + 1 LLM replica per GPU node = 6 model replicas.

**NOTE:** You cannot derive the correct number of GPUs from "10,000 users." GPU count is a consequence of workload, VRAM and concurrency — not user count.

### How I Would Actually Calculate 6 GPUs

```
10,000 registered users
       ▼
2,000 daily active
       ▼
500 peak concurrent
       ▼
100 requests/sec peak
       ▼
LLM benchmark
       ▼
X requests/sec/GPU
       ▼
Required GPU count
```

**Example A — 20 concurrent generations per GPU:**
```
500 concurrent / 20 per GPU = 25 GPUs
+ HA headroom (×1.2) = ~30 GPUs
```

**Example B — 80 concurrent requests per GPU:**
```
500 / 80 ≈ 7 GPUs
+ redundancy ≈ 10 GPUs
```

> An architect should never say: *"10K users means 10 GPUs."*

### The Inference Layer

```
               GPU EC2
          ┌───────┴────────┐
          ▼                ▼
        Linux           NVIDIA Driver
          └───────┬────────┘
                  ▼
              CUDA → PyTorch → vLLM
                              │
                    ┌─────────┴────────┐
                    ▼                  ▼
                 Scheduler         KV Cache
                    └────────┬────────┘
                             ▼
                        33B INT4 LLM
```

**vLLM handles:** request scheduling, continuous batching, KV-cache management, token generation, GPU utilization, streaming.

### What Happens Inside vLLM

Instead of processing requests A→B→C→D serially, the engine batches:

```
                 vLLM
          ┌────────┼─────────┐
          ▼        ▼         ▼
        Req A    Req B     Req C
          └────────┼─────────┘
                   ▼
             GPU execution
                   ▼
             Token streams
```

---

## 4. Model Storage & Deployment

### Model Storage

Don't store the 33B model inside the container image. Use:

```
                    S3
                     │ model artifact
                     ▼
              Model Registry
                     ▼
                GPU startup
                     ▼
              Local NVMe/EBS
                     ▼
                  vLLM
```

S3 layout:
```
S3/
 ├── model-v1/
 ├── model-v2/
 ├── tokenizer/
 └── configuration/
```

Deployment flow:
```
New Model → S3 → Validation → Benchmark → Security scan → Canary → Production
```

### Model Deployment (CI/CD)

```
Developer → Git → CI/CD
                    ├── Unit tests
                    ├── Security scan
                    ├── Container scan
                    ├── Model validation
                    ├── Performance benchmark
                    └── Integration tests
                            ▼
                        Container
                            ▼
                       ECR Registry
                            ▼
                       Deployment
                            ▼
                       GPU Cluster
```

### Kubernetes / EKS Version

Use **EKS** for the inference platform rather than manually managing GPU EC2 instances.

```
                         EKS
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          AZ-A          AZ-B          AZ-C
        ┌────────┐   ┌────────┐   ┌────────┐
        │ GPU    │   │ GPU    │   │ GPU    │
        │ Nodes  │   │ Nodes  │   │ Nodes  │
        └───┬────┘   └───┬────┘   └───┬────┘
            ▼            ▼            ▼
         vLLM Pod     vLLM Pod     vLLM Pod
            └────────────┼────────────┘
                         ▼
                     33B LLM
```

**EKS Control Plane:** deployment, scheduling, health checks, rolling update, node management.
**GPU Node:** NVIDIA GPU → vLLM Pod.

---

## 5. Scaling & Failure Handling

### Autoscaling

**CPU autoscaling alone is wrong for LLM workloads.** You care about:

```
Queue depth
GPU utilization
Tokens/sec
Request latency
Time-to-first-token
Active generations
KV-cache utilization
```

```
                    Metrics
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Queue depth     GPU usage       TTFT
        └──────────────┼──────────────┘
                       ▼
                  Autoscaler
                       ▼
                 GPU Node Count
             ┌─────────┴─────────┐
             ▼                   ▼
         Scale Out            Scale In
```

Example thresholds:
```
Queue depth < 20   → 6 GPUs
Queue depth > 100  → 10 GPUs
Queue depth > 250  → 16 GPUs
```

### What If One GPU Dies?

Classic CTO/architect question.

```
                 Inference Router
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      GPU-01         GPU-02         GPU-03
        │              │              │
       OK              X              OK
```

```
GPU-02 unhealthy → Remove from routing → Requests → GPU-01 / GPU-03 → Auto-replace GPU-02
```

> **Never make one GPU a single point of failure.**

### What If the Whole AZ Fails?

```
                 Router
        ┌───────────┼───────────┐
        ▼           ▼           ▼
       AZ-A        AZ-B        AZ-C
        │           │           │
      GPU ×        GPU ✓       GPU ✓
```
Traffic shifts to AZ-B and AZ-C. Maintain enough spare capacity to survive an AZ failure.

---

## 6. Observability

Don't only monitor `CPU = 50%`. For LLM infrastructure:

```
                    OBSERVABILITY
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       API Layer       GPU Layer        LLM Layer
          ├─ RPS          ├─ GPU %         ├─ TTFT
          ├─ latency      ├─ VRAM          ├─ tokens/sec
          ├─ errors       ├─ temperature   ├─ queue time
          └─ 5xx          └─ utilization   ├─ KV cache
                                           └─ generation time
```

Useful production dashboard:
```
IDFC CODER — PRODUCTION DASHBOARD

Requests/sec                 87
Active users                421
Queue depth                  32

P50 latency               1.2 sec
P95 latency               4.8 sec
P99 latency              10.3 sec

TTFT                       0.9 sec
Tokens/sec/GPU              65

GPU utilization             82%
GPU VRAM                    78%

Error rate                 0.12%
5xx rate                   0.03%

Healthy GPUs                  28
Total GPUs                   30
```

---

## Key Interview Takeaways

1. **Context Engine > blind repo dump.** Send relevant files, symbols, imports, recent changes.
2. **Edge security chain:** Route 53 → CloudFront → WAF → ALB → Auth.
3. **Size EC2 on peak RPS, not registered users.** Use load testing; autoscale 6→12→30.
4. **Prompt Gateway is the policy brain:** auth, policy, rate limit, context build, model routing.
5. **Redis** for rate limits, sessions, cache.
6. **Queue (Kafka/SQS)** decouples API from GPU to survive burst traffic.
7. **INT4 33B ≈ 16.5 GB weights, but ~23 GB real footprint** (KV cache + activations + runtime + headroom).
8. **Never say "10K users = 10 GPUs."** Derive GPU count from concurrency benchmarking.
9. **vLLM enables continuous batching** — the core of GPU efficiency.
10. **EKS over manual EC2** for GPU fleet management.
11. **Autoscale on queue depth / TTFT / GPU utilization,** never CPU alone.
12. **Design for GPU and AZ failure** — no single point of failure.
13. **Observability must cover API + GPU + LLM layers** (TTFT, tokens/sec, KV cache, VRAM).
