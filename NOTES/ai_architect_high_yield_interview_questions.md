# AI Architect Interview Playbook: High-Yield System Design Questions

> **Purpose:** Practice architect-level answers to production AI system design questions.  
> **How to use this file:** For each question, lead with requirements, describe the architecture, explain key trade-offs, identify failure modes, and define how you would validate the design. Treat the suggested answers as structured starting points—not scripts to memorize.

---

## 1. A Repeatable Framework for Architect-Level Answers

Avoid jumping straight to a framework or cloud service. Start by establishing the problem and constraints.

### Step 1: Clarify functional requirements

Ask:
- Who are the users and what tasks must the system support?
- Is the assistant read-only, or can it perform actions?
- Which data sources and APIs must it access?
- Does it need multi-turn conversation, citations, workflow state or human approval?
- What constitutes a successful answer or task?

### Step 2: Clarify non-functional requirements

Establish measurable targets for:

| Dimension | Questions to ask |
|---|---|
| Traffic | Average and peak QPS? Bursts? Request-size distribution? |
| Latency | Is the target for first token or complete response? What are p95/p99 SLOs? |
| Availability | Required uptime, recovery time and graceful-degradation behavior? |
| Cost | Budget per request/task? Monthly inference and infrastructure budget? |
| Quality | Accuracy, retrieval recall, citation quality and tool success targets? |
| Security | Tenant isolation, PII, data residency, retention and audit requirements? |
| Consistency | How fresh must enterprise data be? Can responses be cached? |
| Operations | Who owns incidents, model upgrades, evaluation and rollback? |

### Step 3: Present a component-level architecture

A reusable starting point is:

```text
Client
  |
API Gateway: authentication, quotas, request-size limits
  |
Trusted policy context + input validation
  |
PII handling where required
  |
Exact cache / eligible semantic cache
  |
Request router and budget/deadline manager
  |
Orchestration graph
  |
  +----------------------+----------------------+
  |                                             |
  v                                             v
RAG retrieval                              Controlled tool gateway
Dense + lexical search                     Auth + schema + policy
Reranking + ACL enforcement                Idempotency + audit
  |                                             |
  +----------------------+----------------------+
                         |
                    LLM Gateway
        Routing, provider quotas, deadlines, fallbacks
                         |
                  Output validation
          Grounding, schema, safety, disclosure policy
                         |
                      Response

Cross-cutting: durable state, secrets, observability, evaluations,
tenant isolation, cost controls, audit and incident response.
```

This is a logical architecture, not a requirement to deploy each box as a separate service. Keep the design as simple as possible while meeting the requirements.

### Step 4: Explain the important trade-offs

Explicitly compare:
- Latency versus reasoning depth.
- Cost versus task quality.
- Cache hit rate versus stale or incorrect responses.
- Logical versus physical tenant isolation.
- Managed APIs versus self-hosted models.
- Agent autonomy versus determinism and control.
- Stronger validation versus additional latency.
- High throughput versus tail-latency SLOs.

### Step 5: Explain failure handling and validation

For every critical dependency, answer:
- What if it times out?
- What if it returns malformed or incomplete data?
- What if a request is retried?
- What if the worker crashes?
- How is the failure observed?
- What is the safe fallback?
- How will you test the behavior before release?

---

# 2. System Design and Scalability

## Question 1: Design an enterprise assistant handling 10,000 queries per minute

**Interviewer prompt:** Design a customer-facing AI agent handling 10,000 queries per minute that queries internal databases and CRM APIs. How do you design caching, rate limiting and queueing to protect downstream APIs and the LLM budget?

### A. Clarify the load before sizing infrastructure

10,000 queries/minute is approximately:

\[
\frac{10,000}{60} \approx 167 \text{ requests/second}
\]

That is an average rate if the stated figure represents a uniform minute. It does not reveal burst rate, active concurrency, prompt size, output length or how many tool calls each request triggers.

Ask:
- Is 10,000/minute an average or peak?
- What is the burst profile?
- What percentage of requests require RAG or CRM calls?
- How many model calls and tool calls occur per user task?
- What are the p95/p99 latency and availability targets?
- What are the per-tenant quotas and budget limits?

Estimate concurrency using Little's Law:

\[
L=\lambda W
\]

At 167 requests/second and 2 seconds average time in the system, about 334 requests are in flight on average. This is a starting estimate, not a capacity guarantee.

### B. Reference design

```text
Clients
   |
API Gateway
   |-- Authentication and tenant identity
   |-- Per-tenant request/token quotas
   |-- Payload limits and abuse protection
   |
Admission control + bounded queue
   |
Exact cache
   |
Semantic cache for approved stable intents
   |
Request router / budget manager
   |
Orchestrator
   |-------------------------|
   |                         |
   v                         v
RAG retrieval             Tool gateway
   |                         |
Vector + BM25             Per-API bulkhead,
ACLs + reranker           concurrency limit and timeout
   |                         |
   |                      CRM / internal APIs
   |                         |
   |-------------------------|
               |
           LLM gateway
     Model routing, deadlines,
     provider quotas and fallback
               |
       Output validation
               |
            Response
```

### C. Protect each scarce resource separately

**Ingress and tenant quotas**
- Limit requests per tenant and overall traffic.
- Use token quotas as well as request quotas because request sizes vary.
- Apply concurrency limits to prevent one tenant from consuming all capacity.
- Reject oversized or clearly abusive requests early.

**Bounded queues and backpressure**
- Use a bounded queue, not an unlimited backlog.
- Enforce deadlines so expired requests do not consume expensive resources.
- Prioritize traffic only when business requirements justify it.
- Return a controlled overload response when capacity is exhausted.
- Avoid retry storms; retries must be bounded and jittered.

**Downstream API protection**
- Give each dependency its own concurrency limit and timeout.
- Use bulkheads so a slow CRM API does not exhaust all worker capacity.
- Apply circuit breakers and respect rate-limit responses.
- Cache only data that is safe to cache and has an acceptable freshness policy.
- Use request coalescing for identical concurrent reads where appropriate.
- Avoid automatic retries for non-idempotent operations.

**LLM budget protection**
- Set per-request model-call, token, time and monetary budgets.
- Route simple tasks to cheaper models or deterministic logic.
- Bound context and output lengths.
- Cache eligible stable responses.
- Detect runaway agent loops.
- Track cost per successful user task and per tenant.

### D. Caching strategy

Use an exact cache first when the normalized request and relevant context match. Semantic caching can help for stable FAQs, but must not be used blindly for account balances, personalized records or time-sensitive facts.

A cache key or eligibility check may need to account for tenant, authorization scope, prompt/model version, locale, source-data version and freshness requirements. Do not let cache reuse bypass authorization.

### E. How to scale and validate

Scale inference and application services independently. Use realistic load tests with varied prompt lengths, output lengths, cache hit rates, tool latency and burst patterns.

Measure:
- p50/p95/p99 end-to-end latency and TTFT.
- Requests and tokens per second.
- Queue wait and rejection rate.
- LLM calls per task and cost per task.
- CRM concurrency, latency, timeout and error rates.
- Cache hit rate and stale-result incidents.
- Success rate under dependency failure.

**Strong interview conclusion:** I would not size GPUs from the user count alone. I would estimate peak request and token demand, benchmark the target model and workload, then enforce admission control and independent quotas at each expensive dependency.

---

## Question 2: Design multi-tenant RAG for thousands of corporate tenants

**Interviewer prompt:** Users must retrieve only documents authorized by their ACL/RBAC roles. Do you filter before or after vector similarity search, and why?

### A. State the security invariant

**Unauthorized documents must never enter the model's context.** A final answer filter is too late if confidential content has already been sent to the model.

### B. Architecture

```text
Authenticated request
       |
Trusted identity / authorization service
       |
Resolve tenant, principal, roles and allowed scopes
       |
Dense + lexical candidate retrieval
       |  Mandatory tenant/ACL filtering
       v
Authorized candidate set only
       |
Reranking
       |
Revalidate source access / freshness
       |
Build bounded context
       |
LLM generation with source references
       |
Output validation and authorized citations
```

### C. Filter placement: the nuanced answer

Prefer **pre-filtering or authorization-constrained retrieval** when the vector engine supports it reliably. This reduces the risk of unauthorized candidates being exposed to downstream components and avoids wasting reranker and context capacity on inaccessible documents.

However, implementation details matter:
- Some systems apply metadata filters within approximate-nearest-neighbor search; filtering behavior can affect recall and performance.
- A post-search authorization check can be a useful defense-in-depth step, but must happen before candidate content reaches the model.
- If a backend cannot enforce filters reliably, use a safer isolation strategy such as separate indexes/collections or a trusted retrieval service.
- Do not rely on model-generated filters or client-supplied tenant IDs.

### D. RBAC, ABAC and isolation options

RBAC grants permissions through roles. ABAC evaluates attributes such as tenant, classification, region, purpose and clearance. Enterprise systems often need both.

Possible isolation levels:
1. Separate databases or deployments for high-sensitivity tenants.
2. Separate collections/indexes with independent access controls.
3. Shared indexes with mandatory trusted tenant/ACL filtering.

Physical separation reduces blast radius but costs more to operate. Shared infrastructure can be efficient but needs strong enforcement, isolation tests and operational controls.

### E. Hidden failure modes to mention

- Cache entries reused across tenants.
- A user's permissions change while an agent is paused.
- Deleted or revoked documents remain indexed.
- Parent-child chunk expansion pulls in unauthorized content.
- Citations link to documents the user cannot open.
- Traces capture sensitive retrieved passages.
- A reranker sees unauthorized candidates before they are removed.

### F. How to test it

Create adversarial tests with cross-tenant identifiers, mixed ACLs, revoked documents and similar queries from different users. Verify that unauthorized text never enters model context, cache responses or traces accessible to the wrong principal.

**Strong interview conclusion:** Tenant authorization is a data-access invariant, not a prompt instruction. Enforce it in trusted retrieval and data-access layers, then add defense-in-depth checks before context assembly and output.

---

## Question 3: Fine-tune an open-weight model with LoRA/QLoRA, or use RAG plus prompting?

**Interviewer prompt:** When do you advocate fine-tuning an open-weight model such as Llama 3 via LoRA/QLoRA versus RAG and prompt engineering on a closed-source frontier API?

### A. Separate the problem types

Use **RAG** when the main problem is access to changing, private or source-grounded knowledge.

Use **fine-tuning** when the main problem is model behavior: consistent task format, domain-specific patterns, style, classification or a specialized transformation that examples can teach.

Use **prompt engineering** first when instructions and examples can achieve the required quality without a model-training pipeline.

These approaches can be combined. Fine-tuning does not eliminate the need for RAG when facts change frequently.

### B. Decision matrix

| Factor | RAG + prompting / hosted frontier API | Open-weight fine-tuning with LoRA/QLoRA |
|---|---|---|
| Private or changing knowledge | Strong fit when retrieval is reliable | Weights are a poor substitute for an updated source of truth |
| Specialized output behavior | Prompting may be enough; fine-tuning can be added | Strong candidate when representative training examples exist |
| Time to first production version | Often faster | Requires data preparation, training and evaluation |
| Data residency | Depends on provider and contract | Can offer more deployment control if self-hosted |
| Operational burden | Provider dependency and API governance | GPU serving, upgrades, security and model operations |
| Cost profile | Usage-based API cost | Training and serving infrastructure plus operations |
| Quality | Often strong general reasoning | Depends on base model, data and task |
| Vendor flexibility | Provider-specific interfaces and behavior | More control over weights, subject to model license |

### C. What LoRA and QLoRA change

**LoRA** trains small low-rank adapter matrices rather than updating all model parameters. This reduces trainable parameter count and can reduce training resource requirements.

**QLoRA** combines a quantized frozen base model with trainable adapters, reducing memory needs during fine-tuning.

Neither technique guarantees better task quality. Training data quality, evaluation, serving efficiency and model limitations still matter.

### D. Decision process

1. Define a measurable failure in the current system.
2. Establish a baseline using prompting and retrieval.
3. Check whether the failure is missing knowledge, retrieval quality, reasoning, output consistency or policy enforcement.
4. Improve data, prompts, retrieval and deterministic controls where appropriate.
5. Fine-tune only if a repeatable behavior gap remains and suitable examples exist.
6. Compare against the baseline on held-out task, safety and regression sets.
7. Compare full lifecycle cost, including serving and maintenance.
8. Deploy with canary and rollback controls.

### E. Common traps

- Fine-tuning to memorize rapidly changing facts.
- Fine-tuning on low-quality or unrepresentative examples.
- Using synthetic training data without validation.
- Comparing models only on a few hand-picked prompts.
- Ignoring inference throughput, license terms and operating costs.
- Assuming fine-tuning can replace authorization or safety controls.

**Strong interview conclusion:** Choose the intervention that matches the failure. RAG supplies current evidence; fine-tuning changes learned behavior; prompting configures a model at inference time. Prove the benefit with evaluation and total-cost analysis.

---

# 3. Agent Orchestration and Failure Modes

## Question 4: Prevent loops, invalid tool calls and cascading failures in a stateful agent

**Interviewer prompt:** In a stateful multi-agent system such as LangGraph, how do you prevent non-deterministic loops, hallucinated function calls and cascading failures when a downstream tool times out or returns malformed JSON?

### A. Design around explicit state transitions

Do not let the model control an unbounded execution loop. Define an explicit graph with typed state, allowed transitions, terminal states and bounded retries.

```text
Model proposes action
        |
        v
Validate tool name and schema
        |
        v
Authorize action and validate policy
        |
        v
Execute with deadline
        |
        v
Validate result
   |             |
Valid          Invalid/error
   |             |
Continue      Bounded retry if transient
or finish     or controlled failure state
```

### B. Prevent non-deterministic loops

- Maximum graph steps and model calls.
- Per-node retry limits.
- Overall deadline and token/money budget.
- Explicit terminal states.
- Detect repeated state/action combinations where useful.
- Require new evidence or a meaningful state change before repeating a step.
- Return a controlled response when the budget is exhausted.

A model-generated statement that it is “done” is not sufficient. The orchestrator should validate whether required steps and postconditions are satisfied.

### C. Handle tool calls safely

- Validate tool name against an allowlist.
- Validate arguments against a strict schema.
- Enforce authorization and business rules outside the model.
- Apply timeouts, concurrency limits and payload limits.
- Use least-privilege credentials.
- Validate tool results before passing them back to the model.
- Never execute malformed JSON or silently coerce dangerous arguments.

A schema-valid request can still be unauthorized; validation and authorization are different checks.

### D. Classify failures before retrying

| Failure | Typical response |
|---|---|
| Timeout with uncertain side-effect outcome | Reconcile operation state; do not blindly retry |
| Transient rate limit | Respect retry guidance and use bounded backoff |
| Network failure on a safe read | Bounded retry may be appropriate |
| Malformed tool response | Validate, record failure, optionally retry if safe |
| Authentication/authorization denial | Fail closed; do not retry with broader privileges |
| Permanent business-rule rejection | Return controlled failure or ask for corrected input |
| Repeated model/tool loop | Stop on budget/loop guard and surface the reason |

### E. Prevent cascading failures

- Per-dependency bulkheads and concurrency limits.
- Circuit breakers for failing services.
- Bounded queues and deadlines.
- Retry budgets and jitter.
- Backpressure.
- Fallback only when semantics and security remain valid.
- Observability for graph transitions, tool errors and retry counts.

### F. Test scenarios

Simulate timeouts, malformed JSON, repeated tool calls, provider rate limits, worker crashes and partial side effects. Assert that the workflow terminates, does not exceed budgets and does not duplicate unsafe actions.

**Strong interview conclusion:** Reliability comes from deterministic orchestration around probabilistic decisions. The model can propose the next action; the graph, policy layer and tool gateway control what actually executes.

---

## Question 5: Handle multi-day human approvals without losing state or tying up workers

**Interviewer prompt:** How do you handle asynchronous human-in-the-loop approvals across multi-day lifecycles without losing state or tying up worker threads?

### A. Use a durable workflow, not a sleeping request handler

Do not keep an HTTP request or worker thread alive while waiting days for approval. Persist the workflow, record a pending approval and release execution capacity.

```text
Prepare action
     |
Validate policy and arguments
     |
Persist pending action + workflow checkpoint
     |
Emit approval task / notification
     |
Suspend workflow; release worker
     |
Human decision arrives later
     |
Authenticate approver and validate decision
     |
Reload workflow and pending action
     |
Revalidate permissions, expiry and state
     |
Execute / reject / cancel
     |
Persist result and audit event
```

### B. Persist the right state

Store:
- Workflow and tenant identifiers.
- Pending action and immutable parameter/version reference.
- Current workflow state and checkpoint.
- Approval status, approver identity and timestamp.
- Expiry and cancellation state.
- Correlation/idempotency key.
- Workflow version and audit references.

Store sensitive data minimally and protect it with access controls and retention policies.

### C. Handle races and stale approvals

An approval can arrive after the action expires, the user's permissions change or the underlying business data changes.

Before execution:
- Verify the approval applies to the exact action and arguments.
- Confirm it has not expired or been revoked.
- Recheck current authorization and business policy.
- Ensure the workflow is still in the expected state.
- Prevent duplicate approval events from executing the action twice.

Use optimistic concurrency, version checks or transactional state transitions where appropriate.

### D. Operational concerns

- Durable queues/events for approval callbacks.
- Notification retries independent of workflow execution.
- A reconciliation job for stuck or expired approvals.
- Clear reject, cancel and timeout states.
- Auditable transitions and idempotent resumption.
- No reliance on in-memory state held by one worker.

**Strong interview conclusion:** Persist state and suspend the workflow. Approval is an asynchronous event that resumes a durable process, not a reason to hold a worker thread or trust stale in-memory state.

---

## Question 6: Sandbox arbitrary Python and dynamic SQL generated by an agent

**Interviewer prompt:** If an agent can execute arbitrary Python scripts or generate dynamic SQL against a replica database, how do you prevent data exfiltration or injection?

### A. Start with least privilege and capability reduction

The safest design is to avoid arbitrary code execution if a narrower tool API can solve the task. Give the agent specific capabilities rather than a general-purpose shell or database credential.

### B. Python execution sandbox

If arbitrary code is genuinely required, run it in a hardened, isolated execution environment with:
- Ephemeral containers or microVMs.
- Non-root user and read-only base filesystem.
- CPU, memory, execution-time and output limits.
- No host filesystem or container-runtime socket access.
- Restricted or disabled network egress.
- No inherited cloud credentials or production secrets.
- Controlled input/output artifact access.
- Process isolation and cleanup after execution.

A Python language-level restriction alone is not a sufficient security sandbox. Isolation must be enforced by the execution environment.

### C. Dynamic SQL controls

Prefer a constrained query service or approved stored procedures over unrestricted SQL generation.

Controls:
- Read-only database identity.
- Parameterized queries for values.
- SQL parser/allowlist for permitted statements and tables.
- Deny DDL, DML and administrative operations unless explicitly required.
- Row-level/column-level security and tenant scoping.
- Statement timeouts, result-size limits and query-cost controls.
- Network access only to the intended database.
- Audit every query and its principal.
- Mask sensitive columns where possible.

Parameterization prevents value injection; it does not by itself make arbitrary SQL structure safe. Validate identifiers and permitted operations separately.

### D. Treat a replica as sensitive

A read replica may still contain regulated or confidential production data. “Read-only” prevents writes but does not prevent bulk extraction, unauthorized joins or exfiltration.

### E. Control outputs and egress

- Limit rows, bytes and execution time.
- Inspect outputs for sensitive fields.
- Restrict external network egress.
- Avoid sending raw database results to an external model unnecessarily.
- Log metadata and query outcomes without indiscriminately logging PII.
- Require approval for high-risk data access or export.

**Strong interview conclusion:** Never rely on the LLM to sandbox itself. Enforce least privilege, isolation, query constraints, resource limits and egress controls outside the model.

---

# 4. Cost Optimization and Latency

## Question 7: A LangGraph workflow takes 14 seconds. Reduce it below 3 seconds.

**Interviewer prompt:** Executives complain that the workflow takes 14 seconds. How do you isolate bottlenecks and decide which architectural levers to use?

### A. First clarify what “3 seconds” means

Is the target:
- Time to first token?
- Complete response time?
- p95 or average latency?
- A read-only answer or a workflow with external side effects?

A 3-second p95 full response is very different from a 3-second first token.

### B. Trace before optimizing

Instrument every graph node and dependency. Decompose the 14 seconds into:
- Gateway and queue wait.
- Retrieval and reranking.
- Each LLM call's TTFT and completion time.
- Tool/API latency.
- Sequential versus parallel work.
- Retry and backoff time.
- Serialization and post-processing.

Build a latency budget for the critical path. Parallel branches should be analyzed by the slowest branch, not by summing all branch durations.

### C. Apply levers based on evidence

| Observed bottleneck | Possible lever | Trade-off |
|---|---|---|
| Too many sequential model calls | Combine steps or remove unnecessary reflection | May reduce reasoning depth |
| Long prompts | Trim history, reduce redundant instructions, retrieve fewer/better chunks | May lose useful context |
| Slow retrieval | Improve indexes, filtering and candidate selection | Index/recall trade-offs |
| Expensive reranking | Reduce candidate set or use a faster reranker | May reduce relevance |
| Slow tools | Parallelize independent reads, add deadlines, optimize APIs | Must preserve dependencies and rate limits |
| Provider latency | Use a suitable faster model/deployment or routing | Quality and provider trade-offs |
| Queueing | Admission control, more capacity, improved batching | Cost versus tail latency |
| Excess retries | Fix root cause and bound retries | Some transient failures may fail faster |
| Repeated stable requests | Safe exact/semantic caching | Freshness and false-hit risk |

### D. Do not parallelize everything

Parallelize independent retrievals or read-only API calls when safe. Do not parallelize steps that depend on prior results, violate downstream concurrency limits or perform conflicting side effects.

### E. Set a measurable optimization loop

1. Capture baseline traces and workload distribution.
2. Identify the dominant critical-path spans.
3. Form a specific hypothesis.
4. Change one major factor at a time.
5. Re-run representative load and quality tests.
6. Compare p50/p95/p99, task quality, failure rate and cost.
7. Roll out gradually with rollback thresholds.

A 14-second workflow may not reach a 3-second full-response target without reducing scope, changing the model, removing steps or relaxing quality requirements. State this rather than promising an arbitrary latency target.

**Strong interview conclusion:** Optimize the measured critical path. Latency reduction is a constrained optimization problem: meet the target while preserving required quality, safety and reliability.

---

## Question 8: Implement semantic caching and invalidate it when enterprise data changes

**Interviewer prompt:** How do you choose the similarity threshold and handle cache invalidation when underlying data changes?

### A. Cache eligibility comes before threshold tuning

Use semantic caching only for request classes where answer reuse is safe. Do not treat all natural-language queries as cacheable.

Usually poor candidates include:
- Account balances and transactions.
- Personalized recommendations.
- Authorization-sensitive information.
- Rapidly changing policies or prices.
- Requests whose answer depends on current state.

### B. Lookup flow

```text
Request
  |
Authenticate and resolve tenant/authorization
  |
Exact cache lookup
  |
Semantic candidate search for eligible intent
  |
Check similarity + intent + context + version + freshness
  |                          |
  | pass                     | fail
  v                          v
Return authorized result   Call model/retrieval
                             |
                       Validate answer
                             |
                       Cache if eligible
```

### C. Choose a threshold empirically

A similarity threshold balances:
- **False hits:** reuse an answer that is not actually appropriate.
- **Misses:** fail to reuse an answer that would have been safe.

Build an evaluation set with paraphrases and hard negatives—questions that look similar but require different answers. Measure false-hit rate, hit rate, task correctness, latency savings and cost savings. Select thresholds by risk class, not from a universal cosine-similarity number.

Similarity should be combined with other checks such as intent/category, tenant scope, authorization, model/prompt version and freshness.

### D. Invalidation and freshness

Possible strategies:
- TTL for content with bounded staleness.
- Versioned cache keys based on knowledge-base or policy version.
- Event-driven invalidation when source records change.
- Explicit invalidation on document deletion or access revocation.
- Bypass caching for high-volatility data.
- Shorter TTLs for more volatile content.

Versioning provides a clear way to prevent old entries from being reused after an update. Event-driven invalidation can reduce stale windows but must be reliable; missed events need reconciliation.

### E. Protect isolation

A semantic cache can leak customer information if a similar question retrieves another user's answer. Enforce tenant and authorization scope before reuse, and exclude sensitive personalized answers from shared semantic caching unless the design can prove safe isolation.

**Strong interview conclusion:** Thresholds are empirical, risk-specific controls. Correctness, authorization and freshness are hard eligibility gates; similarity alone is never enough.

---

# 5. Governance, Evaluation and Day-2 Operations

## Question 9: Regression-test a new embedding model or LLM version before production

**Interviewer prompt:** How do you automate regression testing before swapping an embedding model or upgrading an LLM?

### A. Version every change

Track versions of:
- Base model and quantization.
- Embedding model and vector index.
- Prompt templates.
- Reranker.
- Tool schemas and graph definition.
- Retrieval configuration.
- Evaluation datasets and evaluator versions.

Without versioning, a quality regression is difficult to reproduce or attribute.

### B. Embedding model migration

Do not mix query vectors and document vectors from incompatible embedding configurations.

1. Preserve the current production index.
2. Build a separate index with the candidate embedding model.
3. Re-embed the corpus consistently.
4. Evaluate retrieval against a versioned query set.
5. Compare Recall@k, MRR, nDCG, retrieval latency and index cost.
6. Evaluate downstream answer quality and citation correctness.
7. Shadow or canary traffic.
8. Switch traffic only after acceptance criteria pass.
9. Keep rollback capability.

### C. LLM/model upgrade evaluation

Use a gold set that covers:
- Common tasks and long-tail cases.
- Ambiguous and adversarial prompts.
- Tool selection and argument correctness.
- Structured-output validity.
- Groundedness and citations.
- Refusal and safety behavior.
- Multilingual and long-context cases if relevant.
- Latency, tokens and cost.

Use deterministic assertions where possible, reference-based metrics where appropriate, model-based graders with calibration, and human review for high-risk samples.

### D. Example release gates

Define thresholds based on the application rather than adopting arbitrary universal numbers:
- No critical security or authorization regression.
- Task success and factual correctness remain within agreed tolerances.
- Retrieval quality meets minimum recall/relevance requirements.
- Structured output and tool schemas remain valid.
- p95/p99 latency and cost remain within budgets.
- Rollback can be executed safely.

### E. Deployment progression

```text
Candidate change
    |
Offline unit + regression + security tests
    |
Shadow evaluation
    |
Canary rollout
    |
Online quality, latency, cost and error monitoring
    |
Accept or rollback
```

For a model upgrade, compare the candidate and baseline on the same examples and, where possible, the same workload distribution. Be alert to nondeterminism and evaluator bias.

**Strong interview conclusion:** A model upgrade is a production code change. Version it, evaluate it against measurable gates, canary it, monitor it and preserve rollback.

---

## Question 10: Defend against indirect prompt injection in an ingested customer document

**Interviewer prompt:** A malicious actor embeds hidden instructions inside a document ingested by RAG. How do you detect and neutralize the injection before an agent executes unauthorized actions?

### A. Threat model

The attack path is:

```text
Malicious document
       |
Ingestion and indexing
       |
User asks a normal question
       |
Document retrieved into context
       |
Model interprets embedded instructions
       |
Potential unauthorized tool call or data disclosure
```

The attack can be visible text, hidden text, misleading formatting or instructions embedded in tool output. Ingestion scanning can help, but cannot guarantee detection.

### B. Defense at multiple layers

**Ingestion**
- Track source and trust level.
- Extract text and relevant document structure.
- Scan/classify suspicious instructions where useful.
- Preserve provenance and access metadata.
- Quarantine or review high-risk sources according to policy.

**Prompt and context construction**
- Clearly separate trusted instructions from retrieved content.
- Treat retrieved content as evidence, not authority.
- Include only relevant, authorized passages.
- Avoid giving retrieved content control over tool policy.

**Tool execution**
- Use an allowlist of tools.
- Validate arguments and schemas.
- Enforce authorization and business policy independently.
- Apply least-privilege credentials and egress restrictions.
- Require human approval for high-impact actions.

**Monitoring and response**
- Test adversarial documents and tool-use scenarios.
- Trace the retrieved source and proposed action.
- Detect policy-denied tool calls and unusual egress.
- Support rapid source quarantine and index removal.
- Preserve audit evidence without unnecessarily retaining sensitive content.

### C. What not to claim

Do not claim that a prompt instruction or injection classifier can guarantee prevention. The robust control is to make unauthorized actions impossible or tightly constrained even if the model is manipulated.

**Strong interview conclusion:** Detection is useful, but prevention depends on capability restriction, independent authorization, least privilege, output validation and safe execution boundaries.

---

# 6. A Concise Interview Answer Structure

For any of these questions, structure the spoken answer in this order:

1. **Requirements:** State the critical functional requirements, workload assumptions and SLOs.
2. **Architecture:** Walk through the main components and request/data flow.
3. **Key decisions:** Explain why you chose each major component.
4. **Failure modes:** Address timeouts, malformed data, retries, overload and partial side effects.
5. **Security:** Explain identity, authorization, tenant isolation, secrets and data handling.
6. **Observability:** Name the metrics, traces and quality signals you need.
7. **Validation:** Explain load tests, regression tests, adversarial tests and rollout/rollback.
8. **Trade-offs:** State what your design optimizes and what it deliberately sacrifices.

A useful sentence pattern is:

> “I would first establish the workload and SLOs. Then I would design the request path around the main resource constraints. For each dependency, I would define a timeout, concurrency limit, failure policy and observable SLO. Finally, I would validate the design using representative load, quality and security tests before a gradual rollout.”

Use this as a structure, not a script. Interviewers usually learn more from how you reason about constraints and failure modes than from how many technologies you name.

---

# 7. Final Principles

- Registered users are not concurrent users; derive capacity from peak traffic and workload distribution.
- Protect each dependency with its own quota, timeout and concurrency budget.
- Enforce tenant authorization before data enters model context.
- Use RAG for changing knowledge and fine-tuning for repeatable behavior gaps.
- Bound every agent loop and treat tool outputs as untrusted.
- Durable checkpoints support recovery, but side effects still require idempotency and reconciliation.
- Never rely on a language model to sandbox its own code or authorize its own actions.
- Optimize latency from traces and the critical path, not intuition.
- Semantic cache thresholds require evaluation with hard negatives and risk-specific policies.
- Model and embedding changes need versioned regression gates, canary rollout and rollback.
- Prompt-injection detection is not a substitute for constrained tools and independent authorization.
- Explain trade-offs explicitly and connect design decisions to measurable requirements.

**Core message:** An architect-level answer demonstrates control over the entire system: workload, data access, probabilistic model behavior, deterministic execution, failure recovery, evaluation and operational cost.
