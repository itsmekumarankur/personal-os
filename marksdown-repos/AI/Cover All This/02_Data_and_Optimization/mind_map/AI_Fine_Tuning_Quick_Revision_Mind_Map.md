# AI Fine-Tuning — Quick Revision Mind Map

> **Core rule:** Diagnose the problem first. Fine-tune when the business needs different learned behavior—not simply because the model lacks current facts.

```text
                     AI CUSTOMIZATION
                            |
                    What is the problem?
                            |
              +-------------+-------------+
              |             |             |
          Instructions   Missing facts   Learned behavior
              |             |             |
           Prompting        RAG         Fine-tuning
              |             |             |
       Tell it what to   Retrieve up-   Teach recurring
       do in this call   to-date facts  task patterns

                    FINE-TUNING METHODS
                            |
              +-------------+-------------+
              |                           |
        Full fine-tuning              PEFT methods
              |                           |
        Update most/all                 LoRA / QLoRA
        model parameters                 |
              |                     Base weights frozen
        High compute and              small adapters trained
        memory cost                       |
                                    lower training footprint

       +--------------+--------------+--------------+
       |              |              |              |
    1. DATA        2. EVALUATE     3. RISKS      4. DEPLOY
       |              |              |              |
   Quality examples Base vs tuned  Overfitting   Version model
   Clean/deduplicate Task success  Forgetting    Safety checks
   Train/validation Accuracy       Data leakage  Canary release
   Test sets         Safety        Bias           Monitor regressions
```

## The essential distinction

- **Prompting = telling:** instructions are supplied with the request.
- **Fine-tuning = teaching:** training updates model parameters to encourage desired behavior.
- **RAG = retrieving:** relevant and current information is supplied at inference time.

Example for a bank:
- Current interest rate → **RAG**
- Professional banking tone → **prompting or fine-tuning**
- Strict JSON output → **prompting first**, fine-tune only if justified by evidence
- Private, changing policy documents → **RAG**, with permissions and source freshness

## Cost and trade-offs

- Full fine-tuning trains many/all parameters and needs memory for weights, gradients, optimizer states, and activations.
- **PEFT** trains a small subset of parameters.
- **LoRA** freezes the base weights and trains small low-rank adapter matrices.
- **QLoRA** combines a quantized base model with adapter training to reduce memory needs.
- Fine-tuning also costs data preparation, evaluation, serving, maintenance, and retraining—not just the training run.

## Architect decision gate

1. Define the business failure and measurable target.
2. Try prompt improvements if instructions are the issue.
3. Use RAG if the problem is missing or changing knowledge.
4. Fine-tune only if repeated behavior/task adaptation is still inadequate.
5. Compare baseline and tuned model on held-out real tasks.
6. Test safety, regressions, and general capabilities before rollout.

> **Leadership question:** “Are we changing the model because behavior must change, or because we haven't provided the right information?”
