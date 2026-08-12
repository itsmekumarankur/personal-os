# Morning Brief — Spec

## What It Does

Pulls unread Gmail (last 12h), today's calendar, and relevant Notion context. Filters through soul.md priorities. Produces a scannable brief in under 3 minutes.

## Inputs

| Source | What | How |
|--------|------|-----|
| Gmail MCP | Unread emails, last 12h | `search_threads` — `in:inbox is:unread newer_than:12h` |
| Google Calendar MCP | All events today | `list_events` with today's date range (IST) |
| Notion MCP | Relevant project pages | `notion-search` on active goals |
| vault/me/goals.md | Priority filter | Read at start |
| soul.md | Voice + filter | Read at start |
| brand/config/brand-config.md | Category tiers | Read at start |

## Priority Filter Logic

Apply brand-config.md tiers to emails:

- **Urgent**: requires action today (job invites, bank/financial, Optimus-related)
- **FYI**: status updates, rejections, LinkedIn signals, newsletters
- **Skip**: travel promos, unsubscribe candidates, generic job board spam

## Output Sections

### 1. Urgent
Emails requiring action. Max 5. One line each: sender + subject + what action needed.

### 2. Today's Calendar
All events with time (IST). Flag: focus blocks, sadhana, work meetings.
Mark meeting-free stretches as "available for deep work."

### 3. Key Context
Top 2-3 Notion/vault pages most relevant to today's work.
One sentence per page: why it matters today.

### 4. FYI
Everything else. No detail — just sender + subject line. Grouped by type.

## People & Company Pages

For every new person in emails or calendar:
- Create `vault/people/{slug}.md` if not already there

For every new company (senders, employers):
- Create `vault/business/{slug}.md` if not already there

## Output Files

- Local: `vault/projects/morning-brief/history/YYYY-MM-DD.md`
- Notion: New page in Daily Briefs DB (`collection://9a3e3367-94aa-4733-b828-eb653e6b1adb`)
  - Name: "Brief YYYY-MM-DD"
  - Date, Urgent Count, FYI Count, Calendar Events, Summary (one-liner)

## Notion Resources

- Daily Briefs database: `collection://9a3e3367-94aa-4733-b828-eb653e6b1adb`
- Daily Briefs page: https://app.notion.com/p/c84faecd6c124f0bae92623ecaa73f55
- Personal OS page: https://app.notion.com/p/3b82145568cd814c9c1eeb5ea21e2f3e

## Sprint Board Contract

Mark "Morning Brief" Done on the Automation Sprint Board when built:
- Sprint Board DB: `collection://9a4012bf-a097-4da2-b1d3-05e2f35a8188`
