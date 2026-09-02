# LLM Agentic AI Engineer — 14-Day Bootcamp (Udemy, 2025)

**Status:** Completed  
**Applied to:** BFSI / Optimus AI layer experiments

---

## What was built (module by module)

| Module | What | Keep? |
|---|---|---|
| 1 - Text GPT | Character AI chatbot via OpenAI API | Yes — base pattern for any chatbot |
| 2 - Vision GPT | Calorie tracker using image input | Yes — vision + structured output pattern |
| 3 - Gradio & Streaming | Adaptive LLM tutor with multi-level UI | Yes — streaming + Gradio UI pattern |
| 4 - Benchmarking LLMs | Landing page generator comparing OpenAI / Claude / Gemini | Yes — model comparison harness |
| 5 - HuggingFace 1 | Open-source model inference | Reference only |
| 6 - HuggingFace 2 | HuggingFace pipelines | Reference only |
| 7 - RAG & LangChain | RAG over restaurant data (Eleven Madison Park) | **Apply to domain-notes** — same architecture works for MF/Demat notes |
| 8 - Pydantic | Structured output validation | Yes — use in any agentic pipeline |
| 9 - FineTuning | PEFT/LoRA fine-tuning on open-source LLM | Reference — expensive to run locally |
| 10 - AutoGen | Multi-model agent teams | Yes — orchestration pattern |
| 11 - LangGraph | Agentic workflows with state graphs | Yes — stateful agent pattern |
| 12 - CrewAI | Role-based agent crews | Reference |
| 13 - N8N | No-code AI agent workflows | Yes — fast prototyping |
| 14 - MCP Servers | Build and connect MCP servers | **High value** — directly applicable to Claude Code setup |

---

## What I would skip next time

- Module 5 & 6 (HuggingFace) if compute is a constraint — GPU required for meaningful work
- Module 12 (CrewAI) — LangGraph covers the same ground with more control

## Highest-leverage module for BFSI work

Module 7 (RAG) applied to `domain-notes/` — your MF, Demat, LAS, and Insurance notes are the corpus. The architecture is identical to the restaurant lab.

## Next experiment

Build a local RAG assistant over `personal-os/domain-notes/` using the Module 7 notebook as the base.
