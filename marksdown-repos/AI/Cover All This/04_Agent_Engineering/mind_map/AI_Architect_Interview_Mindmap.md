# AI Architect Interview — Mind Map for Quick Recall

> Source: [ai_architect_interview_notes.md](https://github.com/itsmekumarankur/personal-os/blob/master/marksdown-repos/AI/Cover%20All%20This/ai_architect_interview_notes.md)
>
> **Core idea:** Design production LLM systems by balancing latency, throughput, cost, answer quality, state/recovery, security, and observability.

```text
AI ARCHITECT: PRODUCTION LLM SYSTEMS
├── 1. Inference Engineering
│   ├── Lifecycle: Prefill → Decode
│   ├── TTFT = time until first token
│   ├── ITL = time between generated tokens
│   ├── E2E latency = total time until answer completes
│   ├── Throughput = requests/sec + tokens/sec
│   ├── Continuous batching → improve GPU utilization; protect wait-time SLOs
│   ├── KV cache → reuse attention state; faster decode but consumes GPU memory
│   ├── PagedAttention → manage KV-cache memory in blocks
│   ├── Speculative decoding → draft model guesses; target model verifies
│   └── Quantization → smaller/faster weights, with quality/runtime trade-offs
├── 2. Cost Engineering
│   ├── Measure cost per completed task, not just per model call
│   ├── Exact cache → same request; semantic cache → similar meaning, validate carefully
│   ├── Model routing → cheap/small model for simple tasks; stronger model for hard tasks
│   ├── Rate limits → cap demand
│   ├── Circuit breaker → stop repeated calls to failing dependency
│   └── Fallback → alternate model/provider or graceful degradation
├── 3. Production RAG
│   ├── Ingest → clean/chunk → embed/index → retrieve → rerank → generate
│   ├── RAG is a pipeline, not just a vector database
│   ├── Chunking: fixed-size / semantic / parent-child / hierarchical
│   ├── Embeddings → numeric representation of semantic meaning
│   ├── Query and document vectors must be compatible
│   └── Embedding-model migration usually requires re-embedding and index validation
├── 4. Agent Scalability & State
│   ├── Agent = controlled workflow: understand → tools → validate → respond
│   ├── Prefer simple workflows over unnecessary multi-agent complexity
│   ├── Checkpoint state → recover after crashes without repeating completed work
│   ├── Bound steps, retries, time, tokens, and cost
│   ├── Human approval for sensitive/high-impact actions
│   ├── Idempotent/reconcilable side effects → safe retries
│   └── Modular steps → easier testing, debugging, and maintenance
├── 5. Enterprise Security & Privacy
│   ├── Direct prompt injection: malicious user instructions
│   ├── Indirect prompt injection: malicious instructions in retrieved content
│   ├── Treat external content as untrusted; constrain tools and permissions
│   ├── Application enforces authorization/business rules; model does not grant access
│   ├── PII: redact or tokenize; control retention and access
│   ├── Secrets: secure storage; never expose API keys to the model
│   └── Tenant isolation across DB, RAG, caches, tools, and logs
└── 6. Observability & Day-2 Operations
    ├── System signals: latency, errors, throughput, GPU/memory, queue depth
    ├── AI signals: correctness, groundedness, retrieval quality, tool outcomes, safety
    ├── Trace full journey: request → retrieval → LLM → tools → final answer
    ├── OpenTelemetry → vendor-neutral telemetry/instrumentation
    ├── Langfuse → LLM calls, prompts, tokens, cost and traces
    ├── Arize Phoenix → inspect traces, retrieval and model behavior
    ├── Offline evaluation → prepared test set before release
    └── Online monitoring → production behavior after release
```

## 1. Inference: diagnose before optimizing

| Symptom | Investigate first |
|---|---|
| High TTFT, healthy ITL | Queueing, prompt length, retrieval/tool latency, prefill |
| Low TTFT, slow completion | Output length, decode throughput, memory bandwidth |
| High p95/p99 latency | Tail workload, queueing, long contexts, noisy neighbors, retries |
| GPU fits model but concurrency fails | KV cache, runtime buffers, temporary memory, active sequences/context length |
| Queue keeps growing | Bounded queue, backpressure, load shedding, admission control |

**Recall:** Prefill processes the input and builds the initial KV cache; decode generates output tokens sequentially. Track p50, p95, and p99 rather than averages alone.

## 2. Capacity and throughput

- Little’s Law intuition: `in-flight requests ≈ arrival rate × average time in system`.
- Example: 20 requests/sec × 2 seconds ≈ 40 requests in flight on average.
- This is not a safe concurrency limit by itself; GPU memory, request length, output length, and workload mix determine capacity.
- Excess traffic can create a feedback loop: queue growth → higher TTFT → client timeouts → retries → even more traffic.
- Use bounded queues, backpressure, admission control, rate limits, and load shedding.

## 3. Cost per task

```text
Total task cost
= all model calls
+ input/output tokens
+ retries
+ tool / retrieval overhead
+ any extra workflow steps
```

Cost levers:
1. Route by task complexity.
2. Cache only when correctness and freshness allow it.
3. Reduce unnecessary prompt/context and output tokens.
4. Bound agent loops and retries.
5. Monitor cost per completed task and per use case.

## 4. RAG mental model

```text
Documents → Clean / Chunk → Embed → Index
                                   ↑
User question → Embed / Search → Rerank → Context
                                            ↓
                                         LLM → Answer
```

- A vector database is one component, not the whole RAG system.
- Bad retrieval can produce a bad answer even when the model is functioning correctly.
- Chunk size and strategy affect context, recall, precision, and cost.
- After an embedding-model change, ensure query/document vector compatibility; re-embed and validate the index as needed.

## 5. Agent reliability pattern

```text
Request
  ↓
Workflow / state machine
  ↓
Step → Validate → Checkpoint → Next step
  ↓
Tool action (authorized, bounded, idempotent/reconcilable)
  ↓
Final validation → Response
```

For recovery after a worker crash:
1. Persist validated state transitions/checkpoints.
2. Resume from the last safe checkpoint.
3. Make side effects idempotent or reconcile their status.
4. Enforce step/time/token/cost limits.
5. Require human approval for sensitive actions.

## 6. Security: defense in depth

- Treat user input and retrieved documents as untrusted.
- Use least-privilege tool credentials and scoped data access.
- Enforce permissions and business rules in application/API/data layers.
- Protect PII with minimization, redaction/tokenization, access controls, and retention policies.
- Isolate tenants across every layer: databases, retrieval indexes, caches, tool calls, telemetry, and logs.
- Never assume a prompt or model refusal is an authorization boundary.

## 7. Observability and release safety

**Trace the complete request:** gateway → queue → retrieval → model → tools → validation → response.

Capture enough metadata to diagnose failures: model/prompt versions, retrieval results, tool status, latency, token counts, cost, and evaluation outcomes. Redact sensitive content.

Safe release loop:
1. Evaluate on a versioned golden dataset.
2. Compare quality, safety, latency, and cost by use case.
3. Test retrieval and tool behavior.
4. Shadow or canary the new version.
5. Monitor production traces and metrics.
6. Roll back when agreed thresholds are breached.
7. Add confirmed production failures to the evaluation set.

## Architect-level interview questions

### Q1. TTFT is high but ITL is healthy. What do you investigate?
Queueing, prompt length, retrieval/tool latency, and prefill before optimizing decode.

### Q2. Why can a model fit on a GPU but fail at production concurrency?
Weights are not the full memory footprint. KV cache, runtime buffers, temporary allocations, context length, and active sequences also consume memory.

### Q3. How do you recover an agent after a worker crash?
Persist validated state transitions, resume from a checkpoint, and make side effects idempotent or reconcilable.

### Q4. How do you prove a new model or prompt is better?
Use a versioned golden set, compare quality and safety by task, test retrieval/tool behavior, then shadow/canary with explicit rollback criteria.

### Q5. LLM spans are fast, but end-to-end latency is high. What next?
Inspect queueing, retrieval, tools, retries, serialization, networking, and post-processing; confirm trace boundaries cover the whole request.

## One-minute recall

- **Inference:** Prefill, decode, TTFT, ITL, throughput, queueing.
- **Efficiency:** batching, KV cache, speculative decoding, quantization.
- **Cost:** cost per task, caching, routing, bounded retries.
- **RAG:** ingest/chunk/embed/retrieve/rerank/generate; retrieval quality matters.
- **Agents:** checkpoint, bound execution, human approval, idempotency.
- **Security:** injection defense, least privilege, PII protection, tenant isolation.
- **Operations:** end-to-end traces, offline evaluation, online monitoring, canary, rollback.

## Self-test checklist

- [ ] Explain TTFT vs ITL and diagnose high TTFT.
- [ ] Explain why KV cache improves speed but reduces concurrency capacity.
- [ ] Explain why continuous batching needs queueing and latency controls.
- [ ] Estimate in-flight requests using arrival rate × time in system.
- [ ] Explain exact cache vs semantic cache and their correctness risks.
- [ ] Draw the full RAG pipeline and explain embedding migration.
- [ ] Explain agent checkpointing and safe retries for side effects.
- [ ] Explain why model output is not an authorization boundary.
- [ ] Distinguish offline evaluation from online monitoring.
- [ ] Describe a safe canary-and-rollback release process.
