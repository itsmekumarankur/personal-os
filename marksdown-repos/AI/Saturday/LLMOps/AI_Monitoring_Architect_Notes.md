# AI Monitoring — Architect's Reference Notes

## Monitoring Requirements

- Prompt monitoring — detect prompt drift and injection attempts
- Cost monitoring — token usage and spend per feature
- Token monitoring — input/output token counts
- Latency monitoring — P50, P95, P99
- Quality monitoring — faithfulness and hallucination rate
- Model drift detection
- Data drift detection

## Recommended Articles

1. [Arize — LLM Observability](https://arize.com/blog-course/llm-observability/)
2. [OpenObserve — LLM Observability Guide](https://openobserve.ai/blog/what-is-llm-observability/)
3. [OWASP — LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
4. [Arize — LLM Tracing and Observability](https://arize.com/blog/llm-tracing-and-observability-with-arize-phoenix/)
5. [Amnic — LLM Observability Guide](https://amnic.com/blogs/llm-observability)

## Monitoring Framework

```text
                 AI MONITORING
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
   OPERATIONS       QUALITY        SECURITY
       │              │              │
   Latency          Faithfulness    Injection
   Tokens           Hallucination   Jailbreak
   Cost             Relevance       PII
   Errors           Groundedness    Tool abuse
       │              │              │
       └──────────────┼──────────────┘
                      ↓
                    DRIFT
                      │
             ┌────────┴────────┐
             ↓                 ↓
        Model Drift        Data Drift
```

## 1. Prompt Monitoring

Monitor prompt version, prompt changes, prompt distribution, prompt length, injection attempts, jailbreak patterns and guardrail triggers.

> Treat prompts like production configuration/code: version them, test them and associate every production trace with a prompt version.

## 2. Cost Monitoring

Track cost/request, cost/user, cost/feature, cost/use-case, cost/model, cost/provider and daily/monthly spend.

```text
Request
 ├── LLM → $0.02
 ├── Search
 ├── LLM → $0.05
 ├── Tool
 ├── LLM → $0.08
 └── LLM → $0.10

Total = $0.25
```

Cost monitoring is also an architectural-efficiency signal.

## 3. Token Monitoring

Track input tokens, output tokens, cached tokens, total tokens and tokens per request/user/feature.

A sudden increase can indicate a larger prompt, excessive RAG context, growing conversation history, an agent loop or oversized tool output.

## 4. Latency Monitoring

Monitor P50, P95, P99 and, for streaming systems, TTFT (Time To First Token).

```text
End-to-End Latency
       │
       ├── Retrieval
       ├── Tool calls
       ├── LLM time
       ├── Guardrails
       └── Response generation
```

## 5. Quality Monitoring

Monitor faithfulness, groundedness, relevance, correctness, hallucination rate, task success, user feedback and refusal rate.

For RAG, distinguish retrieval failure from generation failure:

```text
Question → Retriever → Documents → LLM → Answer
```

## 6. Model Drift

Model drift means model behaviour/performance changes over time. Monitor quality score, output distribution, error rate, latency, refusal rate, task success and safety metrics.

Potential causes include model/provider updates, prompt changes, input-distribution changes, retrieval changes and configuration changes.

## 7. Data Drift

Data drift means the input/context distribution changes over time.

For GenAI also monitor embedding distribution, retrieved-document distribution, context length, source-data freshness, document changes and query distribution.

## Model Drift vs Data Drift

```text
Quality ↓
   ↓
Check model version
   ↓
Check prompt version
   ↓
Check input/data distribution
   ↓
Check RAG retrieval
   ↓
Check model output
   ↓
Identify root cause
```

## Complete AI Monitoring Architecture

```text
                 USER REQUEST
                      │
                      ▼
                 AI APPLICATION
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
        Prompt       RAG        Agent
          │           │           │
          ↓           ↓           ↓
         LLM       Vector DB    Tools
          │           │           │
          └───────────┼───────────┘
                      ↓
                   RESPONSE
                      │
              ┌───────┴────────┐
              ↓                ↓
        OBSERVABILITY       EVALUATION
              │                │
     ┌────────┼────────┐       │
     ↓        ↓        ↓       ↓
   Cost    Latency   Tokens   Quality
     │        │        │       │
     └────────┼────────┴───────┘
              ↓
            DRIFT
          ┌───┴───┐
          ↓       ↓
        Data    Model
        Drift   Drift
          │       │
          └───┬───┘
              ↓
           ALERTING
              ↓
        INVESTIGATION
              ↓
       PROMPT / RAG /
       MODEL / DATA
       IMPROVEMENT
```

## AI Architect Interview Answer

> "I would monitor the system across five dimensions: reliability, cost, quality, security and drift. Reliability includes P50/P95/P99 latency, TTFT, errors and tool/RAG latency. Cost includes input/output tokens and spend per request, feature and user. Quality includes faithfulness, groundedness, relevance, hallucination and task success. Security monitoring covers prompt injection, jailbreaks, PII leakage and unauthorized tool usage. Finally, I would monitor data and model drift by tracking changes in input distributions, embeddings, retrieval behaviour and model output quality. All of this would be correlated through distributed traces so that an AI response can be traced back to its prompt, model, retrieved context, tools and evaluation result."

## One Sentence to Remember

> **AI monitoring is not just "Is my model up?" — it is "Is my AI system reliable, affordable, secure, high-quality, and behaving consistently as data, models and user behaviour change?"**
