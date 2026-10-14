# MLOps vs LLMOps — Mind Map for Quick Recall

> **Core distinction:** MLOps operationalizes ML models; LLMOps operationalizes the LLM-powered application around the model.

```text
AI OPERATIONS
├── MLOps = model lifecycle
│   ├── Data → preparation → features
│   ├── Training → experiments → evaluation
│   ├── Model registry → deployment → monitoring
│   └── Drift → retraining / governance
├── LLMOps = LLM application lifecycle
│   ├── Prompt + model + context
│   ├── RAG / embeddings / vector index / retrieved documents
│   ├── Agents and tools
│   ├── Guardrails and safety
│   ├── Evaluation: groundedness, relevance, correctness, hallucination
│   └── Tracing, tokens, latency, cost, feedback
└── Shared foundations
    └── Versioning, CI/CD, testing, monitoring, security, governance
```

## Comparison at a glance

| Dimension | MLOps | LLMOps |
|---|---|---|
| Primary unit | ML model and dataset | LLM application/workflow |
| Typical output | Score/classification/prediction | Generated answer or action |
| Main artifacts | Data, features, model | Prompt, model, context, RAG, tools, guardrails |
| Improvement loop | Often retrain/redeploy | Often tune prompt, retrieval, model, tools, or guardrails |
| Evaluation | Accuracy, precision, recall, F1, AUC, RMSE | Groundedness, relevance, correctness, safety, completeness |
| Monitoring | Accuracy, latency, data/model drift | Quality, tokens, cost, latency, tool behavior, safety |
| Cost profile | Often training + inference | Often repeated inference/token cost |
| Debugging | Data → features → model | Prompt → context → model → tools → response |

## Mental models

```text
MLOps:
Data → Features → Model → Prediction → Monitor → Retrain

LLMOps:
User → Prompt → Context/RAG → Model ↔ Tools/Agent
     → Guardrails → Response → Evaluate → Improve
```

## Why LLMOps needs extra visibility

For each response, identify:
- Which prompt and model version were used?
- Which documents/context were retrieved?
- Which tools were called and with what outcome?
- How many input/output tokens were consumed?
- What did the request cost and how long did it take?
- Was the answer correct, grounded, safe, and useful?

## Versioning / lineage

A reproducible AI response may depend on:

`Prompt version + Model version + Retriever version + Vector index + Source documents + Tool versions + Guardrail version`

If one answer fails, this lineage helps pinpoint what changed.

## Architect's decision rule

Do not ask, “Do we have MLOps, so are we done?” Ask, “Can we observe and evaluate the full GenAI workflow, including prompts, retrieval, tools, safety, quality, and cost?”

**One-line memory hook:** *MLOps runs the model lifecycle; LLMOps runs the AI application lifecycle.*

## Self-test

- [ ] Give a bank example of MLOps (e.g., loan-default prediction).
- [ ] Name five LLMOps artifacts beyond model weights.
- [ ] Explain why changing a prompt may improve an application without retraining the model.
- [ ] Name three LLM evaluation measures that differ from classic ML metrics.
- [ ] Explain how version lineage helps debug a bad answer.
