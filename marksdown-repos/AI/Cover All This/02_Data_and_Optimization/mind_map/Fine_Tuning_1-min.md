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

Think of an AI model as a student who already knows many things.

1. PEFT — The overall approach
Instead of retraining the entire AI model, train only a small part of it. This saves time, money, and computing power.

2. LoRA — One specific method of doing PEFT
Instead of changing the student's original textbook, you give them a small set of extra notes to learn the new topic.

Remember: PEFT is the strategy; LoRA is one way to implement that strategy.
- **Benefit:** smaller training footprint; multiple task-specific adapters can share one base model.

## Banking example

- Fine-tuning teaches: tone, response structure, complaint classification, domain-specific task patterns.
- RAG supplies: current product terms, internal documents, latest policies, regulatory information.
- Don't fine-tune a model just because it lacks today's policy—the policy may change tomorrow.

> **Leadership question:** “Are we solving a behavior problem or a knowledge problem?”
