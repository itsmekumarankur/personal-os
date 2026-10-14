# Fine-Tuning & Customization — Architect Quick Revision Mind Map

> **Architect principle:** Diagnose first, choose the least complex solution that meets the business requirement, and prove the improvement with evidence.

```text
                 MODEL CUSTOMIZATION DECISION
                              |
                    Diagnose the failure
                              |
             +----------------+----------------+
             |                |                |
       Missing facts     Instructions      Repeated behavior
             |                |                |
            RAG         Prompt engineering   Fine-tuning
             |                |                |
      Current/private   Fast to test;       Train a reusable
      knowledge         no model training   behavior adaptation

                     FINE-TUNING OPTIONS
                              |
              +---------------+----------------+
              |                                |
          Full fine-tuning                   PEFT
              |                                |
      Update all/most weights            Train small subset
      Flexible, resource-heavy           of parameters
                                               |
                                         LoRA / QLoRA
                                               |
                                    Freeze base; train adapters
                                    QLoRA uses quantized base

      +----------------+----------------+----------------+
      |                |                |                |
   1. DATA          2. COST          3. EVIDENCE       4. OPERATIONS
      |                |                |                |
   Quality samples  Training memory   Baseline tests   Versioning
   Deduplicate      GPU / runtime     Held-out data    Safety review
   Remove leakage   Serving cost      Task success     Canary rollout
   Split datasets   Maintenance       Regression tests Monitoring
                    Retraining        Human evaluation Rollback plan
```

## Full fine-tuning: why memory exceeds model size

Training memory includes:

**Weights + gradients + optimizer state + activations + runtime overhead**

A 7B model with FP16 weights uses roughly 14 GB for weights alone. Full training can require substantially more memory; the exact amount depends on optimizer, precision, sequence length, batch size, and memory-saving techniques. Do not size a training GPU using weight memory alone.

## LoRA mental model

- Original weight matrix \(W\) remains frozen.
- Learn a smaller update \(\Delta W = B \times A\).
- New effective weights: \(W_{\text{new}} = W + \Delta W\).
- Lower trainable-parameter count usually reduces training memory and makes task-specific adapters easier to store.
- Validate whether the adaptation is expressive enough for the task.

## Decision table

| Requirement | First option to evaluate |
|---|---|
| Current facts, policy, rates, customer-specific data | RAG |
| One-off or adjustable instructions | Prompting |
| Consistent style, format, classification, task behavior | Prompting baseline, then fine-tuning if needed |
| Large, fundamental model behavior change with suitable data/resources | Consider full fine-tuning |
| Targeted customization with limited training resources | PEFT / LoRA / QLoRA |

## Production lifecycle

**Define target → Prepare data → Train → Evaluate → Safety/regression tests → Register/version → Canary deploy → Monitor → Roll back or iterate**

Measure:
- Task quality and failure rates
- Safety and unwanted behavior
- General capability regressions
- Training and serving cost
- Latency and throughput
- Maintenance burden as requirements change

## Architect / VP-level questions

1. What business metric should improve?
2. Why won't prompting or RAG solve the problem?
3. Is the training data representative, lawful to use, and free of leakage?
4. What is the baseline, and what result justifies the cost?
5. What capabilities could regress?
6. Who owns model updates, monitoring, and rollback?

> **Remember:** RAG changes what the model can see. Prompting tells it what to do now. Fine-tuning changes learned behavior.
