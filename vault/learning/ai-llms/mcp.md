---
tags: [ai, mcp, anthropic, protocol, tool-use, agents]
date_created: 2026-08-08
date_updated: 2026-08-08
sources: [architect-kit/mcp/mcp-deep-dive, architect-kit/mcp/mcp-enterprise-patterns]
---

# MCP — Model Context Protocol

Anthropic's open protocol for giving LLMs structured access to tools, data, and context. Not a framework — a standard interface.

## What It Solves

Before MCP: every tool integration was custom code. You'd write a wrapper, define the schema, handle errors — per tool, per model, per project.

MCP standardizes the interface. Any MCP-compliant server can be plugged into any MCP-compliant client (Claude Code, VS Code extension, etc.) without custom wiring.

## Architecture

```
Host (Claude Code / your app)
  ↓ MCP Client
  ↓ stdio or HTTP transport
MCP Server (Gmail, Calendar, Notion, filesystem, databases)
  ↓ exposes Tools, Resources, Prompts
```

- **Tools**: functions the model can call (send email, read calendar, query DB)
- **Resources**: data the model can read (files, docs, live data)
- **Prompts**: reusable prompt templates exposed by the server

## This OS Uses MCP

Every integration in this Personal OS is an MCP server:
- `mcp__claude_ai_Gmail__*` — Gmail read/write/label
- `mcp__claude_ai_Google_Calendar__*` — Calendar events
- `mcp__claude_ai_Notion__*` — Notion pages and databases

That's why `/setup` was able to check Gmail, Calendar, and Notion without custom code — they're all MCP servers already connected.

## Enterprise Patterns (from architect-kit notes)

- **Multi-server composition**: one agent connects to multiple MCP servers simultaneously
- **Authorization**: MCP servers can enforce per-tool permissions — important in regulated environments
- **Sampling**: servers can ask the model for completions (model-to-server direction, not just server-to-model)
- **Stateful sessions**: MCP maintains session context across multiple tool calls

## Relevance to idfc-coder

The Jira-integrated agent in idfc-coder could be refactored as an MCP server: Jira as a resource, code generation as a tool, PR opening as a tool. Standardized, composable, auditable.

## Related

- [[learning/ai-llms/ai-agents]] — MCP is the tool-use layer for agents
- [[projects/personal-os/status]] — This OS is built on MCP
