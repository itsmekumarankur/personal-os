# AI Architect Interview Playbook: High-Yield System Design Questions

> **Purpose:** Practice architect-level answers to production AI system design questions.
> **How to use this file:** For each question, lead with requirements, describe the architecture, explain key trade-offs, identify failure modes, and define how you would validate the design.

---

## 1. A Repeatable Framework for Architect-Level Answers

**Short answer:**
Requirements → Architecture → Trade-offs → Failure modes → Validation.

1. **Functional requirements:** Users, tasks, read-only vs actions, data sources, multi-turn, success criteria.
2. **Non-functional requirements:** Traffic, latency (p95/p99), availability, cost, quality, security, freshness, ownership.
3. **Architecture:** Gateway → policy/validation → PII → cache → router/budget → orchestration → RAG + tools → LLM gateway → output validation → response. Keep it logical, not necessarily microservices.
4. **Trade-offs:** Latency vs depth, cost vs quality, cache hit vs staleness, isolation vs efficiency, managed vs self-hosted, autonomy vs control.
5. **Failure & validation:** Timeouts, malformed data, retries, crashes, observability, safe fallback, pre-release tests.

---

# 2. System Design and Scalability

## Question 1: Design an enterprise assistant handling 10,000 queries per minute

**Short answer:**
10,000/min ≈ 167 req/s. Use Little's Law: L = λW. At 2s average, ~334 in flight. But peaks, prompt sizes, and tool calls matter more.

**Protect each scarce resource separately:**
- **Ingress:** Per-tenant request + token quotas, concurrency limits, payload caps.
- **Queues:** Bounded, deadline-aware, backpressure, controlled overload, jittered retries.
- **Downstream APIs:** Per-dependency concurrency, timeouts, bulkheads, circuit breakers, request coalescing, no blind retries on non-idempotent calls.
- **LLM budget:** Per-request token/time/cost budgets, cheap-model routing, bounded context/output, cache stable answers, detect runaway loops.

**Caching:** Exact cache first. Semantic only for stable, non-personalized, non-time-sensitive intents. Cache key must include tenant, auth scope, model/prompt version, locale, data version.

**Scaling:** Scale inference and app services independently. Load test with realistic prompt/output/tool/burst profiles. Track p50/p95/p99, TTFT, queue wait, rejections, cost per task, CRM errors, cache hit rate, stale incidents.

**Architect close:** Never size GPUs from user count. Estimate peak token demand, benchmark, then enforce admission control and independent quotas.

---

## Question 2: Design multi-tenant RAG for thousands of corporate tenants

**Short answer:**
**Security invariant: unauthorized documents must never enter model context.**

**Filter placement:** Prefer pre-filtering or authorization-constrained retrieval. Post-search checks are defense-in-depth, not the primary control. If backend can't enforce filters reliably, use separate indexes/collections or a trusted retrieval service. Never trust model-generated filters or client-supplied tenant IDs.

**Isolation options:**
1. Separate DB/deployment for high-sensitivity tenants.
2. Separate collections/indexes.
3. Shared index + mandatory trusted filtering.

Physical separation = smaller blast radius, higher cost. Shared = efficient, needs strong enforcement.

**Hidden failures:** Cross-tenant cache reuse, permission changes mid-workflow, deleted docs still indexed, parent-child chunk leaks, citations to inaccessible docs, traces capturing sensitive passages, reranker seeing unauthorized candidates.

**Test:** Adversarial cross-tenant queries, mixed ACLs, revoked docs. Verify unauthorized text never enters context, cache, or traces.

**Architect close:** Tenant authorization is a data-access invariant, not a prompt instruction.

---

## Question 3: Fine-tune an open-weight model with LoRA/QLoRA, or use RAG plus prompting?

**Short answer:**
- **RAG:** For changing, private, source-grounded knowledge.
- **Fine-tuning:** For behavior — format, style, classification, specialized transformations.
- **Prompting:** First choice when instructions + examples suffice.
- **Combine:** Fine-tuning doesn't replace RAG for changing facts.

**LoRA:** Trains small low-rank adapters. **QLoRA:** Quantized frozen base + trainable adapters. Neither guarantees better quality.

**Decision process:** Define measurable failure → baseline with prompting/RAG → diagnose (knowledge vs retrieval vs reasoning vs consistency vs policy) → improve data/prompts/retrieval/controls → fine-tune only if behavior gap remains → compare on held-out sets → compare full lifecycle cost → canary + rollback.

**Traps:** Fine-tuning to memorize facts, bad data, unvalidated synthetic data, cherry-picked prompts, ignoring throughput/license/cost, assuming fine-tuning replaces authorization/safety.

**Architect close:** RAG supplies evidence; fine-tuning changes behavior; prompting configures at inference. Prove benefit with evaluation + total cost.

---

# 3. Agent Orchestration and Failure Modes

## Question 4: Prevent loops, invalid tool calls and cascading failures in a stateful agent

**Short answer:**
**Design around explicit state transitions — not unbounded model loops.**

**Loop prevention:** Max steps, per-node retries, overall deadline + token/money budget, explicit terminal states, repeated-state detection, require new evidence to repeat, controlled response on budget exhaustion. Model saying "done" isn't enough — validate postconditions.

**Tool safety:** Allowlist names, strict schema validation, authorization outside model, timeouts/concurrency/payload limits, least privilege, validate results. Schema-valid ≠ authorized.

**Failure classification:**
- Timeout + uncertain side effect → reconcile, don't blind retry.
- Rate limit → respect guidance + bounded backoff.
- Safe read network failure → bounded retry.
- Malformed response → validate, record, retry if safe.
- Auth denial → fail closed.
- Business rejection → controlled failure.
- Repeated loop → stop on guard.

**Cascading prevention:** Bulkheads, circuit breakers, bounded queues, retry budgets, backpressure, safe fallbacks, observability.

**Test:** Timeouts, malformed JSON, repeated calls, rate limits, crashes, partial side effects. Assert termination, budget compliance, no duplicate unsafe actions.

**Architect close:** The model proposes; the graph, policy layer, and tool gateway control what executes.

---

## Question 5: Handle multi-day human approvals without losing state or tying up workers

**Short answer:**
**Don't hold workers or HTTP requests. Persist state and suspend the workflow.**

**Flow:** Prepare → validate → persist pending action + checkpoint → emit approval task → suspend & release worker → human decides later → authenticate approver → reload → revalidate permissions/expiry/state → execute/reject/cancel → persist + audit.

**Persist:** Workflow/tenant IDs, pending action + immutable params/version, state/checkpoint, approval status/approver/timestamp, expiry/cancellation, idempotency key, workflow version, audit refs.

**Races:** Verify approval matches exact action + args, not expired/revoked, recheck authorization/policy, confirm expected state, prevent duplicate execution. Use optimistic concurrency/version checks.

**Ops:** Durable queues, notification retries, reconciliation for stuck approvals, clear reject/cancel/timeout states, auditable transitions, idempotent resumption.

**Architect close:** Approval is an async event resuming a durable process — not a reason to hold a thread or trust stale memory.

---

## Question 6: Sandbox arbitrary Python and dynamic SQL generated by an agent

**Short answer:**
**Avoid arbitrary execution if a narrower tool API works. Otherwise, enforce isolation outside the model.**

**Python sandbox:** Ephemeral containers/microVMs, non-root, read-only FS, CPU/memory/time/output limits, no host FS or runtime socket, restricted egress, no inherited credentials, controlled I/O artifacts, process isolation + cleanup. Language-level restrictions alone are insufficient.

**SQL controls:** Read-only identity, parameterized values, parser/allowlist for statements + tables, deny DDL/DML/admin, row/column security, tenant scoping, timeouts, result-size/cost limits, network only to intended DB, audit every query, mask sensitive columns. Parameterization ≠ safe arbitrary SQL structure.

**Replica is still sensitive:** Read-only prevents writes, not bulk extraction, unauthorized joins, or exfiltration.

**Output/egress:** Limit rows/bytes/time, inspect outputs, restrict egress, avoid raw results to external models, log metadata not PII, require approval for high-risk access.

**Architect close:** Never rely on the LLM to sandbox itself. Enforce least privilege, isolation, query constraints, limits, and egress controls externally.

---

# 4. Cost Optimization and Latency

## Question 7: A LangGraph workflow takes 14 seconds. Reduce it below 3 seconds.

**Short answer:**
**Measure → Identify → Optimize → Validate.**

1. **Measure:** Trace every node, LLM call, retrieval step, API. Find where 14s goes.
2. **Optimize bottleneck:**
   - Too many LLM calls → remove/combine.
   - Slow APIs → parallelize independent calls.
   - Large prompts → trim context.
   - Slow retrieval → optimize search/reranking.
   - Repeated requests → cache safely.
3. **Validate:** Compare latency, quality, failure rate, cost.
4. **Deploy:** Canary + rollback.

**Principle:** Don't optimize blindly. Fix the slowest critical-path part first while preserving quality and security.

**Architect close:** Use traces to find the bottleneck, optimize the critical path, validate sub-3s without compromising quality or reliability.

---

## Question 8: Implement semantic caching and invalidate it when enterprise data changes

**Short answer:**
**Eligibility before threshold tuning.** Semantic caching only for safe-to-reuse request classes. Avoid: balances, personalized recs, auth-sensitive info, fast-changing policies/prices, state-dependent answers.

**Lookup:** Auth → exact cache → semantic candidate search → check similarity + intent + context + version + freshness → return authorized result or call model/retrieval → validate → cache if eligible.

**Threshold:** Empirical, risk-specific. Build paraphrases + hard negatives. Measure false-hit rate, hit rate, correctness, latency/cost savings. Combine similarity with intent, tenant scope, authorization, model/prompt version, freshness.

**Invalidation:** TTL, versioned keys, event-driven invalidation, explicit invalidation on deletion/revocation, bypass for volatile data, shorter TTLs for volatile content. Versioning prevents stale reuse; event-driven needs reconciliation.

**Isolation:** Semantic cache can leak across tenants. Enforce tenant + auth scope before reuse. Exclude sensitive personalized answers from shared caching unless isolation is proven.

**Architect close:** Thresholds are empirical, risk-specific controls. Correctness, authorization, and freshness are hard gates — similarity alone is never enough.

---

# 5. Governance, Evaluation and Day-2 Operations

## Question 9: Regression-test a new embedding model or LLM version before production

**Short answer:**
**Threat:** Upgrade may reduce accuracy, retrieval, safety, or performance despite demos.

**Release gates:**
1. **Version everything:** Model, embeddings, index, prompts, reranker, tool schemas, eval datasets.
2. **Embedding migration:** Separate index, re-embed consistently, compare Recall@k, MRR, nDCG, latency, cost. Never mix incompatible configs.
3. **LLM evaluation:** Versioned gold dataset — accuracy, groundedness, citations, tool calls, structured outputs, security, edge cases. Automated metrics + human review for high-risk.
4. **Gates:** Acceptable quality, zero critical security regressions, valid tool outputs, latency/cost within budget.
5. **Rollout:** Offline → shadow → canary → production monitoring. Keep previous model + index for rollback.

**Architect close:** A model upgrade is a production code change. Compare candidate vs baseline on same test cases, use measurable criteria, roll back on regression.

---

## Question 10: Defend against indirect prompt injection in an ingested customer document

**Short answer:**
**Threat:** Malicious document contains hidden instructions; RAG retrieves it; LLM follows them → unauthorized actions or data exposure.

**Layered defense:**
1. **Ingestion:** Track provenance + trust level, scan suspicious content, quarantine high-risk docs.
2. **Context:** Treat retrieved docs as untrusted evidence, not instructions. Include only relevant, authorized content.
3. **Tool execution:** Allowlist tools, validate args, enforce independent authorization, least-privilege credentials, human approval for high-impact actions.
4. **Monitoring:** Log retrieval sources + tool decisions, detect denied actions, test adversarial docs, support rapid quarantine + index removal.

**Architect close:** Never rely solely on prompts or injection classifiers. Even if the LLM is manipulated, independent authorization and execution controls must prevent unauthorized actions.

---

**Core message:** An architect-level answer demonstrates control over the entire system — workload, data access, probabilistic model behavior, deterministic execution, failure recovery, evaluation, and operational cost.
