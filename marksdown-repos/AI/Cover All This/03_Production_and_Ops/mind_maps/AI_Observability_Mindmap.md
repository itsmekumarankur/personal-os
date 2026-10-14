# AI Observability — Mind Map for Quick Recall

> **Core idea:** AI can return HTTP 200 with normal CPU and latency yet still give a wrong answer. Observability must explain behavior, not just infrastructure health.

```text
AI OBSERVABILITY
├── 1. Purpose
│   ├── What did the AI do?
│   ├── Why did it do it?
│   ├── Where did it fail?
│   └── How well did it perform, how long did it take, and what did it cost?
├── 2. Trace = core debugging unit
│   ├── One request → parent/child spans
│   ├── LLM calls, prompts/model IDs, tokens, latency
│   ├── Agent decisions, iterations, termination reason
│   ├── Tool/API calls, retries, errors
│   └── RAG query, embedding, top-K docs, scores, reranker, context
├── 3. Telemetry signals
│   ├── Traces → execution path and dependency timings
│   ├── Metrics → trends, SLOs, alerts
│   └── Logs → detailed events and error context
├── 4. OpenTelemetry (OTel)
│   ├── Common, vendor-neutral instrumentation layer
│   ├── App → OTel SDK/API → Collector → backends
│   └── Avoid tightly coupling application code to one vendor
├── 5. AI-specific signals
│   ├── Quality: groundedness, relevance, correctness, hallucination
│   ├── Cost/tokens: input/output tokens, cost per request
│   ├── Performance: TTFT, E2E latency, tool/retrieval latency
│   ├── Safety: injection, PII, guardrail triggers
│   └── Agent behavior: loops, retries, tool selection, termination
├── 6. Debugging
│   ├── Slow answer? Find the slow span
│   ├── Wrong answer? Inspect retrieval/context and generation
│   ├── High cost? Find token spikes, repeated calls, agent loops
│   └── Tool failure? Inspect status, latency, retries, payload safely
└── 7. Feedback loop
    └── Trace → evaluate → review failures → improve prompt/RAG/model/tools → deploy
```

## Reference architecture

```text
AI App (LLM + RAG + Agent + Tools)
             ↓ instrument all steps
       OpenTelemetry
             ↓
       OTel Collector
        /     |      \
    Traces  Metrics  Logs
      ↓       ↓       ↓
  AI tracing  Dashboards  Log/SIEM platform
        \      |      /
         Evaluation & alerts
                  ↓
          Feedback / datasets
                  ↓
       Prompt, RAG, model, tool fixes
```

## Three pillars — quick distinction

- **Traces:** What happened during this particular request, and where was time spent?
- **Metrics:** Is the system meeting targets across many requests?
- **Logs:** What detailed event/error information helps explain an incident?

## Instrument the whole workflow

Do not instrument only the LLM. Include:
- application request and correlation IDs
- prompt/model versions
- every LLM call
- agent decisions and iteration count
- tool/API calls, status, latency, retries
- retrieval query, documents, scores, reranking and context
- guardrail/validation outcomes
- token usage, cost, latency and evaluation result

Protect sensitive content: avoid indiscriminate capture of secrets, credentials, or personal data; apply redaction, access controls, and retention rules.

## Tool selection principle

Choose a tracing/evaluation platform that fits your workflow, but keep instrumentation portable where possible. OpenTelemetry can standardize telemetry transport; AI platforms may add trace visualization, prompt management, datasets, evaluation, and agent debugging.

## Interview recall

**Question:** If the AI returns a wrong answer with HTTP 200, how do you find the cause?

**Answer:** Follow the end-to-end trace. Check prompt/model version, retrieval context and scores, tool outputs, validation/guardrail results, retries, and final evaluation. Use metrics for trends and logs for event details.

**One-line memory hook:** *Logs tell you events; metrics show trends; traces explain the journey.*

## Self-test

- [ ] Explain why traces are especially useful for agentic AI.
- [ ] Give one example each of trace, metric, and log.
- [ ] Explain how OTel reduces vendor lock-in.
- [ ] Diagnose a wrong RAG answer using the trace.
- [ ] Name sensitive data that should be redacted or access-controlled.
