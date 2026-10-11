# AI Architect Interview Notes: Production LLM Systems

> **Purpose:** Interview-focused notes on the engineering decisions, failure modes, trade-offs, and design principles that matter when building production AI systems.  
> **Scope:** Inference engineering, cost engineering, RAG, agent state, security, and observability.  
> **Approach:** Prioritize explanations that demonstrate architectural judgment over lists of tools or definitions.

---

## 1. Inference Engineering: Serving, Throughput, and Latency

### 1.1 Understand the inference lifecycle

Autoregressive LLM inference has two broad phases:

- **Prefill:** Processes the input prompt and builds the initial key-value (KV) cache. It can parallelize computation across prompt tokens.
- **Decode:** Generates output tokens sequentially. Each step uses the existing context and extends the KV cache.

This distinction matters because a request can be slow to start, slow to stream, or both.

| Metric | Meaning | Typical causes of degradation |
|---|---|---|
| **Time to First Token (TTFT)** | Time from request submission to the first generated token | Queueing, long prompts, retrieval/tool delays, slow prefill |
| **Inter-Token Latency (ITL)** | Time between successive generated tokens | Decode bottlenecks, memory bandwidth, GPU contention |
| **End-to-end latency** | Time until the complete answer is available | LLM latency plus retrieval, tools, orchestration and post-processing |
| **Throughput** | Work completed per unit time; measure requests/sec and tokens/sec separately | Insufficient capacity, poor batching, memory or compute limits |

A useful approximation for a streaming response is:

\[
T_{\text{total}} \approx TTFT + (N-1)\times ITL
\]

where \(N\) is the number of output tokens and ITL is the average interval between tokens. The exact measurement boundary must be defined consistently.

**Interview insight:** If TTFT is high but ITL is healthy, investigate queueing, prompt length, retrieval and prefill before optimizing decode. If TTFT is low but completion is slow, investigate output length, decode throughput and memory bandwidth.

Measure **p50, p95 and p99**, not only averages. A system can have a good average and still provide a poor experience for a meaningful fraction of users.

### 1.2 Throughput, concurrency and queueing

Throughput and latency are related, but they are not interchangeable. A service may handle many short requests per second while struggling with fewer requests that have long prompts and long outputs.

Little's Law gives a useful queueing relationship:

\[
L = \lambda W
\]

- \(L\): average number of requests in the system
- \(\lambda\): average arrival rate
- \(W\): average time in the system

If a service receives 20 requests/second and average time in the system is 2 seconds, approximately 40 requests are in flight on average. This is not a safe concurrency limit; memory, GPU capacity and workload distribution still determine the practical limit.

**Failure pattern:** Excess traffic grows the queue, increases TTFT, causes client timeouts, triggers retries and can create a retry storm.

**Architectural response:** Use bounded queues, admission control, backpressure, deadlines, load shedding and capacity planning. A longer queue alone does not fix insufficient serving capacity.

### 1.3 Continuous batching

Traditional static batching can leave GPU capacity unused when requests in the same batch finish at different times. **Continuous batching** lets the scheduler reconsider the active batch between generation iterations: completed requests leave and new requests can enter when capacity permits.

**Benefits**
- Better GPU utilization and aggregate token throughput.
- Less idle time from variable output lengths.
- Better support for concurrent streaming requests.

**Trade-offs**
- Scheduling is more complex.
- Long prompts can compete with ongoing decode work.
- Poor admission policies can increase tail latency.
- Fairness between tenants and request priorities needs explicit design.

**Interview insight:** Optimize against the workload's SLOs, not maximum tokens/second alone. A throughput improvement that worsens p99 latency beyond the agreed SLO is not a successful optimization.

### 1.4 KV cache and PagedAttention

The **KV cache** stores attention keys and values for prior tokens. It avoids repeatedly recomputing historical attention representations during autoregressive generation. The cache improves decode efficiency but consumes memory.

A useful approximate KV-cache memory formula for a conventional decoder-only transformer is:

\[
M_{\text{KV}} \approx 2 \times L \times S \times H_{KV} \times D_H \times B
\]

Where:
- \(L\): number of transformer layers
- \(S\): cached sequence length
- \(H_{KV}\): number of key/value heads
- \(D_H\): dimension per head
- \(B\): bytes per cache element
- Factor 2: keys and values

This is an estimate; architecture, cache precision, parallelism and implementation details change actual usage.

**Key distinction:** Model-weight memory and KV-cache memory are separate budgets. A model can fit on a GPU but still run out of memory at the desired context length and concurrency.

**PagedAttention**, associated with vLLM, manages KV cache in blocks rather than requiring each sequence's cache to occupy one large contiguous allocation. This can reduce fragmentation and improve memory utilization, particularly for variable-length concurrent requests. It does not eliminate finite memory limits or long-context compute costs.

**Serving-engine choice:** Evaluate the target model, GPU, context distribution, concurrency, streaming behavior, operational support and SLOs. Do not choose an engine from a single benchmark.

### 1.5 Speculative decoding

Speculative decoding uses a smaller **draft model** to propose multiple tokens, then a larger **target model** verifies them. With a suitable verification algorithm, the method can preserve the target model's intended output distribution while reducing the number of sequential target-model decoding steps.

It works best when:
- The draft model is cheap.
- Proposed tokens have a high acceptance rate.
- Target-model verification is efficient.
- Decode is the actual bottleneck.

It may provide little benefit when proposals are frequently rejected or the workload is dominated by queueing or prefill.

**Do not confuse it with model routing:** routing chooses a model for a request; speculative decoding uses draft-and-verify within generation.

### 1.6 Quantization: BF16, FP8 and INT4

Quantization lowers the numerical precision used for weights, activations or cache values to reduce memory use and potentially improve speed.

| Format | Approximate raw storage/value | Main consideration |
|---|---:|---|
| BF16 | 2 bytes | Strong baseline with broad dynamic range; more memory |
| FP8 | 1 byte | Can improve memory bandwidth and throughput on supported hardware |
| INT4 | 0.5 byte | Very compact weights, but quality and kernel efficiency require validation |

These are raw representation sizes, not full deployment footprints. Metadata, scales, unquantized layers, runtime buffers and KV cache add overhead.

For a hypothetical 70-billion-parameter model, raw weight storage is roughly 140 GB in BF16, 70 GB in FP8, or 35 GB at 4 bits per parameter, using decimal units. Actual memory needs are higher.

**Decision principle:** Choose the lowest-cost configuration that meets quality, latency and reliability SLOs. Benchmark with representative prompts, output lengths, concurrency and task-specific evaluations. A smaller format is not automatically faster; hardware and kernel support matter.

### 1.7 A disciplined inference optimization process

1. Establish a baseline with realistic traffic.
2. Measure TTFT, ITL, output-token throughput, p95/p99 latency and GPU memory.
3. Separate queueing, prefill, decode and application overhead.
4. Tune batching and admission control.
5. Evaluate quantization and speculative decoding where appropriate.
6. Re-run quality, safety and load tests.
7. Compare cost per successful task—not just raw throughput.

---

## 2. Cost Engineering and Token Economics

### 2.1 Measure cost per task, not just per model call

A basic token-priced inference estimate is:

\[
C_{\text{request}} =
\frac{T_{\text{in}}P_{\text{in}}+T_{\text{out}}P_{\text{out}}}{10^6}
\]

where token counts are multiplied by the relevant price per million tokens. Use the provider's actual pricing, including any separate cached-input or reasoning-token rates.

The visible user question may be a small part of the total input. System instructions, conversation history, retrieved documents, tool outputs and agent planning calls can dominate token usage.

**Measure:**
- Cost per model call.
- Cost per completed user task.
- Input/output tokens by workflow and tenant.
- Retry and agent-loop overhead.
- Cache savings.
- Cost by model and feature.

A multi-step agent can make several LLM calls for one user request. Cost controls should therefore include per-request model-call, token, step, time and monetary budgets.

### 2.2 Exact cache versus semantic cache

**Exact caching** reuses a response when a normalized key and all relevant context match. It is predictable when keys include the required model, prompt, tenant, authorization and data-version context.

**Semantic caching** finds prior queries with similar meanings, often through embeddings. It can improve hit rates for paraphrased questions, but can return an answer that is similar in wording yet wrong for the current question.

Example:
- “What is the maximum withdrawal limit?”
- “What is the minimum withdrawal limit?”

These are semantically related but require different answers.

**Safe design**
1. Check an exact cache first.
2. Use semantic caching only for eligible, stable answer classes.
3. Apply tenant, identity, authorization and freshness checks before reuse.
4. Use a validated similarity threshold and consider ambiguity.
5. Version entries when prompts, policies, models or knowledge sources change.
6. Avoid shared semantic caching for personalized or sensitive answers unless isolation and correctness can be guaranteed.

A vector similarity score is not proof that two questions are factually equivalent. For changing financial data, retrieve from the source of truth.

### 2.3 Model routing and cascades

A model router chooses a model based on task complexity, quality requirements, latency, cost and availability.

Good candidates for smaller models or deterministic logic include intent classification, language detection, fixed-schema extraction and bounded summarization. Complex synthesis may need a stronger model. Sensitive operations require authorization and business logic regardless of model size.

**Routing approaches**
- **Rules:** predictable and auditable; less flexible.
- **Classifier/SLM:** handles varied language; classification errors can misroute work.
- **Cascade:** try a cheaper path and escalate if validation fails; adds latency and relies on useful escalation criteria.

Track routing accuracy, task success by model, escalation rate, cost per successful task, latency and safety outcomes. Do not optimize only for the percentage of requests sent to the smallest model.

### 2.4 Rate limits, circuit breakers and fallbacks

Rate-limit at the appropriate boundaries using requests, tokens, concurrency and spend:
- API gateway for ingress protection.
- Tenant quota layer for fairness.
- Orchestrator for agent budgets.
- Inference service for GPU capacity.
- Provider adapter for vendor quotas.

A **circuit breaker** stops repeatedly calling a failing dependency:
- **Closed:** calls proceed.
- **Open:** calls are rejected or redirected.
- **Half-open:** limited test calls determine whether recovery has occurred.

A fallback hierarchy may include a primary deployment, an alternate region/provider, a smaller model for supported tasks, or a deterministic graceful-degradation response.

**Critical safeguards**
- Use end-to-end deadlines.
- Apply bounded retries with exponential backoff and jitter.
- Respect provider retry guidance.
- Avoid retrying non-idempotent side effects blindly.
- Prevent fallback storms.
- Preserve the same security and safety policy across providers.
- Do not bypass a safety refusal merely by switching to a less restrictive model.

---

## 3. Production RAG Architecture

### 3.1 RAG is a pipeline, not a vector database

Retrieval-Augmented Generation (RAG) retrieves external evidence and supplies it to a model for answer generation. It is useful for enterprise knowledge, frequently updated content and traceable sources. It does **not** guarantee correctness: retrieval may miss evidence, find misleading passages or expose unauthorized data, and the model may still misinterpret retrieved content.

Separate the system into two pipelines.

**Ingestion**
1. Connect to approved sources.
2. Parse text, tables, headings and page structure.
3. Normalize and deduplicate.
4. Preserve provenance and access-control metadata.
5. Chunk documents.
6. Generate embeddings.
7. Index dense vectors and lexical text.
8. Validate and publish a versioned index.

**Online query**
1. Authenticate and resolve trusted authorization scope.
2. Normalize the query.
3. Retrieve candidates using dense and/or lexical search.
4. Merge candidate lists.
5. Rerank candidates.
6. Validate authorization, freshness and relevance.
7. Construct a bounded context.
8. Generate, validate and cite the answer.

Index publication should avoid exposing partially updated or inconsistent data. Deletions and access revocations must propagate to the index.

### 3.2 Chunking strategies

| Strategy | Benefit | Risk |
|---|---|---|
| Fixed-size chunks | Simple and predictable | May split concepts, tables or definitions |
| Semantic chunks | Aligns with topic boundaries | More complex; variable sizes |
| Parent-child chunks | Small chunks support retrieval while parent context restores meaning | Context expansion increases token cost |
| Hierarchical chunks | Supports document → chapter → section → paragraph retrieval | More complex indexing and retrieval logic |

Chunk size and overlap are workload-specific; there is no universal best value. Evaluate with representative questions and retrieval metrics.

Preserve document ID, chunk ID, parent/section ID, tenant and ACL metadata, version, content hash, source location and embedding version.

### 3.3 Embeddings and embedding-model migrations

Embeddings represent text as vectors so semantically related text can be retrieved. Query and document vectors must be compatible.

Distinguish:
- **Data drift:** the documents or queries change.
- **Embedding-model change:** the vector representation changes.
- **Index inconsistency:** query and document vectors use incompatible configurations.

A safe migration:
1. Build a representative retrieval evaluation set.
2. Record baseline Recall@k, MRR, nDCG and downstream answer quality.
3. Build a separate index with the new embedding model.
4. Re-embed the corpus consistently.
5. Compare quality, latency, cost and memory.
6. Shadow or canary the new index.
7. Switch traffic and retain rollback capability.

Do not change the query embedding model while leaving an incompatible document index in place.

### 3.4 Dense search, BM25 and hybrid retrieval

**Dense retrieval** uses vector similarity. It can handle paraphrases and semantic relationships but may miss exact identifiers or retrieve related-but-wrong content.

**BM25** is a lexical ranking method that scores documents using query-term matching, term frequency and inverse document frequency. It is useful for product codes, error messages, policy identifiers and exact terminology, but may miss relevant passages with different wording.

**Hybrid search** combines both candidate sets. Reciprocal Rank Fusion (RRF) is one way to combine rankings:

\[
RRF(d)=\sum_{r\in R}\frac{1}{k+\operatorname{rank}_r(d)}
\]

where \(R\) is the set of rankings and \(k\) is a smoothing constant. RRF combines ranks without assuming dense and sparse raw scores are on the same scale.

### 3.5 Cross-encoder reranking

A bi-encoder embeds queries and documents separately, making large-scale candidate retrieval efficient. A cross-encoder scores a query-document pair jointly and is typically used to rerank a smaller candidate set.

A common pattern is:
1. Retrieve dozens or hundreds of candidates.
2. Score candidates with a reranker.
3. Keep the most relevant evidence that fits the context budget.

Reranking can improve ordering, but it cannot recover a relevant document that the first-stage retriever never retrieved. Evaluate end-to-end answer quality, not reranker scores alone.

### 3.6 Enterprise tenancy and RBAC

A vector search result is not automatically authorized for the current user. Tenant and document permissions must be derived from trusted identity and policy services—not from model-generated filters.

**Secure retrieval pattern**
1. Authenticate the principal.
2. Resolve tenant, role and allowed scopes using trusted services.
3. Apply ACL/tenant filters during candidate retrieval.
4. Validate authorization before context assembly.
5. Recheck permissions before sensitive tool execution.
6. Scope caches, checkpoints, logs and object storage access.
7. Test adversarial cross-tenant requests and access revocation.

RBAC grants permissions through roles. ABAC evaluates attributes such as tenant, classification, region, purpose and clearance. Some systems need both.

Physical tenant separation can reduce blast radius but costs more to operate. Shared indexes can be economical but demand strict enforcement and testing. A post-generation filter is insufficient because unauthorized data may already have reached the model.

---

## 4. Agentic Scalability and State Management

### 4.1 Treat an agent as a stateful workflow

A tool-using agent may classify a request, retrieve evidence, call APIs, validate results, request approval and resume later. It is a workflow with probabilistic decisions—not merely one LLM call.

Use an explicit graph or state machine with:
- Defined nodes and transitions.
- Validated state updates.
- Deadlines and bounded retries.
- Authorization checks before tools.
- Terminal success, failure, rejection and cancellation states.
- Auditable execution records.

Use the simplest workflow that solves the task. A deterministic sequence of API calls may be more reliable than a multi-agent swarm.

### 4.2 Checkpointing and recovery

A checkpoint persists enough validated workflow state to resume after a worker crash or interruption. State may include the current node, completed steps, safe tool-result references, retry counts, approval status and workflow version.

**Recovery pattern**
1. Execute a node.
2. Validate its output.
3. Persist the state transition.
4. Continue to the next node.
5. After failure, reload the latest valid checkpoint.
6. Resume without repeating unsafe side effects.

PostgreSQL is often useful for durable workflow and business state; Redis can support low-latency caching and coordination, depending on persistence and recovery configuration. Neither technology automatically makes a workflow correct—transaction boundaries, durability, concurrency and recovery behavior must be designed.

Checkpointing does **not** guarantee exactly-once execution of external side effects.

### 4.3 Bound agent execution

An agent can loop, repeatedly call tools or exhaust its budget. Set independent limits for:
- Graph steps.
- Model calls.
- Tool calls.
- Retries per node.
- Wall-clock duration.
- Token budget.
- Monetary budget.

Stop or request clarification when required information is missing, evidence is insufficient, a permanent error occurs, policy denies the action or the budget is exhausted. Return a controlled terminal state and record the reason.

### 4.4 Human-in-the-loop approval

For high-impact actions, persist the proposed action and pause the workflow for human review.

A safe approval process:
1. Validate the proposed arguments and policy.
2. Persist a pending action and checkpoint.
3. Show the exact action and parameters to the approver.
4. Record approval or rejection with identity and timestamp.
5. Bind approval to the exact action/version.
6. At execution time, revalidate authority, expiry and arguments.
7. Execute and verify the result.
8. Record an audit event.

Approval is not permission to alter the approved parameters. A model asking itself whether an action is safe is not equivalent to human authorization.

### 4.5 Idempotent tool execution

A timeout does not prove that a downstream operation failed. A payment service may complete a transaction while its response is lost; blindly retrying can create a duplicate.

For side-effecting operations:
- Generate a stable idempotency key for the logical operation.
- Persist intent and operation status.
- Have the downstream service deduplicate requests where possible.
- Use states such as `PENDING`, `SUCCEEDED`, `FAILED` and `UNKNOWN`.
- Reconcile uncertain outcomes before retrying.
- Prevent a second logical operation while the first is unresolved.

Idempotency makes retries safer; it does not magically guarantee exactly-once execution across distributed systems.

### 4.6 Subgraphs versus monolithic agent swarms

Modular subgraphs provide explicit interfaces, state ownership and fault boundaries. A monolithic swarm can be quick to prototype but may become difficult to debug, test and govern as agents and tools multiply.

Use modular workflows when responsibilities can be separated—for example, intent classification, knowledge retrieval, eligibility checking, approval and response validation. Avoid adding agents simply because the framework supports them.

---

## 5. Enterprise Security, Privacy and Data Isolation

### 5.1 Direct and indirect prompt injection

**Direct injection:** the user tells the model to ignore instructions or reveal protected information.

**Indirect injection:** malicious instructions are placed in retrieved documents, web pages, emails or tool outputs. A user may ask a normal question, but retrieved content tries to redirect the model or trigger an unsafe action.

Prompt wording alone cannot reliably eliminate this risk.

**Defense in depth**
1. Treat user input, retrieved documents and tool outputs as untrusted data.
2. Separate trusted instructions from untrusted content.
3. Limit tools to the minimum needed.
4. Validate tool schemas and arguments.
5. Enforce authorization and business policy outside the model.
6. Restrict outbound network access.
7. Require approval for sensitive actions.
8. Test adversarial retrieval and tool-use scenarios.
9. Monitor suspicious behavior and contain incidents.

### 5.2 Secure tool calling

The model should **propose** an action; the application decides whether it may execute.

A secure tool path includes:
1. Schema validation.
2. Tool allowlist checks.
3. Identity and authorization checks.
4. Business-rule validation.
5. Argument constraints and rate limits.
6. Least-privilege credentials.
7. Result validation and audit logging.

Valid JSON is not proof of authorization. For example, a syntactically valid request for a customer's balance must still be checked against the authenticated principal's permissions.

### 5.3 PII redaction and tokenization

- **Redaction:** removes or replaces sensitive values with placeholders.
- **Tokenization:** replaces sensitive values with controlled tokens whose mapping is stored separately.

A pre-egress pipeline can classify data, detect PII, apply policy, redact/tokenize, call an approved model, inspect output and rehydrate values only through an authorized component when required.

Important limitations:
- Detectors can miss sensitive data, including unusual formats and multilingual text.
- Excessive redaction can destroy information needed for the task.
- Stable tokens can reveal linkability.
- Prompts, outputs, embeddings, caches and traces may all contain sensitive information.

Treat tokenization as a privacy control, not proof of anonymization. Minimize retention and restrict access to mapping services and logs.

### 5.4 Secrets and tenant isolation

Never put API keys, database passwords or privileged credentials in prompts, model-visible state or ordinary logs. Use a secret manager, workload identity, scoped credentials, rotation and restricted outbound access.

Tenant isolation must cover the entire data path:

| Component | Key control |
|---|---|
| API gateway | Authenticate principal and tenant |
| Orchestrator | Carry trusted tenant context |
| Vector/lexical search | Enforce tenant and document ACLs |
| Database and object storage | Enforce data permissions |
| Cache | Scope keys and validate reuse context |
| Agent checkpoints | Prevent cross-tenant thread access |
| Tools | Authorize each operation |
| Observability | Restrict sensitive trace access |
| Secrets | Least-privilege workload credentials |

A cache leak is a security incident: similar questions must not cause one user's account data to be returned to another. Revoked permissions and deleted documents must be reflected in indexes, caches and persisted workflows.

---

## 6. Observability and Day-2 Operations

### 6.1 Why ordinary application monitoring is insufficient

An HTTP 200 response can still be incorrect, unsupported, unsafe or unauthorized. LLM observability must cover infrastructure performance and AI behavior.

A useful trace should connect:
- API request and authentication.
- Cache lookup.
- Embedding and retrieval.
- Reranking.
- LLM calls and model versions.
- Tool execution and retries.
- Checkpoint writes and approval pauses.
- Output validation.
- Final result.

Capture timings, status, model/tool identifiers, token counts and safe metadata. Avoid indiscriminate storage of raw prompts, completions and tool results; traces can contain sensitive data and incur significant cost.

### 6.2 OpenTelemetry, Langfuse and Arize Phoenix

- **OpenTelemetry:** vendor-neutral instrumentation and context propagation for traces, metrics and logs across application services and infrastructure.
- **Langfuse:** LLM-focused tracing, prompt/version workflows, token/cost visibility and evaluation capabilities, depending on deployment and version.
- **Arize Phoenix:** AI observability with tracing, retrieval inspection and evaluation workflows, depending on version.

These tools overlap but are not identical. OpenTelemetry can provide cross-service instrumentation, while an LLM-focused platform can provide specialized inspection and evaluation. Avoid collecting the same high-volume sensitive payloads into several systems without a clear reason.

### 6.3 Production metrics

**Performance**
- Request rate and error rate.
- TTFT and ITL p50/p95/p99.
- End-to-end latency.
- Queue depth and wait time.
- Input/output tokens per second.
- GPU utilization and memory pressure.
- Provider timeout and rate-limit rates.

**Cost**
- Tokens and cost per task.
- Cost by model, tenant and feature.
- Retry and agent-loop overhead.
- Cache hit rate and savings.

**RAG quality**
- Recall@k, MRR and nDCG@k.
- Citation correctness.
- Context relevance and answer groundedness.
- Empty/low-confidence retrieval rate.

**Agent quality**
- Task completion rate.
- Correct tool selection and argument validity.
- Tool success rate.
- Steps per task and escalation rate.
- Recovery success and duplicate-side-effect attempts.

**Security**
- Unauthorized retrieval/tool attempts.
- Cross-tenant isolation test failures.
- Policy violations and sensitive-data exposure.
- Secret leakage in logs or traces.

Define every metric's measurement boundary, aggregation window and alert threshold. Avoid high-cardinality labels such as raw prompts or arbitrary tool arguments.

### 6.4 Offline gold-set evaluation versus online monitoring

**Offline evaluation** uses a curated, versioned set of questions, evidence and expected behavior. It is repeatable and useful as a release gate.

**Online monitoring** observes actual production traffic and detects new patterns, latency changes, retrieval failures, tool failures, routing shifts and cost increases. Ground truth may not be available immediately.

A robust release process is:

1. Evaluate candidate model, prompt and index versions offline.
2. Run security, quality and regression checks.
3. Shadow traffic where feasible.
4. Canary the candidate.
5. Monitor SLOs and reviewed quality samples.
6. Roll back if quality, safety or reliability regresses.

Evaluate factual correctness, faithfulness, completeness, citation accuracy, safety, tool correctness and instruction following separately. Model-based judges can help scale evaluations but can also be wrong; calibrate them against human-reviewed examples and deterministic checks.

### 6.5 Day-2 incident thinking

| Symptom | Investigate first |
|---|---|
| TTFT spikes | Queueing, prompt length, retrieval and prefill |
| ITL degrades | Decode throughput, GPU contention and KV memory |
| GPU out-of-memory | Weights, KV cache, context length and concurrency |
| RAG quality drops | Corpus changes, embedding/index versions and retrieval metrics |
| Provider rate limits | Quota usage, concurrency and retry behavior |
| Agent loops | Graph transitions, retry counts and stop conditions |
| Duplicate actions | Idempotency records and reconciliation |
| Cross-tenant leakage | Authorization filters, cache keys and persisted state |
| Cost increases | Tokens per task, model routing, retries and cache hits |

A disciplined incident process detects, scopes, contains, traces, identifies root cause, validates the fix, runs regression tests and rolls out safely. Connect technical symptoms to business impact and affected users.

---

## 7. Reference Architecture and Key Trade-offs

A typical enterprise AI request path is:

```text
Client
  |
API Gateway: authentication, quotas, request limits
  |
Orchestrator: policy, deadlines, tenant context
  |
Exact cache / eligible semantic cache
  |
Model router: rules, smaller model or stronger model
  |
  +----------------------+----------------------+
  |                                             |
  v                                             v
RAG retrieval                              Controlled tool gateway
Dense + BM25 + reranking                  Auth + policy + idempotency
  |                                             |
  +----------------------+----------------------+
                         |
                  LLM inference service
                  Batching + KV cache
                         |
                  Output validation
                  Safety + schema + citations
                         |
                      Response

Cross-cutting:
Durable workflow state | Secret management | Tenant isolation
OpenTelemetry | LLM evaluation | Cost monitoring | Audit records
```

This is a reference pattern, not a requirement to deploy every component separately.

| Decision | Benefit | Main risk/trade-off |
|---|---|---|
| Smaller vs. stronger model | Cost and latency savings | Quality regression |
| Semantic cache vs. no cache | More reuse for paraphrases | False matches, stale data and leakage |
| More RAG context | Broader evidence coverage | Higher token cost and latency |
| Reranking | Better candidate ordering | Additional latency/cost |
| Physical vs. logical tenant isolation | Stronger separation vs. operational efficiency | Cost vs. enforcement complexity |
| More agent autonomy | Flexible planning | More failure paths and harder governance |
| Rich traces | Better diagnosis | Privacy, storage and cost exposure |
| Aggressive batching | Higher throughput | Potential tail-latency degradation |

The correct choice depends on workload, quality thresholds, security requirements, latency SLOs and operating cost.

---

## 8. Interview Questions Worth Practicing

Try to answer each question by explaining the diagnostic process, trade-offs and failure modes—not just naming a tool.

1. **TTFT is high but ITL is healthy. What do you investigate first?**  
   Separate queueing, retrieval/tool latency, prompt size and prefill before optimizing decode.

2. **How would you estimate capacity for 10,000 registered users?**  
   Estimate peak request rate, active concurrency, prompt/output distributions and SLOs. Load-test the model and GPU configuration; registered users are not equivalent to concurrent requests.

3. **Why can a model fit on a GPU but fail at production concurrency?**  
   KV cache, runtime buffers and temporary memory are additional to weights; context length and active sequences affect capacity.

4. **When is semantic caching unsafe?**  
   Personalized, sensitive, time-varying or subtly different questions require strict scope, freshness and correctness checks—or should bypass semantic reuse.

5. **Why is a vector database not a complete RAG solution?**  
   Retrieval alone does not provide ingestion quality, lexical matching, reranking, authorization, freshness, provenance or grounded generation.

6. **How do you prevent cross-tenant RAG leakage?**  
   Derive scope from authenticated identity, filter during retrieval, validate before context assembly, scope caches/checkpoints and test revocation and adversarial cases.

7. **How do you recover an agent after a worker crash?**  
   Persist validated state transitions, resume from a checkpoint and make side effects idempotent or reconcilable.

8. **How do you avoid duplicate payments after a timeout?**  
   Use stable idempotency keys, durable operation status, downstream deduplication and reconciliation before retrying uncertain outcomes.

9. **How do you defend against indirect prompt injection?**  
   Treat retrieved content as untrusted, restrict tools, independently authorize actions, validate arguments, limit egress and require approval for sensitive operations.

10. **How do you know a new model or prompt is better?**  
    Use a versioned gold set, compare quality and safety by task, test retrieval/tool behavior, then shadow or canary with rollback criteria.

11. **LLM spans are fast, but end-to-end latency is high. What next?**  
    Inspect retrieval, queueing, tools, retries, serialization, networking and post-processing; verify trace boundaries.

12. **A cost optimization improves latency but reduces answer quality. How do you decide?**  
    Compare against explicit quality and safety gates, evaluate by task/risk class and choose only configurations that satisfy required SLOs.

---

## 9. Final Principles to Remember

- Optimize the actual bottleneck, not the most visible component.
- Measure p95/p99 and cost per successful task, not only averages and tokens per second.
- Separate model weights from KV-cache capacity when planning inference.
- Treat semantic similarity as a retrieval signal, not proof of answer equivalence.
- Build RAG as a versioned data pipeline with provenance, access controls and evaluation.
- Enforce authorization in deterministic application code, never by trusting model intent.
- Checkpointing enables recovery but does not guarantee exactly-once side effects.
- Bound agent steps, time, retries, tokens and money.
- Treat prompts, retrieved content, tool arguments and model outputs as untrusted.
- Combine offline quality gates with online monitoring and safe rollouts.
- Design for failure, recovery, auditability and controlled degradation from the start.

**Core interview message:** A production AI Architect engineers a reliable system around probabilistic inference. The goal is not simply to choose a powerful model; it is to deliver measurable quality with bounded latency and cost, enforceable security, recoverable workflows and observable behavior.
