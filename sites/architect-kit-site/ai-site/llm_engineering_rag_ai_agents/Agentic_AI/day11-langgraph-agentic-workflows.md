# ✈️ Agentic AI Workflows with LangGraph — Building an AI Travel Agent — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty notebook" to "a multi-tool AI travel agent that checks news, searches real flights and hotels, and reasons about which tool to use — wrapped in a Gradio chat interface." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

Think of this notebook as **nine stops on a road trip**:

```
🏁 START      🧭 LANGGRAPH 101      📝 FIRST GRAPH (NO TOOLS)      🌐 ADD TRANSLATION
Overview  →  State/Nodes/Edges →  Summarize a Text        →  Chain Two Steps

🔍 ONE TOOL + ROUTING      🧮 CUSTOM TOOL      ✈️ REAL FLIGHT SEARCH      🧳 FULL TRAVEL AGENT      🎛️ GRADIO CHAT
Web Search + Decide   →  Wrap Any Function →  Live Amadeus API   →  All Tools Combined →  Chat in Browser
```

By the end, you go from "a graph that just summarizes text" to a genuine agentic system that decides *for itself* which real-world tools to call — news search, live flight data, hotel search — to answer a travel question, all wired into a chat interface.

---

## Stop 1 — 🏁 Project Overview: The AI Travel Agent
**What's happening:** Screenshots preview the finished product — an AI agent that can research travel destinations, check news/advisories, and search real flights and hotels, all through natural conversation.

**Why it matters:** Frames the ambitious end goal up front — this isn't a single LLM call, it's a full multi-step, multi-tool workflow.

---

## Stop 2 — 🧭 Understand LangGraph & Its Key Components & Features
**What's happening:** A conceptual introduction to **LangGraph** — a library built on top of LangChain for creating stateful, multi-step (and potentially multi-agent) workflows using a graph structure. The five core building blocks are introduced:
- **StateGraph** — the core object for building a workflow
- **Nodes** — functions or agents that perform specific tasks
- **Edges** — connections that control the flow between nodes
- **State** — information that persists and flows across nodes
- **Conditional Routing** — logic for deciding which path to follow next

**Why it matters:** Every later stop is just a variation on these five concepts — understanding them here makes everything that follows feel like an extension rather than new material.

---

## Stop 3 — 📝 Build the First Agentic Workflow in LangGraph (Summarization, No Tools)
**What's happening:** The simplest possible LangGraph workflow gets built to nail the fundamentals:
1. Define an `AgentState` (a `TypedDict`) holding `input_text` and `summary`
2. Define a `summarize_step()` node — a plain function that calls an LLM and updates the state
3. Build a `StateGraph`, add the summarize node, wire up a single edge to `END`, set the entry point, and `compile()` it

**Why it matters:** This is "Hello World" for LangGraph — one node, one edge, no branching — proving the State → Node → Edge mental model actually works before anything more complex is layered on.

**Practice challenge:** Swap in a different input text and rerun the workflow to see the summary change.

---

## Stop 4 — 🌐 Build an Agentic Workflow (Summarization + Translation, No Tools)
**What's happening:** The graph grows to two sequential steps. The `AgentState` gains a `translated_summary` field, and a new `translate_step()` node takes the summary from Stop 3 and translates it (English → Spanish) via another LLM call. The graph now chains: `summarize` → `translate` → `END`.

**Why it matters:** This is the first real taste of *composing* a workflow — each node builds on the previous node's output, and the state object carries accumulated results forward through the whole pipeline.

**Practice challenge:** Define a new `sentiment_step()` node that classifies the translated text as positive/negative/neutral, and wire it into the graph as a third step.

---

## Stop 5 — 🔍 LangGraph with a Single Tool (Web Search) Using ToolNode & Conditional Edge
**What's happening:** The agent gets its first real "superpower" — the ability to search the web via the **Tavily** search tool. Several new concepts combine here:
- A `tavily_search_tool` is defined and given to the LLM
- `call_model_with_tools()` binds the tool(s) to the model so it *can* choose to call them
- LangGraph's prebuilt **`ToolNode`** handles actually executing whichever tool the model decides to call
- A **conditional edge**, driven by a `should_continue()` function, inspects the model's last message: if it requested a tool call, route to the `"action"` node (the ToolNode); if not, route to `__end__`

**Why it matters:** This is the true leap from "workflow" to "agent" — the graph itself doesn't hardcode whether a tool gets used; the LLM decides at runtime, and the conditional edge routes accordingly.

**Practice challenge:** Ask something that shouldn't need a web search (like *"What is 2 + 2?"*) and trace through the DEBUG logs to confirm the `action` node never fires.

---

## Stop 6 — 🧮 Create and Add a Custom New Tool
**What's happening:** Beyond built-in tools like Tavily, this stop shows how to turn **any** Python function into a tool the agent can call, using the `@tool` decorator. A simple example, `get_current_date_tool()`, returns today's date — useful groundwork for later, relative-date travel queries ("next week", "in July").

**Why it matters:** This is the extensibility unlock — once you know how to wrap a function with `@tool`, you can hand the agent essentially any capability your code can express.

**Practice challenge:** Build a new tool that performs addition and subtraction, add it to the tools list, and test the agent with it.

---

## Stop 7 — ✈️ Flight Search Using Amadeus & ToolNode
**What's happening:** A real-world, live-data tool gets wired in: `search_flights_tool()`, built on the **Amadeus** Flight Offers Search API (using a free test-environment client). It accepts structured parameters — origin/destination IATA codes, dates, passenger count, travel class — and returns real flight pricing and availability.

**Why it matters:** This moves the agent from "can browse the web" to "can query structured, authoritative live data" — a meaningfully different (and more reliable) capability than general web search for something like flight prices.

**Practice challenge:** Build an analogous hotel-search tool for NYC using specific check-in/check-out dates.

---

## Stop 8 — 🧳 Bringing It All Together — the Full Travel Booking Agent
**What's happening:** All the tools built so far — Tavily web search, the current-date tool, and the Amadeus flight search — get combined into a single `tools` list and handed to one graph: `app_travel_agent`. A realistic, multi-part prompt (*fetch travel advisories, find the cheapest flight, format the combined output*) demonstrates the agent autonomously deciding which tools to call, in which order, to satisfy a genuinely compound request.

**Why it matters:** This is the payoff moment — a single agent reasoning across multiple tools and data sources to answer a real, multi-faceted travel question, exactly like the product envisioned back in Stop 1.

**Practice challenge:** Ask about a trip to Paris in July instead, and see how the agent adapts its tool calls to the new destination and dates.

---

## Stop 9 — 🎛️ Integrating with Gradio
**What's happening:** The final polish — the multi-tool travel agent is wrapped in a Gradio `ChatInterface` via a `travel_agent_chat()` generator function. It **streams** the agent's output live, including visible notices of which tool was called and what it returned (e.g., `**Tool:** search_flights_tool`), so the user can watch the agent's reasoning and tool use unfold in real time, not just see a final answer.

**Why it matters:** This turns a script-based agent into a genuinely usable chat product — complete with transparency into *which* tools were used along the way, which builds trust in the agent's answers.

---

## 🏆 What You Walk Away With
By the end of this notebook, you've built a real, multi-tool **agentic AI travel assistant**:

✅ Learned LangGraph's core building blocks — State, Nodes, Edges, and Conditional Routing
✅ Built a simple linear graph, then chained multiple sequential steps together
✅ Gave an agent its first tool (web search) with conditional routing via `ToolNode`
✅ Learned to wrap any Python function as a tool with `@tool`
✅ Integrated a real, live external API (Amadeus) for flight and hotel search
✅ Combined multiple tools into one agent capable of genuinely compound reasoning
✅ Wrapped the finished agent in a streaming Gradio chat interface with visible tool use

**Next natural steps** (not in this notebook, but the logical Stop 10): adding persistent memory across chat sessions (LangGraph's checkpointing), and adding a booking-confirmation tool so the agent can move from "search" to "book" end-to-end.

---

*Guide generated from `Build_Agentic_AI_Workflows_Using_LangGraph.ipynb`*
