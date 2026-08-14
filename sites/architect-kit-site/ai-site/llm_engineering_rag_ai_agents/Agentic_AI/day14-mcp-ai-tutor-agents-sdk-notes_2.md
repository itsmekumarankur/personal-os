# 🔌 MCP AI Tutor — Connecting an Agent to the Toolkit — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty notebook" to "an AI agent that discovers a running MCP toolkit server and calls its tools on its own, in a live back-and-forth conversation." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

This notebook is the **client half** of a two-part project (the server was built in the companion notebook, `day14-mcp-ai-tutor-agents-sdk-notes_1`). Think of it as **six stops**:

```
🏁 START      🧭 UNDERSTAND MCP      🔧 SETUP + CONNECT      🖥️ START THE SERVER
Overview  →  The Universal Adapter →  Libraries + SSE URL →  (In Companion Notebook)

🔍 DISCOVER THE TOOLS      🤖 BUILD THE AGENT & CHAT LIVE
Fetch the Manifest    →  Autonomous Tool-Calling Conversation
```

By the end, you go from "I have four AI tools sitting in a server" to "an AI agent that automatically figures out which of those tools to call, with what arguments, based purely on a live conversation with you."

---

## Stop 1 — 🏁 Project Overview
**What's happening:** The notebook picks up right after prior projects (chatbots, tutors, image processors, multi-agent systems) and poses a new problem: how does an AI model reliably use *external* tools without a custom-built integration for each one?

**Why it matters:** This frames the whole notebook around a real, common pain point — plugin-style integrations don't scale, and MCP is presented as the standardized fix.

---

## Stop 2 — 🧭 Understanding MCP (Model-Context-Protocol)
**What's happening:** A conceptual breakdown of MCP's two key pieces:
- **MCP Server** — an application (in this case, the Gradio app built in the companion notebook) that exposes one or more tools over HTTP
- **Manifest** (`/mcp/manifest.json` or `/schema`) — a standard JSON description of every available tool: its name, what it does, what inputs it needs, and what it returns

**The analogy:** MCP is like a **universal plug adapter** for AI tools — instead of custom wiring for every device, a model can ask any MCP-enabled service "what tools do you offer?" and get a consistent, structured answer.

**Why it matters:** This is the mental model for everything that follows — discovery (via the manifest) and execution (via calling a named tool with specific arguments) are the two core mechanics MCP standardizes.

---

## Stop 3 — 🔧 Install Key Libraries & API Keys
**What's happening:**
- Installs `openai-agents` (the **OpenAI Agents SDK**) plus `gradio`, `openai`, `python-dotenv`, `requests`, `httpx`, and `pillow`
- Loads the OpenAI API key from `.env`
- Defines `MCP_BASE`, the local URL (`http://localhost:7860/gradio_api/mcp/sse`) where the tutor MCP server (from the companion notebook) is expected to be running
- Introduces `MCPServerSse` — a class from the Agents SDK that connects to an MCP server over **Server-Sent Events (SSE)**, a protocol for the server to push real-time updates to the client

**Why it matters:** This assembles the client-side toolkit — the pieces needed to *find* and *talk to* the server, as opposed to the server-building tools used in the companion notebook.

---

## Stop 4 — 🖥️ Build & Run the MCP Server (Setup Is in a Separate Notebook)
**What's happening:** A pointer back to the companion notebook — you need to actually open and run `MCP Server.ipynb` (i.e., `day14-mcp-ai-tutor-agents-sdk-notes_1`) so the four-tool server is live and listening before anything in *this* notebook can connect to it. The key change enabling MCP mode there is simply `launch(mcp=True)`.

**Why it matters:** This is a genuine two-process setup — a running server in one notebook, and a client connecting to it from another — which mirrors how real MCP deployments actually work (client and server are typically separate applications entirely).

**Practice challenge:** Add a new tool to the server that explains a concept in a different language, then confirm it shows up from the client side.

---

## Stop 5 — 🔍 Discover Available Tools & Fetch the Manifest (Schema)
**What's happening:** Acting as a genuine MCP *client*, the notebook makes an HTTP GET request to the server's `/schema` endpoint using `httpx`, via a `fetch_schema()` helper function. The returned JSON manifest is pretty-printed, showing exactly what tools the AI Tutor server offers, their parameters, and their descriptions — the same information an AI agent would use to decide which tool fits a given request.

**Why it matters:** This proves the "discovery" half of MCP works end-to-end — before any AI agent gets involved, you can see with your own eyes exactly what capabilities the server is advertising and how they're described.

**Practice challenge:** Go improve the docstring of `explain_concept` in the server notebook to be more descriptive, restart the server, and re-fetch the schema here — confirming the manifest updates automatically to reflect the improved description (the notebook shows a before/after schema screenshot pair demonstrating exactly this).

---

## Stop 6 — 🤖 Create an AI Agent Using the OpenAI Agents SDK That Uses MCP Tools
**What's happening:** This is where everything converges. The **OpenAI Agents SDK** is introduced — a lightweight framework built around a few core primitives:
- **Agents** — LLMs equipped with instructions and tools
- **Handoffs** — letting agents delegate specific sub-tasks to other agents
- **Guardrails** — validating agent inputs

An `Agent` named "Smart Assistant" is created, with detailed instructions describing all four MCP tools (their names, arguments, and what each streams back), so the agent knows exactly what's available and how to call it correctly.

The agent then **connects to the live MCP server** via `mcp_tool.connect()` (opening the SSE channel), and enters a real conversational loop: you type a message, the agent decides — entirely on its own — whether and which tool to call, executes it against the live server, and responds, with conversation history (`result.to_input_list()`) carried forward turn to turn until you type `"exit"`.

A final inspection step loops through the conversation history to print exactly which tools were called and with what arguments — full transparency into the agent's decisions.

**Why it matters:** This is the full payoff of the two-notebook project — an AI agent that doesn't have any tool logic hardcoded into it; instead, it discovers what's possible from the MCP manifest and decides, live, in natural conversation, which capability to invoke and when.

---

## 🏆 What You Walk Away With
By the end of this notebook, you've built a genuine, standards-based **agent-to-tool connection**:

✅ Learned the core MCP concepts — servers, manifests, and standardized tool discovery
✅ Connected to a running MCP server over Server-Sent Events using the Agents SDK
✅ Fetched and inspected a live tool manifest, and saw it update when a tool's docstring changed
✅ Built a real `Agent` (via the OpenAI Agents SDK) equipped with knowledge of all available MCP tools
✅ Ran a live, multi-turn conversation where the agent autonomously chose which tools to call
✅ Learned how to inspect an agent's tool-calling history for transparency and debugging

**Next natural steps** (not in this notebook, but the logical continuation): adding **Handoffs** so a second, specialized agent could take over specific requests, and adding **Guardrails** to validate user inputs before they ever reach a tool call.

---

*Guide generated from `day14-mcp-ai-tutor-agents-sdk-notes_2.ipynb`*
