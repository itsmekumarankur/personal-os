# LLM Model Serving & APIs — A 5-Minute AI Architect Guide

> **Goal:** Understand how a trained LLM becomes a production API and how to architect model serving for latency, throughput, scalability, reliability, and cost.

---

## 1. What Is Model Serving?

Training creates a model.

Serving makes that model available to applications.

```text
                 TRAINING
                    |
                    v
              Model Weights
                    |
                    v
             Model Registry
                    |
                    v
                 SERVING
                    |
                    v
               API Endpoint
                    |
                    v
              Applications
```

A simple definition:

> **Model serving is the infrastructure and software required to load a model, accept inference requests, execute the model, and return predictions.**

---

# 2. Basic LLM Serving Architecture

```text
                 User / App
                     |
                     v
              +-------------+
              | API Gateway |
              +-------------+
                     |
                     v
              +-------------+
              | Auth / Rate |
              | Limiting     |
              +-------------+
                     |
                     v
              +-------------+
              | Model Router|
              +-------------+
                     |
          +----------+----------+
          |                     |
          v                     v
    Model Server A        Model Server B
          |                     |
          v                     v
        GPU(s)                 GPU(s)
          |                     |
          +----------+----------+
                     |
                     v
                 Response
```

The model server is responsible for:

- loading the model
- tokenization
- batching
- GPU execution
- decoding
- streaming
- returning responses

---

# 3. Why Not Just Expose the Model Directly?

A production system needs more than:

```python
model.generate(prompt)
```

You need:

```text
                    API
                     |
          +----------+----------+
          |                     |
       Security             Reliability
          |                     |
    Authentication        Timeouts
    Authorization         Retries
    Rate limits           Circuit breakers
          |                     |
          +----------+----------+
                     |
                 Model Server
                     |
          +----------+----------+
          |                     |
      Performance          Observability
          |                     |
       Batching             Metrics
       Caching              Tracing
       Streaming            Logging
```

This is why model serving is a platform architecture problem.

---

# 4. Common API Pattern

A typical LLM API request looks conceptually like:

```text
POST /v1/chat/completions

{
  "model": "my-llm",
  "messages": [
    {
      "role": "user",
      "content": "Explain Kafka"
    }
  ],
  "temperature": 0.2,
  "max_tokens": 500
}
```

The server:

```text
Request
  |
  v
Validate
  |
  v
Authenticate
  |
  v
Select model
  |
  v
Tokenize
  |
  v
Inference
  |
  v
Decode
  |
  v
Response
```

Many modern inference servers expose OpenAI-compatible APIs, which makes application integration easier.

---

# 5. Streaming Responses

Without streaming:

```text
Request
   |
   |---------- wait ----------|
   |                           |
   v                           v
Request                     Full response
```

With streaming:

```text
Request
   |
   v
First token
   |
   v
token
   |
   v
token
   |
   v
token
   |
   v
...
```

This improves perceived responsiveness.

```text
User
 |
 | Request
 v
API
 |
 v
Model Server
 |
 +---- token 1 ---->
 |
 +---- token 2 ---->
 |
 +---- token 3 ---->
 |
 +---- token 4 ---->
```

Streaming is especially useful for chat applications.

---

# 6. Batching

Suppose four users send requests.

Without batching:

```text
Request A --> GPU
Request B --> GPU
Request C --> GPU
Request D --> GPU
```

With batching:

```text
A ---\
B ----+--> Batch --> GPU
C ----+
D ---/
```

Batching improves GPU utilization.

But large batches can increase latency.

Therefore:

```text
Batch size ↑
     |
     +--> Throughput often ↑
     |
     +--> GPU utilization ↑
     |
     +--> Individual latency may ↑
```

This is an important production trade-off.

---

# 7. Continuous Batching

Traditional batching waits for a batch to form.

LLM serving can use **continuous batching**.

Conceptually:

```text
Time --->

Request A: [==========]
Request B:     [=======]
Request C:       [=========]
Request D:           [=====]

GPU scheduler continuously
adds/removes requests.
```

This helps keep the GPU busy while different requests generate different numbers of tokens.

Modern LLM serving engines such as vLLM use sophisticated scheduling and memory-management techniques to improve serving efficiency.

---

# 8. Model Server Responsibilities

A production model server often manages:

```text
                Model Server
                     |
      +--------------+--------------+
      |              |              |
      v              v              v
   Tokenizer     Scheduler       GPU Runtime
                     |
                     v
              Batch Management
                     |
                     v
                 KV Cache
                     |
                     v
               Token Generation
```

It may also handle:

- request queues
- dynamic batching
- model loading
- GPU allocation
- streaming
- quantized models
- tensor parallelism
- metrics

---

# 9. Model Gateway / Router

Large platforms may serve multiple models.

```text
                  Client
                    |
                    v
              Model Gateway
                    |
       +------------+-------------+
       |            |             |
       v            v             v
    Small LLM    Large LLM    Specialized
                               Model
```

Routing can depend on:

- task
- latency requirement
- cost
- model capability
- tenant
- region
- availability

Example:

```text
Simple classification
        |
        v
    Small model

Complex reasoning
        |
        v
    Large model
```

This is often called **model routing**.

---

# 10. Autoscaling

LLM servers are expensive because GPUs are expensive.

A production platform needs capacity management.

```text
                 Traffic
                    |
                    v
              Load Balancer
                    |
          +---------+---------+
          |         |         |
          v         v         v
        GPU 1     GPU 2     GPU 3
          |
          v
      GPU utilization
          |
          v
       Scaling
```

Possible scaling signals:

- request queue depth
- GPU utilization
- tokens/sec
- TTFT
- active requests
- memory utilization

Traditional CPU autoscaling based only on CPU percentage is often insufficient for LLM workloads.

---

# 11. Latency and Throughput

Two critical metrics:

### Latency

How long does one request take?

```text
Request -----------------> Response
          2.5 seconds
```

### Throughput

How much work can the system process?

```text
1000 requests
       |
       v
requests/sec
tokens/sec
```

For LLMs, measure:

```text
TTFT  = Time To First Token

TPOT  = Time Per Output Token

E2E   = End-to-End Latency

TPS   = Tokens Per Second
```

A production SLO might therefore be expressed around:

```text
P95 TTFT
P95/P99 E2E latency
Output tokens/sec
Error rate
```

---

# 12. API Gateway vs Model Gateway

These are different concerns.

```text
Client
  |
  v
API Gateway
  |
  |-- Authentication
  |-- Authorization
  |-- Rate limiting
  |-- WAF
  |-- API policies
  |
  v
Model Gateway
  |
  |-- Model selection
  |-- Routing
  |-- Fallback
  |-- Provider selection
  |
  v
Model Server
  |
  v
GPU
```

The separation becomes valuable when the organization serves:

- multiple models
- multiple providers
- multiple teams
- multiple tenants
- multiple regions

---

# 13. Failure Handling

LLM inference is expensive and can fail.

Potential failures:

```text
Client
  |
  v
API Gateway
  |
  v
Model Router
  |
  +---- Model A unavailable
  |
  +---- GPU OOM
  |
  +---- Queue overloaded
  |
  +---- Timeout
  |
  +---- Provider unavailable
```

Possible strategies:

```text
Failure
  |
  +--> Retry
  |
  +--> Fallback model
  |
  +--> Fallback provider
  |
  +--> Queue
  |
  +--> Graceful degradation
```

Retries must be carefully controlled because blindly retrying expensive GPU requests can make overload worse.

---

# 14. Observability

An LLM serving platform should monitor at least:

```text
                Observability
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
   Technical      Cost           Quality
       |             |             |
   Latency       Tokens         Evaluation
   Errors        GPU cost       Feedback
   Throughput    Cost/request   Hallucination
   GPU usage
```

Important metrics:

- P50/P95/P99 latency
- TTFT
- TPOT
- input tokens
- output tokens
- requests/sec
- tokens/sec
- GPU utilization
- GPU memory
- queue depth
- error rate
- cost/request
- model quality metrics

---

# 15. Security

LLM APIs should be treated like any production API.

```text
              Internet
                  |
                  v
                WAF
                  |
                  v
             API Gateway
                  |
          +-------+-------+
          |               |
     Authentication    Rate Limit
          |               |
          +-------+-------+
                  |
                  v
             AI Platform
```

Consider:

- authentication
- authorization
- tenant isolation
- prompt injection defenses
- input validation
- output filtering
- secrets protection
- PII handling
- audit logging
- abuse prevention

---

# 16. LLM Serving Stack

A typical stack might look like:

```text
Application
     |
     v
API Gateway
     |
     v
AI / Model Gateway
     |
     v
Inference Server
     |
     +---- vLLM / similar engine
     |
     v
CUDA / GPU Runtime
     |
     v
GPU
     |
     v
LLM
```

The exact technology can vary.

The architecture is more important than memorizing a specific product.

---

# 17. Production Architecture

A more complete design:

```text
                         USERS
                           |
                           v
                    +-------------+
                    |     WAF     |
                    +-------------+
                           |
                           v
                    +-------------+
                    | API Gateway |
                    +-------------+
                           |
                    Auth / Rate Limit
                           |
                           v
                    +-------------+
                    | AI Gateway  |
                    | / Router    |
                    +-------------+
                      /     |     \
                     /      |      \
                    v       v       v
                Model A   Model B  External API
                  |         |
                  v         v
              +-----+   +-----+
              |GPU  |   |GPU  |
              +-----+   +-----+
                  \       /
                   \     /
                    v   v
                Observability
```

Cross-cutting platform components:

```text
+------------------------------------------------------+
| Security | Monitoring | Logging | Tracing | Cost     |
+------------------------------------------------------+
```

---

# 18. Key Architecture Questions

When designing LLM serving, ask:

### Capacity

```text
How many requests/sec?
How many tokens/sec?
How many concurrent users?
```

### Model

```text
Which model?
What parameter size?
What context length?
What quantization?
```

### GPU

```text
How much VRAM?
How many GPUs?
One GPU or multi-GPU?
```

### Latency

```text
Required TTFT?
Required P95/P99?
Streaming required?
```

### Cost

```text
Cost/request?
GPU utilization?
Idle GPU capacity?
```

### Reliability

```text
What happens when the GPU fails?
What happens when the model is overloaded?
Is there a fallback?
```

---

# 19. The AI Architect's Mental Model

Think of LLM serving as five layers:

```text
                 LLM Serving
                      |
       +--------------+--------------+
       |              |              |
    Traffic         Model          Compute
    Layer           Layer           Layer
       |              |              |
    Gateway        Router         GPU
    Auth           Version        Runtime
    Rate Limit     Registry       Memory
       |              |              |
       +--------------+--------------+
                      |
                 Observability
                      |
             +--------+--------+
             |        |        |
           Cost    Quality   Reliability
```

---

# 20. Architect's Cheat Sheet

| Concept | What it solves |
|---|---|
| Model Server | Runs inference |
| API Gateway | Secures and governs API traffic |
| Model Gateway | Routes requests to models/providers |
| Batching | Improves GPU utilization |
| Continuous Batching | Efficiently handles variable-length generation |
| KV Cache | Avoids recomputing attention state |
| Streaming | Improves perceived responsiveness |
| Quantization | Reduces memory/cost |
| Tensor Parallelism | Splits model computation across GPUs |
| Autoscaling | Matches capacity to demand |
| Rate Limiting | Protects the platform |
| Fallback | Improves resilience |
| Observability | Measures performance, cost, and quality |

---

## Final Mental Model

> **Model serving is the bridge between an AI model and a production application.**

The model itself is only one component.

A production-grade LLM platform must solve:

```text
             MODEL
               |
               v
      +------------------+
      | How do we serve? |
      +------------------+
               |
       +-------+-------+
       |       |       |
       v       v       v
    Latency Throughput Cost
       |       |       |
       +-------+-------+
               |
               v
        Reliability
               |
               v
         Observability
               |
               v
           Security
```

For an AI Architect, the key skill is connecting **model characteristics → GPU requirements → serving strategy → API architecture → SLOs → cost**.
