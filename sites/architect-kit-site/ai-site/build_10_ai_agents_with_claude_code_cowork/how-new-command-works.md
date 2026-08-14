# How `/new` Works — Explained Simply

## The Big Idea (in one line)

`/new` is **not code**. It's just a text file (`new.md`) full of instructions. When you type `/new`, Claude reads that file and follows the steps written in it — like following a recipe.

```
You type /new
     ↓
Claude opens .claude/commands/new.md
     ↓
Claude follows the steps written inside it
     ↓
Claude creates/updates some .md files
     ↓
A brand-new command now exists
```

No servers, no build step, no JavaScript. Just Claude reading a file and acting on it.

---

## Where It Lives

```
.claude/
└── commands/
    └── new.md   ← this file IS the /new command
```

Every command in the project (`/morning-brief`, `/reflect`, `/design-lab`, etc.) works the exact same way — each is just its own `.md` file sitting in `.claude/commands/`.

---

## What Happens, Step by Step

### Step 1 — Understand what you want to build
- If you explained it clearly, Claude figures out on its own:
  - What it **does**
  - What it **reads** (inputs)
  - What it **produces** (outputs)
  - Whether it runs **automatically (scheduled)** or **on-demand**
- If you were vague, Claude asks 3 quick questions:
  1. What should it do?
  2. What data does it need?
  3. Should it run automatically, or only when you call it?

### Step 2 — Scaffold the files
Claude creates:
| File | Purpose |
|---|---|
| `.claude/commands/{name}.md` | The new command itself |
| `vault/projects/{name}/status.md` | Tracks progress of this project |

Then it updates:
| File | Why |
|---|---|
| `CLAUDE.md` | Adds the new command to the master routing table |
| `vault/index.md` | So Obsidian can find/link it |
| `vault/log.md` | Append-only history log |

### Step 3 — Actually build it
Claude writes the real logic for the command and tests that it works.

### Step 4 — Finalize
- If the command needs to run on a schedule, Claude tells you to run `/cron-setup`, which creates a **systemd timer job** that fires `claude -p "Run /{command}"` automatically.
- Otherwise, the command is just ready to use whenever you type it.

---

## The One Sentence Summary

> **Everything is a markdown file.** `/new` is a set of written instructions that tells Claude how to create *more* markdown files — and once those files exist, they become new commands themselves.

---

## Quick Analogy

Think of `.claude/commands/` as a folder of **recipe cards**. `/new` is the recipe for *"how to write a new recipe card."* When you use it, Claude:
1. Asks what dish (command) you want,
2. Writes a new recipe card (`{name}.md`) for it,
3. Adds it to the recipe index (`CLAUDE.md`),
4. And — if needed — sets a kitchen timer (`/cron-setup`) to make it automatically.

---

## Source Code — `.claude/commands/new.md`

````markdown
# /new — Create a New Automation or Project

Build any new automation. The process is always the same regardless of what you're building.

## Step 1: Understand What to Build

If the user described it in detail, extract:
- What it does (purpose in on
- What it reads (vault pages, inbox, external sources)
- What it produces (wiki pages, files, reports)
- Whether it runs on a schedu

If they described it briefly,
1. "What should it do?"
2. "What data does it need?"
3. "Should it run automatical call it?"

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

[Description: what it does, w

## Step 1: Read State
[What it reads from vault/]

## Step 2: [Main Logic]
[What it does]

## Step 3: Vault Update
[What it writes back]

## Output
[What the user sees]

Project Status Template

vault/projects/{name}/status.md:
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

Step 3: Build It

Build the automation followin. Make it work.

Step 4: Finalize

- Update .claude/commands/{name}.md with actual implementation details
- Confirm: "/{name} is now av
- If it should run on a schedule: add to scheduler/schedule.md, tell user to run
/cron-setup
- Update routing table in CLAUDE.md

Learner-Specific Automation Ideas

When the user asks for a new automation, offer these if relevant:
- Spaced repetition reviewer — surfaces concepts learned 1 week, 2 weeks, 1 month ago
- Book processor — structureds → concepts → connections)
- Research deep dive — multi-agent research on a specific topic
- Podcast processor — transcribe and ingest audio learning
- Note linker — scan for concepts in recent notes and add [[wiki links]]
- Skill demonstrator — given problem to demonstrate it

---
````
