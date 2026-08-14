# 🎯 Fine-Tuning with LoRA & PEFT — Teaching a Small LLM a Specific Job — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty Colab notebook" to "a small open-source model fine-tuned to classify financial news sentiment better than it could zero-shot." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

Think of this notebook as **eight stops on a road trip**:

```
🏁 START      🔧 SETUP+GPU      📊 LOAD & SPLIT DATA      💬 FORMAT FOR CHAT
Overview  →  Libs + Login  →  Train/Test Sets     →  Structured Prompts

📏 EVALUATION METRICS      🎲 ZERO-SHOT BASELINE      🛠️ FINE-TUNE (LoRA)      🏆 EVALUATE THE UPGRADE
Precision/Recall/F1   →  How Good "Out of the Box"? →  Teach It the Task →  Before vs. After
```

By the end, you go from "a generic small LLM that sort of gets sentiment analysis" to "a purpose-tuned model that's measurably better at this exact task" — and you can prove it with numbers.

---

## Stop 1 — 🏁 Understand the Problem Statement and Business Case
**What's happening:** Screenshots and framing introduce the core comparison this notebook is built to answer: does **fine-tuning** an open-source model on your specific data actually beat just using it **zero-shot** (straight out of the box, no training)?

**Why it matters:** This sets up a genuine experiment, not just a demo — everything that follows exists to produce a fair, measurable answer to that question.

---

## Stop 2 — 🔧 Import Key Libraries and Datasets
**What's happening:** The heaviest toolbox yet gets installed:
- `transformers`, `accelerate`, `torch` — the model-running fundamentals
- `datasets` — for loading the financial sentiment dataset
- **`peft`** — Parameter-Efficient Fine-Tuning, the library that makes LoRA possible
- **`trl`** — Hugging Face's training library, providing `SFTTrainer`
- `scikit-learn` — for accuracy, classification reports, and confusion matrices later
- `gradio` — for a UI (though the heavy lifting here is model comparison, not a chat app)

A Hugging Face login and GPU check follow the now-familiar pattern.

**Why it matters:** Fine-tuning is a fundamentally heavier task than inference-only work in earlier notebooks — this stop assembles the specific tools needed to actually *train*, not just *run*, a model.

**Practice challenge:** Confirm a GPU is detected, and think through why GPU access is even *more* critical here than in prior projects — training involves backpropagation across millions of parameters, which would take days on a CPU versus minutes/hours on a GPU.

---

## Stop 3 — 📊 Load and Prepare the Financial News Dataset
**What's happening:** The `Daniel-ML/sentiment-analysis-for-financial-news-v2` dataset is loaded from the Hugging Face Hub — financial news sentences labeled `positive`, `negative`, or `neutral`. After inspecting its structure and unique labels, it's split into a **90% training set** and a **10% test set** (with a fixed random seed for reproducibility).

**Why it matters:** The train/test split is the backbone of the entire experiment — the model only ever *learns* from the training set, and is only ever *judged* on the test set it hasn't seen, which is what makes the later comparison fair.

**Practice challenge:** Use Seaborn to count how many samples fall into each sentiment class, and think about how class imbalance could bias both training and evaluation.

---

## Stop 4 — 💬 Format the Data into Supervised Fine-Tuning (SFT) Format
**What's happening:** Raw `(text, sentiment)` pairs aren't directly usable for training a chat-style model — they need to look like a real conversation. A `format_for_sft_gemma()` function wraps each example into a structured chat template (using Gemma's special tokens like `<start_of_turn>user` / `<start_of_turn>model`), embedding both the question ("classify this sentence") *and* the correct answer directly into the training text.

**Why it matters:** This is the secret to how SFT training actually works — the model isn't taught abstract rules, it's shown thousands of complete "conversations" where the correct label always follows the question, and learns the pattern via ordinary next-token prediction.

**Practice challenge:** Try a different sample from the dataset, and compare the formatted output using the DeepSeek model's chat template versus Gemma's — noting how their special tokens differ.

---

## Stop 5 — 📏 Confusion Matrix & Classification Metrics (Precision, Recall, F1-Score)
**What's happening:** A conceptual stop covering how to actually *judge* a classifier fairly: accuracy alone can be misleading (especially with imbalanced classes), so this introduces **precision**, **recall**, **F1-score**, and the **confusion matrix** as the real toolkit for evaluation.

**Why it matters:** These are exactly the metrics used two stops later to compare the zero-shot and fine-tuned models — understanding them here makes those results actually interpretable rather than just "a number that's bigger."

---

## Stop 6 — 🎲 Perform Zero-Shot Classification with the Base Model (Inference Only)
**What's happening:** Before any training happens, the notebook establishes a **baseline**: how well does `google/gemma-3-1b-it` (loaded in 4-bit quantization, untouched by any fine-tuning) do at this exact sentiment task, just from a well-written prompt?
1. Load the quantized base model and tokenizer
2. Build a zero-shot prompt explicitly listing the three allowed labels
3. Run inference across the entire test set
4. Compute accuracy, a full classification report, and a confusion matrix

**Why it matters:** Without this baseline, "the fine-tuned model got 85% accuracy" means nothing — this stop gives you the "before" picture the whole experiment is designed to beat.

**Practice challenge:** Simplify the zero-shot system prompt (e.g., dropping the explicit label list) and see whether — and how much — performance changes, building intuition for why small models can be quite prompt-sensitive.

---

## Stop 7 — 🛠️ Fine-Tuning the Open Source Model (PEFT/LoRA & SFTTrainer)
**What's happening:** The centerpiece of the notebook — actually teaching the model this specific task:
- **PEFT (Parameter-Efficient Fine-Tuning):** instead of updating all of a model's billions of parameters, small trainable "adapter" layers are added on top, and only *those* get trained
- **LoRA (Low-Rank Adaptation):** the specific PEFT technique used, injecting compact trainable low-rank matrices into the model's layers
- **`SFTTrainer`:** wraps the whole training loop, working on a causal language-modeling objective — the model simply learns to predict the correct label token as "the next word" after seeing the formatted prompt from Stop 4
- `TrainingArguments` configure the practical training details: batch size, gradient accumulation, learning rate, and number of epochs — tuned to fit within Colab's free-tier limits

**Why it matters:** LoRA is *why* this fine-tuning is even feasible on free hardware — full fine-tuning of billions of parameters would be far too memory-hungry, but training a small set of adapter weights fits comfortably.

---

## Stop 8 — 🏆 Evaluate the Fine-Tuned Model
**What's happening:** The moment of truth. The fine-tuned adapter is reloaded and merged back onto a freshly loaded copy of the base model:
1. Load the tokenizer from the saved adapter directory
2. Reload the quantized base model
3. Attach the trained LoRA adapter weights on top
4. Run the *exact same* zero-shot-style evaluation function from Stop 6 — same test set, same metrics — but now using the fine-tuned model

The resulting accuracy, classification report, and confusion matrix can be placed directly side-by-side against Stop 6's baseline numbers.

**Why it matters:** This closes the loop on the original business question from Stop 1 — with matched methodology (same test data, same metrics, same prompt style), you get a genuinely fair, numeric answer to "did fine-tuning actually help?"

**Practice challenge:** Plot the fine-tuned model's confusion matrix and compare it directly against the base model's — which classes improved most, and are there any classes where fine-tuning didn't help (or hurt)?

---

## 🏆 What You Walk Away With
By the end of this notebook, you've run a genuine, rigorous **fine-tuning experiment**:

✅ Learned how PEFT and LoRA make fine-tuning feasible on free GPU hardware
✅ Correctly split data into training and held-out test sets
✅ Formatted raw labeled data into a proper chat-style SFT training format
✅ Learned the precision/recall/F1/confusion-matrix toolkit for fair classifier evaluation
✅ Measured a zero-shot baseline before touching any training
✅ Fine-tuned a real open-source model using `SFTTrainer` and a LoRA adapter
✅ Reloaded and evaluated the fine-tuned model under identical conditions to prove (or disprove) the improvement

**Next natural steps** (not in this notebook, but the logical Stop 9): training for more epochs or tuning the learning rate to see if performance improves further, and testing whether the fine-tuned adapter generalizes to financial news from a different source than the training data.

---

*Guide generated from `day9-finetuning-lora-peft-notes.ipynb`*
