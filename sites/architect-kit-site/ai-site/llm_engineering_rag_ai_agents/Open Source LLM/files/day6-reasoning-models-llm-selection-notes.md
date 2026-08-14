# 🧩 Reasoning Models & Choosing the Right LLM — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty Colab notebook" to "a DeepSeek reasoning model that reads real financial news and explains its sentiment call step by step, wrapped in a Gradio app." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

Think of this notebook as **eight stops on a road trip**:

```
🏁 START      🤗 DATASETS+SETUP      📰 LOAD NEWS DATA      🧠 LOAD DEEPSEEK
Overview  →  Libs + HF Login   →  Real Financial News →  A "Reasoning" Model

🧭 CHOOSE THE RIGHT MODEL      🏆 LEADERBOARDS      🔍 REASON + CLASSIFY      🎛️ GRADIO APP
Decision Framework        →  Compare Benchmarks →  Structured Sentiment →  Click & Analyze
```

By the end, you go from "which AI model should I even use?" to a working tool that reads real financial headlines and produces a step-by-step reasoning trace *plus* a clean sentiment label — through a clickable web interface.

---

## Stop 1 — 🏁 Project Overview & Key Learning Objectives
**What's happening:** The notebook picks up where the previous open-source lesson left off. Instead of just classifying news as positive/negative/neutral, the goal here is to use a model that can **explain its reasoning** — using a DeepSeek model known for strong instruction-following and step-by-step logic.

**Why it matters:** Sets the north star for the whole notebook — not just "get an answer" but "get an answer *with a visible thought process*," which matters a lot when you need to trust or audit an AI's financial call.

---

## Stop 2 — 🤗 Explore Hugging Face Datasets & Install Key Libraries
**What's happening:**
- Installs `transformers`, `accelerate`, `bitsandbytes`, `torch` (same reasoning-model toolkit as before), plus a new addition: **`datasets`** — Hugging Face's library for pulling ready-made datasets straight from the Hub.
- Repeats the Hugging Face login step (needed for gated models).
- Runs the familiar GPU availability check.

**Practice challenge:** Browse the Hugging Face Datasets Hub, find the most-downloaded news dataset, search specifically for `all_news_finance_sm_1h2023`, and try the AI Query feature to filter news by a specific source like CNBC.

**Why it matters:** This is the toolbox-and-fuel stop — libraries installed, GPU confirmed, and now a whole new capability (structured dataset loading) added to the kit.

---

## Stop 3 — 📰 Load Financial News Datasets from Hugging Face
**What's happening:** The `PaulAdversarial/all_news_finance_sm_1h2023` dataset is pulled directly from the Hub with `load_dataset()`. Its structure and columns (`title`, `description`, and more) are inspected, then viewed as a Pandas DataFrame for readability. A small helper function `combine_news_text()` merges the title and description into one clean `full_text` field — the actual input the LLM will read.

**Why it matters:** Real, messy, real-world data replaces a single hand-typed test sentence — the model is about to be tested on genuine financial news headlines, not toy examples.

**Practice challenge:** Inspect other available columns (like `main_domain`, `created_at`), display 10 sample rows, and figure out how to pull just the `full_text` of the 100th news item.

---

## Stop 4 — 🧠 Load & Test the DeepSeek Reasoning Model
**What's happening:** The model of choice is `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` — small enough (1.5B parameters) to fit on a free Colab GPU with 4-bit quantization, but strong at instruction-following and logical steps thanks to its training background.

The prompt format uses special tags to *invite* visible reasoning:
```
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant
<think>
```
That `<think>` tag nudges the model to "think out loud" before answering. A helper function, `format_model_output()`, then splits the raw output into a **Reason** section and a final **Output** section for clean display.

**Why it matters:** This is the "aha" moment of the notebook — instead of a flat answer, you get a transparent chain of reasoning you can actually read and evaluate.

**Practice challenge:** Test the model on a simple logic/math riddle (like counting apples given away) and reflect on how this differs from a normal conversational chatbot reply.

---

## Stop 5 — 🧭 A Framework for Choosing the Right Model for Your Business
**What's happening:** A conceptual stop — before committing to any one model, the notebook lays out a decision framework for picking the right LLM for a real business use case: balancing factors like task complexity, latency needs, cost, context window size, and whether reasoning transparency (like Stop 4's `<think>` trace) is actually required.

**Why it matters:** Not every task needs a big reasoning model — this stop is about developing the judgment to match model choice to the actual business problem, not just picking the flashiest option.

---

## Stop 6 — 🏆 Model Leaderboards & Old/New Benchmarks
**What's happening:** A tour of several public leaderboards used to compare LLMs objectively:
- The old and new **Open LLM Leaderboard**
- The **LLM Performance Leaderboard** (speed/efficiency focused)
- The **Big Code Models Leaderboard** (coding-specific)
- The **Open Medical LLM Leaderboard** (domain-specific)

**Why it matters:** Reinforces Stop 5's framework with concrete tools — these leaderboards are where you'd actually go to compare candidate models against each other on the dimensions that matter for your use case.

---

## Stop 7 — 🔍 Prompting for Reasoning & Classification
**What's happening:** This is the core deliverable — the `analyze_news_sentiment()` function, which:
1. Builds a detailed prompt instructing the model to act as a **concise Financial News Analyst**
2. Explicitly asks for reasoning *and* a final classification (Positive / Negative / Neutral), each clearly labeled
3. Runs the news dataset's `full_text` through the DeepSeek pipeline
4. Parses the response into separate reasoning and classification pieces using regular expressions

It's tested against several random news items from the real dataset, printing both the reasoning trace and the final sentiment call for each.

**Why it matters:** This is where Stops 3 and 4 combine into the actual product — real financial news in, an auditable, explained sentiment call out.

**Practice challenge:** Pick a specific, interesting news item by index (instead of a random one) and evaluate whether the reasoning and classification genuinely make sense for that story.

---

## Stop 8 — 🎛️ Building the Gradio Interface
**What's happening:** The sentiment analysis pipeline is wrapped in a Gradio web app with:
- A textbox showing the current news item
- A button to fetch a new random news item from the dataset
- A button to trigger the analysis
- Separate display areas for the **Reasoning** and the **Classification**

**Why it matters:** This turns a script you run cell-by-cell into a genuinely usable, clickable tool — anyone (not just someone comfortable in a notebook) can pull up a random headline and see the AI's reasoning and verdict.

---

## 🏆 What You Walk Away With
By the end of this notebook, you've built a transparent, reasoning-driven **financial sentiment analysis tool**:

✅ Learned how to load and prep real-world datasets from Hugging Face
✅ Ran a genuine open-source "reasoning" model (DeepSeek) on a free GPU
✅ Learned to elicit and parse a visible chain-of-thought using `<think>` tags
✅ Built a framework for deciding which LLM actually fits a given business need
✅ Explored public leaderboards for objectively comparing model candidates
✅ Engineered a prompt that reliably separates reasoning from final classification
✅ Wrapped it all into a clickable Gradio app for random-headline sentiment analysis

**Next natural steps** (not in this notebook, but the logical Stop 9): batch-scoring the entire news dataset instead of random single items, and comparing DeepSeek's reasoning quality against a larger paid-API model on the same headlines.

---

*Guide generated from `day6-reasoning-models-llm-selection-notes.ipynb`*
