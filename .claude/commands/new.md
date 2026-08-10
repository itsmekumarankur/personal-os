# /new — Create a New Automation or Project

Build any new automation. The process is always the same regardless of what you're building.

## Step 1: Understand What to Build

If the user described it in detail, extract:
- What it does (purpose in one sentence)
- What it reads (vault pages, inbox, external sources)
- What it produces (wiki pages, files, reports)
- Whether it runs on a schedule or on-demand

If they described it briefly, ask:
1. "What should it do?"
2. "What data does it need?"
3. "Should it run automatically on a schedule, or when you call it?"

## Step 2: Scaffold

1. Find the next number: check what's in `vault/projects/` and pick the next integer
2. Create the command file: `.claude/commands/{name}.md`
3. Create the project status page: `vault/projects/{name}/status.md`
4. Update the routing table in `CLAUDE.md`
5. Update `vault/index.md`
6. Append to `vault/log.md`

### Command File Template

`.claude/commands/{name}.md`:
```markdown
# /{name} — [What It Does in One Line]

[Description: what it does, when to use it]

## Step 1: Read State
[What it reads from vault/]

## Step 2: [Main Logic]
[What it does]

## Step 3: Vault Update
[What it writes back]

## Output
[What the user sees]
```

### Project Status Template

`vault/projects/{name}/status.md`:
```markdown
---
tags: [project, automation]
date_created: [date]
date_updated: [date]
---

# [Name] — Status

## What This Is
[Description]

## Status
[ ] Built
[ ] Tested
[ ] Scheduled

## Related Pages
[[vault/links]]
```

## Step 3: Build It

Build the automation following what was described. Test it. Make it work.

## Step 4: Finalize

- Update `.claude/commands/{name}.md` with actual implementation details
- Confirm: "/{name} is now available."
- If it should run on a schedule: add to `scheduler/schedule.md`, tell user to run `/cron-setup`
- Update routing table in CLAUDE.md

## Learner-Specific Automation Ideas

When the user asks for a new automation, offer these if relevant:
- **Spaced repetition reviewer** — surfaces concepts learned 1 week, 2 weeks, 1 month ago
- **Book processor** — structured ingestion for books (chapters → concepts → connections)
- **Research deep dive** — multi-agent research on a specific topic
- **Podcast processor** — transcribe and ingest audio learning
- **Note linker** — scan for concepts in recent notes and add `[[wiki links]]`
- **Skill demonstrator** — given a skill, generate a practice problem to demonstrate it
