# /status — System Health Check

Quick check of the whole system. Two modes.

## Quick Mode (default)

Read `vault/log.md` last 5 entries. Report:
- Last 3 things learned or ingested (when, what)
- Active courses and approximate last-touched date
- Anything in `inbox/` that hasn't been ingested yet
- Next scheduled tasks from `scheduler/schedule.md`

Keep it under 10 lines. The user wants a snapshot.

## Full Mode (/status full)

### 1. Identity
Read `soul.md`. Is it filled in? If not: "soul.md is still a template — run /setup to fill it in."

### 2. Vault Health
Count pages in each section:
- `vault/me/` — pages about the user
- `vault/learning/` — concept pages by domain
- `vault/courses/` — course tracking
- `vault/projects/` — project statuses
- `vault/spirituality/` — practices and insights
- `vault/people/` — people encountered
- `vault/ideas/` — raw ideas
- `vault/research/` — research outputs
- `vault/sources/` — archived raw sources

Last vault update timestamp (from log.md).

### 3. Course Status
Read `vault/courses/tracker.md`. Quick summary: how many active, how many completed, what's most recently touched.

### 4. Project Status
Read each `vault/projects/*/status.md`. One line per project.

### 5. Inbox
List `inbox/`. Any unprocessed files?

### 6. Scheduled Tasks
Read `scheduler/schedule.md`. List commands and their frequencies.

### 7. Connections (if MCP available)
Test any connected MCP tools. Report which are live.

### 8. Open Loops
From recent journal entries and log: any open questions or unresolved threads?
