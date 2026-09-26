# Fine-Tuning — A 5-Minute AI Architect Guide

> **Goal:** Understand what fine-tuning changes, when to use it instead of prompting or RAG, the major fine-tuning approaches, and the production architecture around training and model deployment.

---

## 1. What Is Fine-Tuning?

Fine-tuning takes a pre-trained model and trains it further on a targeted dataset.

```text
                 Pre-trained Model
                        |
                        v
                Domain Dataset
                        |
                        v
                 Fine-Tuning
                        |
                        v
             Specialized Model
```

The base model already knows general patterns.

Fine-tuning changes its parameters so it behaves better for a particular task, style, domain, or instruction format.

---

# 2. Pre-training vs Fine-Tuning

### Pre-training

```text
Huge generic dataset
        |
        v
Massive compute
        |
        v
Base model
```

### Fine-tuning

```text
Base model
    +
Smaller targeted dataset
    |
    v
Specialized behavior
```

The difference:

```text
Pre-training
= Learn broad language/world patterns

Fine-tuning
= Adapt the model to a target behavior/domain/task
```

---

# 3. Fine-Tuning vs Prompting vs RAG

This is one of the most important AI Architect decisions.

```text
                 Need?
                   |
        +----------+----------+
        |          |          |
      Prompt       RAG     Fine-tune
        |          |          |
 Behavior      Knowledge    Behavior /
 formatting    / context    capability
```

Use **prompting** when:

```text
"Tell the model how to behave."
```

Use **RAG** when:

```text
"Give the model current/private information."
```

Use **fine-tuning** when:

```text
"Adapt the model's behavior/capability using examples."
```

These can also be combined.

---

# 4. Typical Fine-Tuning Dataset

A supervised dataset might look like:

```text
Input:
"Classify this customer complaint..."

Output:
"Billing Issue"
```

Many examples:

```text
Example 1 -> Label A
Example 2 -> Label B
Example 3 -> Label A
...
```

For instruction tuning:

```text
Instruction
     |
     v
Input
     |
     v
Desired Response
```

Dataset quality matters enormously.

---

# 5. Full Fine-Tuning

In full fine-tuning:

```text
Base Model
    |
    v
All / most model parameters updated
    |
    v
New Model
```

Conceptually:

```text
Model
+---------------------+
| Parameters          |
| ██████████████████  | <-- updated
| ██████████████████  |
| ██████████████████  |
+---------------------+
```

Advantages:

- maximum flexibility
- can strongly adapt the model

Costs:

- high GPU memory
- expensive training
- large model checkpoints
- operational complexity

---

# 6. Parameter-Efficient Fine-Tuning

PEFT methods update only a small portion of parameters.

```text
Base Model
    |
    +------------------+
    |                  |
 Frozen parameters   Small trainable
                     parameters
                          |
                          v
                     Fine-tuned
```

One popular technique is **LoRA**.

---

# 7. LoRA

LoRA means **Low-Rank Adaptation**.

Instead of modifying the full weight matrix:

```text
Original W
```

LoRA learns smaller matrices that represent an update:

```text
W' = W + ΔW

where

ΔW ≈ A × B
```

Conceptually:

```text
                 Base Model
                    |
                    | Frozen
                    v
             +-------------+
Input ------>|     W       |------+
             +-------------+      |
                                   +--> Output
             +-------------+      |
Input ------>|   A × B     |------+
             +-------------+
                 Trainable
```

This dramatically reduces the number of trainable parameters.

---

# 8. Why LoRA Is Useful

Instead of storing:

```text
Full model copy
```

you can often store:

```text
Base model
     +
Small adapter
```

Architecture:

```text
             Base Model
                 |
       +---------+---------+
       |                   |
       v                   v
   Adapter A            Adapter B
   Finance              Support
       |                   |
       v                   v
   Task A              Task B
```

This can make multiple specialized variants easier to manage.

---

# 9. Fine-Tuning Pipeline

```text
Raw Data
   |
   v
Cleaning
   |
   v
Deduplication
   |
   v
Quality Filtering
   |
   v
Train / Validation Split
   |
   v
Fine-Tuning
   |
   v
Evaluation
   |
   v
Model Registry
   |
   v
Deployment
```

The hardest part is often not running the training job.

It is creating **high-quality training data and reliable evaluation**.

---

# 10. Evaluation

Do not ask only:

> "Did training loss decrease?"

Measure the actual business task.

```text
Fine-tuned model
       |
       v
Evaluation suite
       |
       +--> Accuracy
       +--> Precision/Recall
       +--> Task success
       +--> Human evaluation
       +--> Safety
       +--> Regression tests
```

Compare:

```text
Base model
    vs
Fine-tuned model
```

on both target tasks and important general capabilities.

---

# 11. Fine-Tuning Risks

Fine-tuning can introduce:

- overfitting
- catastrophic forgetting
- data leakage
- unsafe behavior
- poor generalization
- biased training behavior

Therefore:

```text
Training
   |
   v
Evaluation
   |
   v
Safety checks
   |
   v
Canary deployment
   |
   v
Production
```

---

# 12. Fine-Tuning and RAG Can Work Together

Suppose a bank wants an AI assistant.

Fine-tuning can teach:

```text
Tone
Output format
Classification behavior
Domain-specific task patterns
```

RAG can provide:

```text
Current policies
Product details
Internal documents
Regulatory information
```

Architecture:

```text
                    User
                      |
                      v
                 Fine-tuned LLM
                      ^
                      |
                     RAG
                      |
              +-------+-------+
              |               |
          Retriever       Vector DB
              |
              v
        Current knowledge
```

---

# 13. When Fine-Tuning May Be the Wrong Tool

If the problem is:

```text
"Model doesn't know today's policy."
```

Fine-tuning may not be the best solution.

Prefer:

```text
RAG
```

If the problem is:

```text
"Model needs to always return our exact classification format."
```

Fine-tuning may be useful, possibly combined with structured output.

If the problem is:

```text
"Model doesn't know a private document."
```

RAG is usually the more direct architectural mechanism.

---

# 14. Production Fine-Tuning Architecture

```text
                 Data Sources
                      |
                      v
              Data Preparation
                      |
                      v
                Training Job
                      |
              +-------+-------+
              |               |
              v               v
          Base Model      Training Data
              |               |
              +-------+-------+
                      |
                      v
                Fine-tuned
                   Model
                      |
                      v
                Model Registry
                      |
                      v
                Evaluation
                      |
                      v
              Model Deployment
                      |
                      v
                 GPU Serving
```

---

# 15. Architect's Cheat Sheet

| Concept | Meaning |
|---|---|
| Fine-Tuning | Further training of a pre-trained model |
| Full Fine-Tuning | Updates most/all model parameters |
| PEFT | Parameter-efficient fine-tuning |
| LoRA | Low-rank adapter-based fine-tuning |
| Adapter | Small trainable component attached to a base model |
| Instruction Tuning | Training on instruction-response examples |
| RAG | Supplies external knowledge at inference time |
| Overfitting | Model learns training examples too specifically |
| Model Registry | Stores/version-controls model artifacts |

---

## Final Mental Model

```text
             Base Model
                  |
       +----------+----------+
       |                     |
   Prompting                Fine-tuning
                             |
                             v
                         Specialized
                           behavior
                             |
                  +----------+----------+
                  |                     |
                 RAG               Structured
                  |                  Output
                  +----------+----------+
                             |
                             v
                         Production
                             |
                             v
                            LLM
```

> **Fine-tuning changes the model; RAG changes the information available to the model at inference time.**

That distinction is fundamental for AI architecture.
