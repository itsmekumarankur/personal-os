# Getting Started — Your Personal OS

## What This Is

A personal AI operating system built around how you actually work: deep learning across AI/LLMs, system design, software engineering, leadership, and inner development. Everything you learn compounds into a wiki (the vault). Commands automate the repetitive parts of learning and knowledge management.

## Prerequisites

**Claude Code:**
```bash
npm install -g @anthropic-ai/claude-code
```

**Obsidian** (free): Download from https://obsidian.md
- Point it at the `vault/` folder inside this directory
- You'll see all your wiki pages as an Obsidian graph

## First Run

Open Claude Code in this folder:
```bash
cd personal-os_byMe
claude
```

Then run:
```
/setup
```

This walks you through:
1. Filling in your `soul.md` (your agent's identity and voice)
2. Seeding the vault from your existing notes and projects
3. Connecting optional tools (Gmail, Calendar, Notion)
4. Setting up Obsidian

Takes about 15-20 minutes.

## Daily Workflow

**Morning:**
```
/study-brief
```
Get: what you're studying today, what to review from yesterday, any scheduled learning.

**When learning something:**
```
/learn
```
Drop an article, course notes, or a PDF into `inbox/` and run `/learn`. It processes the content and weaves it into the wiki.

**When you want to practice:**
```
/design-lab
```
Get a system design problem, work it out, get structured feedback.

**Evening:**
```
/reflect
```
Journal the day, consolidate what you learned, update your vault.

**Friday:**
```
/weekly-report
```
What you learned this week, what concepts connected, what to focus on next week.

## Folder Map

```
personal-os_byMe/
├── CLAUDE.md          — The orchestrator. Tells the agent how to behave.
├── soul.md            — Your identity and voice. Fill this in via /setup.
├── inbox/             — Drop raw sources here (articles, PDFs, notes).
├── outputs/           — Deliverables from commands land here.
├── vault/             — Your knowledge wiki. Open this in Obsidian.
│   ├── index.md       — Master catalog of all pages.
│   ├── log.md         — Append-only activity log.
│   ├── me/            — About you: role, goals, preferences, journal.
│   ├── learning/      — Knowledge by domain.
│   │   ├── ai-llms/
│   │   ├── system-design/
│   │   ├── software-engineering/
│   │   ├── leadership/
│   │   ├── business-strategy/
│   │   └── career/
│   ├── courses/       — Progress tracker for all courses.
│   ├── projects/      — Active project status pages.
│   ├── spirituality/  — Practices and insights.
│   ├── ideas/         — Raw ideas, experiments.
│   ├── people/        — Authors, mentors, teachers you encounter.
│   ├── sources/       — Immutable archive of raw sources.
│   └── research/      — Research outputs.
├── scheduler/         — Cron schedules for automated commands.
└── projects/          — All your live projects.
    ├── architect-kit/ — System design study lab.
    ├── leadership-kit/ — 100-Day Shift + fintech domain notes + daily journal.
    ├── antarmukh/     — Spiritual web presence (antarmukh.shivmarg.in).
    ├── shunya-hub/    — Shiva Within hub (shivawithin.in).
    └── sankalp-site/  — Placeholder/old repo.
```

## Available Commands

| Command | When to Use |
|---------|-------------|
| `/setup` | First run — fill soul.md and seed the vault |
| `/study-brief` | Morning — today's plan + yesterday's recap |
| `/learn` | Any time — ingest a course, article, or resource |
| `/ingest` | Drop anything in inbox/ and process it into the wiki |
| `/course-tracker` | Check progress across all your courses |
| `/design-lab` | Practice a system design problem |
| `/reflect` | Evening — journal and consolidate |
| `/career-radar` | Track your skills and growth areas |
| `/weekly-report` | Friday — synthesize the week |
| `/lint` | Check vault health |
| `/status` | Quick system health check |
| `/new` | Build a new automation |
| `/cron-setup` | Set up scheduled commands |

## Tips

- The vault compounds over time. The more you use `/learn` and `/reflect`, the more valuable it gets.
- Open the vault in Obsidian to see the knowledge graph — concepts connecting to each other visually.
- Drop files in `inbox/` any time and run `/ingest` to process them.
- All your live projects live in `projects/` — the vault references them but never overwrites them.
