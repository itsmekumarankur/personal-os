# AI Monitoring — Mind Map for Quick Recall

> **Core idea:** Uptime does not mean the AI is healthy. Monitor whether it is reliable, affordable, safe, and producing useful answers.

```text
AI MONITORING
├── 1. Operations / Reliability
│   ├── Latency: P50 / P95 / P99; TTFT for streaming
│   ├── Errors, timeouts, retries, tool failures
│   ├── Throughput and queue depth
│   └── End-to-end latency = retrieval + tools + LLM + guardrails
├── 2. Cost
│   ├── Cost per request / user / feature / use case
│   ├── Provider and model spend; daily/monthly budget
│   └── Find expensive agent loops, repeated calls, oversized prompts
├── 3. Tokens
│   ├── Input, output, cached, total tokens
│   └── Spikes may mean long history, excess RAG context, tool output, or loops
├── 4. Quality
│   ├── Correctness, relevance, groundedness, faithfulness
│   ├── Hallucination rate, task success, refusal rate
│   └── For RAG: distinguish retrieval failure from generation failure
├── 5. Security
│   ├── Prompt injection and jailbreak attempts
│   ├── PII leakage and unsafe output
│   └── Unauthorized tool use; guardrail triggers
├── 6. Drift
│   ├── Model drift: output/quality changes over time
│   └── Data drift: incoming queries, documents, embeddings, or context change
└── 7. Response loop
    └── Instrument → Alert → Trace/investigate → Fix prompt/RAG/model/data → Re-evaluate
```

## Quick diagnosis: quality suddenly drops

1. Check model and model version.
2. Check prompt version and recent prompt changes.
3. Check input/data distribution and freshness.
4. Check retrieval results, top-K, and context quality.
5. Check tool/API outputs and final model response.
6. Identify the root cause; fix and evaluate before rollout.

## Architect's mental model

`Request → Prompt / RAG / Agent / Tools → Response → Metrics + Traces + Evaluation → Drift detection → Alert → Improvement`

Every production trace should let you connect the response to its prompt, model, retrieved context, tools, token usage, latency, cost, and evaluation result.

## Interview recall

**Question:** How do you know if AI is becoming slower, more expensive, less accurate, or unsafe?

**Answer structure:** Reliability + Cost + Tokens + Quality + Security + Drift; correlate them using end-to-end traces and alert on meaningful changes.

**One-line memory hook:** *Monitor not just whether the model is up, but whether the whole AI system is working well.*

## Self-test

- [ ] Can I explain P50 vs P95 vs P99?
- [ ] Can I distinguish model drift from data drift?
- [ ] Can I explain how token spikes increase cost?
- [ ] Can I separate a RAG retrieval problem from a generation problem?
- [ ] Can I trace one bad answer from request to response?
