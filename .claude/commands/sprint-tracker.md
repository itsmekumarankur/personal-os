# /sprint-tracker — Daily Standup from Notion Sprint Board

Reads the Automation Sprint Board in Notion, generates a standup summary, and tracks velocity.

## Step 1: Read the Board

Query the Notion Automation Sprint Board:
- Data source: `collection://9a4012bf-a097-4da2-b1d3-05e2f35a8188`
- Fetch all rows: Name, Status, Category, Priority, Built Date
- Group by Status: Done / In Progress / To Do

## Step 2: Generate Standup Summary

Format:

```
## Daily Standup — YYYY-MM-DD

Done (N): [list names]
In Progress (N): [list names]
To Do (N): [list names]

Velocity: N/10 (N%)
Next up: [highest priority To Do item]
```

## Step 3: Calculate Velocity

- Read previous standup files from `vault/projects/sprint-tracker/standups/`
- Compare Done count today vs yesterday for delta
- Show trend: up / flat / down

## Step 4: Write Local Standup

Save to: `vault/projects/sprint-tracker/standups/YYYY-MM-DD.md`

## Step 5: Post to Notion

Create a new page titled "Standup YYYY-MM-DD" under:
https://app.notion.com/p/3b82145568cd814c9c1eeb5ea21e2f3e

Use callout blocks for Done (green), In Progress (yellow), To Do (gray).
Append velocity table at bottom.

## Step 6: Update vault/log.md

Append: `## [YYYY-MM-DD HH:MM] /sprint-tracker | Standup: N done, N in progress, N to do. Velocity: N/10`

## Contract: Mark Yourself Done

When any automation is built, before finishing:
1. Use `notion-update-page` to set Status = "Done" and Built Date = today on the Sprint Board row
2. Run this command to generate an updated standup
3. Notion Sprint Board: `collection://9a4012bf-a097-4da2-b1d3-05e2f35a8188`
