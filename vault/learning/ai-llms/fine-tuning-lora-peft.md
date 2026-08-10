---
tags: [ai, llms, fine-tuning, lora, peft, open-source]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/llm-engineering-bootcamp/day9]
---

# Fine-Tuning — LoRA & PEFT

Teaching a model a specific job without retraining all its weights.

## The Problem with Full Fine-Tuning

A 7B parameter model has ~7 billion floating-point numbers to update. Full fine-tuning requires backprop through all of them — too memory-hungry for free or low-cost GPU environments.

## PEFT — Parameter-Efficient Fine-Tuning

Train only a small subset of the model's parameters. The base model is frozen; you add small trainable components on top. LoRA is the dominant PEFT technique.

## LoRA — Low-Rank Adaptation

Instead of updating the full weight matrix W, decompose the update into two small matrices:
```
W_new = W + (A × B)
```
Where A and B are low-rank (rank 4–16 is typical). You only train A and B — millions of parameters instead of billions. At inference, merge them back in.

**The analogy from the day9 notebook:** don't replace the engine, add a turbocharger. The original model is unchanged; you carry the adapter separately.

## SFT Format — How the Training Data Works

The model doesn't learn abstract rules. It sees thousands of complete Q&A pairs formatted as conversations, and learns to predict the correct next token:

```
<user> Classify this financial news sentence: "Company Q beats earnings." </user>
<assistant> positive </assistant>
```

The format uses the target model's chat template (Gemma uses `<start_of_turn>`, DeepSeek uses its own tokens). Mismatch in template = degraded training.

## Evaluation: Zero-Shot Baseline vs. Fine-Tuned

The rigorous approach from the day9 experiment:
1. Measure base model zero-shot accuracy (no training, just a well-written prompt)
2. Fine-tune with LoRA on your labeled data
3. Evaluate the fine-tuned model under identical conditions
4. Compare with precision/recall/F1/confusion matrix — not just raw accuracy

Accuracy alone is misleading with class imbalance. F1 is more honest.

## Tooling

- `peft` (HuggingFace): LoRA config, wraps any transformer model
- `trl` SFTTrainer: handles the training loop
- `transformers` + `accelerate` + `torch`: model loading and GPU management
- 4-bit quantization (bitsandbytes): loads the base model in reduced precision so it fits in GPU RAM

## When to Reach for This (vs. RAG)

Fine-tune when the task is narrow, stable, and label-defined. For BFSI compliance content that changes monthly, RAG is better. For fixed sentiment classification on a domain corpus — fine-tuning wins.

## Related

- [[learning/ai-llms/rag]] — The other path when data changes often
- [[learning/ai-llms/llm-engineering-bootcamp]] — Day 9 of the bootcamp
