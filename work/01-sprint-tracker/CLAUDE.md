# Sprint Tracker — Spec

## What It Does

Reads the Notion Automation Sprint Board, generates a standup summary (Done / In Progress / To Do with counts), and tracks velocity over time.

## Inputs

- Notion Automation Sprint Board — `collection://9a4012bf-a097-4da2-b1d3-05e2f35a8188`
- Notion Personal OS page — `https://app.notion.com/p/3b82145568cd814c9c1eeb5ea21e2f3e`
- Previous standup files in `vault/projects/sprint-tracker/standups/`

## Outputs

- `vault/projects/sprint-tracker/standups/YYYY-MM-DD.md` — local standup
- Notion standup page under Personal OS
- Velocity table appended from prior standups

## Board Schema

| Property | Type | Values |
|----------|------|--------|
| Name | Title | automation name |
| Status | Select | To Do / In Progress / Done |
| Category | Select | Daily / Weekly / On-demand |
| Priority | Select | High / Medium / Low |
| Built Date | Date | ISO date when marked Done |

## Velocity Tracking

Count Done items vs total across consecutive standup files.
Compare today vs yesterday (delta) for momentum signal.

## Contract: Future Automations

Every automation built inside this OS MUST:
1. Mark itself Done on the Sprint Board (update Status = "Done", Built Date = today)
2. Create a Notion standup page under Personal OS for the day it's built
3. Run `/sprint-tracker` after marking itself done to generate an updated standup

Notion Sprint Board DB: `collection://9a4012bf-a097-4da2-b1d3-05e2f35a8188`
Personal OS Notion page: `https://app.notion.com/p/3b82145568cd814c9c1eeb5ea21e2f3e`
