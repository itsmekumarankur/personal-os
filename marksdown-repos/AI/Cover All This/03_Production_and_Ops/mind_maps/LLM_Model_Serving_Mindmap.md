# LLM Model Serving — Mind Map for Quick Recall

> **Core idea:** Training creates model weights; serving makes the model available to applications reliably and economically.

```text
LLM MODEL SERVING
├── 1. Request path
│   └── Client → WAF/API Gateway → Auth & limits → Model Gateway/Router
│       → Inference server → GPU/model → Response
├── 2. Model server responsibilities
│   ├── Load model and tokenize input
│   ├── Queue and schedule requests
│   ├── Batch requests; manage KV cache and GPU memory
│   ├── Run inference and decode tokens
│   └── Stream response; emit metrics/traces
├── 3. Performance
│   ├── Latency: time for a request
│   ├── Throughput: requests/sec or tokens/sec
│   ├── TTFT: time to first token
│   ├── TPOT: time per output token
│   └── E2E latency: total request-to-completion time
├── 4. Efficiency
│   ├── Batching → better GPU utilization, but may add waiting latency
│   ├── Continuous batching → admit/remove requests while others generate
│   ├── KV cache → reuse attention state across generated tokens
│   └── Quantization / parallelism can improve fit or throughput, with trade-offs
├── 5. Routing and scaling
│   ├── Small model for simple/cheap tasks; larger model for complex tasks
│   ├── Route by capability, latency, cost, tenant, region, availability
│   └── Scale using queue depth, GPU/memory use, tokens/sec, TTFT, active requests
├── 6. Reliability
│   ├── Timeouts, bounded retries, circuit breakers
│   ├── Fallback model/provider where appropriate
│   ├── Queue management and graceful degradation
│   └── Avoid retry storms and overload amplification
├── 7. Security
│   ├── Authentication, authorization, tenant isolation
│   ├── Rate limits, WAF, input/output validation
│   └── Prompt-injection controls, PII handling, audit logs
└── 8. Operations
    ├── Observe latency, errors, throughput, GPU/memory, queue depth
    ├── Observe tokens, cost/request, and output quality
    └── Define SLOs and test under realistic load
```

## Architecture sketch

```text
Users
  ↓
WAF / API Gateway ── auth, quotas, rate limits
  ↓
Model Gateway ────── model selection, routing, fallback
  ↓
Inference Servers ── batching, scheduling, KV cache, streaming
  ↓
GPU workers / model replicas
  ↓
Response

Cross-cutting: security + metrics + traces + logs + cost + quality evaluation
```

## Key trade-offs to remember

| Choice | Benefit | Trade-off |
|---|---|---|
| Larger batch | Better throughput / GPU use | Can increase individual latency |
| Streaming | Faster perceived response | Client must handle partial output |
| Bigger model | May improve capability | Higher latency and serving cost |
| More replicas | More capacity / resilience | Higher GPU cost |
| Retries | Can recover transient failures | Can worsen overload if unbounded |

## API Gateway vs Model Gateway

- **API Gateway:** security and API policy — authentication, authorization, rate limits, WAF.
- **Model Gateway:** AI-specific routing — model/provider choice, fallback, capability/cost routing.
- **Inference server:** executes model inference on available compute.

## Interview recall

**Question:** Can this model meet expected traffic and latency targets without making AI too expensive?

Answer in this order: traffic and SLOs → model/GPU memory fit → throughput and batching → scaling signals → failure strategy → cost per request → observability and load tests.

**One-line memory hook:** *A model is only production-ready when it can serve real traffic reliably, fast enough, and at acceptable cost.*

## Self-test

- [ ] Define serving, latency, throughput, TTFT, and TPOT.
- [ ] Explain why batching has a latency/throughput trade-off.
- [ ] Explain why CPU-only autoscaling signals are insufficient for GPU workloads.
- [ ] Separate API Gateway responsibilities from Model Gateway responsibilities.
- [ ] Describe what happens when the queue is overloaded or a GPU runs out of memory.
