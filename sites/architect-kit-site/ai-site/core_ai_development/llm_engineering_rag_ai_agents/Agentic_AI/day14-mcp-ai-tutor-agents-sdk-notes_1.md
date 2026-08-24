# 🧰 MCP AI Tutor — Building the Toolkit Server — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty notebook" to "a running server exposing four AI-tutoring tools that any AI agent can discover and use." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

This notebook is the **server half** of a two-part project — think of it as **two stops**:

```
🔧 SETUP + DEFINE THE TOOLS      🚀 LAUNCH THE SERVER
Import Libs + 4 AI Functions →  Turn Them Into an MCP Toolkit
```

By the end, you have a live, running server exposing four separate AI-tutoring capabilities — each one independently callable by name, ready for any MCP-compatible client (including an AI agent) to discover and use. (The *client* side — an agent actually calling these tools — is covered in the companion notebook, `day14-mcp-ai-tutor-agents-sdk-notes_2`.)

---

## Stop 1 — 🔧 Import Key Libraries & Define the Key Functions for the MCP Server
**What's happening:**
- Installs `gradio[mcp]` — Gradio's built-in support for exposing an app as an **MCP (Model-Context-Protocol)** server, meaning its functions can be discovered and called by other AI tools, not just used through a web UI
- Sets up the OpenAI client, loading the API key securely from `.env`
- Defines an `EXPLANATION_LEVELS` dictionary mapping 1–5 to plain-English complexity descriptions (from "like I'm 5 years old" to "like an expert in the field") — this powers adjustable depth across multiple tools

Then, **four separate AI-powered tools** are built, each as a Python generator function that streams its response token-by-token for a responsive feel:

| Tool | What it does |
|---|---|
| 🧠 `explain_concept(question, level)` | Streams an explanation of any topic at a chosen complexity level (1–5) |
| 📝 `summarize_text(text, compression_ratio)` | Streams a summary compressed to roughly a chosen fraction of the original length |
| 🎴 `generate_flashcards(topic, num_cards)` | Streams a set of Q/A study flashcards in JSON-lines format |
| ❓ `quiz_me(topic, level, num_questions)` | Streams a multiple-choice quiz, followed by an answer key |

Each function includes input validation (blank text, out-of-range numbers) that returns a clear error message instead of crashing.

**Why it matters:** This is the "build the toolbox" stop — four genuinely independent, reusable AI capabilities, each with clear inputs and a docstring describing exactly what it does. That clarity matters a lot later: an AI agent deciding *which* tool to call relies entirely on reading these descriptions.

---

## Stop 2 — 🚀 Launch the Gradio MCP Server
**What's happening:** A `build_demo()` function assembles all four tools into a single **Gradio Blocks** interface, with one tab per tool (Explain Concept, Summarize Text, Flashcards, and — implied — Quiz Me), each with its own inputs (textboxes, sliders) and a button to trigger it.

Critically, when this app is launched with `mcp=True` (as instructed in the companion notebook), Gradio doesn't just serve a web page — it also exposes a **machine-readable manifest/schema** describing each tool, its parameters, and what it returns. That's what lets an external AI agent "discover" and correctly call these tools programmatically, not just a human clicking buttons.

**Why it matters:** This is the moment the notebook stops being "four AI functions in a Python file" and becomes a genuine **service** — a running toolkit that other software (including AI agents, as shown in the companion notebook) can query and use over a standard protocol.

---

## 🏆 What You Walk Away With
By the end of this notebook, you've built a working, tool-exposing **MCP server**:

✅ Learned how MCP lets a server describe its tools in a way AI agents can discover and use
✅ Built four distinct, streaming, input-validated AI-tutoring functions
✅ Learned how adjustable parameters (explanation level, compression ratio, card/question count) make one tool flexible for many use cases
✅ Assembled all four tools into a single Gradio app with a tab per tool
✅ Learned that `launch(mcp=True)` is the one-line change that turns a normal Gradio app into a discoverable MCP toolkit

**Next natural steps:** This is exactly where the companion notebook (`day14-mcp-ai-tutor-agents-sdk-notes_2`) picks up — fetching this server's manifest from a separate client notebook, and building an OpenAI Agents SDK agent that discovers and calls these four tools autonomously.

---

*Guide generated from `day14-mcp-ai-tutor-agents-sdk-notes_1.ipynb`*
