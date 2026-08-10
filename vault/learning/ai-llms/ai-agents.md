---
tags: [ai, agents, multi-agent, autogen, langgraph, crewai, n8n, mcp]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/llm-engineering-bootcamp/days10-14]
---

# AI Agents — Multi-Agent Systems

Moving from "one LLM answers one question" to "a team of specialized agents coordinates on a task."

## Core Concept

An agent is an LLM with a role, a system message, and optionally tool access. Agents can:
- Talk to each other (message passing)
- Use tools (web search, code execution, API calls)
- Run autonomously or with human-in-the-loop

## Frameworks Studied

### AutoGen (Microsoft) — Day 10

Multi-model agent teams. The key insight: AutoGen doesn't care which model powers which agent, so you can mix providers in one team.

Architecture: each agent has a role (CMO, Marketer, Social Media Strategist) defined by its system message. Agents converse via `initiate_chat()` or `GroupChat`.

- **GroupChat**: adds a `GroupChatManager` that arbitrates who speaks next
- **UserProxyAgent**: puts you in the conversation loop (`human_input_mode="ALWAYS"`)
- **Multi-model**: CMO on Gemini for high-level strategy, Marketer on GPT for tactical ideas, Strategist on Claude

### LangGraph — Day 11

Agentic workflows as directed graphs. Better than simple chain-of-calls because you can model branching, cycles (retry loops), and conditional routing. Good fit when workflow has well-defined states.

### CrewAI — Day 12

Role-based agent crews. Each agent has a role, goal, backstory, and tools. Tasks are assigned to agents; CrewAI orchestrates execution. Higher-level abstraction than AutoGen — less flexibility, more convention.

Use case from day12: data science agent — automated predictive analytics pipeline with specialized roles.

### n8n — Day 13

No-code/low-code agentic workflows. Integrates LLMs into larger automation graphs with 400+ integrations. Good for connecting AI to business systems without writing orchestration code.

### MCP — Model Context Protocol — Day 14

Anthropic's protocol for giving agents structured access to tools and context. Not a framework — a protocol. The agent calls tools via a standardized schema; the server handles execution. Personal OS is built on MCP (Claude Code's Gmail, Calendar, Notion integrations are MCP tools).

## Key Design Questions for Any Multi-Agent System

1. **Who orchestrates?** Centralized manager (GroupChatManager) vs. peer-to-peer conversation
2. **How do agents communicate?** Message passing, shared state, or structured tool calls
3. **What triggers each agent?** Event, turn-based, or task assignment
4. **Human-in-the-loop?** Where and when does a human get to redirect?
5. **How do you handle disagreement or loops?** Max turns, termination conditions, fallback

## Practical Note

At IDFC, the Jira-integrated coding agent (part of idfc-coder) is an agentic system: it polls tickets, generates code, validates, opens PRs. That's an autonomous agent with tool use — no multi-agent coordination, but the same core loop.

## Related

- [[learning/ai-llms/mcp]] — The protocol underlying tool use in this OS
- [[learning/ai-llms/llm-engineering-bootcamp]] — Days 10-14
- [[projects/architect-kit/status]] — Where these notebooks live
