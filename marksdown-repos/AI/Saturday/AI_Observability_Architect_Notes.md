# AI Observability — Architect's Notes

> **Audience:** AI Architect / Engineering Architect  
> **Goal:** Understand AI/LLM observability from an enterprise architecture perspective in a ~7-minute read.

## Reference Articles

1. https://coresolutions.ltd/blog/llm-observability-opentelemetry-genai
2. https://valuestreamai.com/blog/ai-logging-observability-guide-2026
3. https://turion.ai/blog/langsmith-vs-langfuse-vs-arize-phoenix/
4. https://latitude.so/blog/best-llm-observability-tools-agents-latitude-vs-langfuse-langsmith

---

# 1. What Is AI Observability?

**AI Observability = the ability to understand what an AI system did, why it did it, how well it performed, where it failed, and how much it cost.**

Traditional systems often look like:

```text
Request → Service → DB → Response
```

AI systems are more like:

```text
User → Agent → LLM → Retrieval → Tools → APIs → More LLM calls → Validation → Response
```

An AI system can be technically healthy but functionally wrong.

For example:

```text
HTTP 200
Latency = 2 sec
No exception
CPU = normal
Memory = normal
```

Yet the LLM can still return a completely incorrect answer.

That is the fundamental difference between traditional monitoring and AI observability.

---

# 2. The Most Important Concept: Trace

For an AI Architect, **trace should be the fundamental debugging primitive**.

A traditional log might say:

```text
POST /portfolio/advice
200 OK
```

An AI trace should explain the entire execution:

```text
TRACE: user_request
│
├── Agent: PortfolioAgent
│
├── LLM Call
│     ├── Model: GPT-x
│     ├── Input tokens: 2,100
│     ├── Output tokens: 500
│     └── Latency: 1.8 sec
│
├── Tool Call: get_customer_profile
│     └── Latency: 120 ms
│
├── Retrieval
│     ├── Vector DB
│     ├── top_k = 5
│     └── relevance score
│
├── LLM Call
│     └── Latency: 2.1 sec
│
├── Tool Call: portfolio_api
│     └── Latency: 800 ms
│
├── Validation
│     └── FAILED
│
├── LLM Retry
│     └── Latency: 1.9 sec
│
└── Final Response
```

Now you can answer:

- Why was it slow?
- Which model was used?
- Why did the agent call the API twice?
- Why did retrieval produce poor context?
- Why did validation fail?
- How many tokens were consumed?
- What did this interaction cost?

For agentic AI, this **trace tree** is much more useful than flat logs.

---

# 3. AI Observability Architecture

Think about observability in four layers:

```text
                 AI APPLICATION
                       │
        ┌──────────────┴──────────────┐
        │                             │
      Agent                         RAG
        │                             │
   ┌────┼────┐                  ┌────┼────┐
   │    │    │                  │    │    │
  LLM Tool Tool              Embed Vector Rerank
        │                             │
        └──────────────┬──────────────┘
                       │
                OpenTelemetry
                       │
                OTel Collector
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      Traces         Metrics         Logs
        │              │              │
    Langfuse       Prometheus       Loki
    Phoenix        Grafana          SIEM
    LangSmith
                       │
                       ▼
              EVALUATION / QUALITY
                       │
                       ▼
              Feedback → Dataset
                       │
                       ▼
              Prompt / Model Change
                       │
                       ▼
                  Production
```

### Architectural principle

**Instrumentation should not be tightly coupled to the observability vendor.**

OpenTelemetry can provide the common telemetry layer, while observability platforms differentiate themselves through visualization, evaluation, prompt management, datasets, and AI/agent debugging.

---

# 4. OpenTelemetry — Why Should an AI Architect Care?

If you remember one infrastructure technology from this topic, remember:

> **OpenTelemetry (OTel).**

Instead of:

```text
Application
   ↓
Langfuse SDK
```

Prefer:

```text
Application
    ↓
OpenTelemetry
    ↓
OTel Collector
    ↓
┌─────────┬──────────┬──────────┐
Langfuse  Prometheus  SIEM
```

This creates a vendor-neutral telemetry layer.

Important GenAI telemetry concepts include:

```text
gen_ai.operation.name
gen_ai.provider.name
gen_ai.request.model
gen_ai.response.model
gen_ai.usage.input_tokens
gen_ai.usage.output_tokens
gen_ai.response.finish_reasons
gen_ai.tool.name
gen_ai.agent.name
gen_ai.conversation.id
```

The standards are evolving, so an architect should isolate instrumentation behind a thin abstraction instead of deeply coupling application code to one observability vendor.

---

# 5. What Should You Instrument?

Do not instrument only the LLM.

Instrument the **entire AI workflow**.

## A. LLM

Capture:

```text
Model
Provider
Input tokens
Output tokens
Latency
Temperature
Finish reason
Request/response status
Model version
```

## B. Agent

Capture:

```text
Agent ID
Agent version
Parent agent
Child agent
Decision
Tool selected
Number of iterations
Termination reason
```

## C. Tools

Capture:

```text
Tool name
Input
Output status
Latency
Retry count
Error
```

For example:

```text
Agent
  ↓
search_customer()
  ↓
get_portfolio()
  ↓
calculate_risk()
  ↓
LLM
```

Each operation should appear in the **same trace**.

## D. RAG

Capture:

```text
Query
Embedding model
Vector DB
Top-K
Retrieved documents
Similarity scores
Reranker
Final context
Retrieval latency
```

This is critical because when the answer is wrong, you need to determine:

> **Was the LLM wrong, or did we give the LLM bad context?**

---

# 6. Metrics: AI's Version of the Golden Signals

Traditional SRE focuses on:

```text
Latency
Traffic
Errors
Saturation
```

AI adds:

```text
Quality
Cost
```

## Performance

```text
P50 latency
P95 latency
P99 latency
Time-to-first-token
Time-to-last-token
```

## Reliability

```text
LLM error rate
Timeout rate
Tool failure rate
Retry rate
Fallback rate
Agent termination failures
```

## Cost

```text
Input tokens
Output tokens
Cost/request
Cost/session
Cost/customer
Cost/agent
Cost/model
```

## AI Quality

```text
Faithfulness
Relevance
Hallucination rate
Refusal rate
Task success
Groundedness
User feedback
```

## RAG

```text
Retrieval relevance
Context precision
Context recall
Faithfulness
Retrieval latency
```

### Architect rule

> **Do not monitor only infrastructure health. Monitor AI behaviour and business quality.**

---

# 7. Cost Observability

Cost can become a major architectural concern in agentic systems.

Consider:

```text
User request
    ↓
Agent
    ↓
LLM #1
    ↓
Tool
    ↓
LLM #2
    ↓
RAG
    ↓
LLM #3
```

Traditional monitoring says:

> Request succeeded.

AI FinOps needs:

```text
Request
 ├── LLM #1 = $0.02
 ├── Tool    = $0.00
 ├── LLM #2 = $0.05
 ├── RAG     = $0.01
 └── LLM #3 = $0.15

Total = $0.23
```

Therefore:

> **Token usage → pricing table → cost calculation**

Cost should generally be treated as a derived metric based on usage and pricing rather than assumed to be a universal telemetry field.

---

# 8. RAG Observability

Consider:

```text
Question
   ↓
Embedding
   ↓
Vector Search
   ↓
Top 10 documents
   ↓
Reranker
   ↓
Top 3 documents
   ↓
Prompt
   ↓
LLM
```

If the answer is wrong, there are two major possibilities.

## Problem A — Retrieval failure

```text
Correct answer exists
        ↓
Vector search fails
        ↓
Wrong documents retrieved
        ↓
LLM receives bad context
        ↓
Wrong answer
```

## Problem B — Generation failure

```text
Correct documents retrieved
        ↓
LLM receives correct context
        ↓
LLM ignores/misinterprets context
        ↓
Wrong answer
```

Without tracing retrieval and generation separately, you cannot distinguish these.

Important RAG metrics include:

- Context precision
- Context recall
- Context relevance
- Faithfulness
- Retrieval latency
- Document freshness
- Embedding quality/drift

---

# 9. Agent Observability

A simple LLM:

```text
User → LLM → Response
```

An agent:

```text
                Agent
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
     LLM       Search      Database
       │          │
       ↓          ↓
    Decision    Results
       │
       ↓
     Tool
       │
       ↓
    Another LLM
       │
       ↓
    Validator
       │
       ↓
    Response
```

Important questions become:

### Decision observability

> Why did the agent choose this tool?

### Path observability

> Why did it take 12 steps instead of 4?

### Loop detection

> Why did it call the same API three times?

### Cost explosion

> Why did this request consume 10× normal tokens?

### Failure propagation

> Which child agent caused the final failure?

For agentic systems, **trace trees** are therefore more useful than traditional flat logs.

---

# 10. Prompt Versioning Is Production Configuration

Traditional software tracks:

```text
Application v2.3.1
```

GenAI needs to track much more:

```text
Application v2.3.1
Prompt v7
Model GPT-X
RAG index v12
Retriever v3
```

Every trace should ideally contain:

```text
application.version
prompt.version
model.version
retriever.version
embedding.version
agent.version
```

Imagine quality suddenly drops at 10:32 AM.

You query:

```text
quality_score
       ↓
decreased at 10:32 AM
       ↓
prompt.version changed from v4 → v5
```

You have immediately narrowed the investigation.

---

# 11. PII and Security

This is especially important for enterprise and banking AI.

Example:

```text
Customer: John Smith
Account: XXXXX
PAN: XXXXX
Portfolio: XXXXX
```

You do not want every engineer or observability platform storing raw sensitive data.

A safer architecture:

```text
Application
     ↓
OTel
     ↓
OTel Collector
     ↓
PII Redaction
     ↓
Sampling
     ↓
Enrichment
     ↓
Observability Backend
```

Example:

```text
"Customer John Smith"
        ↓
"Customer [NAME]"
```

Architectural controls should include:

- PII redaction
- Encryption
- Access control
- Retention policies
- Audit trails
- Sampling
- Data residency controls

### Architect rule

> **Never make raw prompt/response logging the default.**

Capture metadata by default. Capture content only when there is a clear operational need and appropriate security controls.

---

# 12. Observability ≠ Evaluation

This distinction is critical.

### Observability asks:

> **What happened?**

Example:

```text
LLM latency       = 2.4 sec
Tokens            = 2,500
Tool calls        = 3
RAG documents     = 5
```

### Evaluation asks:

> **Was it good?**

Example:

```text
Faithfulness      = 0.72
Relevance         = 0.81
Task success      = FAIL
```

Therefore, a mature AI platform needs:

```text
                Production
                    ↓
                 Traces
                    ↓
                Failures
                    ↓
                Evaluation
                    ↓
                 Dataset
                    ↓
             Prompt / Model
                Improvement
                    ↓
                Regression
                   Tests
                    ↓
                Deployment
```

This is the **observability → evaluation → improvement loop**.

---

# 13. Where Major Tools Fit

Do not ask:

> "Which observability tool is best?"

Ask:

> **"What architectural problem am I solving?"**

## LangSmith

Strong fit when your architecture is heavily based on:

```text
LangChain
LangGraph
```

Useful capabilities include tracing, evaluations, prompt workflows, and deep integration with the LangChain ecosystem.

## Langfuse

Useful when you want:

```text
OpenTelemetry
+
Self-hosting
+
Framework independence
+
LLM tracing
+
Prompt/evaluation capabilities
```

Particularly relevant when infrastructure control or data residency matters.

## Arize Phoenix

Strong fit around:

```text
OpenTelemetry
+
RAG
+
Evaluation
+
ML/embedding monitoring
```

## Helicone

Useful for relatively quick LLM visibility and gateway-style capabilities with low instrumentation overhead.

## Braintrust

More evaluation-centric, especially when evaluation results need to participate in development and release workflows.

### The architectural takeaway

These tools overlap, but their strengths differ across:

```text
Tracing
Evaluation
RAG
Agent workflows
Prompt management
Self-hosting
OpenTelemetry
Developer experience
```

Choose based on architecture rather than brand popularity.

---

# 14. Enterprise AI Observability Architecture

If designing an enterprise AI platform, avoid making the observability platform itself an architectural dependency.

A good pattern is:

```text
                    AI APPLICATION
                          │
          ┌───────────────┼────────────────┐
          │               │                │
       Agent            RAG             Tools
          │               │                │
          └───────────────┼────────────────┘
                          │
                    OpenTelemetry
                          │
                          ▼
                  OTel Collector
                          │
             ┌────────────┼────────────┐
             │            │            │
          Traces        Metrics       Logs
             │            │            │
             ▼            ▼            ▼
         Langfuse     Prometheus     Loki/SIEM
         /Phoenix       Grafana
             │
             ▼
        AI Evaluation
             │
       ┌─────┴─────┐
       ↓           ↓
    Offline      Online
     Evals        Evals
       │           │
       └─────┬─────┘
             ↓
       Quality Gates
             ↓
      CI/CD Deployment
```

### Core architectural principle

> **OTel is the telemetry layer; the AI observability platform is a consumer of telemetry.**

This reduces vendor lock-in.

---

# 15. What I Would Monitor in a Banking AI Platform

For an enterprise/fintech AI platform, the dashboard should contain:

## Reliability

```text
LLM error rate
Tool failure rate
Timeouts
Retries
Fallback rate
Agent loop detection
```

## Performance

```text
P50/P95/P99 latency
TTFT
Tool latency
RAG latency
LLM latency
```

## Cost

```text
Cost/request
Cost/customer
Cost/use-case
Tokens/request
Model-wise spend
Provider-wise spend
```

## Quality

```text
Faithfulness
Groundedness
Relevance
Task completion
Hallucination
Refusal
User feedback
```

## Security

```text
PII detection
Prompt injection
Jailbreak attempts
Sensitive-data leakage
Unauthorized tool invocation
```

## RAG

```text
Retrieval precision
Retrieval recall
Context relevance
Embedding drift
Document freshness
```

## Agent

```text
Steps/request
Tool calls/request
Agent loops
Agent success rate
Decision failures
Fallback frequency
```

---

# 16. The 30-Second AI Architect Interview Answer

If asked:

> **"How would you design observability for an enterprise GenAI platform?"**

A strong answer is:

> "I would treat every AI workflow as a distributed trace rather than a collection of logs. LLM calls, retrieval, tool calls, agent decisions and validation steps would be represented as correlated spans using OpenTelemetry. An OTel Collector would handle routing, sampling, PII redaction and enrichment before sending telemetry to metrics, logging and AI-specific observability backends.
>
> I would monitor four dimensions: reliability and latency, token/cost consumption, AI quality, and security. For RAG I'd capture retrieval quality and context provenance; for agents I'd capture execution paths, tool calls, loops and decision outcomes.
>
> I'd also version prompts, models, agents and retrieval components so every production response is reproducible. Finally, I'd connect production traces to evaluation datasets and regression tests, creating a closed loop from production failure → evaluation → improvement → deployment."

That is the level at which an AI Architect should discuss observability—not merely saying:

> "We use Langfuse."

---

# 17. Mental Model to Remember

```text
             AI OBSERVABILITY
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
     TRACE        METRIC        LOG
       │            │            │
       └────────────┼────────────┘
                    ↓
              AI QUALITY
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
       RAG        AGENT        LLM
        │           │           │
        └───────────┼───────────┘
                    ↓
                  COST
                    ↓
                SECURITY
                    ↓
              EVALUATION
                    ↓
              IMPROVEMENT
```

## One sentence to remember

> **Traditional observability tells you whether the system is running; AI observability tells you what the AI did, why it did it, how much it cost, and whether what it did was actually good.**

---

# Reference Articles

- Core Solutions — LLM Observability with OpenTelemetry and GenAI  
  https://coresolutions.ltd/blog/llm-observability-opentelemetry-genai

- ValueStreamAI — AI Logging & Observability Guide 2026  
  https://valuestreamai.com/blog/ai-logging-observability-guide-2026

- Turion — LangSmith vs Langfuse vs Arize Phoenix  
  https://turion.ai/blog/langsmith-vs-langfuse-vs-arize-phoenix/

- Latitude — Best LLM Observability Tools for Agents  
  https://latitude.so/blog/best-llm-observability-tools-agents-latitude-vs-langfuse-langsmith
