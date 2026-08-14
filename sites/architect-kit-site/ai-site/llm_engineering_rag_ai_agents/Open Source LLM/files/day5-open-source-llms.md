# 🦙 Open-Source LLMs — Build Your Own PDF Q&A Bot — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty Colab notebook" to "a free, open-source LLM running on a GPU that answers questions about your PDF, wrapped in a Gradio app." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

Think of this notebook as **nine stops on a road trip**, all running on a free Google Colab GPU instead of a paid API:

```
🏁 START      🤗 EXPLORE HF      🔧 SETUP+GPU      🧵 PIPELINES      🔤 TOKENIZERS
Overview  →  Model Hub     →  Libs+Token+GPU →  Easy Inference →  Text→Numbers

🧠 LOAD A REAL LLM      📄 READ A PDF      🙋 Q&A LOGIC      🎛️ MULTI-MODEL GRADIO APP
Quantized Model    →  pypdf Extraction →  Prompt + Answer →  Swap Models Live
```

By the end, you go from "I have no idea how to run an LLM myself" to "I'm running an open-source model on a free GPU, answering questions about a real PDF, through a model-switching web app."

---

## Stop 1 — 🏁 Understand the Problem Statement & Key Learning Objectives
**What's happening:** The notebook opens with a visual overview of the goal — unlike the paid-API notebooks in this course, this one runs everything on **open-source models** you download and run yourself on a GPU (via Google Colab).

**Why it matters:** Sets expectations — no OpenAI/Anthropic key needed here; the "brain" running the show is a downloadable model rather than an API call.

---

## Stop 2 — 🤗 Explore Hugging Face
**What's happening:** A guided tour of [huggingface.co/models](https://huggingface.co/models) — the "app store" for open-source AI models. You learn to filter by task (Text Generation), sort by downloads, and recognize model-size hints in names (`2b`, `4k-instruct`, etc.) that tell you whether a model will actually fit on a free Colab GPU.

**Practice challenge:** Search for `phi`, `gemma`, `qwen`, or `llama` models, open one's model card, and test it directly in the browser with a prompt like *"Explain Newton's second law..."*

**Why it matters:** Choosing the *right-sized* model is the single biggest factor in whether this notebook will even run on free hardware.

---

## Stop 3 — 🔧 Install Key Libraries, Get an HF Token, & Check for GPU
**What's happening:** The toolbox gets assembled:
- `transformers` — the core Hugging Face library for models & tokenizers
- `accelerate` — runs models efficiently across hardware
- `bitsandbytes` — enables **quantization** (loading models in 4-bit/8-bit), which is what makes big models fit in a small free GPU
- `torch` — the deep learning engine underneath everything
- `pypdf` — for later PDF reading
- `gradio` — for the web interface

You also generate a **Hugging Face access token** (needed for "gated" models like some Llama/Gemma versions) and run a GPU availability check — since these models are far too slow to run on a CPU alone.

**Why it matters:** LLMs are massive matrix-multiplication machines — without a GPU and without quantization, this whole notebook would take hours instead of seconds per answer.

**Practice challenge:** Compare CPU vs. T4 GPU vs. A100 GPU speed in Colab's Runtime settings.

---

## Stop 4 — 🧵 Hugging Face Transformers Library: Pipelines
**What's happening:** Introduces `pipeline()` — the easiest on-ramp into using any Hugging Face model with just a couple of lines of code. It's demonstrated using **ProsusAI/finbert**, a model fine-tuned for financial sentiment analysis, tested on a sample headline about Apple losing money to tariffs.

**Why it matters:** `pipeline()` hides all the complexity (tokenizing, running the model, decoding) behind one simple function call — a gentle first taste of running a real model yourself.

**Practice challenge:** Run finbert against two more financial headlines and sanity-check the sentiment results.

---

## Stop 5 — 🔤 Hugging Face Transformers Library: AutoTokenizer
**What's happening:** Before any model can "read" your text, it needs to be converted into numbers. `AutoTokenizer` automatically fetches the correct tokenizer for whichever model you choose (e.g., GPT-2's) and converts a sentence into a list of token IDs.

**Why it matters:** Understanding tokenization here sets up everything that follows — every prompt, every PDF snippet, and every generated answer flows through this text ↔ numbers translation layer.

**Practice challenge:** Load a different tokenizer (like `bert-base-uncased`), tokenize the same sentence, and compare how differently each model splits up words and handles spaces.

---

## Stop 6 — 🧠 Hugging Face Transformers Library: AutoModelForCausalLM
**What's happening:** The centerpiece — actually loading a real, runnable open-source LLM:
1. Pick a model ID (e.g., `microsoft/Phi-4-mini-instruct`)
2. Load its tokenizer via `AutoTokenizer`
3. Load the model itself via `AutoModelForCausalLM`, using a `BitsAndBytesConfig` to load it in **4-bit quantization** — shrinking its memory footprint so it fits on a free GPU
4. Generate text two ways: the low-level `.generate()` method, and the higher-level `pipeline()` shortcut

**Why it matters:** This is the "aha" moment of the whole notebook — you're not calling someone else's API anymore, you're running your own copy of a genuine LLM, live, on borrowed GPU hardware.

**Practice challenge:** Swap the prompt for something new (a poem about a cat, a different factual question) and observe how the model responds.

---

## Stop 7 — 📄 Read PDF Documents & Extract Text Using pypdf
**What's happening:** To build a real Q&A tool, you need something to ask questions *about*. A sample PDF (a Google earnings-call transcript) is downloaded, opened with `pypdf.PdfReader`, and its text is extracted page-by-page and joined into one long string.

**Why it matters:** This is the "raw material" stop — turning a static document into a plain-text blob the LLM can actually read as context.

**Practice challenge:** Print the *last* 500 characters of the extracted PDF text and sanity-check it against the real document.

---

## Stop 8 — 🙋 Build the Q&A Logic & Prompt the Model
**What's happening:** The two ingredients — a loaded LLM and extracted PDF text — get combined via **prompt engineering**. The `answer_question_from_pdf()` function:
1. Truncates the document text to a safe character limit (`MAX_CONTEXT_CHARS`) so it doesn't overwhelm the model
2. Builds a prompt combining that context with the user's question
3. Sends it through the pipeline and returns the generated answer

**Why it matters:** This is where the notebook becomes a genuinely useful tool — ask a real question about a real document, and get an answer grounded in that document's actual content.

**Practice challenge:** Ask a different question about the earnings transcript, like *"How many monthly users are using AI?"*

---

## Stop 9 — 🎛️ Switch Models & Build a Gradio Interface
**What's happening:** The final upgrade — instead of being locked into one model, the app lets you **choose between multiple open-source models** (Llama 3.2, Phi-4 Mini, Gemma 3, Qwen 2.5) at runtime:
1. A dictionary maps friendly names to Hugging Face model IDs
2. A `load_llm_model()` function swaps out the currently loaded model — unloading the old one first, since Colab's free GPU can't hold several LLMs in memory at once
3. A `handle_submit()` function wires a typed question to the currently active model
4. A full **Gradio Blocks interface** ties it all together: a model-selector dropdown, a question box, and an answer box, all running live in the browser

**Why it matters:** This transforms a one-off script into a genuinely flexible tool — the same PDF Q&A workflow, but now with the ability to A/B test different open-source models live, without touching code.

**Practice challenge:** Add a new model (like Qwen 2.5) to the `available_models` dictionary, test it, and compare its answers to the others.

---

## 🏆 What You Walk Away With
By the end of this notebook, you've gone from "AI = someone else's API" to genuinely **running your own open-source LLM stack**:

✅ Learned how to browse and evaluate models on the Hugging Face Hub
✅ Set up quantization to run big models on free GPU hardware
✅ Used `pipeline()`, `AutoTokenizer`, and `AutoModelForCausalLM` hands-on
✅ Extracted real text from a PDF document
✅ Built a working prompt-engineered Q&A function grounded in that document
✅ Wrapped the whole thing in a Gradio app that can swap between multiple open-source models live

**Next natural steps** (not in this notebook, but the logical Stop 10): chunking longer PDFs with a vector database instead of a single truncated context window (true RAG), and comparing quantized open-source model quality against the paid APIs used in earlier lessons.

---

*Guide generated from `day5-open-source-llms.ipynb`*
