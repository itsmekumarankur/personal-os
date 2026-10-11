# AI Architect Interview Notes: Production LLM Systems


> **Scope:** Inference engineering, cost engineering, RAG, agent state, security, and observability.  

---

## 1. Inference Engineering:

### 1.1 Understand the inference lifecycle

LLM inference has two broad phases:

- **Prefill:** Processes the input prompt and builds the initial key-value (KV) cache. 
- **Decode:** Generates output tokens sequentially. 

This distinction matters because a request can be slow to start, slow to stream, or both.

| Metric | Meaning | Typical causes of degradation |
|---|---|---|
| **Time to First Token (TTFT)** | Time from request submission to the first generated token | Queueing, long prompts |
| **Inter-Token Latency (ITL)** | Time between successive generated tokens | Decode bottlenecks, memory bandwidth|
| **End-to-end latency** | Time until the complete answer is available | |
| **Throughput** | measure requests/sec and tokens/sec  | poor batching,  compute limits |

**Interview insight:** If TTFT is high but ITL is healthy, investigate queueing, prompt length, retrieval and prefill before optimizing decode. If TTFT is low but completion is slow, investigate output length, decode throughput and memory bandwidth.

Measure **p50, p95 and p99**, not only averages. 

### 1.2 Throughput, concurrency and queueing

A service may handle many short requests per second while struggling with fewer requests that have long prompts and long outputs.

If a service receives 20 requests/second and average time in the system is 2 seconds, approximately 40 requests are in flight on average. This is not a safe concurrency limit; memory, GPU capacity and workload distribution still determine the practical limit.

**Failure pattern:** Excess traffic grows the queue, increases TTFT, causes client timeouts, triggers retries.

**Architectural response:** Use bounded queues, backpressure, load shedding 

### 1.3 Continuous batching
Continuous batching = Keep the GPU busy by continuously replacing finished requests with new ones.

Imagine a bus carrying 10 passengers. When some passengers get off, new passengers can board immediately instead of waiting for everyone to get off.

- Benefit: Better GPU usage and faster processing of multiple AI requests.
- Challenge: Must ensure some users don't wait too long.

Remember: The goal is to serve more users efficiently without making anyone wait too long.

### 1.4 KV cache and PagedAttention

KV Cache = AI’s short-term memory of the conversation.

Imagine you are reading a book. Every time you read a new sentence, you don't reread the entire book to understand it. You remember what you have already read.

- Without KV Cache: AI repeatedly recalculates information from previous words. This wastes time.
- With KV Cache: AI saves useful information from previous words and reuses it to generate the next word faster.

Why is it useful?

- ⚡ Faster responses.
- 🔄 Less repeated computation.
- 🧠 But it consumes GPU memory, especially for long conversations and many users.

### 1.5 Speculative decoding

Speculative decoding = Guess first, verify later.
Imagine a fast junior employee drafts 5 words in advance. A senior employee quickly checks whether those words are correct.
- Draft model: Quickly guesses the next few words.
- Target model: Checks those guesses.
- Benefit: If most guesses are correct, the AI generates answers faster.
When does it help? When the guesses are usually correct and checking them is efficient.
- Speculative decoding: One AI model guesses; another verifies.

### 1.6 Quantization: BF16, FP8 and INT4

Quantization lowers the numerical precision used for weights, activations or cache values to reduce memory use and potentially improve speed.

| Format | Approximate raw storage/value | 
|---|---:|
| BF16 | 2 bytes |
| FP8 | 1 byte | 
| INT4 | 0.5 byte | 

These are raw representation sizes, not full deployment footprints. Metadata, scales, unquantized layers, runtime buffers and KV cache add overhead.

For a hypothetical 70-billion-parameter model, raw weight storage is roughly 140 GB in BF16, 70 GB in FP8, or 35 GB at 4 bits per parameter, using decimal units. Actual memory needs are higher.

**Decision principle:** Choose the lowest-cost configuration that meets quality, latency and reliability SLOs.


---

## 2. Cost Engineering and Token Economics

### 1. Measure cost per task
Don't measure only the cost of one AI call. Measure the total cost to complete one user's task, including retries and multiple AI calls.
### 2. Exact cache vs Semantic cache
- Exact cache: Same question → reuse the saved answer.
- Semantic cache: Similar question → try to reuse an answer, but verify it's correct.
### 3. Model routing
Use a small, cheaper model for simple tasks and a powerful, expensive model for complex tasks.
### 4. Rate limits, Circuit breakers and Fallbacks
- Rate limit: Restrict how many requests users can make.
- Circuit breaker: Stop calling a service that is repeatedly failing.
- Fallback: If the main AI fails, switch to an alternative.

---

## 3. Production RAG Architecture

### 3.1 RAG is a pipeline, not a vector database

RAG = Search for relevant information + Give it to AI + Generate an answer.

Example: AI searches your company documents, finds the relevant information, and answers your question using it.

Basic steps:

1. Store documents and prepare them for search.
2. Search for relevant information when a question comes.
3. Give that information to AI.
4. AI generates an answer based on it.

Remember: A vector database is only one part of RAG. RAG can still give wrong answers if the search finds the wrong information.

### 3.2 Chunking strategies

Chunking = Breaking large documents into smaller pieces so AI can search them easily.

- Fixed-size: Break into equal-sized pieces.
- Semantic: Break according to meaning.
- Parent-child: Find a small piece, then retrieve its larger section for context.
- Hierarchical: Search from document → chapter → section → paragraph.

Remember: Good chunking helps AI find the right information.

### 3.3 Embeddings and embedding-model migrations

Embeddings = Converting text into numbers that represent its meaning.

Example: “How do I reset my password?” and “I forgot my password” have similar meanings, so their embeddings may be close together.

Embedding-model migration means switching to a new model that converts text into these numbers. Usually, you must regenerate the document embeddings so searches remain compatible.

### 3.3 Embeddings and embedding-model migrations

Embeddings represent text as vectors so semantically related text can be retrieved. Query and document vectors must be compatible.

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
