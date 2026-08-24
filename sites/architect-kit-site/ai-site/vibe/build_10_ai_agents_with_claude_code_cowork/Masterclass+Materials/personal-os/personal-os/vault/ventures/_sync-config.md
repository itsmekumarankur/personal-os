---
tags: [config, ventures, sync]
purpose: Whitelist of which files to mirror from each venture's repo into vault/ventures/{name}/docs/
---

# Venture Sync Config

`/venture-sync` reads this file to decide what to mirror. Edit the `sync_files:` list per venture to add or drop docs. Skip CLAUDE.md, AGENTS.md, AGENT.md, CODEX.md, GEMINI.md, README.md — those are sysprompts or boilerplate, not knowledge.

```yaml
ventures:
  brandmodal:
    code_path: ~/Desktop/brandmodal
    sync_files: [GTM_TRACKER.md, TASKS.md, plan.md, ADMIN_GUIDE.md]
    project_source: plan.md   # file whose H2 headings define sub-projects

  alphastar:
    code_path: ~/Desktop/AlphaStar
    sync_files: [TODOS.md, beliefs.md, crash_protocol.md, scoring_checklist.md]
    project_source: TODOS.md

  insightai:
    code_path: ~/Desktop/insightai
    sync_files: [CHANGELOG.md]
    project_source: null

  finance-us:
    code_path: ~/Desktop/finance-us
    sync_files: [SOURCES.md]
    project_source: null

  stemplicity:
    code_path: ~/Desktop/stemplicity
    sync_files: []
    project_source: null
```

## Auto-skip rules

Never sync these even if listed: `CLAUDE.md`, `AGENTS.md`, `AGENT.md`, `CODEX.md`, `GEMINI.md`, `README.md`, `CHANGELOG.md` if it exceeds 500 lines.

## Output paths

Each synced file lands at `vault/ventures/{venture}/docs/{filename}` with frontmatter prepended:

```yaml
---
source: <absolute path>
synced: YYYY-MM-DD
git_sha: <short>
read_only: true   # never edit; edit the source instead
---
```
