# Fine-Tuning — Quick Revision Mind Map

> **Core rule:** Fine-tune to change **how the model behaves**. Use RAG to change **what information it can access**.

```text
                         FINE-TUNING
                              |
       +----------------------+----------------------+
       |                      |                      |
   1. PURPOSE             2. CHOOSE TOOL          3. METHODS
       |                      |                      |
   Pre-trained model      Prompting               Full fine-tuning
   + targeted data        -> instructions         -> update most/all
       |                  RAG                     parameters
       v                  -> current/private      PEFT
   Specialized               knowledge             -> update a small part
   behavior                Fine-tuning            LoRA
                           -> behavior/task        -> small trainable
                              adaptation              adapters
                                                      |
                                                  Base model stays
                                                  mostly frozen

       +----------------------+----------------------+
       |                      |                      |
   4. DATA PIPELINE        5. EVALUATION          6. RISKS
       |                      |                      |
   Collect data            Compare base vs        Overfitting
   Clean + deduplicate     fine-tuned model       Catastrophic forgetting
   Filter for quality      Accuracy               Data leakage
   Train/validation split  Precision/recall       Unsafe or biased behavior
   Fine-tune               Task success           Poor generalization
   Evaluate                Human review
   Model registry          Safety + regression
   Deploy                  tests
       |
   Data quality matters more than
   simply running a training job.

       +----------------------+----------------------+
                              |
                       7. PRODUCTION
                              |
                    Data preparation
                              |
                       Training job
                              |
                       Fine-tuned model
                              |
                        Model registry
                              |
                      Evaluation + safety
                              |
                      Canary deployment
                              |
                        GPU serving
```

## The 10-second decision

| Problem | First choice |
|---|---|
| “Follow these instructions / format the answer” | **Prompting** |
| “Use today's policy or a private document” | **RAG** |
| “Consistently classify, respond, or follow a specialized style” | **Fine-tuning** |
| Need specialized behavior **and** current/private knowledge | **Fine-tuning + RAG** |

## LoRA in one glance

- **Full fine-tuning:** update most/all model parameters; flexible, but costly in compute, memory, and storage.
- **PEFT:** train only a small subset of parameters.
- **LoRA (Low-Rank Adaptation):** keep the base model mostly frozen and train small adapter matrices.
- **Benefit:** smaller training footprint; multiple task-specific adapters can share one base model.

## Banking example

- Fine-tuning teaches: tone, response structure, complaint classification, domain-specific task patterns.
- RAG supplies: current product terms, internal documents, latest policies, regulatory information.
- Don't fine-tune a model just because it lacks today's policy—the policy may change tomorrow.

## Architect / Engineering Manager checklist

1. **Diagnose first:** behavior problem or missing-knowledge problem?
2. **Start with the simplest option:** prompting before training when it is sufficient.
3. **Protect data:** clean, deduplicate, quality-filter, and prevent sensitive-data leakage.
4. **Prove improvement:** compare against the base model on real tasks and general capabilities.
5. **Release safely:** evaluation → safety checks → canary → production; monitor regressions.
6. **Account for total cost:** training, GPU serving, evaluation, maintenance, and model updates.

## Quick recall

- **Fine-tuning changes:** model parameters / learned behavior.
- **RAG changes:** information supplied at inference time.
- **Pre-training:** broad patterns from huge datasets.
- **Instruction tuning:** examples of instructions and desired responses.
- **Model registry:** stores and versions model artifacts.
- **Overfitting:** learns training examples too specifically.

> **Leadership question:** “Are we solving a behavior problem or a knowledge problem?”
