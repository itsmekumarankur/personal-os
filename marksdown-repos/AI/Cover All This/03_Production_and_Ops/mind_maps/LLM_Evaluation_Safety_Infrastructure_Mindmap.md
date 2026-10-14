# LLM Evaluation, Safety & AI Infrastructure — Mind Map

> **Core idea:** Production readiness means proving the AI works, controlling what it can do, and continuously measuring behavior, risk, latency, and cost.

```text
PRODUCTION AI
├── 1. Evaluation — “Is it good enough?”
│   ├── Public benchmarks: general capability; not proof of app quality
│   ├── Application-specific golden dataset: normal + edge + failure cases
│   ├── Automated metrics / rules
│   ├── LLM-as-a-Judge: pointwise, pairwise, reference-based, rubric-based
│   └── Human review: domain nuance, safety, real user satisfaction
├── 2. Quality dimensions
│   ├── Correctness and completeness
│   ├── Groundedness / faithfulness to source
│   ├── Relevance and task success
│   ├── Safety and policy compliance
│   └── Hallucination detection and citation checks
├── 3. Judge limitations
│   ├── Position bias, verbosity bias, self-preference
│   ├── Style may be mistaken for substance
│   └── Calibrate against a human-reviewed gold set; judge ≠ ground truth
├── 4. Hallucination
│   ├── Intrinsic: contradicts provided source
│   ├── Extrinsic: claim is unsupported by source
│   └── Signals: source/citation checks, entailment/NLI, consistency (not proof)
├── 5. Safety controls
│   ├── Input: validate, detect injection/jailbreak, classify risk
│   ├── Retrieval/tools: least privilege, authorization, scoped data access
│   ├── Output: policy checks, grounding/format validation, PII filtering
│   └── Operations: audit, incident response, abuse limits, red-team tests
├── 6. AI infrastructure
│   ├── Gateway/router: select model by task, cost, latency, capability
│   ├── Serving: inference workers, GPU capacity, queueing, batching
│   ├── RAG: retrieval, vector index, context and source freshness
│   ├── Observability: traces + metrics + logs
│   └── Governance: versioning, access control, evaluation gates, rollback
└── 7. Continuous loop
    └── Evaluate → release gate → monitor traces/feedback → review failures
        → update dataset / prompts / retrieval / model / guardrails → re-evaluate
```

## Evaluation approaches — when to use which

| Method | Best use | Limitation |
|---|---|---|
| Public benchmark | Compare broad model capability | May not represent your application |
| Golden dataset | Regression testing for your real use cases | Needs maintenance and coverage |
| Automated checks | Fast, repeatable rules (format, citations, policy) | Cannot capture every nuance |
| LLM-as-a-Judge | Scale rubric-based scoring/comparison | Has biases; must be calibrated |
| Human review | Domain nuance, safety, ambiguous cases | Expensive and slower |

## Build a useful evaluation set

Include:
- easy and common requests
- normal business flows
- edge cases and ambiguous questions
- adversarial prompts and injection attempts
- unsupported questions that should be refused or escalated
- sensitive-data and authorization cases
- known hallucination traps and source conflicts

Track performance by use case and risk level, not just one aggregate score.

## Safety design — defense in depth

```text
User input
   ↓
Input validation / injection checks
   ↓
Identity + authorization + scoped retrieval
   ↓
Model routing → RAG / tools → generation
   ↓
Output validation / safety / PII checks
   ↓
Response or safe refusal/escalation

Across every stage: traces + metrics + audit + evaluation
```

A guardrail is not a substitute for authorization. Enforce permissions in APIs and data layers; do not rely on the model to decide whether a user may access protected information.

## Architect's release checklist

- [ ] Define quality, safety, latency, and cost targets.
- [ ] Create a representative golden dataset, including edge cases.
- [ ] Compare automated and human judgments; calibrate any LLM judge.
- [ ] Test prompt injection, data leakage, tool misuse, and refusal behavior.
- [ ] Enforce least privilege and validate tool/API authorization outside the model.
- [ ] Trace prompt/model/context/tool versions for every important request.
- [ ] Use staged rollout, monitoring, rollback, and incident ownership.
- [ ] Feed production failures into the evaluation dataset.

## Interview recall

**Question:** How do you know an AI assistant is safe and good enough for a bank?

**Answer structure:** Define risk-based criteria → evaluate against a business-specific golden set → combine automated, judge, and human review → enforce input/tool/output controls → trace and monitor production → use feedback for continuous improvement.

**One-line memory hook:** *Evaluation proves quality; safety constrains risk; observability explains production behavior.*

## Self-test

- [ ] Distinguish a public benchmark from an application golden dataset.
- [ ] Explain intrinsic vs extrinsic hallucination.
- [ ] Name three LLM-as-a-Judge biases.
- [ ] Explain why authorization must be enforced outside the LLM.
- [ ] Describe the production evaluation and improvement loop.
