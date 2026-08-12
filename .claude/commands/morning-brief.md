# /morning-brief — Daily Brief from Gmail, Calendar, and Notion

Pulls unread emails, today's calendar, and relevant Notion context. Filtered through your priorities. Scannable in under 3 minutes.

## Step 1: Load Priorities

Read in order:
1. `soul.md` — current focus areas
2. `vault/me/goals.md` — active goals
3. `brand/config/brand-config.md` — email tier definitions

## Step 2: Pull Gmail (last 12h unread)

```
mcp__claude_ai_Gmail__search_threads
query: "in:inbox is:unread newer_than:12h"
pageSize: 20
```

Classify each email:
- **Urgent**: action needed today (job invites needing response, bank/financial, anything from known contacts)
- **FYI**: status updates, rejections, LinkedIn signals, fintech/AI newsletters
- **Skip**: travel promos, generic job board blasts (Hirist/Foundit), unsubscribe candidates

## Step 3: Pull Calendar

```
mcp__claude_ai_Google_Calendar__list_events
startTime: today 00:00 IST
endTime: today 23:59 IST
orderBy: startTime
```

Format each event: `HH:MM — Event Name (duration)`
Flag: [FOCUS], [SADHANA], [MEETING], [PERSONAL]
Identify deep-work windows (gaps between events >90 min).

## Step 4: Search Notion for Context

```
mcp__claude_ai_Notion__notion-search
query: "optimus leadership AI learning"
page_size: 3
```

Pick the 2-3 most relevant pages. One sentence each: why relevant today.

## Step 5: Classify People and Companies

For every new person in emails or calendar attendees:
- Check if `vault/people/{first-last}.md` exists
- If not, create it with: name, context (where seen), date first seen

For every new company:
- Check if `vault/business/{company-slug}.md` exists
- If not, create it with: name, context, relationship type

## Step 6: Generate Brief

Format:

```
# Morning Brief — YYYY-MM-DD

## Urgent (N)
[sender] — [subject] — ACTION: [what to do]

## Today's Calendar
[time] — [event] [flag] [duration]
...
Deep work windows: [HH:MM–HH:MM]

## Key Context
- [page title]: [why relevant today]
- [page title]: [why relevant today]

## FYI (N)
Job updates: [list]
LinkedIn: [list]
News: [list]
```

## Step 7: Save Local

`vault/projects/morning-brief/history/YYYY-MM-DD.md`

## Step 8: Post to Notion

Create page in Daily Briefs DB (`collection://9a3e3367-94aa-4733-b828-eb653e6b1adb`):
- Name: "Brief YYYY-MM-DD"
- Date: today
- Urgent Count: N
- FYI Count: N
- Calendar Events: N
- Summary: one-line summary

Content: full brief using callout blocks (red for Urgent, blue for Calendar, green for Context, gray for FYI).

## Step 9: Update Log

`vault/log.md`: `## [YYYY-MM-DD HH:MM] /morning-brief | N urgent, N FYI, N calendar events. N new people/companies added to vault.`
